//! WU-007: cost accounting for reusable, proof-certified parity lemmas.
//! Controlled synthetic probes, not production SAT runtime benchmarks.
//! Reuses the independently verified WU-006 GF(2) + RUP diagnostic.

#[allow(dead_code)]
#[path = "wu006_guarded_xnf_consensus.rs"]
mod core;

#[derive(Debug, Clone, Copy)]
enum Family {
    Shared,
    Independent,
    SharedWithDecoyLeaves { leaves: usize },
}

struct Scenario {
    name: String,
    n: usize,
    original: Vec<Vec<u64>>,
    target: Vec<Vec<u64>>,
    // Each target's oracle-relevant original-clause subset.  This is an
    // unrealistically privileged relevance oracle, not a deployable policy.
    relevant: Vec<Vec<Vec<u64>>>,
}

fn add_guarded_edge(clauses: &mut Vec<Vec<u64>>, edge_false: u64, guard: usize, rhs: u64) {
    clauses.push(vec![(1u64 << guard) | rhs, edge_false]);
    clauses.push(vec![1u64 << guard, edge_false]);
}

fn path_clauses(
    edges: usize,
    rhs: u64,
    x: usize,
    y: usize,
    z_start: usize,
    guard_start: usize,
) -> Vec<Vec<u64>> {
    let vertices: Vec<usize> = std::iter::once(x)
        .chain(z_start..z_start + edges - 1)
        .chain(std::iter::once(y))
        .collect();
    let mut clauses = Vec::new();
    for (i, e) in vertices.windows(2).enumerate() {
        let edge_false = (1u64 << e[0]) | (1u64 << e[1]) |
            if i + 1 == edges { 0 } else { rhs };
        add_guarded_edge(&mut clauses, edge_false, guard_start + i, rhs);
    }
    clauses
}

fn scenario(edges: usize, cuts: usize, family: Family) -> Scenario {
    assert!((2..=8).contains(&edges));
    assert!((1..=8).contains(&cuts));
    match family {
        Family::Shared | Family::SharedWithDecoyLeaves { .. } => {
            let leaves = if let Family::SharedWithDecoyLeaves { leaves } = family { leaves } else { 0 };
            let core_n = 2 * edges + 2;
            let n = core_n + cuts - 1 + 2 * leaves;
            assert!(n < 62);
            let rhs = 1u64 << n;
            let path = path_clauses(edges, rhs, 0, 1, 3, edges + 2);
            let mut decoys = Vec::new();
            for i in 0..leaves {
                // Both guards imply x XOR wi=0.  This connects to x, but
                // w_i is unconstrained elsewhere, so it does not strengthen
                // the x/y target relation.
                let w = core_n + cuts - 1 + i;
                let p = core_n + cuts - 1 + leaves + i;
                add_guarded_edge(&mut decoys, 1 | (1 << w) | rhs, p, rhs);
            }
            // Put decoys first, so they cannot be ignored by an artificially
            // favorable clause scan ordering.
            let original = [decoys, path.clone()].concat();
            let mut targets = Vec::new();
            for i in 0..cuts {
                let a = if i == 0 { 2 } else { core_n + i - 1 };
                targets.push(vec![1 | rhs, 2 | rhs, (1 << a) | rhs]);
            }
            Scenario {
                name: format!("{:?}-m{edges}-cuts{cuts}", family),
                n,
                original,
                relevant: vec![path; cuts],
                target: targets,
            }
        }
        Family::Independent => {
            let block = 2 * edges + 2;
            let n = block * cuts;
            assert!(n < 62);
            let rhs = 1u64 << n;
            let mut original = Vec::new();
            let mut targets = Vec::new();
            let mut relevant = Vec::new();
            for j in 0..cuts {
                let off = j * block;
                let path = path_clauses(
                    edges, rhs, off, off + 1, off + 3, off + edges + 2,
                );
                original.extend(path.clone());
                relevant.push(path);
                targets.push(vec![(1 << off) | rhs,
                    (1 << (off + 1)) | rhs,
                    (1 << (off + 2)) | rhs]);
            }
            Scenario { name: format!("independent-m{edges}-cuts{cuts}"), n,
                original, target: targets, relevant }
        }
    }
}

fn prove_units(original: &[Vec<u64>], n: usize) -> (Vec<Vec<u64>>, usize) {
    let f = core::Fixture { n, target: Vec::new(), guarded: original.to_vec() };
    let (units, scans) = core::derive_unit_consensus(&f);
    (units, scans)
}

// This is a genuinely separate count from candidate-generation cost: a
// RUP replay can be expensive even if no solver search is performed.
fn verify_candidates(
    target: &[u64], clauses: &[Vec<u64>], units: &[Vec<u64>], n: usize,
) -> (usize, usize, usize) {
    let proposals = core::unit_global_candidates(target, units, n + 1);
    let oracle = core::exact_hyperplanes(target, n + 1);
    let mut certified = 0;
    let mut scans = 0;
    for h in &proposals {
        assert!(oracle.iter().any(|other| core::same_span(h, other, n + 1)));
        let (valid, work) = core::rup_replay(h, clauses, n);
        certified += valid as usize;
        scans += work;
    }
    (proposals.len(), certified, scans)
}

#[derive(Debug)]
#[allow(dead_code)]
struct Measurement {
    name: String,
    cuts: usize,
    original_clauses: usize,
    derived_lemmas: usize,
    candidate_count: usize,
    certified_count: usize,
    cached_lemma_scans: usize,
    cached_candidate_scans: usize,
    repeated_scans: usize,
    cached_scans: usize,
    oracle_relevant_scans: usize,
    global_oracle_scans: usize,
    global_oracle_certified: usize,
    direct_rup_certified: usize,
}

fn measure(s: &Scenario) -> Measurement {
    let (all_units, lemma_scans) = prove_units(&s.original, s.n);
    let augmented = [s.original.as_slice(), all_units.as_slice()].concat();
    let mut candidate_scans = 0;
    let mut candidate_count = 0;
    let mut certified_count = 0;
    let mut global_oracle_scans = 0;
    let mut global_oracle_certified = 0;
    let mut direct_rup_certified = 0;
    let mut oracle_relevant_scans = 0;
    for (i, target) in s.target.iter().enumerate() {
        let (count, cert, cost) = verify_candidates(target, &augmented, &all_units, s.n);
        candidate_count += count;
        certified_count += cert;
        candidate_scans += cost;
        // Exact rank-three oracle on both original and augmented formula.
        for h in core::exact_hyperplanes(target, s.n + 1) {
            direct_rup_certified += core::rup_replay(&h, &s.original, s.n).0 as usize;
            let (valid, scans) = core::rup_replay(&h, &augmented, s.n);
            global_oracle_certified += valid as usize;
            global_oracle_scans += scans;
        }
        // Best-case relevance oracle: it knows which input clauses to
        // retain for this target. Its proof remains sound for the full
        // formula (proof from a subset), but this relevance oracle is
        // extra information unavailable to our tested algorithm.
        let local = &s.relevant[i];
        let (local_units, local_lemma_scans) = prove_units(local, s.n);
        let local_augmented = [local.as_slice(), local_units.as_slice()].concat();
        let (_, local_certified, local_scans) =
            verify_candidates(target, &local_augmented, &local_units, s.n);
        assert_eq!(local_certified, cert);
        oracle_relevant_scans += local_lemma_scans + local_scans;
    }
    let cuts = s.target.len();
    Measurement {
        name: s.name.clone(), cuts, original_clauses: s.original.len(),
        derived_lemmas: all_units.len(), candidate_count, certified_count,
        cached_lemma_scans: lemma_scans, cached_candidate_scans: candidate_scans,
        repeated_scans: cuts * lemma_scans + candidate_scans,
        cached_scans: lemma_scans + candidate_scans,
        oracle_relevant_scans, global_oracle_scans,
        global_oracle_certified, direct_rup_certified,
    }
}

// Each timed pipeline executes ONLY the relevant construction and proof
// checks. The diagnostic exact oracle, comparison bookkeeping, and tests
// are not part of timed production-like loops.
fn cached_pipeline(s: &Scenario) -> (usize, usize) {
    let (units, lemma_scans) = prove_units(&s.original, s.n);
    let augmented = [s.original.as_slice(), units.as_slice()].concat();
    let mut count = 0;
    let mut scans = lemma_scans;
    for target in &s.target {
        let (_, verified, work) = verify_candidates(target, &augmented, &units, s.n);
        count += verified;
        scans += work;
    }
    (count, scans)
}

fn repeated_pipeline(s: &Scenario) -> (usize, usize) {
    let mut count = 0;
    let mut scans = 0;
    for target in &s.target {
        let (units, lemma_scans) = prove_units(&s.original, s.n);
        let augmented = [s.original.as_slice(), units.as_slice()].concat();
        let (_, verified, work) = verify_candidates(target, &augmented, &units, s.n);
        count += verified;
        scans += lemma_scans + work;
    }
    (count, scans)
}

fn relevance_oracle_pipeline(s: &Scenario) -> (usize, usize) {
    let mut count = 0;
    let mut scans = 0;
    for (target, relevant) in s.target.iter().zip(&s.relevant) {
        let (units, lemma_scans) = prove_units(relevant, s.n);
        let augmented = [relevant.as_slice(), units.as_slice()].concat();
        let (_, verified, work) = verify_candidates(target, &augmented, &units, s.n);
        count += verified;
        scans += lemma_scans + work;
    }
    (count, scans)
}

fn median_microseconds<F: Fn() -> (usize, usize)>(operation: F, repetitions: usize) -> f64 {
    use std::time::Instant;
    for _ in 0..4 { std::hint::black_box(operation()); }
    let mut samples = Vec::new();
    for _ in 0..7 {
        let start = Instant::now();
        for _ in 0..repetitions { std::hint::black_box(operation()); }
        samples.push(start.elapsed().as_secs_f64() * 1_000_000. / repetitions as f64);
    }
    samples.sort_by(f64::total_cmp);
    samples[3]
}

fn main() {
    println!("WU-007 certificate replay counts; no solver-runtime / search-speed claim");
    for cuts in [1, 2, 4, 8] {
        println!("shared {:?}", measure(&scenario(4, cuts, Family::Shared)));
    }
    for cuts in [2, 3, 4, 5] {
        println!("disjoint {:?}", measure(&scenario(3, cuts, Family::Independent)));
    }
    for leaves in [0, 2, 4, 8] {
        println!("decoy {:?}", measure(&scenario(4, 4,
            Family::SharedWithDecoyLeaves { leaves })));
    }
    for benchmark in [
        scenario(4, 8, Family::Shared),
        scenario(3, 5, Family::Independent),
        scenario(4, 4, Family::SharedWithDecoyLeaves { leaves: 8 }),
    ] {
        println!("WU-007 diagnostic Rust proof-pipeline wall-time (median us/run; NOT SAT solver runtime): {} cached={:.1} repeated={:.1} oracle-relevance={:.1}",
            benchmark.name,
            median_microseconds(|| cached_pipeline(&benchmark), 25),
            median_microseconds(|| repeated_pipeline(&benchmark), 25),
            median_microseconds(|| relevance_oracle_pipeline(&benchmark), 25));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shared_verified_lemmas_reduce_repeated_certificate_work_only() {
        for cuts in [1, 2, 4, 8] {
            let result = measure(&scenario(4, cuts, Family::Shared));
            assert_eq!(result.certified_count, 3 * cuts);
            assert_eq!(result.global_oracle_certified, 3 * cuts);
            assert_eq!(result.direct_rup_certified, 0);
            assert_eq!(result.derived_lemmas, 4);
            assert_eq!(result.candidate_count, 3 * cuts);
            assert_eq!(result.repeated_scans - result.cached_scans,
                (cuts - 1) * result.cached_lemma_scans);
        }
    }

    #[test]
    fn shared_global_cache_can_lose_against_relevance_scoping() {
        for cuts in [2, 3, 4, 5] {
            let result = measure(&scenario(3, cuts, Family::Independent));
            assert_eq!(result.certified_count, 3 * cuts);
            assert_eq!(result.derived_lemmas, 3 * cuts);
            assert!(result.cached_scans > result.oracle_relevant_scans);
        }
    }

    #[test]
    fn connected_irrelevant_decoys_do_not_add_certified_hyperplanes() {
        let base = measure(&scenario(4, 4, Family::Shared));
        for leaves in [2, 4, 8] {
            let result = measure(&scenario(4, 4,
                Family::SharedWithDecoyLeaves { leaves }));
            assert_eq!(result.certified_count, base.certified_count);
            assert_eq!(result.global_oracle_certified, base.global_oracle_certified);
            assert_eq!(result.derived_lemmas, 4 + leaves);
            assert!(result.cached_scans > base.cached_scans);
            assert!(result.cached_scans > result.oracle_relevant_scans);
        }
    }

    #[test]
    fn all_proposals_are_exact_oracle_subspaces_and_rup_certified() {
        for s in [scenario(4, 4, Family::Shared),
            scenario(3, 3, Family::Independent),
            scenario(4, 3, Family::SharedWithDecoyLeaves { leaves: 4 })] {
            let r = measure(&s);
            assert_eq!(r.candidate_count, r.certified_count);
            assert_eq!(r.global_oracle_certified, r.certified_count);
        }
    }

    #[test]
    fn independently_executed_pipelines_match_reported_scan_totals() {
        for s in [scenario(4, 8, Family::Shared),
            scenario(3, 5, Family::Independent),
            scenario(4, 4, Family::SharedWithDecoyLeaves { leaves: 8 })] {
            let reported = measure(&s);
            assert_eq!(cached_pipeline(&s), (reported.certified_count, reported.cached_scans));
            assert_eq!(repeated_pipeline(&s), (reported.certified_count, reported.repeated_scans));
            assert_eq!(relevance_oracle_pipeline(&s),
                (reported.certified_count, reported.oracle_relevant_scans));
        }
    }
}
