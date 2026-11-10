//! WU-008: candidate parity-lemma selection, with an exact bounded
//! minimum-weight support oracle. No Boolean assignments are enumerated.
//! A priori lemma cost estimates here are only diagnostic cost proxies.

#[allow(dead_code)]
#[path = "wu006_guarded_xnf_consensus.rs"]
pub(crate) mod core;

#[derive(Clone)]
pub(crate) struct Lemma {
    pub(crate) falsity: u64,
    pub(crate) weight: u32,
}

pub(crate) struct Fixture {
    pub(crate) name: String,
    pub(crate) n: usize,
    pub(crate) f: Vec<u64>,
    pub(crate) original: Vec<Vec<u64>>,
    pub(crate) lemmas: Vec<Lemma>,
}

fn parity_guard_fixture(name: &str, variable_count: usize, edges: &[(usize, usize, bool)]) -> Fixture {
    assert!(variable_count >= 3);
    assert!((2..=12).contains(&edges.len()));
    let n = variable_count + edges.len();
    assert!(n < 62);
    let rhs = 1u64 << n;
    let mut original = Vec::new();
    let mut lemmas = Vec::new();
    for (i, &(u, v, true_rhs)) in edges.iter().enumerate() {
        assert!(u < variable_count && v < variable_count && u != v);
        let falsity = (1u64 << u) | (1u64 << v) | if true_rhs { 0 } else { rhs };
        let guard = 1u64 << (variable_count + i);
        let left = vec![guard | rhs, falsity];
        let right = vec![guard, falsity];
        assert!(core::same_span(&core::semantic_consensus(&left, &right, n + 1)
            .expect("complementary guarded pair must have a consensus"), &[falsity], n + 1));
        original.extend([left, right]);
        // For this exact clause order, independent RUP of lemma i scans
        // 2(i+1) clauses. This is a cheap *fixture-specific* cost proxy;
        // it is not an available performance oracle in general CDCL.
        lemmas.push(Lemma { falsity, weight: 2 * (i as u32 + 1) });
    }
    Fixture { name: name.into(), n,
        f: vec![1 | rhs, 2 | rhs, 4 | rhs], original, lemmas }
}

pub(crate) fn path_with_leaves(length: usize, leaves: usize) -> Fixture {
    let variables = 3 + length - 1 + leaves;
    let nodes: Vec<usize> = std::iter::once(0)
        .chain(3..(3 + length - 1))
        .chain(std::iter::once(1)).collect();
    let mut edges: Vec<(usize, usize, bool)> = nodes.windows(2).enumerate()
        .map(|(i, e)| (e[0], e[1], i + 1 == length)).collect();
    for i in 0..leaves { edges.push((0, 3 + length - 1 + i, false)); }
    parity_guard_fixture(&format!("single-path-{length}-leaves-{leaves}"), variables, &edges)
}

pub(crate) fn parallel_paths(a: usize, b: usize) -> Fixture {
    let variables = 3 + (a - 1) + (b - 1);
    let mut edges = Vec::new();
    for (length, z_start) in [(a, 3), (b, 3 + a - 1)] {
        let nodes: Vec<usize> = std::iter::once(0)
            .chain(z_start..z_start + length - 1)
            .chain(std::iter::once(1)).collect();
        edges.extend(nodes.windows(2).enumerate().map(|(i, e)| {
            (e[0], e[1], i + 1 == length)
        }));
    }
    parity_guard_fixture(&format!("parallel-{a}-{b}"), variables, &edges)
}

fn rng_next(s: &mut u64) -> u64 {
    *s ^= *s << 13;
    *s ^= *s >> 7;
    *s ^= *s << 17;
    *s
}

pub(crate) fn seeded_graph(seed: u64) -> Fixture {
    let mut s = seed.wrapping_mul(0x9e3779b97f4a7c15).wrapping_add(0x1234_5678_9abc_def1);
    let variable_count = 7; // x, y, a, z3, z4, z5, z6
    let mut values = [false; 7];
    values[1] = true; // ensure x XOR y=1
    for z in values.iter_mut().skip(3) { *z = rng_next(&mut s) & 1 != 0; }
    let mut pairs = vec![(0, 3), (3, 4), (4, 1)];
    while pairs.len() < 9 {
        let u = [0, 1, 3, 4, 5, 6][(rng_next(&mut s) % 6) as usize];
        let v = [0, 1, 3, 4, 5, 6][(rng_next(&mut s) % 6) as usize];
        if u == v { continue; }
        let e = (u.min(v), u.max(v));
        if !pairs.iter().any(|&(a, b)| (a.min(b), a.max(b)) == e) {
            pairs.push((u, v));
        }
    }
    let edges: Vec<(usize, usize, bool)> = pairs.into_iter()
        .map(|(u, v)| (u, v, values[u] ^ values[v])).collect();
    parity_guard_fixture(&format!("seeded-graph-{seed}"), variable_count, &edges)
}

pub(crate) fn rank_anchor(f: &[u64], units: &[u64], n: usize) -> Vec<u64> {
    let mut joined = vec![1u64 << n];
    joined.extend(units);
    core::intersect(f, &joined, n + 1)
}

fn selected_rows(lemmas: &[Lemma], mask: usize) -> Vec<u64> {
    lemmas.iter().enumerate().filter_map(|(i, l)| {
        if mask >> i & 1 != 0 { Some(l.falsity) } else { None }
    }).collect()
}

fn preserves_anchor(anchor: &[u64], lemmas: &[Lemma], mask: usize, n: usize) -> bool {
    let mut span = vec![1u64 << n];
    span.extend(selected_rows(lemmas, mask));
    core::contained(anchor, &span, n + 1)
}

fn support_cost(lemmas: &[Lemma], mask: usize) -> u32 {
    lemmas.iter().enumerate().filter(|(i, _)| mask >> i & 1 != 0)
        .map(|(_, l)| l.weight).sum()
}

// Independent leave-one-out essentiality is a *hypothesis*, not a proof
// of completeness: it fails if two redundant supports both suffice.
fn leave_one_out(lemmas: &[Lemma], anchor: &[u64], n: usize) -> (usize, usize) {
    let all = (1usize << lemmas.len()) - 1;
    let mut needed = 0;
    for i in 0..lemmas.len() {
        if !preserves_anchor(anchor, lemmas, all ^ (1 << i), n) { needed |= 1 << i; }
    }
    (needed, lemmas.len())
}

// Standard deletion-based minimal support: always retains the entire
// full-set anchor, but its cost depends on deletion order.
pub(crate) fn deletion_minimize(lemmas: &[Lemma], anchor: &[u64], n: usize, descending_cost: bool)
    -> (usize, usize)
{
    let mut order: Vec<usize> = (0..lemmas.len()).collect();
    if descending_cost {
        order.sort_by_key(|&i| (std::cmp::Reverse(lemmas[i].weight), i));
    }
    let mut kept = (1usize << lemmas.len()) - 1;
    for &i in &order {
        let candidate = kept ^ (1 << i);
        if preserves_anchor(anchor, lemmas, candidate, n) { kept = candidate; }
    }
    (kept, order.len())
}

// Diagnostic exact support oracle, EXPONENTIAL IN NUMBER OF REASONS.
// Enumerates subsets of equations only; never Boolean assignments.
fn exact_min_support(lemmas: &[Lemma], anchor: &[u64], n: usize) -> (usize, usize) {
    assert!(lemmas.len() <= 12);
    let mut best_mask = 0;
    let mut best = (u32::MAX, u32::MAX, usize::MAX);
    let mut calls = 0;
    for mask in 0..1usize << lemmas.len() {
        calls += 1;
        if !preserves_anchor(anchor, lemmas, mask, n) { continue; }
        let candidate = (support_cost(lemmas, mask), mask.count_ones(), mask);
        if candidate < best { best = candidate; best_mask = mask; }
    }
    assert_ne!(best.0, u32::MAX);
    (best_mask, calls)
}

#[derive(Debug)]
#[allow(dead_code)]
struct ResultRow {
    name: String,
    lemmas: usize,
    full_anchor_rank: usize,
    loo_count: usize,
    loo_cost: u32,
    loo_preserves: bool,
    deletion_count: usize,
    deletion_cost: u32,
    weighted_count: usize,
    weighted_cost: u32,
    exact_count: usize,
    exact_cost: u32,
    exact_subsets: usize,
    selected_proof_scans: usize,
    selected_final_rup: usize,
    full_proof_scans: usize,
    full_final_rup: usize,
}

fn evaluate(f: &Fixture) -> ResultRow {
    let all = selected_rows(&f.lemmas, (1 << f.lemmas.len()) - 1);
    let anchor = rank_anchor(&f.f, &all, f.n);
    assert_eq!(anchor.len(), 1, "controlled examples must have one global conflict equation");
    let (loo, _) = leave_one_out(&f.lemmas, &anchor, f.n);
    let (del, _) = deletion_minimize(&f.lemmas, &anchor, f.n, false);
    let (weighted, _) = deletion_minimize(&f.lemmas, &anchor, f.n, true);
    let (exact, exact_subsets) = exact_min_support(&f.lemmas, &anchor, f.n);
    for mask in [del, weighted, exact] {
        assert!(preserves_anchor(&anchor, &f.lemmas, mask, f.n));
    }
    let verify = |mask: usize| -> (usize, usize) {
        let units = selected_rows(&f.lemmas, mask);
        let mut scans = 0;
        let mut premises = f.original.clone();
        for &unit in &units {
            let (valid, work) = core::rup_replay(&[unit], &f.original, f.n);
            assert!(valid, "selected premise lemma requires original-formula proof");
            scans += work;
            premises.push(vec![unit]);
        }
        let candidate_units: Vec<Vec<u64>> = units.iter().map(|&x| vec![x]).collect();
        let candidates = core::unit_global_candidates(&f.f, &candidate_units, f.n + 1);
        let mut cert = 0;
        for h in &candidates {
            let (valid, work) = core::rup_replay(h, &premises, f.n);
            scans += work;
            cert += valid as usize;
        }
        (scans, cert)
    };
    let (selected_proof_scans, selected_final_rup) = verify(weighted);
    let (full_proof_scans, full_final_rup) = verify((1 << f.lemmas.len()) - 1);
    assert_eq!(selected_final_rup, full_final_rup);
    ResultRow { name: f.name.clone(), lemmas: f.lemmas.len(),
        full_anchor_rank: anchor.len(),
        loo_count: loo.count_ones() as usize, loo_cost: support_cost(&f.lemmas, loo),
        loo_preserves: preserves_anchor(&anchor, &f.lemmas, loo, f.n),
        deletion_count: del.count_ones() as usize, deletion_cost: support_cost(&f.lemmas, del),
        weighted_count: weighted.count_ones() as usize,
        weighted_cost: support_cost(&f.lemmas, weighted),
        exact_count: exact.count_ones() as usize, exact_cost: support_cost(&f.lemmas, exact),
        exact_subsets, selected_proof_scans, selected_final_rup,
        full_proof_scans, full_final_rup }
}

fn abstract_weighted_counterexample() -> (u32, u32, usize, usize) {
    // Four equations A,B,A+B+C,C and desired target A+B.
    // Two representations cost 3+3=6 vs 1+4=5.
    // Expensive-first deletion discards C (4) because A,B still work;
    // it consequently misses the globally cheaper alternative.
    let lemmas = vec![
        Lemma { falsity: 1, weight: 3 },
        Lemma { falsity: 2, weight: 3 },
        Lemma { falsity: 1 | 2 | 4, weight: 1 },
        Lemma { falsity: 4, weight: 4 },
    ];
    let target = vec![1 | 2];
    let (greedy, calls) = deletion_minimize(&lemmas, &target, 3, true);
    let (exact, exact_calls) = exact_min_support(&lemmas, &target, 3);
    (support_cost(&lemmas, greedy), support_cost(&lemmas, exact), calls, exact_calls)
}

pub(crate) fn collect_lemmas_from_original(original: &[Vec<u64>], n: usize) -> Vec<Lemma> {
    let mut found: Vec<Lemma> = Vec::new();
    for i in 0..original.len() {
        for j in i + 1..original.len() {
            let Some(lemma) = core::semantic_consensus(&original[i], &original[j], n + 1)
                else { continue; };
            if lemma.len() != 1 || found.iter().any(|old| {
                core::same_span(&[old.falsity], &lemma, n + 1)
            }) { continue; }
            // Fixture-specific proxy: for complementary guard pairs the
            // direct two-clause RUP proof scans up to clause j inclusive.
            // This is NOT a validated cost predictor on arbitrary XNF.
            found.push(Lemma { falsity: lemma[0], weight: (j + 1) as u32 });
        }
    }
    found
}

pub(crate) fn verify_with_chosen(f: &Fixture, selected: &[Lemma]) -> (usize, usize) {
    let mut scans = 0;
    let mut premises = f.original.clone();
    for lemma in selected {
        let (valid, work) = core::rup_replay(&[lemma.falsity], &f.original, f.n);
        assert!(valid);
        scans += work;
        premises.push(vec![lemma.falsity]);
    }
    let candidate_units: Vec<Vec<u64>> = selected.iter().map(|l| vec![l.falsity]).collect();
    let mut certified = 0;
    for h in core::unit_global_candidates(&f.f, &candidate_units, f.n + 1) {
        let (valid, work) = core::rup_replay(&h, &premises, f.n);
        scans += work;
        certified += valid as usize;
    }
    (scans, certified)
}

// Both variants pay the same pairwise semantic-consensus discovery cost.
// Selective additionally pays repeated Gaussian tests; only then can it
// skip proof verification of unwanted intermediate lemmas.
fn runtime_pipeline(f: &Fixture, selective: bool) -> (usize, usize) {
    let lemmas = collect_lemmas_from_original(&f.original, f.n);
    assert_eq!(lemmas.len(), f.lemmas.len());
    let chosen_mask = if selective {
        let all = lemmas.iter().map(|l| l.falsity).collect::<Vec<_>>();
        let anchor = rank_anchor(&f.f, &all, f.n);
        deletion_minimize(&lemmas, &anchor, f.n, true).0
    } else {
        (1usize << lemmas.len()) - 1
    };
    let selected: Vec<Lemma> = lemmas.iter().enumerate().filter_map(|(i, l)| {
        if chosen_mask >> i & 1 != 0 { Some(l.clone()) } else { None }
    }).collect();
    verify_with_chosen(f, &selected)
}

fn median_microseconds<F: Fn() -> (usize, usize)>(op: F, repetitions: usize) -> f64 {
    use std::time::Instant;
    for _ in 0..4 { std::hint::black_box(op()); }
    let mut samples = Vec::new();
    for _ in 0..7 {
        let start = Instant::now();
        for _ in 0..repetitions { std::hint::black_box(op()); }
        samples.push(start.elapsed().as_secs_f64() * 1_000_000. / repetitions as f64);
    }
    samples.sort_by(f64::total_cmp);
    samples[3]
}

fn main() {
    for f in [path_with_leaves(4, 0), path_with_leaves(4, 8),
        parallel_paths(3, 3), parallel_paths(3, 4)] {
        println!("WU-008 {:?}", evaluate(&f));
    }
    println!("WU-008 abstract weighted-crossing witness (greedy_cost, exact_cost, greedy_tests, oracle_tests)={:?}",
        abstract_weighted_counterexample());
    let mut seed_count = 0;
    let mut essential_fail = 0;
    let mut weighted_gap = 0;
    let mut total_gap = 0u64;
    for seed in 0..64 {
        let e = evaluate(&seeded_graph(seed));
        seed_count += 1;
        essential_fail += (!e.loo_preserves) as usize;
        weighted_gap += (e.weighted_cost > e.exact_cost) as usize;
        total_gap += (e.weighted_cost - e.exact_cost) as u64;
    }
    println!("WU-008 64 fixed-seed XOR-graph diagnostics: essential_failures={essential_fail}/{seed_count}, weighted_deletion_above_exact={weighted_gap}/{seed_count}, sum_excess_cost={total_gap}; NO solver speed claim");
    for fixture in [path_with_leaves(4, 0), path_with_leaves(4, 8),
        parallel_paths(3, 3), seeded_graph(17)] {
        println!("WU-008 end-to-end diagnostic parity proof pipeline median us/run: {} all={:.1} selective={:.1} (7 batches ×25 reps, NOT SAT runtime)",
            fixture.name,
            median_microseconds(|| runtime_pipeline(&fixture, false), 25),
            median_microseconds(|| runtime_pipeline(&fixture, true), 25));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn chain_and_connected_leaves_are_trimmed_without_losing_rup() {
        for leaves in [0, 2, 4, 8] {
            let r = evaluate(&path_with_leaves(4, leaves));
            assert!(r.loo_preserves);
            assert_eq!(r.loo_count, 4);
            assert_eq!(r.weighted_count, 4);
            assert_eq!(r.exact_count, 4);
            assert_eq!(r.full_final_rup, 3);
            assert_eq!(r.selected_final_rup, 3);
        }
    }

    #[test]
    fn parallel_paths_defeat_independent_necessity() {
        for f in [parallel_paths(3, 3), parallel_paths(3, 4)] {
            let r = evaluate(&f);
            assert_eq!(r.loo_count, 0);
            assert!(!r.loo_preserves);
            assert_eq!(r.weighted_count, r.exact_count);
            assert_eq!(r.selected_final_rup, 3);
        }
    }

    #[test]
    fn weighted_deletion_is_not_a_general_minimum_cost_algorithm() {
        let (greedy_cost, exact_cost, calls, exact_calls) = abstract_weighted_counterexample();
        assert_eq!((greedy_cost, exact_cost), (6, 5));
        assert_eq!((calls, exact_calls), (4, 16));
    }

    #[test]
    fn fixed_seed_graph_corpus_has_only_certified_selected_final_candidates() {
        for seed in 0..64 {
            let e = evaluate(&seeded_graph(seed));
            assert_eq!(e.full_final_rup, 3);
            assert_eq!(e.selected_final_rup, 3);
            assert!(e.weighted_cost >= e.exact_cost);
            assert_eq!(e.exact_subsets, 512);
        }
    }

    #[test]
    fn whole_pipeline_including_pairwise_discovery_preserves_all_final_certificates() {
        for f in [path_with_leaves(4, 0), path_with_leaves(4, 8),
            parallel_paths(3, 3), seeded_graph(17)] {
            assert_eq!(runtime_pipeline(&f, false).1, 3);
            assert_eq!(runtime_pipeline(&f, true).1, 3);
            let discovered = collect_lemmas_from_original(&f.original, f.n);
            assert_eq!(discovered.len(), f.lemmas.len());
            for (i, lemma) in discovered.iter().enumerate() {
                assert!(core::same_span(&[lemma.falsity], &[f.lemmas[i].falsity], f.n + 1));
                assert_eq!(lemma.weight, f.lemmas[i].weight);
            }
        }
    }
}
