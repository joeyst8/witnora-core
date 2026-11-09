//! WU-005: falsification of an intrinsic reason-intersection hyperplane
//! proposer against a bounded exact RUP(⊕) oracle. SAT 2026 §8 motivation.
//! No Boolean assignments are enumerated; no scalable SAT claim is made.

fn rank(mut rows: Vec<u64>, width: usize) -> usize {
    let mut r = 0;
    for bit in 0..width {
        if let Some(p) = (r..rows.len()).find(|&i| (rows[i] >> bit) & 1 == 1) {
            rows.swap(r, p);
            for j in (r + 1)..rows.len() {
                if (rows[j] >> bit) & 1 == 1 {
                    rows[j] ^= rows[r];
                }
            }
            r += 1;
        }
    }
    r
}

fn independent(rows: &[u64], width: usize) -> Vec<u64> {
    let mut basis = Vec::new();
    for &row in rows {
        let old = rank(basis.clone(), width);
        basis.push(row);
        if rank(basis.clone(), width) == old {
            basis.pop();
        }
    }
    basis
}

fn contained(small: &[u64], large: &[u64], width: usize) -> bool {
    rank([small, large].concat(), width) == rank(large.to_vec(), width)
}

fn same_span(a: &[u64], b: &[u64], width: usize) -> bool {
    contained(a, b, width) && contained(b, a, width)
}

// Gaussian intersection: find linear dependencies among the two sets of
// columns, then project kernel vectors onto the left coefficient block.
fn intersect(a: &[u64], b: &[u64], width: usize) -> Vec<u64> {
    assert!(width < 63);
    let left = independent(a, width);
    let right = independent(b, width);
    let cols: Vec<u64> = left.iter().chain(&right).copied().collect();
    assert!(cols.len() < 63);
    let mut equations: Vec<u64> = (0..width)
        .map(|bit| cols.iter().enumerate().fold(0, |s, (j, r)| s | (((r >> bit) & 1) << j)))
        .collect();
    let mut pivots = Vec::new();
    let mut next = 0;
    for col in 0..cols.len() {
        if let Some(p) = (next..width).find(|&i| (equations[i] >> col) & 1 == 1) {
            equations.swap(p, next);
            for i in 0..width {
                if i != next && (equations[i] >> col) & 1 == 1 {
                    equations[i] ^= equations[next];
                }
            }
            pivots.push(col);
            next += 1;
        }
    }
    let mut intersection = Vec::new();
    for free in 0..cols.len() {
        if pivots.contains(&free) {
            continue;
        }
        let mut kernel = 1u64 << free;
        for (i, &pivot) in pivots.iter().enumerate() {
            if (equations[i] >> free) & 1 == 1 {
                kernel |= 1 << pivot;
            }
        }
        let row = left.iter().enumerate().fold(0, |s, (i, &r)| {
            if (kernel >> i) & 1 == 1 { s ^ r } else { s }
        });
        intersection.push(row);
    }
    independent(&intersection, width)
}

// Diagnostic oracle: all 2^d-1 hyperplanes of the learned falsity span.
fn exact_hyperplanes(f: &[u64], width: usize) -> Vec<Vec<u64>> {
    let basis = independent(f, width);
    let d = basis.len();
    assert!((2..=10).contains(&d), "bounded oracle, not general search");
    (1..(1usize << d)).map(|functional| {
        let pivot = functional.trailing_zeros() as usize;
        (0..d).filter(|&j| j != pivot)
            .map(|j| if (functional >> j) & 1 == 0 { basis[j] } else { basis[j] ^ basis[pivot] })
            .collect()
    }).collect()
}

// Hypothesis H5: use only source reasons G and their intrinsic K=F∩G.
// If K is a hyperplane, nominate it. If codim_F K = 2, only three
// hyperplanes contain K. Skip all smaller K to enforce ≤3 candidates/reason.
// This set is invariant under changes of generating bases, but may be
// INCOMPLETE. Every candidate still needs a separate RUP(⊕) check.
fn reason_guided(f: &[u64], reasons: &[Vec<u64>], width: usize) -> Vec<Vec<u64>> {
    let basis = independent(f, width);
    let d = basis.len();
    assert!(d >= 2);
    let mut candidates: Vec<Vec<u64>> = Vec::new();
    for reason in reasons {
        let k = intersect(&basis, reason, width);
        extend_candidates(&basis, &k, width, &mut candidates);
    }
    assert!(candidates.len() <= 3 * reasons.len());
    candidates
}

// Enumerate at most three hyperplanes containing an intrinsic anchor K.
// When codim_F(K)>2 we deliberately do not nominate a candidate.
fn extend_candidates(f: &[u64], k: &[u64], width: usize, candidates: &mut Vec<Vec<u64>>) {
    let d = f.len();
    let proposals = if k.len() + 1 == d {
        vec![k.to_vec()]
    } else if k.len() + 2 == d {
        let mut extended = k.to_vec();
        let mut complement = Vec::new();
        for &row in f {
            if !contained(&[row], &extended, width) {
                extended.push(row);
                complement.push(row);
            }
        }
        assert_eq!(complement.len(), 2);
        vec![
            [k, &[complement[0]]].concat(),
            [k, &[complement[1]]].concat(),
            [k, &[complement[0] ^ complement[1]]].concat(),
        ]
    } else {
        Vec::new()
    };
    for h in proposals {
        assert_eq!(rank(h.clone(), width), d - 1);
        if !candidates.iter().any(|old| same_span(old, &h, width)) {
            candidates.push(h);
        }
    }
}

// Research-only k-local extension: allow Gaussian composition of the row
// spans of up to k input reasons, and the constant equation 1.  The subset
// enumeration is in reason count (not Boolean assignments).  This is not
// advertised as a scalable candidate generator.
fn k_local_candidates(f: &[u64], reasons: &[Vec<u64>], width: usize, k: usize) -> Vec<Vec<u64>> {
    assert!(reasons.len() < 20, "bounded diagnostic reason-subset search");
    let basis = independent(f, width);
    let one = 1 << (width - 1);
    let mut candidates = Vec::new();
    for mask in 1usize..(1usize << reasons.len()) {
        if mask.count_ones() as usize > k { continue; }
        let mut joined = vec![one];
        for (i, rows) in reasons.iter().enumerate() {
            if (mask >> i) & 1 == 1 { joined.extend(rows); }
        }
        let anchor = intersect(&basis, &joined, width);
        extend_candidates(&basis, &anchor, width, &mut candidates);
    }
    candidates
}

// Complete-system GF(2) closure for the *unit-parity* fragment only.
// One global intersection uses Gaussian elimination on O(m) rows; there
// is no exponential subset search. Do not apply it to disjunctive XNF
// clauses: those do not each assert all their falsity rows as equations.
fn unit_parity_global_candidates(f: &[u64], reasons: &[Vec<u64>], width: usize) -> Vec<Vec<u64>> {
    assert!(reasons.iter().all(|reason| reason.len() == 1));
    let basis = independent(f, width);
    let one = 1 << (width - 1);
    let mut joined = vec![one];
    for reason in reasons { joined.extend(reason); }
    let anchor = intersect(&basis, &joined, width);
    let mut candidates = Vec::new();
    extend_candidates(&basis, &anchor, width, &mut candidates);
    candidates
}

// Fixed-point parity RUP replay; independent of how candidates are made.
// It returns a certificate-work proxy: number of clause scans, including
// scans for failed candidates. This is NOT solver runtime.
fn rup_replay(start: &[u64], clauses: &[Vec<u64>], n: usize) -> (bool, usize) {
    let width = n + 1;
    let one = 1 << n;
    let mut known = independent(start, width);
    if contained(&[one], &known, width) {
        return (false, 0);
    }
    let mut scans = 0;
    loop {
        let mut changed = false;
        for clause in clauses {
            scans += 1;
            let total = [known.as_slice(), clause.as_slice()].concat();
            if rank(total.clone(), width) != rank(total.clone(), n) {
                continue;
            }
            match rank(total, n) - rank(known.clone(), n) {
                0 => return (true, scans),
                1 => {
                    let falsity = clause.iter().find(|&&row| !contained(&[row], &known, width))
                        .expect("rank-one reason must contain a new row");
                    known.push(*falsity ^ one);
                    changed = true;
                }
                _ => {}
            }
        }
        if !changed {
            return (false, scans);
        }
    }
}

struct Fixture {
    name: &'static str,
    n: usize,
    f: Vec<u64>,
    database: Vec<Vec<u64>>,
}

fn classic_fixture() -> Fixture {
    // WU-004's learned clause C=!x OR !y OR !a, calibrated against
    // an actual one-step affine-resolution proof in that milestone.
    let rhs = 1 << 4;
    let x = 1 | rhs;
    let y = 2 | rhs;
    let a = 4 | rhs;
    let b = 8 | rhs;
    Fixture {
        name: "WU004-CNF-calibration",
        n: 4,
        f: vec![x, y, a],
        database: vec![
            vec![x, a, b ^ rhs], // !x OR !a OR b
            vec![y, b], // !y OR !b
            vec![x, y ^ rhs], // x -> y
            vec![y, x ^ rhs], // y -> x
        ],
    }
}

fn parity_composition_fixture() -> Fixture {
    // Weak sound learned clause has falsity x=1,y=1,a=1. Two native
    // unit parity equations force x XOR y=1 through an auxiliary z:
    //   x XOR z = 0,    y XOR z = 1.
    // Individually each falsity span has zero intersection with F because
    // it contains z; together they refute x XOR y=0. Thus all local K_i=0.
    composition_path_fixture(2)
}

fn composition_path_fixture(edges: usize) -> Fixture {
    assert!((2..=12).contains(&edges));
    let n = edges + 2;
    let rhs = 1u64 << n;
    let vertices: Vec<usize> = std::iter::once(0)
        .chain(3..(edges + 2))
        .chain(std::iter::once(1))
        .collect();
    assert_eq!(vertices.len(), edges + 1);
    let database = vertices.windows(2).enumerate().map(|(i, edge)| {
        // Actual parity equation u XOR v = 0, except the final edge = 1.
        // Clause falsity row flips that right-hand side.
        let falsity_rhs = if i + 1 == edges { 0 } else { rhs };
        vec![(1u64 << edge[0]) | (1u64 << edge[1]) | falsity_rhs]
    }).collect();
    Fixture {
        name: "native-XOR-path-locality-barrier",
        n,
        f: vec![1 | rhs, 2 | rhs, 4 | rhs],
        database,
    }
}

#[derive(Debug, PartialEq, Eq)]
struct Evaluation {
    oracle_proposals: usize,
    oracle_verified: usize,
    oracle_scans: usize,
    guided_proposals: usize,
    guided_verified: usize,
    guided_scans: usize,
    missed_verified: usize,
}

fn evaluate(fixture: &Fixture) -> Evaluation {
    let width = fixture.n + 1;
    let oracle = exact_hyperplanes(&fixture.f, width);
    let guided = reason_guided(&fixture.f, &fixture.database, width);
    let mut oracle_valid = Vec::new();
    let mut oracle_scans = 0;
    for h in &oracle {
        let (valid, scans) = rup_replay(h, &fixture.database, fixture.n);
        oracle_scans += scans;
        if valid { oracle_valid.push(h); }
    }
    let mut guided_valid = Vec::new();
    let mut guided_scans = 0;
    for h in &guided {
        assert!(oracle.iter().any(|candidate| same_span(candidate, h, width)));
        let (valid, scans) = rup_replay(h, &fixture.database, fixture.n);
        guided_scans += scans;
        if valid { guided_valid.push(h); }
    }
    let missed = oracle_valid.iter().filter(|&h| {
        !guided_valid.iter().any(|g| same_span(h, g, width))
    }).count();
    Evaluation {
        oracle_proposals: oracle.len(),
        oracle_verified: oracle_valid.len(),
        oracle_scans,
        guided_proposals: guided.len(),
        guided_verified: guided_valid.len(),
        guided_scans,
        missed_verified: missed,
    }
}

fn main() {
    for fixture in [classic_fixture(), parity_composition_fixture()] {
        let evaluation = evaluate(&fixture);
        println!("WU-005 {}: {:?}", fixture.name, evaluation);
    }
    for edges in 2..=6 {
        let fixture = composition_path_fixture(edges);
        let base = evaluate(&fixture);
        let mut stats = Vec::new();
        for k in 1..=edges {
            let candidates = k_local_candidates(&fixture.f, &fixture.database, fixture.n + 1, k);
            let valid = candidates.iter().filter(|h| rup_replay(h, &fixture.database, fixture.n).0).count();
            stats.push((k, candidates.len(), valid));
        }
        let global = unit_parity_global_candidates(&fixture.f, &fixture.database, fixture.n + 1);
        let global_valid = global.iter().filter(|h| rup_replay(h, &fixture.database, fixture.n).0).count();
        println!("WU-005 XOR path edges={edges}: exact-certified={} k-local (k, proposed, certified)={:?}; global-unit-GF2 proposed={} certified={}", base.oracle_verified, stats, global.len(), global_valid);
    }
    println!("Boundary: local reason intersections are basis-invariant but NOT complete under parity composition.");
    println!("No general complexity or SAT speedup claim; exact oracle is exponential in rank.");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn calibration_recall_and_cost_measured_against_full_oracle() {
        let e = evaluate(&classic_fixture());
        assert_eq!(e.oracle_proposals, 7);
        assert_eq!(e.oracle_verified, 4);
        assert!(e.guided_proposals < e.oracle_proposals);
        assert_eq!(e.guided_verified, 4);
        assert_eq!(e.missed_verified, 0);
    }

    #[test]
    fn composition_adversary_falsifies_completeness() {
        let f = parity_composition_fixture();
        let e = evaluate(&f);
        assert_eq!(e.oracle_proposals, 7);
        assert!(e.oracle_verified >= 1);
        assert_eq!(e.guided_proposals, 0);
        assert_eq!(e.missed_verified, e.oracle_verified);
        let x = 1 | (1 << 4);
        let y = 2 | (1 << 4);
        let a = 4 | (1 << 4);
        let needed = [x ^ y, a]; // intrinsic parity constraint x XOR y=0, plus a=1
        assert!(exact_hyperplanes(&f.f, 5).iter().any(|h| same_span(h, &needed, 5)));
        assert!(rup_replay(&needed, &f.database, 4).0);
    }

    #[test]
    fn every_gauge_of_the_learned_basis_preserves_guided_subspaces() {
        for fixture in [classic_fixture(), parity_composition_fixture()] {
            let reference = reason_guided(&fixture.f, &fixture.database, 5);
            let b = independent(&fixture.f, 5);
            let all: Vec<u64> = (1..8).map(|mask| {
                b.iter().enumerate().fold(0, |acc, (i, &r)| {
                    if (mask >> i) & 1 == 1 { acc ^ r } else { acc }
                })
            }).collect();
            let mut bases = 0;
            for &i in &all {
                for &j in &all {
                    for &k in &all {
                        let alt = [i, j, k];
                        if rank(alt.to_vec(), 5) != 3 { continue; }
                        bases += 1;
                        let produced = reason_guided(&alt, &fixture.database, 5);
                        assert_eq!(reference.len(), produced.len());
                        assert!(reference.iter().all(|h| produced.iter().any(|p| same_span(h, p, 5))));
                    }
                }
            }
            assert_eq!(bases, 168);
        }
    }

    #[test]
    fn standalone_reason_generators_cannot_fake_composition() {
        let f = parity_composition_fixture();
        for reason in &f.database {
            assert!(intersect(&f.f, reason, 5).is_empty());
        }
        // But their two unit equations together imply x XOR y=1.
        let x = 1 | (1 << 4);
        let y = 2 | (1 << 4);
        assert!(rup_replay(&[x ^ y], &f.database, 4).0);
    }

    #[test]
    fn xor_paths_force_unbounded_local_reason_depth() {
        for edges in 2..=6 {
            let fixture = composition_path_fixture(edges);
            let width = fixture.n + 1;
            let one = 1 << fixture.n;
            let basis = independent(&fixture.f, width);
            let implied_difference = (1 | one) ^ (2 | one);
            let exact = exact_hyperplanes(&basis, width);
            let exact_valid = exact.iter().filter(|h| rup_replay(h, &fixture.database, fixture.n).0).count();
            assert_eq!(exact_valid, 3, "path edges={edges}");
            for mask in 1usize..(1usize << edges) {
                let mut joined = vec![one];
                for i in 0..edges {
                    if (mask >> i) & 1 == 1 { joined.extend(&fixture.database[i]); }
                }
                let anchor = intersect(&basis, &joined, width);
                if mask.count_ones() as usize == edges {
                    assert_eq!(anchor.len(), 1);
                    assert!(same_span(&anchor, &[implied_difference], width));
                } else {
                    assert!(anchor.is_empty(), "edges={edges}, proper subset={mask:b}");
                }
            }
            for k in 1..edges {
                assert!(k_local_candidates(&basis, &fixture.database, width, k).is_empty(), "edges={edges} k={k}");
            }
            let complete_depth = k_local_candidates(&basis, &fixture.database, width, edges);
            assert_eq!(complete_depth.len(), 3);
            assert!(complete_depth.iter().all(|h| rup_replay(h, &fixture.database, fixture.n).0));
            let global = unit_parity_global_candidates(&basis, &fixture.database, width);
            assert_eq!(global.len(), exact_valid);
            assert!(global.iter().all(|h| rup_replay(h, &fixture.database, fixture.n).0));
            assert!(global.iter().all(|h| complete_depth.iter().any(|k| same_span(h, k, width))));
        }
    }

    #[test]
    fn pairwise_composition_recovers_two_edges_but_not_three() {
        let two = composition_path_fixture(2);
        let three = composition_path_fixture(3);
        assert_eq!(k_local_candidates(&two.f, &two.database, two.n + 1, 2).len(), 3);
        assert!(k_local_candidates(&three.f, &three.database, three.n + 1, 2).is_empty());
        assert_eq!(k_local_candidates(&three.f, &three.database, three.n + 1, 3).len(), 3);
    }
}
