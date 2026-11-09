//! W042: preregistered, cost-inclusive root lookahead against dynamic MOMS.
//! Diagnostic DPLL only. Never promotes an unchecked SAT/UNSAT certificate.

use serde_json::{json, Value};
use std::io::{self, Read};
use std::time::Instant;

#[derive(Clone, Debug)]
struct Formula {
    n: usize,
    clauses: Vec<Vec<i32>>,
}

#[derive(Clone, Debug, Default)]
struct Stats {
    clause_visits: u64,
    nodes: u64,
    decisions: u64,
    unit_assignments: u64,
    probe_calls: u64,
    gate_activations: u64,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Policy {
    Degree,
    Moms,
    Probe,
    GatedProbe,
}

impl Policy {
    const ALL: [Self; 4] = [Self::Degree, Self::Moms, Self::Probe, Self::GatedProbe];

    fn name(self) -> &'static str {
        match self {
            Self::Degree => "degree",
            Self::Moms => "moms",
            Self::Probe => "probe",
            Self::GatedProbe => "gated_probe",
        }
    }
}

#[derive(Debug)]
struct Budget;

fn visit(stats: &mut Stats, cap: u64) -> Result<(), Budget> {
    if stats.clause_visits >= cap {
        return Err(Budget);
    }
    stats.clause_visits += 1;
    Ok(())
}

fn lit_true(lit: i32, assignment: &[i8]) -> bool {
    let v = assignment[lit.unsigned_abs() as usize - 1];
    v >= 0 && (v == 1) == (lit > 0)
}

fn propagate(f: &Formula, assignment: &mut [i8], stats: &mut Stats, cap: u64)
    -> Result<bool, Budget>
{
    loop {
        let mut changed = false;
        for clause in &f.clauses {
            visit(stats, cap)?;
            let (mut free, mut unit, mut satisfied) = (0usize, 0i32, false);
            for &lit in clause {
                let idx = lit.unsigned_abs() as usize - 1;
                if assignment[idx] == -1 {
                    free += 1;
                    unit = lit;
                } else if lit_true(lit, assignment) {
                    satisfied = true;
                    break;
                }
            }
            if satisfied {
                continue;
            }
            if free == 0 {
                return Ok(false);
            }
            if free == 1 {
                let idx = unit.unsigned_abs() as usize - 1;
                let value = if unit > 0 { 1 } else { 0 };
                if assignment[idx] == -1 {
                    assignment[idx] = value;
                    stats.unit_assignments += 1;
                    changed = true;
                }
            }
        }
        if !changed {
            return Ok(true);
        }
    }
}

fn degrees(f: &Formula, stats: &mut Stats, cap: u64) -> Result<Vec<usize>, Budget> {
    let mut counts = vec![0; f.n];
    for clause in &f.clauses {
        visit(stats, cap)?;
        for &lit in clause {
            counts[lit.unsigned_abs() as usize - 1] += 1;
        }
    }
    Ok(counts)
}

fn all_satisfied(f: &Formula, assignment: &[i8], stats: &mut Stats, cap: u64)
    -> Result<bool, Budget>
{
    for clause in &f.clauses {
        visit(stats, cap)?;
        if !clause.iter().any(|&lit| lit_true(lit, assignment)) {
            return Ok(false);
        }
    }
    Ok(true)
}

/// Clause visits are charged once per source clause. Counts arise only from
/// shortest unresolved clauses. Return an empty ranking iff all are satisfied.
fn moms_ranking(f: &Formula, assignment: &[i8], stats: &mut Stats, cap: u64)
    -> Result<Vec<(usize, usize)>, Budget>
{
    let mut open: Vec<Vec<usize>> = Vec::new();
    let mut min_len = usize::MAX;
    for clause in &f.clauses {
        visit(stats, cap)?;
        if clause.iter().any(|&lit| lit_true(lit, assignment)) {
            continue;
        }
        let free: Vec<usize> = clause.iter()
            .map(|lit| lit.unsigned_abs() as usize - 1)
            .filter(|&idx| assignment[idx] == -1)
            .collect();
        if free.is_empty() {
            // propagate() rejects this contradiction before selection.
            return Ok(Vec::new());
        }
        min_len = min_len.min(free.len());
        open.push(free);
    }
    if open.is_empty() {
        return Ok(Vec::new());
    }
    let mut scores = vec![0usize; f.n];
    for row in &open {
        if row.len() == min_len {
            for &idx in row {
                scores[idx] += 1;
            }
        }
    }
    let mut ranking: Vec<(usize, usize)> = (0..f.n)
        .filter(|&idx| assignment[idx] == -1)
        .map(|idx| (idx, scores[idx]))
        .collect();
    ranking.sort_by(|a, b| b.1.cmp(&a.1).then(a.0.cmp(&b.0)));
    Ok(ranking)
}

fn root_choice(
    f: &Formula,
    assignment: &[i8],
    policy: Policy,
    stats: &mut Stats,
    cap: u64,
) -> Result<Option<usize>, Budget> {
    let ranking = moms_ranking(f, assignment, stats, cap)?;
    if ranking.is_empty() {
        return Ok(None);
    }
    if policy == Policy::Moms {
        return Ok(Some(ranking[0].0));
    }
    if policy == Policy::GatedProbe &&
        (ranking.len() < 2 || ranking[0].1.saturating_sub(ranking[1].1) > 1)
    {
        return Ok(Some(ranking[0].0));
    }
    stats.gate_activations += 1;
    let mut best = None;
    for &(idx, moms) in ranking.iter().take(8) {
        let mut gains = [0usize; 2];
        for (side, &value) in [1i8, 0i8].iter().enumerate() {
            let mut trial = assignment.to_vec();
            trial[idx] = value;
            let before = trial.iter().filter(|&&v| v != -1).count();
            stats.probe_calls += 1;
            let consistent = propagate(f, &mut trial, stats, cap)?;
            gains[side] = if consistent {
                trial.iter().filter(|&&v| v != -1).count() - before
            } else {
                f.n + 1
            };
        }
        let key = (gains[0].min(gains[1]), moms);
        if best.is_none_or(|(_, best_key): (usize, (usize, usize))| key > best_key) {
            best = Some((idx, key));
        }
    }
    Ok(Some(best.expect("nonempty ranking").0))
}

fn dpll(
    f: &Formula,
    mut assignment: Vec<i8>,
    policy: Policy,
    degree_order: &[usize],
    root: bool,
    stats: &mut Stats,
    cap: u64,
) -> Result<Option<Vec<i8>>, Budget> {
    stats.nodes += 1;
    if !propagate(f, &mut assignment, stats, cap)? {
        return Ok(None);
    }
    let choice = if policy == Policy::Degree {
        if all_satisfied(f, &assignment, stats, cap)? {
            return Ok(Some(assignment));
        }
        degree_order.iter().copied().find(|&idx| assignment[idx] == -1)
    } else if root {
        root_choice(f, &assignment, policy, stats, cap)?
    } else {
        moms_ranking(f, &assignment, stats, cap)?.first().map(|v| v.0)
    };
    let Some(idx) = choice else {
        return Ok(Some(assignment));
    };
    stats.decisions += 1;
    for value in [1i8, 0i8] {
        let mut branch = assignment.clone();
        branch[idx] = value;
        if let Some(answer) = dpll(f, branch, policy, degree_order, false, stats, cap)? {
            return Ok(Some(answer));
        }
    }
    Ok(None)
}

fn solve(f: &Formula, policy: Policy, cap: u64) -> Value {
    let mut stats = Stats::default();
    let result = (|| {
        let mut degree_order = Vec::new();
        if policy == Policy::Degree {
            let degree = degrees(f, &mut stats, cap)?;
            degree_order = (0..f.n).collect();
            degree_order.sort_by(|&a, &b| degree[b].cmp(&degree[a]).then(a.cmp(&b)));
        }
        dpll(f, vec![-1; f.n], policy, &degree_order, true, &mut stats, cap)
    })();
    let (verdict, assignment) = match result {
        Ok(Some(bits)) => ("SAT", Some(bits)),
        Ok(None) => ("UNSAT", None),
        Err(Budget) => ("CENSORED", None),
    };
    json!({
        "verdict": verdict,
        "assignment": assignment,
        "clause_visits": stats.clause_visits,
        "nodes": stats.nodes,
        "decisions": stats.decisions,
        "unit_assignments": stats.unit_assignments,
        "probe_calls": stats.probe_calls,
        "gate_activations": stats.gate_activations,
    })
}

fn parse_formula(value: &Value) -> Result<(Formula, u64, usize), String> {
    let n = value["nvars"].as_u64().ok_or("missing nvars")? as usize;
    if !(1..=128).contains(&n) {
        return Err("nvars must be between 1 and 128".into());
    }
    let rows = value["clauses"].as_array().ok_or("missing clauses")?;
    if rows.is_empty() {
        return Err("empty source clause list not supported by this diagnostic".into());
    }
    let mut clauses = Vec::with_capacity(rows.len());
    for row in rows {
        let vals = row.as_array().ok_or("non-array clause")?;
        if vals.is_empty() {
            return Err("empty clauses must be handled by source validation".into());
        }
        let mut clause = Vec::with_capacity(vals.len());
        let mut seen = vec![false; n];
        for v in vals {
            let lit = v.as_i64().ok_or("non-integer literal")?;
            if lit == 0 || lit.unsigned_abs() > n as u64 {
                return Err("literal outside nvars".into());
            }
            let idx = lit.unsigned_abs() as usize - 1;
            if seen[idx] {
                return Err("repeated source variable inside a clause".into());
            }
            seen[idx] = true;
            clause.push(lit as i32);
        }
        clauses.push(clause);
    }
    let cap = value["scan_cap"].as_u64().unwrap_or(2_000_000);
    let repeats = value["repeats"].as_u64().unwrap_or(3) as usize;
    if cap == 0 || !(1..=16).contains(&repeats) {
        return Err("invalid scan cap/repeats".into());
    }
    Ok((Formula { n, clauses }, cap, repeats))
}

fn evaluate(f: &Formula, cap: u64, repeats: usize) -> Value {
    let mut records: Vec<Vec<(Value, u128)>> = vec![Vec::new(); Policy::ALL.len()];
    for rep in 0..repeats {
        for offset in 0..Policy::ALL.len() {
            let index = (rep + offset) % Policy::ALL.len();
            let policy = Policy::ALL[index];
            let start = Instant::now();
            let result = solve(f, policy, cap);
            let nanos = start.elapsed().as_nanos();
            records[index].push((result, nanos));
        }
    }
    let mut output = serde_json::Map::new();
    for (i, policy) in Policy::ALL.iter().enumerate() {
        let first = records[i][0].0.clone();
        assert!(records[i].iter().all(|v| v.0 == first), "nondeterministic solver output");
        let mut elapsed: Vec<u128> = records[i].iter().map(|v| v.1).collect();
        elapsed.sort_unstable();
        let middle = elapsed[elapsed.len() / 2];
        let mut result = first;
        result["median_wall_ns"] = json!(middle as u64);
        result["wall_repeats_ns"] = json!(records[i].iter().map(|v| v.1 as u64).collect::<Vec<_>>());
        output.insert(policy.name().into(), result);
    }
    json!({"nvars": f.n, "source_clause_count": f.clauses.len(),
           "scan_cap": cap, "repeats": repeats, "arms": output})
}

fn main() {
    let mut raw = String::new();
    io::stdin().read_to_string(&mut raw).expect("read source JSON");
    let value: Value = serde_json::from_str(&raw).expect("valid source JSON");
    let (formula, cap, repeats) = parse_formula(&value).expect("valid source CNF");
    println!("{}", evaluate(&formula, cap, repeats));
}

#[cfg(test)]
mod tests {
    use super::*;

    fn small(n: usize, clauses: Vec<Vec<i32>>) -> Formula {
        Formula { n, clauses }
    }

    fn truth_sat(f: &Formula) -> bool {
        (0..(1usize << f.n)).any(|bits| {
            f.clauses.iter().all(|clause| clause.iter().any(|&lit| {
                let value = ((bits >> (lit.unsigned_abs() as usize - 1)) & 1) != 0;
                value == (lit > 0)
            }))
        })
    }

    #[test]
    fn fixed_satisfiable_and_unsatisfiable() {
        for f in [small(3, vec![vec![1, 2], vec![-1, 3], vec![-3, 2]]),
                  small(2, vec![vec![1], vec![-1], vec![2]])] {
            let truth = truth_sat(&f);
            for policy in Policy::ALL {
                let r = solve(&f, policy, 2_000_000);
                assert_eq!(r["verdict"], if truth { "SAT" } else { "UNSAT" });
            }
        }
    }

    #[test]
    fn deterministic_randomized_truth_tables() {
        let mut x: u32 = 0x04_20_20_42;
        for _ in 0..320 {
            let n = 2 + (x as usize % 6);
            let mut rows = Vec::new();
            for _ in 0..(3 * n) {
                let mut row = Vec::new();
                let mut seen = vec![false; n];
                for _ in 0..(n.min(3)) {
                    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
                    let mut idx = x as usize % n;
                    while seen[idx] { idx = (idx + 1) % n; }
                    seen[idx] = true;
                    row.push(if x & 0x100 != 0 { -(idx as i32 + 1) } else { idx as i32 + 1 });
                }
                rows.push(row);
            }
            let f = small(n, rows);
            let truth = truth_sat(&f);
            for policy in Policy::ALL {
                let result = solve(&f, policy, 2_000_000);
                assert_eq!(result["verdict"], if truth { "SAT" } else { "UNSAT" });
                if truth {
                    let vals = result["assignment"].as_array().unwrap();
                    assert!(f.clauses.iter().all(|clause| clause.iter().any(|&lit| {
                        let index = lit.unsigned_abs() as usize - 1;
                        vals[index].as_i64().unwrap_or(-1) == if lit > 0 { 1 } else { 0 }
                    })));
                }
            }
        }
    }

    #[test]
    fn cap_and_malformed_inputs_fail_closed() {
        let f = small(3, vec![vec![1, 2, 3], vec![-1, 2, 3]]);
        for policy in Policy::ALL {
            assert_eq!(solve(&f, policy, 1)["verdict"], "CENSORED");
        }
        assert!(parse_formula(&json!({"nvars": 3, "clauses": [[1,-1]]})).is_err());
        assert!(parse_formula(&json!({"nvars": 3, "clauses": [[0]]})).is_err());
        assert!(parse_formula(&json!({"nvars": 3, "clauses": [[4]]})).is_err());
        assert!(parse_formula(&json!({"nvars": 3, "clauses": [[1]], "scan_cap": 0})).is_err());
    }
}
