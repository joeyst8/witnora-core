//! WU-010: controlled amortization of already certified parity clauses
//! over many distinct SAT assumption queries to the *same source CNF*.
//! This is repeated independent DPLL calls plus cached sound lemmas;
//! it is NOT an incremental CDCL implementation or industrial benchmark.

#[allow(dead_code)]
#[path = "wu009_search_integration.rs"]
mod prior;

use prior::previous::{self, Fixture, Lemma};
use std::hint::black_box;
use std::time::Instant;

#[derive(Clone, Copy, Debug)]
enum Mode { Plain, AllCertified, SelectedCertified }

struct Prepared {
    clauses: Vec<Vec<i32>>,
    proof_scans: usize,
    added_cnf: usize,
}

fn prepare(f: &Fixture, mode: Mode) -> Prepared {
    let source = [f.original.as_slice(), &[f.f.clone()]].concat();
    let mut clauses = prior::cnf_from_xnf(&source, f.n);
    let initial = clauses.len();
    let mut proof_scans = 0;
    if !matches!(mode, Mode::Plain) {
        let candidates = previous::collect_lemmas_from_original(&f.original, f.n);
        assert_eq!(candidates.len(), f.lemmas.len());
        let chosen: Vec<Lemma> = if matches!(mode, Mode::SelectedCertified) {
            let rows: Vec<u64> = candidates.iter().map(|l| l.falsity).collect();
            let anchor = previous::rank_anchor(&f.f, &rows, f.n);
            let mask = previous::deletion_minimize(&candidates, &anchor, f.n, true).0;
            candidates.into_iter().enumerate().filter_map(|(i, l)|
                (mask >> i & 1 != 0).then_some(l)).collect()
        } else {
            candidates
        };
        let (scans, checked) = previous::verify_with_chosen(f, &chosen);
        assert_eq!(checked, 3);
        proof_scans = scans;
        let selected: Vec<Vec<u64>> = chosen.iter().map(|l| vec![l.falsity]).collect();
        let final_clauses = previous::core::unit_global_candidates(&f.f, &selected, f.n + 1);
        assert_eq!(final_clauses.len(), 3);
        clauses.extend(prior::cnf_from_xnf(&selected, f.n));
        clauses.extend(prior::cnf_from_xnf(&final_clauses, f.n));
    }
    let added_cnf = clauses.len() - initial;
    Prepared { clauses, proof_scans, added_cnf }
}

fn next_rng(state: &mut u64) -> u64 {
    *state ^= *state << 13;
    *state ^= *state >> 7;
    *state ^= *state << 17;
    *state
}

// Deterministic, distinct assumptions of exactly 3 distinct variables.
// This creates varied SAT *queries*, not separate random formulas and not
// copies of a single repeated query. Never enumerates full CNF assignments.
fn queries(n: usize) -> Vec<Vec<i32>> {
    let limit = n.min(14);
    assert!(limit >= 6);
    let mut all = Vec::new();
    for a in 0..limit {
        for b in a + 1..limit {
            for c in b + 1..limit {
                for signs in 0..8 {
                    all.push([a, b, c].iter().enumerate().map(|(i, &v)| {
                        let lit = v as i32 + 1;
                        if signs >> i & 1 == 1 { lit } else { -lit }
                    }).collect::<Vec<_>>());
                }
            }
        }
    }
    let mut state = 0x5f37_59df_a104_82bc;
    for i in (1..all.len()).rev() {
        let j = (next_rng(&mut state) % (i as u64 + 1)) as usize;
        all.swap(i, j);
    }
    all.truncate(512);
    assert_eq!(all.len(), 512);
    all
}

#[derive(Default, Debug, Clone, Copy)]
struct Accumulated {
    sat: usize,
    nodes: u64,
    scans: u64,
}

fn search_queries(prepared: &Prepared, n: usize, assumption_list: &[Vec<i32>]) -> Accumulated {
    let mut total = Accumulated::default();
    for assumptions in assumption_list {
        let mut cnf = prepared.clauses.clone();
        cnf.extend(assumptions.iter().map(|&lit| vec![lit]));
        let (model, cost) = prior::solve_cnf(&cnf, n);
        total.sat += model.is_some() as usize;
        total.nodes += cost.nodes;
        total.scans += cost.clause_scans;
    }
    total
}

fn full_session(f: &Fixture, mode: Mode, assumption_list: &[Vec<i32>]) -> Accumulated {
    let prepared = prepare(f, mode);
    search_queries(&prepared, f.n, assumption_list)
}

fn median_session_us(f: &Fixture, mode: Mode, query_list: &[Vec<i32>]) -> f64 {
    let repeats = match query_list.len() {
        0..=8 => 24, 9..=32 => 12, 33..=128 => 4, _ => 2,
    };
    for _ in 0..3 { black_box(full_session(f, mode, query_list)); }
    let mut samples = Vec::new();
    for _ in 0..7 {
        let start = Instant::now();
        for _ in 0..repeats { black_box(full_session(f, mode, query_list)); }
        samples.push(start.elapsed().as_secs_f64() * 1e6 / repeats as f64);
    }
    samples.sort_by(f64::total_cmp);
    samples[3]
}

fn sample(f: &Fixture, all_queries: &[Vec<i32>], count: usize) -> [f64; 3] {
    let q = &all_queries[..count];
    let modes = [Mode::Plain, Mode::AllCertified, Mode::SelectedCertified];
    let prepared: Vec<Prepared> = modes.iter().map(|&m| prepare(f, m)).collect();
    let accum: Vec<Accumulated> = prepared.iter()
        .map(|p| search_queries(p, f.n, q)).collect();
    assert_eq!(accum[0].sat, accum[1].sat);
    assert_eq!(accum[1].sat, accum[2].sat);
    let times = std::array::from_fn(|i| median_session_us(f, modes[i], q));
    println!("WU-010 {} queries={} sat={} | scans plain={} all={} selected={} | prep-rup-scans all={} selected={} | learned-cnf all={} selected={} | session median us plain={:.1} all={:.1} selected={:.1}",
        f.name, count, accum[0].sat, accum[0].scans, accum[1].scans,
        accum[2].scans, prepared[1].proof_scans, prepared[2].proof_scans,
        prepared[1].added_cnf, prepared[2].added_cnf,
        times[0], times[1], times[2]);
    times
}

fn main() {
    for f in [previous::path_with_leaves(4, 0), previous::path_with_leaves(4, 8),
              previous::seeded_graph(17), previous::seeded_graph(121)] {
        let q = queries(f.n);
        let mut first_win = [None, None];
        for count in [1, 8, 32, 128, 512] {
            let times = sample(&f, &q, count);
            for i in 0..2 {
                if first_win[i].is_none() && times[i + 1] < times[0] {
                    first_win[i] = Some(count);
                }
            }
        }
        println!("WU-010 {} first observed win among tested sessions: all={:?}, selected={:?} (NONE means no crossover by 512; cannot infer global crossover)",
            f.name, first_win[0], first_win[1]);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;

    #[test]
    fn bank_contains_512_distinct_legal_three_unit_queries() {
        for n in [10, 16, 26] {
            let bank = queries(n);
            let unique: HashSet<_> = bank.iter().cloned().collect();
            assert_eq!(unique.len(), 512);
            assert!(bank.iter().all(|q| q.len() == 3 && q.iter()
                .all(|&lit| lit.unsigned_abs() as usize <= n)));
        }
    }

    #[test]
    fn certified_lemmas_are_reusable_for_512_distinct_assumptions() {
        for f in [previous::path_with_leaves(4, 0), previous::path_with_leaves(4, 8),
                  previous::seeded_graph(17), previous::seeded_graph(121)] {
            let bank = queries(f.n);
            let p = prepare(&f, Mode::Plain);
            let a = prepare(&f, Mode::AllCertified);
            let s = prepare(&f, Mode::SelectedCertified);
            assert!(a.proof_scans >= s.proof_scans);
            for q in bank {
                let mut sat_results = Vec::new();
                for prepared in [&p, &a, &s] {
                    let mut cnf = prepared.clauses.clone();
                    cnf.extend(q.iter().map(|&lit| vec![lit]));
                    sat_results.push(prior::solve_cnf(&cnf, f.n).0.is_some());
                }
                assert!(sat_results.iter().all(|&sat| sat == sat_results[0]));
            }
        }
    }
}
