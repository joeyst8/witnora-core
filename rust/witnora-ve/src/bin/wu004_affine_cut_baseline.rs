//! WU-004: independently reimplement Beame--Sun's *known* affine-resolution
//! step (SAT 2026, Definition 2.8 / Algorithm 3) as a baseline for future
//! parity 1-UIP and certified clause-minimization research.
//! No novelty, performance, or complexity claim is made by this executable.

fn rank(mut rows: Vec<u64>, width: usize) -> usize {
    let mut r = 0;
    for bit in 0..width {
        if let Some(p) = (r..rows.len()).find(|&i| (rows[i] >> bit) & 1 == 1) {
            rows.swap(r, p);
            for i in (r + 1)..rows.len() {
                if (rows[i] >> bit) & 1 == 1 {
                    rows[i] ^= rows[r];
                }
            }
            r += 1;
        }
    }
    r
}

fn independent(rows: &[u64], width: usize) -> Vec<u64> {
    let mut selected = Vec::new();
    for &row in rows {
        let prior = rank(selected.clone(), width);
        selected.push(row);
        if rank(selected.clone(), width) == prior {
            selected.pop();
        }
    }
    selected
}

fn contained(rows: &[u64], ambient: &[u64], width: usize) -> bool {
    rank([ambient, rows].concat(), width) == rank(ambient.to_vec(), width)
}

/// Polynomial-time GF(2) intersection, via the kernel of [A | B]. The
/// left and right sides are row subspaces of augmented affine equations.
fn intersect(a: &[u64], b: &[u64], width: usize) -> Vec<u64> {
    assert!(width < 63);
    let left = independent(a, width);
    let right = independent(b, width);
    let columns: Vec<u64> = left.iter().chain(&right).copied().collect();
    let k = columns.len();
    assert!(k < 63);
    let mut system: Vec<u64> = (0..width)
        .map(|bit| {
            columns.iter().enumerate().fold(0u64, |acc, (j, row)| {
                acc | (((row >> bit) & 1) << j)
            })
        })
        .collect();
    let mut pivots = Vec::new();
    let mut row_index = 0;
    for col in 0..k {
        if let Some(p) = (row_index..width).find(|&i| (system[i] >> col) & 1 == 1) {
            system.swap(p, row_index);
            for i in 0..width {
                if i != row_index && (system[i] >> col) & 1 == 1 {
                    system[i] ^= system[row_index];
                }
            }
            pivots.push(col);
            row_index += 1;
        }
    }
    let mut answer = Vec::new();
    for free in 0..k {
        if pivots.contains(&free) {
            continue;
        }
        let mut kernel = 1u64 << free;
        for (i, &pivot) in pivots.iter().enumerate() {
            if (system[i] >> free) & 1 == 1 {
                kernel |= 1 << pivot;
            }
        }
        let value = left.iter().enumerate().fold(0u64, |acc, (i, row)| {
            if (kernel >> i) & 1 == 1 { acc ^ row } else { acc }
        });
        answer.push(value);
    }
    independent(&answer, width)
}

/// Two-sided semantic correctness: the first clause's falsity subspace
/// uses the currently TRUE trail row, while the reason's falsity subspace
/// uses the NEGATION of that row. The result is the published affine rule.
fn affine_resolve(
    learned_falsity: &[u64],
    reason_falsity: &[u64],
    earlier: &[u64],
    propagated: u64,
    n: usize,
) -> Vec<u64> {
    let width = n + 1;
    let one = 1u64 << n;
    assert!(contained(learned_falsity, &[earlier, &[propagated]].concat(), width));
    assert!(!contained(learned_falsity, earlier, width));
    assert!(contained(reason_falsity, &[earlier, &[propagated ^ one]].concat(), width));
    assert!(!contained(reason_falsity, earlier, width));
    let total = [learned_falsity, reason_falsity, &[one]].concat();
    let result = intersect(&total, earlier, width);
    assert!(contained(&result, earlier, width));
    assert!(!contained(&[one], &result, width));
    result
}

#[derive(Clone, Debug)]
struct Trace {
    n: usize,
    trail: Vec<u64>, // one decision at index 0; all subsequent entries are propagated
    reasons: Vec<Vec<u64>>, // falsity spaces, one per propagation
    conflict: Vec<u64>,
}

fn learn(trace: &Trace) -> (Vec<u64>, usize) {
    let width = trace.n + 1;
    assert!(trace.trail.len() == trace.reasons.len() + 1);
    assert_eq!(rank(trace.trail.clone(), width), trace.trail.len());
    assert!(contained(&trace.conflict, &trace.trail, width));
    let mut f = independent(&trace.conflict, width);
    let mut steps = 0;
    // This is the special case with one current decision level and no
    // level-zero units: asserting is exactly a rank-one falsity space.
    for i in (1..trace.trail.len()).rev() {
        if rank(f.clone(), width) == 1 {
            break;
        }
        let earlier = &trace.trail[..i];
        if contained(&f, earlier, width) {
            continue;
        }
        f = affine_resolve(&f, &trace.reasons[i - 1], earlier, trace.trail[i], trace.n);
        steps += 1;
    }
    assert_eq!(rank(f.clone(), width), 1, "learned clause must assert at root");
    assert!(contained(&f, &trace.trail, width));
    (f, steps)
}

/// Independently check RUP(⊕) soundness: suppose all equations falsifying
/// the proposed learned clause hold, then run exact XNF unit propagation
/// on the original clauses. Success requires deriving a contradiction.
fn rup_metrics(start: &[u64], clauses: &[Vec<u64>], n: usize) -> Option<(usize, usize)> {
    let width = n + 1;
    let one = 1 << n;
    let mut known = independent(start, width);
    if contained(&[one], &known, width) {
        return None; // reject a tautology as an uninformative certificate
    }
    let mut scans = 0;
    let mut propagated = 0;
    loop {
        let mut updated = false;
        for clause in clauses {
            scans += 1;
            let total = [known.as_slice(), clause.as_slice()].concat();
            if rank(total.clone(), width) != rank(total.clone(), n) {
                continue; // clause already true
            }
            match rank(total, n) - rank(known.clone(), n) {
                0 => return Some((scans, propagated)), // contradiction
                1 => {
                    let witness = clause.iter().copied().find(|&x| !contained(&[x], &known, width));
                    let Some(falsifying) = witness else { panic!("rank-one quotient missing witness") };
                    let implied = falsifying ^ one;
                    assert!(!contained(&[implied], &known, width));
                    known.push(implied);
                    updated = true;
                    propagated += 1;
                }
                _ => {}
            }
        }
        if !updated {
            return None;
        }
    }
}

fn rup_check(start: &[u64], clauses: &[Vec<u64>], n: usize) -> bool {
    rup_metrics(start, clauses, n).is_some()
}

fn classical_first_uip(parents: &[Vec<usize>], conflict_parents: &[usize]) -> usize {
    let last = parents.len() + 1;
    let mut edges = Vec::new();
    for (i, parent_set) in parents.iter().enumerate() {
        edges.extend(parent_set.iter().map(|&p| (p, i + 1)));
    }
    edges.extend(conflict_parents.iter().map(|&p| (p, last)));
    (0..last)
        .filter(|&excluded| {
            if excluded == 0 {
                return true;
            }
            let mut stack = vec![0];
            let mut seen = vec![false; last + 1];
            while let Some(node) = stack.pop() {
                if node == last {
                    return false;
                }
                if node == excluded || seen[node] {
                    continue;
                }
                seen[node] = true;
                stack.extend(edges.iter().filter(|&&(p, q)| p == node && q != excluded).map(|&(_, q)| q));
            }
            true
        })
        .max()
        .expect("decision dominates conflict")
}

fn cnf_trace(antecedents: &[Vec<usize>], conflict_parents: &[usize]) -> Trace {
    let n = antecedents.len() + 1;
    let rhs = 1 << n;
    let reasons = antecedents.iter().enumerate().map(|(i, parents)| {
        let mut f: Vec<u64> = parents.iter().map(|&p| (1 << p) | rhs).collect();
        f.push(1 << (i + 1));
        f
    }).collect();
    Trace {
        n,
        trail: (0..n).map(|i| (1 << i) | rhs).collect(),
        reasons,
        conflict: conflict_parents.iter().map(|&p| (1 << p) | rhs).collect(),
    }
}

fn enumerate_cnf(n: usize, mut visit: impl FnMut(&[Vec<usize>], &[usize])) {
    fn extend(
        n: usize, index: usize, parents: &mut Vec<Vec<usize>>,
        visit: &mut impl FnMut(&[Vec<usize>], &[usize]),
    ) {
        if index == n {
            for mask in 1..(1u64 << (n - 1)) {
                let conflict: Vec<usize> = (0..n - 1)
                    .filter(|&j| (mask >> j) & 1 == 1)
                    .chain(std::iter::once(n - 1)).collect();
                visit(parents, &conflict);
            }
            return;
        }
        for mask in 1..(1u64 << index) {
            parents.push((0..index).filter(|&j| (mask >> j) & 1 == 1).collect());
            extend(n, index + 1, parents, visit);
            parents.pop();
        }
    }
    extend(n, 1, &mut Vec::new(), &mut visit);
}

fn non_cnf_gauge_trace(mask: u64) -> Trace {
    let n = 4;
    let rhs = 1 << n;
    let a = 1 | rhs;
    let b = 2 | rhs;
    let d = 8;
    let c = 4 | rhs;
    let h = c ^ (if mask & 1 != 0 { a } else { 0 })
        ^ (if mask & 2 != 0 { b } else { 0 })
        ^ (if mask & 4 != 0 { d } else { 0 });
    Trace {
        n,
        trail: vec![a, b, d, h],
        reasons: vec![vec![a, 2], vec![b, 8 | rhs], vec![4 | 8, b ^ 4 ^ 8]],
        conflict: vec![b, c],
    }
}

/// Bounded, exact oracle for codimension-one strengthenings of an XNF
/// clause. There are 2^d-1 hyperplanes of a d-dimensional GF(2) subspace:
/// this is exponential in d and is NOT proposed as a scalable minimizer.
fn hyperplanes(falsity: &[u64], width: usize) -> Vec<Vec<u64>> {
    let b = independent(falsity, width);
    let d = b.len();
    assert!((1..=10).contains(&d), "research oracle has a strict rank budget");
    (1..(1usize << d))
        .map(|functional| {
            let pivot = functional.trailing_zeros() as usize;
            let rows: Vec<u64> = (0..d)
                .filter(|&j| j != pivot)
                .map(|j| if (functional >> j) & 1 == 0 { b[j] } else { b[j] ^ b[pivot] })
                .collect();
            assert_eq!(rank(rows.clone(), width), d - 1);
            rows
        })
        .collect()
}

fn same_subspace(a: &[u64], b: &[u64], width: usize) -> bool {
    contained(a, b, width) && contained(b, a, width)
}

fn minimization_witness() -> (Vec<u64>, Vec<Vec<u64>>) {
    // x=1, y=1, a=1 are antecedents at mixed decision levels; b=1 is
    // propagated by (!x OR !a OR b), then (!y OR !b) conflicts.
    // Resolving on b yields C = (!x OR !y OR !a) with falsity
    // F = span(x=1, y=1, a=1), rank 3.
    // The extra implications x->y and y->x make *both* !x OR !a and
    // !y OR !a valid but incomparable certified strengthenings.
    let n = 4;
    let rhs = 1 << n;
    let x = 0b0001 | rhs;
    let y = 0b0010 | rhs;
    let a = 0b0100 | rhs;
    let b = 0b1000 | rhs;
    let reason_b = vec![x, a, b ^ rhs];
    let conflict = vec![y, b];
    let learned = affine_resolve(&conflict, &reason_b, &[x, y, a], b, n);
    assert!(same_subspace(&learned, &[x, y, a], n + 1));
    let database = vec![
        reason_b,
        conflict,
        vec![x, y ^ rhs], // x -> y
        vec![y, x ^ rhs], // y -> x
    ];
    (learned, database)
}

fn certified_hyperplanes() -> (usize, usize) {
    let (learned, database) = minimization_witness();
    let all = hyperplanes(&learned, 5);
    let verified: Vec<_> = all.iter().filter(|&candidate| rup_check(candidate, &database, 4)).collect();
    let rhs = 1 << 4;
    let x = 1 | rhs;
    let y = 2 | rhs;
    let a = 4 | rhs;
    assert!(rup_check(&learned, &database, 4));
    assert!(verified.iter().any(|&h| same_subspace(h, &[x, a], 5)));
    assert!(verified.iter().any(|&h| same_subspace(h, &[y, a], 5)));
    (all.len(), verified.len())
}

fn certified_hyperplane_cost_range() -> (usize, usize) {
    let (learned, database) = minimization_witness();
    let mut costs: Vec<usize> = hyperplanes(&learned, 5)
        .iter()
        .filter_map(|h| rup_metrics(h, &database, 4).map(|(scans, _)| scans))
        .collect();
    costs.sort_unstable();
    (*costs.first().expect("at least one certified candidate"),
     *costs.last().expect("at least one certified candidate"))
}

fn report() -> (usize, usize) {
    let mut total = 0;
    let mut mismatches = 0;
    for n in [4, 5] {
        enumerate_cnf(n, |parents, conflict| {
            let t = cnf_trace(parents, conflict);
            let (learned, _) = learn(&t);
            let expected = (1u64 << classical_first_uip(parents, conflict)) | (1 << n);
            if !contained(&learned, &[expected], n + 1) || !contained(&[expected], &learned, n + 1) {
                mismatches += 1;
            }
            let clauses = [t.reasons.clone(), vec![t.conflict.clone()]].concat();
            assert!(rup_check(&learned, &clauses, n));
            total += 1;
        });
    }
    (total, mismatches)
}

fn main() {
    let (cases, mismatches) = report();
    println!("WU-004 baseline: {cases} CNF traces; {mismatches} differences from classical 1-UIP.");
    assert_eq!(mismatches, 0);
    let first = learn(&non_cnf_gauge_trace(0)).0;
    for gauge in 0..8 {
        let t = non_cnf_gauge_trace(gauge);
        let (learned, _) = learn(&t);
        assert!(contained(&learned, &first, t.n + 1) && contained(&first, &learned, t.n + 1));
        assert!(rup_check(&learned, &[t.reasons.clone(), vec![t.conflict.clone()]].concat(), t.n));
    }
    println!("All 8 equivalent non-CNF gauge trails learn the identical subspace.");
    println!("Every learned clause also passes an independent RUP(XOR) propagation check.");
    let (candidates, verified) = certified_hyperplanes();
    println!("Bounded rank-three minimization: {candidates} hyperplanes, {verified} RUP(XOR)-verified strict strengthenings.");
    let (min_scans, max_scans) = certified_hyperplane_cost_range();
    println!("Certificate replay scan counts for certified strengthenings: {min_scans}..{max_scans} (fixed clause order).");
    println!("At least two verified strengthenings are incomparable: (!x OR !a) and (!y OR !a).");
    println!("Boundary: this replicates a published algorithm; 1-UIP generalization remains OPEN.");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn all_cnf_traces_agree_with_classical_uip_and_verify() {
        assert_eq!(report(), (4872, 0));
    }

    #[test]
    fn all_eight_non_cnf_gauges_learn_same_verified_subspace() {
        let canonical = learn(&non_cnf_gauge_trace(0)).0;
        for mask in 0..8 {
            let t = non_cnf_gauge_trace(mask);
            let (learned, _) = learn(&t);
            assert!(contained(&learned, &canonical, 5) && contained(&canonical, &learned, 5));
            assert!(rup_check(&learned, &[t.reasons.clone(), vec![t.conflict.clone()]].concat(), 4));
        }
    }

    #[test]
    fn affine_intersection_is_subspace_invariant() {
        let a = [0b11001u64, 0b01110u64];
        let b = [0b10001u64, 0b11010u64];
        let x = intersect(&a, &b, 5);
        for basis_a in [[a[0], a[1]], [a[0] ^ a[1], a[0]], [a[1], a[0] ^ a[1]]] {
            let y = intersect(&basis_a, &b, 5);
            assert!(contained(&x, &y, 5) && contained(&y, &x, 5));
        }
    }

    #[test]
    fn multiple_incomparable_rup_certified_hyperplanes() {
        let (all, verified) = certified_hyperplanes();
        assert_eq!(all, 7);
        assert!(verified >= 2);
        let (min_scans, max_scans) = certified_hyperplane_cost_range();
        assert!(max_scans >= min_scans && min_scans > 0);
    }

    #[test]
    fn hyperplane_set_independent_of_all_168_gf2_three_bases() {
        let (learned, _) = minimization_witness();
        let width = 5;
        let original = hyperplanes(&learned, width);
        let mut nonzero = Vec::new();
        for mask in 1..8usize {
            let row = learned.iter().enumerate().fold(0u64, |acc, (i, &r)| {
                if (mask >> i) & 1 == 1 { acc ^ r } else { acc }
            });
            nonzero.push(row);
        }
        let mut bases_checked = 0;
        for &first in &nonzero {
            for &second in &nonzero {
                for &third in &nonzero {
                    let alternative = [first, second, third];
                    if rank(alternative.to_vec(), width) != 3 {
                        continue;
                    }
                    bases_checked += 1;
                    let other = hyperplanes(&alternative, width);
                    assert!(other.iter().all(|h| original.iter().any(|o| same_subspace(h, o, width))));
                    assert!(original.iter().all(|h| other.iter().any(|o| same_subspace(h, o, width))));
                }
            }
        }
        assert_eq!(bases_checked, 168);
    }
}
