//! WU-006: semantic two-clause consensus and staged RUP(⊕) proofs.
//! The consensus is a specialization of known Res(⊕)/affine resolution,
//! NOT a new inference rule. No Boolean assignments are enumerated.

fn rank(mut rows: Vec<u64>, width: usize) -> usize {
    let mut r = 0;
    for bit in 0..width {
        if let Some(p) = (r..rows.len()).find(|&i| (rows[i] >> bit) & 1 != 0) {
            rows.swap(r, p);
            for j in r + 1..rows.len() {
                if (rows[j] >> bit) & 1 != 0 { rows[j] ^= rows[r]; }
            }
            r += 1;
        }
    }
    r
}

fn independent(rows: &[u64], width: usize) -> Vec<u64> {
    let mut b = Vec::new();
    for &row in rows {
        let old = b.len();
        b.push(row);
        if rank(b.clone(), width) == old { b.pop(); }
    }
    b
}

fn contained(a: &[u64], b: &[u64], width: usize) -> bool {
    rank([a, b].concat(), width) == rank(b.to_vec(), width)
}

fn same_span(a: &[u64], b: &[u64], width: usize) -> bool {
    contained(a, b, width) && contained(b, a, width)
}

// Kernel of [A|B], projected back to the left span; Gaussian elimination.
fn intersect(a: &[u64], b: &[u64], width: usize) -> Vec<u64> {
    let left = independent(a, width);
    let right = independent(b, width);
    let cols: Vec<u64> = left.iter().chain(&right).copied().collect();
    assert!(cols.len() < 63 && width < 63);
    let mut eqs: Vec<u64> = (0..width).map(|bit| {
        cols.iter().enumerate().fold(0, |row, (j, v)| row | (((v >> bit) & 1) << j))
    }).collect();
    let mut pivots = Vec::new();
    let mut next = 0;
    for col in 0..cols.len() {
        if let Some(p) = (next..width).find(|&i| (eqs[i] >> col) & 1 != 0) {
            eqs.swap(p, next);
            for i in 0..width {
                if i != next && (eqs[i] >> col) & 1 != 0 { eqs[i] ^= eqs[next]; }
            }
            pivots.push(col);
            next += 1;
        }
    }
    let mut intersection = Vec::new();
    for free in 0..cols.len() {
        if pivots.contains(&free) { continue; }
        let mut kernel = 1 << free;
        for (i, &pivot) in pivots.iter().enumerate() {
            if (eqs[i] >> free) & 1 != 0 { kernel |= 1 << pivot; }
        }
        let row = left.iter().enumerate().fold(0, |v, (i, r)| {
            if (kernel >> i) & 1 != 0 { v ^ r } else { v }
        });
        intersection.push(row);
    }
    independent(&intersection, width)
}

// A known, specialized resolution case expressed intrinsically in the
// *falsity subspaces* of the two disjunctive XNF clauses. Each clause has
// exactly one dimension over their intersection, and the independent
// dimensions are complementary modulo that intersection. Their conjunction
// entails the clause whose falsity span is the intersection.
fn semantic_consensus(a: &[u64], b: &[u64], width: usize) -> Option<Vec<u64>> {
    let left = independent(a, width);
    let right = independent(b, width);
    let common = intersect(&left, &right, width);
    if common.len() + 1 != left.len() || common.len() + 1 != right.len() { return None; }
    let one = 1 << (width - 1);
    if !contained(&[one], &[left, right].concat(), width) { return None; }
    if contained(&[one], &common, width) { return None; }
    Some(common)
}

// Independent parity unit-propagation/RUP replay; input rows describe
// falsity of each *whole clause*, not asserted unit equations.
fn rup_replay(start: &[u64], clauses: &[Vec<u64>], n: usize) -> (bool, usize) {
    let width = n + 1;
    let one = 1 << n;
    let mut known = independent(start, width);
    if contained(&[one], &known, width) { return (false, 0); }
    let mut scans = 0;
    loop {
        let mut changed = false;
        for clause in clauses {
            scans += 1;
            let total = [known.as_slice(), clause.as_slice()].concat();
            if rank(total.clone(), width) != rank(total.clone(), n) { continue; }
            match rank(total, n) - rank(known.clone(), n) {
                0 => return (true, scans),
                1 => {
                    let new_falsity = clause.iter().find(|&&row| !contained(&[row], &known, width))
                        .expect("unit consequence has an outside row");
                    known.push(*new_falsity ^ one);
                    changed = true;
                }
                _ => {}
            }
        }
        if !changed { return (false, scans); }
    }
}

fn exact_hyperplanes(f: &[u64], width: usize) -> Vec<Vec<u64>> {
    let b = independent(f, width);
    let d = b.len();
    assert!((2..=10).contains(&d));
    (1..1usize << d).map(|mask| {
        let pivot = mask.trailing_zeros() as usize;
        (0..d).filter(|&j| j != pivot).map(|j| {
            if (mask >> j) & 1 != 0 { b[j] ^ b[pivot] } else { b[j] }
        }).collect()
    }).collect()
}

fn extend_from_anchor(f: &[u64], k: &[u64], width: usize) -> Vec<Vec<u64>> {
    let d = f.len();
    if k.len() + 1 == d { return vec![k.to_vec()]; }
    if k.len() + 2 != d { return vec![]; }
    let mut used = k.to_vec();
    let mut complement = Vec::new();
    for &row in f {
        if !contained(&[row], &used, width) {
            used.push(row);
            complement.push(row);
        }
    }
    assert_eq!(complement.len(), 2);
    vec![
        [k, &[complement[0]]].concat(),
        [k, &[complement[1]]].concat(),
        [k, &[complement[0] ^ complement[1]]].concat(),
    ]
}

// Whole-system Gaussian closure is valid *only* for proved unit clauses.
fn unit_global_candidates(f: &[u64], units: &[Vec<u64>], width: usize) -> Vec<Vec<u64>> {
    assert!(units.iter().all(|u| u.len() == 1));
    let basis = independent(f, width);
    let mut joined = vec![1 << (width - 1)];
    for unit in units { joined.extend(unit); }
    let anchor = intersect(&basis, &joined, width);
    extend_from_anchor(&basis, &anchor, width)
}

struct Fixture {
    n: usize,
    target: Vec<u64>,
    guarded: Vec<Vec<u64>>,
}

fn guarded_path(edges: usize) -> Fixture {
    assert!((2..=12).contains(&edges));
    let n = 2 * edges + 2;
    let rhs = 1u64 << n;
    let vertices: Vec<usize> = std::iter::once(0)
        .chain(3..(edges + 2))
        .chain(std::iter::once(1))
        .collect();
    let mut guarded = Vec::new();
    for (i, edge) in vertices.windows(2).enumerate() {
        let edge_false = (1 << edge[0]) | (1 << edge[1]) |
            if i + 1 == edges { 0 } else { rhs };
        let guard = 1 << (edges + 2 + i);
        // (p=0 OR edge_true) AND (p=1 OR edge_true).
        guarded.push(vec![guard | rhs, edge_false]);
        guarded.push(vec![guard, edge_false]);
    }
    Fixture { n, target: vec![1 | rhs, 2 | rhs, 4 | rhs], guarded }
}

fn derive_unit_consensus(fixture: &Fixture) -> (Vec<Vec<u64>>, usize) {
    let mut lemmas: Vec<Vec<u64>> = Vec::new();
    let mut scans = 0;
    for i in 0..fixture.guarded.len() {
        for j in i + 1..fixture.guarded.len() {
            let Some(k) = semantic_consensus(&fixture.guarded[i], &fixture.guarded[j], fixture.n + 1)
                else { continue; };
            if k.len() != 1 || lemmas.iter().any(|old| same_span(old, &k, fixture.n + 1)) {
                continue;
            }
            // Verify with original premises, not with candidate-generation logic.
            let (valid, work) = rup_replay(&k, &fixture.guarded, fixture.n);
            scans += work;
            assert!(valid, "a purported consensus lemma must be independently RUP-certified");
            lemmas.push(k);
        }
    }
    (lemmas, scans)
}

#[derive(Debug)]
#[allow(dead_code)] // All fields are reported in Debug output and/or tests.
struct Score {
    original_rup: usize,
    stage2_rup: usize,
    exact_hyperplanes: usize,
    derived_unit_lemmas: usize,
    lemma_scans: usize,
    original_candidate_scans: usize,
    augmented_candidate_scans: usize,
}

fn score(fixture: &Fixture) -> Score {
    let width = fixture.n + 1;
    let exact = exact_hyperplanes(&fixture.target, width);
    let mut original_rup = 0;
    let mut original_candidate_scans = 0;
    for h in &exact {
        let (valid, scans) = rup_replay(h, &fixture.guarded, fixture.n);
        original_rup += valid as usize;
        original_candidate_scans += scans;
    }
    let (lemmas, lemma_scans) = derive_unit_consensus(fixture);
    let augmented = [fixture.guarded.as_slice(), lemmas.as_slice()].concat();
    let candidates = unit_global_candidates(&fixture.target, &lemmas, width);
    let mut augmented_candidate_scans = 0;
    let mut stage2_rup = 0;
    for h in candidates {
        assert!(exact.iter().any(|old| same_span(old, &h, width)));
        let (valid, scans) = rup_replay(&h, &augmented, fixture.n);
        stage2_rup += valid as usize;
        augmented_candidate_scans += scans;
    }
    Score { original_rup, stage2_rup, exact_hyperplanes: exact.len(),
        derived_unit_lemmas: lemmas.len(), lemma_scans,
        original_candidate_scans, augmented_candidate_scans }
}

// In an *unsound* naive method, one might incorrectly treat the E parts
// of (p=0 OR E1) and (p=1 OR E2) as asserted equations E1 and E2.
// Here these disjunctive clauses can hold with E1=false; no global unit
// closure is allowed. One explicit model suffices to refute the inference.
fn split_guard_counterexample() -> Fixture {
    let n = 5;
    let rhs = 1 << n;
    let xz_false = 1 | 8 | rhs; // E1: x XOR z = 0
    let yz_false = 2 | 8;       // E2: y XOR z = 1
    let guard = 16;
    Fixture { n, target: vec![1 | rhs, 2 | rhs, 4 | rhs],
        guarded: vec![vec![guard | rhs, xz_false], vec![guard, yz_false]] }
}

#[cfg(test)]
fn equation_holds(row: u64, assignment: u64, n: usize) -> bool {
    (((row & ((1 << n) - 1)) & assignment).count_ones() + ((row >> n) & 1) as u32) % 2 == 0
}

#[cfg(test)]
fn clause_holds(clause_falsity: &[u64], assignment: u64, n: usize) -> bool {
    !clause_falsity.iter().all(|&row| equation_holds(row, assignment, n))
}

fn main() {
    for m in 2..=6 {
        println!("WU-006 guarded-XNF path m={m}: {:?}", score(&guarded_path(m)));
    }
    let bad = split_guard_counterexample();
    println!("WU-006 split-guard counterexample: consensus={:?}, naive global closure unsound; no Boolean assignment enumeration",
        semantic_consensus(&bad.guarded[0], &bad.guarded[1], bad.n + 1));
    println!("Certificate distinction: direct RUP vs staged RUP with individually certified intermediate lemmas.");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn guarded_xnf_requires_staged_proof() {
        for m in 2..=6 {
            let f = guarded_path(m);
            let s = score(&f);
            assert_eq!(s.exact_hyperplanes, 7);
            assert_eq!(s.original_rup, 0, "direct original-formula RUP m={m}");
            assert_eq!(s.derived_unit_lemmas, m);
            assert_eq!(s.stage2_rup, 3, "with logged unit lemmas m={m}");
        }
    }

    #[test]
    fn each_semantic_pair_is_independently_rup_certified() {
        for m in 2..=6 {
            let f = guarded_path(m);
            for i in 0..m {
                let a = &f.guarded[2 * i];
                let b = &f.guarded[2 * i + 1];
                let derived = semantic_consensus(a, b, f.n + 1).unwrap();
                assert_eq!(derived.len(), 1);
                assert!(rup_replay(&derived, &[a.clone(), b.clone()], f.n).0);
            }
        }
    }

    #[test]
    fn consensus_respects_all_gauges_of_a_two_dimensional_clause_pair() {
        let f = guarded_path(2);
        for edge in 0..2 {
            let a = &f.guarded[edge * 2];
            let b = &f.guarded[edge * 2 + 1];
            let reference = semantic_consensus(a, b, f.n + 1).unwrap();
            let basis_variants = |rows: &[u64]| -> Vec<Vec<u64>> {
                let u = rows[0];
                let v = rows[1];
                vec![vec![u, v], vec![v, u], vec![u, u ^ v],
                    vec![u ^ v, u], vec![v, u ^ v], vec![u ^ v, v]]
            };
            for alt_a in basis_variants(a) {
                for alt_b in basis_variants(b) {
                    let result = semantic_consensus(&alt_a, &alt_b, f.n + 1).unwrap();
                    assert!(same_span(&result, &reference, f.n + 1));
                    assert!(rup_replay(&result, &[alt_a.clone(), alt_b.clone()], f.n).0);
                }
            }
        }
    }

    #[test]
    fn splitting_the_guard_makes_naive_globalization_unsound() {
        let f = split_guard_counterexample();
        assert!(semantic_consensus(&f.guarded[0], &f.guarded[1], f.n + 1).is_none());
        // Model x=y=a=1, z=0, p=0 satisfies both disjunctions, but
        // falsifies the proposed target (and its rank-two strengthenings).
        let witness = 1 | 2 | 4;
        assert!(f.guarded.iter().all(|c| clause_holds(c, witness, f.n)));
        assert!(f.target.iter().all(|&row| equation_holds(row, witness, f.n)));
        assert!(exact_hyperplanes(&f.target, f.n + 1).iter().all(|h| {
            h.iter().all(|&row| equation_holds(row, witness, f.n))
        }));
        // Individual E1/E2 are not logically asserted by their guards.
        let bad_units = vec![vec![1 | 8 | (1 << f.n)], vec![2 | 8]];
        assert_eq!(unit_global_candidates(&f.target, &bad_units, f.n + 1).len(), 3);
        assert!(exact_hyperplanes(&f.target, f.n + 1).iter().all(|h| {
            !rup_replay(h, &f.guarded, f.n).0
        }));
    }

    #[test]
    fn semantically_equivalent_guard_clause_has_same_consensus() {
        let f = guarded_path(3);
        let a = &f.guarded[0];
        let b = &f.guarded[1];
        let alt_a = vec![a[0] ^ a[1], a[1]];
        let alt_b = vec![b[0], b[0] ^ b[1]];
        assert!(!alt_a.contains(&a[0]));
        assert!(!alt_b.contains(&b[1]));
        let original = semantic_consensus(a, b, f.n + 1).unwrap();
        let changed = semantic_consensus(&alt_a, &alt_b, f.n + 1).unwrap();
        assert!(same_span(&original, &changed, f.n + 1));
    }

    #[test]
    fn every_rank_two_xnf_clause_pair_with_consensus_is_rup_sound_in_three_variables() {
        // Exhaustively enumerate rank-2 *equation subspaces* over the
        // 4-dimensional augmented GF(2) space, not Boolean assignments.
        let n = 3;
        let width = n + 1;
        let one = 1 << n;
        let mut spaces: Vec<Vec<u64>> = Vec::new();
        for u in 1..(1 << width) {
            for v in (u + 1)..(1 << width) {
                let pair = vec![u, v];
                if contained(&[one], &pair, width) { continue; }
                if !spaces.iter().any(|old| same_span(old, &pair, width)) {
                    spaces.push(pair);
                }
            }
        }
        assert_eq!(spaces.len(), 28, "rank-2 consistent equation subspaces");
        let mut applicable = 0;
        for (i, a) in spaces.iter().enumerate() {
            for b in spaces.iter().skip(i + 1) {
                if let Some(lemma) = semantic_consensus(a, b, width) {
                    applicable += 1;
                    assert_eq!(lemma.len(), 1);
                    assert!(rup_replay(&lemma, &[a.clone(), b.clone()], n).0,
                        "sound two-clause entailment must have a short RUP proof");
                }
            }
        }
        assert_eq!(applicable, 42, "all applicable semantic-consensus pairs");
    }
}
