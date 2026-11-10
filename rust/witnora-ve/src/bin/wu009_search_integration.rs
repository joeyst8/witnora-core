//! WU-009: actual SAT-search gate for independently certified parity lemmas.
//! This is an explicitly small, unoptimized DPLL reference, NOT CDCL or Xorcle.
//! Measurements include all lemma discovery, selection, proof and CNF costs.

#[allow(dead_code)]
#[path = "wu008_counterfactual_support.rs"]
mod previous;

use previous::{Fixture, Lemma};
use std::hint::black_box;
use std::time::Instant;

#[derive(Clone, Copy, Debug)]
enum Mode { Plain, AllCertified, SelectedCertified }

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
struct SearchCost {
    nodes: u64,
    decisions: u64,
    propagations: u64,
    clause_scans: u64,
}

#[derive(Debug)]
struct Run {
    sat: bool,
    cost: SearchCost,
    proof_scans: usize,
    learned_cnf: usize,
}

// Truth-table conversion is bounded by the *local* clause support, never
// the global formula's assignment space. Forbidding a falsifying local
// assignment produces a standard CNF clause. All test supports have <=3 vars.
fn xnf_clause_to_cnf(rows: &[u64], n: usize) -> Vec<Vec<i32>> {
    assert!(n < 61);
    let variable_mask = (1u64 << n) - 1;
    let support = rows.iter().fold(0u64, |acc, &row| acc | (row & variable_mask));
    let variables: Vec<usize> = (0..n).filter(|&v| support >> v & 1 != 0).collect();
    assert!(variables.len() <= 8, "WU-009 only encodes bounded local XNF clauses");
    let mut clauses = Vec::new();
    for bits in 0..1usize << variables.len() {
        let assignment = variables.iter().enumerate().fold(0u64, |acc, (j, &v)| {
            acc | (((bits >> j & 1) as u64) << v)
        });
        if rows.iter().all(|&r| ((r & assignment).count_ones() as usize
            + ((r >> n & 1) as usize)) % 2 == 0)
        {
            clauses.push(variables.iter().enumerate().map(|(j, &v)| {
                let id = (v + 1) as i32;
                if bits >> j & 1 == 1 { -id } else { id }
            }).collect());
        }
    }
    clauses
}

fn cnf_from_xnf(clauses: &[Vec<u64>], n: usize) -> Vec<Vec<i32>> {
    clauses.iter().flat_map(|c| xnf_clause_to_cnf(c, n)).collect()
}

fn true_literal(lit: i32, value: i8) -> bool {
    value >= 0 && (value == 1) == (lit > 0)
}

// Full, instrumented DPLL search with Boolean unit propagation.
// No cached search results, oracle calls, or parity-specific search code.
fn solve_cnf(clauses: &[Vec<i32>], n: usize) -> (Option<Vec<i8>>, SearchCost) {
    let mut degree = vec![0usize; n];
    for clause in clauses {
        for &lit in clause {
            let variable = lit.unsigned_abs() as usize - 1;
            assert!(variable < n);
            degree[variable] += 1;
        }
    }
    let mut order: Vec<usize> = (0..n).collect();
    order.sort_by_key(|&v| (std::cmp::Reverse(degree[v]), v));

    fn recurse(clauses: &[Vec<i32>], order: &[usize], mut values: Vec<i8>,
        cost: &mut SearchCost) -> Option<Vec<i8>>
    {
        cost.nodes += 1;
        loop {
            let mut changed = false;
            for clause in clauses {
                cost.clause_scans += 1;
                let mut open = 0;
                let mut last = 0;
                let mut satisfied = false;
                for &lit in clause {
                    let v = values[lit.unsigned_abs() as usize - 1];
                    if true_literal(lit, v) { satisfied = true; break; }
                    if v < 0 { open += 1; last = lit; }
                }
                if satisfied { continue; }
                if open == 0 { return None; }
                if open == 1 {
                    let index = last.unsigned_abs() as usize - 1;
                    let wanted = if last > 0 { 1 } else { 0 };
                    if values[index] >= 0 && values[index] != wanted { return None; }
                    if values[index] < 0 {
                        values[index] = wanted;
                        cost.propagations += 1;
                        changed = true;
                    }
                }
            }
            if !changed { break; }
        }
        let mut all_satisfied = true;
        for clause in clauses {
            cost.clause_scans += 1;
            if !clause.iter().any(|&lit| true_literal(lit,
                values[lit.unsigned_abs() as usize - 1]))
            {
                all_satisfied = false;
                break;
            }
        }
        if all_satisfied { return Some(values); }
        let variable = *order.iter().find(|&&v| values[v] < 0)
            .expect("an unresolved, nonconflicting clause has a free literal");
        cost.decisions += 1;
        for chosen in [0, 1] {
            let mut next = values.clone();
            next[variable] = chosen;
            if let Some(model) = recurse(clauses, order, next, cost) { return Some(model); }
        }
        None
    }
    let mut cost = SearchCost::default();
    let model = recurse(clauses, &order, vec![-1; n], &mut cost);
    if let Some(values) = &model {
        assert!(clauses.iter().all(|c| c.iter().any(|&lit| {
            true_literal(lit, values[lit.unsigned_abs() as usize - 1])
        })), "returned model must satisfy every CNF clause");
    }
    (model, cost)
}

// Independent Boolean-CNF RUP cross-check, used in tests; it does not use
// the GF(2)/XNF RUP code that nominated or accepted the parity conclusions.
// RUP asks whether unit propagation of CNF + negated candidate conflicts.
fn cnf_rup(clauses: &[Vec<i32>], candidate: &[i32], n: usize) -> bool {
    let mut values = vec![-1i8; n];
    for &lit in candidate {
        let index = lit.unsigned_abs() as usize - 1;
        let wanted = if lit > 0 { 0 } else { 1 };
        if values[index] >= 0 && values[index] != wanted { return true; }
        values[index] = wanted;
    }
    loop {
        let mut changed = false;
        for clause in clauses {
            let mut open = 0;
            let mut last = 0;
            let mut satisfied = false;
            for &lit in clause {
                let value = values[lit.unsigned_abs() as usize - 1];
                if true_literal(lit, value) { satisfied = true; break; }
                if value < 0 { open += 1; last = lit; }
            }
            if satisfied { continue; }
            if open == 0 { return true; }
            if open == 1 {
                let index = last.unsigned_abs() as usize - 1;
                let wanted = if last > 0 { 1 } else { 0 };
                if values[index] >= 0 && values[index] != wanted { return true; }
                if values[index] < 0 {
                    values[index] = wanted;
                    changed = true;
                }
            }
        }
        if !changed { return false; }
    }
}

fn prepare_and_solve(f: &Fixture, assumptions: &[i32], mode: Mode) -> Run {
    let mut source = f.original.clone();
    source.push(f.f.clone());
    let mut cnf = cnf_from_xnf(&source, f.n);
    for &lit in assumptions { cnf.push(vec![lit]); }
    let original_cnf = cnf.clone();
    let mut proof_scans = 0;
    if !matches!(mode, Mode::Plain) {
        // Nomination uses only previously established semantic consensus.
        let candidates = previous::collect_lemmas_from_original(&f.original, f.n);
        assert_eq!(candidates.len(), f.lemmas.len());
        let chosen: Vec<Lemma> = if matches!(mode, Mode::SelectedCertified) {
            let rows: Vec<u64> = candidates.iter().map(|l| l.falsity).collect();
            let anchor = previous::rank_anchor(&f.f, &rows, f.n);
            let mask = previous::deletion_minimize(&candidates, &anchor, f.n, true).0;
            candidates.iter().enumerate().filter_map(|(i, l)|
                if mask >> i & 1 != 0 { Some(l.clone()) } else { None }).collect()
        } else {
            candidates
        };
        // Verify every chosen lemma against the original premises; then
        // verify every final XNF consequence against the extended premises.
        let (scans, certified) = previous::verify_with_chosen(f, &chosen);
        proof_scans = scans;
        assert_eq!(certified, 3);
        let units: Vec<Vec<u64>> = chosen.iter().map(|l| vec![l.falsity]).collect();
        let final_lemmas = previous::core::unit_global_candidates(&f.f, &units, f.n + 1);
        assert_eq!(final_lemmas.len(), certified);
        cnf.extend(cnf_from_xnf(&units, f.n));
        cnf.extend(cnf_from_xnf(&final_lemmas, f.n));
    }
    let learned_cnf = cnf.len() - original_cnf.len();
    let (model, cost) = solve_cnf(&cnf, f.n);
    if let Some(values) = &model {
        // The reported result is checked against the *unaugmented* CNF.
        assert!(original_cnf.iter().all(|c| c.iter().any(|&lit|
            true_literal(lit, values[lit.unsigned_abs() as usize - 1]))));
    }
    Run { sat: model.is_some(), cost, proof_scans, learned_cnf }
}

fn timing_us(f: &Fixture, assumptions: &[i32], mode: Mode) -> f64 {
    for _ in 0..3 { black_box(prepare_and_solve(f, assumptions, mode)); }
    let mut measurements = Vec::new();
    for _ in 0..7 {
        let start = Instant::now();
        for _ in 0..12 { black_box(prepare_and_solve(f, assumptions, mode)); }
        measurements.push(start.elapsed().as_secs_f64() * 1e6 / 12.0);
    }
    measurements.sort_by(f64::total_cmp);
    measurements[3]
}

fn report(f: &Fixture, assumptions: &[i32], label: &str) -> [f64; 3] {
    let modes = [Mode::Plain, Mode::AllCertified, Mode::SelectedCertified];
    let runs: Vec<Run> = modes.iter().map(|&mode| prepare_and_solve(f, assumptions, mode)).collect();
    assert_eq!(runs[0].sat, runs[1].sat);
    assert_eq!(runs[1].sat, runs[2].sat);
    let times = std::array::from_fn(|i| timing_us(f, assumptions, modes[i]));
    println!("WU-009 {} {} sat={} | plain nodes={} scans={} | all nodes={} scans={} proof={} extra_cnf={} | selected nodes={} scans={} proof={} extra_cnf={} | full-pipeline medians_us plain={:.1} all={:.1} selected={:.1}",
        f.name, label, runs[0].sat, runs[0].cost.nodes, runs[0].cost.clause_scans,
        runs[1].cost.nodes, runs[1].cost.clause_scans, runs[1].proof_scans, runs[1].learned_cnf,
        runs[2].cost.nodes, runs[2].cost.clause_scans, runs[2].proof_scans, runs[2].learned_cnf,
        times[0], times[1], times[2]);
    times
}

fn main() {
    for f in [previous::path_with_leaves(4, 0), previous::path_with_leaves(4, 8),
              previous::parallel_paths(3, 3), previous::seeded_graph(17)] {
        report(&f, &[-1, 2], "SAT x0/y1");
        report(&f, &[1, 2], "UNSAT x1/y1");
    }
    let mut wins_all = 0;
    let mut wins_selected = 0;
    let mut slowdown_all = 0.;
    let mut slowdown_selected = 0.;
    for seed in 100..116 {
        let f = previous::seeded_graph(seed);
        let timing = report(&f, &[1, 2], "held-out UNSAT");
        wins_all += (timing[1] < timing[0]) as usize;
        wins_selected += (timing[2] < timing[0]) as usize;
        slowdown_all += timing[1] / timing[0];
        slowdown_selected += timing[2] / timing[0];
    }
    println!("WU-009 held-out 16 UNSAT seeds: total-runtime wins vs plain: all={wins_all}/16 selected={wins_selected}/16; mean case slowdown ratio all={:.2}x selected={:.2}x. Prototype DPLL only; NO CDCL or industrial claim.",
        slowdown_all / 16., slowdown_selected / 16.);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn local_xnf_translation_matches_simple_guard_and_parity_equations() {
        let n = 3;
        let rhs = 1u64 << n;
        // x=y (falsity x^y^1), with a complementary guard.
        let f = [vec![4 | rhs, 1 | 2 | rhs], vec![4, 1 | 2 | rhs]];
        let cnf = cnf_from_xnf(&f, n);
        let all = [vec![1 | 2 | rhs]];
        let learned = cnf_from_xnf(&all, n);
        for x in 0..2 {
            for y in 0..2 {
                for p in 0..2 {
                    let assignment = [x, y, p];
                    let eval = |clauses: &[Vec<i32>]| clauses.iter().all(|clause| clause.iter().any(|&lit| {
                        true_literal(lit, assignment[lit.unsigned_abs() as usize - 1])
                    }));
                    assert_eq!(eval(&cnf), x == y);
                    assert_eq!(eval(&learned), x == y);
                }
            }
        }
    }

    #[test]
    fn certificate_insertion_never_changes_sat_status_on_fixed_corpus() {
        for f in [previous::path_with_leaves(4, 0), previous::path_with_leaves(4, 8),
                  previous::parallel_paths(3, 3), previous::seeded_graph(17)] {
            for (assumptions, sat) in [([-1, 2], true), ([1, 2], false)] {
                for mode in [Mode::Plain, Mode::AllCertified, Mode::SelectedCertified] {
                    let result = prepare_and_solve(&f, &assumptions, mode);
                    assert_eq!(result.sat, sat, "{} mode={mode:?}", f.name);
                    if !matches!(mode, Mode::Plain) {
                        assert_eq!(result.proof_scans > 0, true);
                        assert!(result.learned_cnf >= 6);
                    }
                }
            }
        }
    }

    #[test]
    fn fresh_graphs_have_agreeing_outcomes_with_and_without_certificates() {
        for seed in 100..132 {
            let f = previous::seeded_graph(seed);
            for assumptions in [[-1, 2], [1, 2]] {
                let baseline = prepare_and_solve(&f, &assumptions, Mode::Plain);
                assert_eq!(baseline.sat, assumptions == [-1, 2]);
                assert_eq!(baseline.sat, prepare_and_solve(&f, &assumptions, Mode::AllCertified).sat);
                assert_eq!(baseline.sat, prepare_and_solve(&f, &assumptions, Mode::SelectedCertified).sat);
            }
        }
    }

    #[test]
    fn independent_boolean_rup_checks_every_staged_encoded_lemma() {
        for f in [previous::path_with_leaves(4, 0), previous::path_with_leaves(4, 8),
                  previous::parallel_paths(3, 3), previous::seeded_graph(17)] {
            let candidates = previous::collect_lemmas_from_original(&f.original, f.n);
            let anchor = previous::rank_anchor(&f.f,
                &candidates.iter().map(|l| l.falsity).collect::<Vec<_>>(), f.n);
            let mask = previous::deletion_minimize(&candidates, &anchor, f.n, true).0;
            for chosen in [candidates.clone(), candidates.iter().enumerate()
                .filter_map(|(i, lemma)| (mask >> i & 1 != 0).then_some(lemma.clone()))
                .collect::<Vec<_>>()]
            {
                let mut cnf = cnf_from_xnf(&f.original, f.n);
                let units: Vec<Vec<u64>> = chosen.iter().map(|l| vec![l.falsity]).collect();
                let final_clauses = previous::core::unit_global_candidates(&f.f, &units, f.n + 1);
                for learned in units.iter().chain(final_clauses.iter()) {
                    for new_clause in xnf_clause_to_cnf(learned, f.n) {
                        assert!(cnf_rup(&cnf, &new_clause, f.n),
                            "{}: staged Boolean-CNF RUP must certify every encoded clause", f.name);
                        cnf.push(new_clause);
                    }
                }
            }
        }
    }
}
