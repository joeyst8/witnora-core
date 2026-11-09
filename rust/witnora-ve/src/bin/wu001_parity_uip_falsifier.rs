//! WU-001: falsify the hypothesis that the affine rank profile of a conflict
//! uniquely determines its first UIP. This is a research diagnostic, not a solver.
//!
//! Rows encode GF(2) equations: low `n` bits are coefficients and bit `n`
//! is the right-hand side. The only Boolean search below is reachability in
//! an implication DAG; no SAT assignments are enumerated.

#[derive(Clone, Debug, PartialEq, Eq)]
enum ClauseUnderPrefix {
    Entailed,
    Conflict,
    Unit,
    NonUnit { quotient_rank: usize },
}

fn rank(mut rows: Vec<u64>, column_count: usize) -> usize {
    let mut r = 0;
    for col in 0..column_count {
        if let Some(pivot) = (r..rows.len()).find(|&i| (rows[i] >> col) & 1 == 1) {
            rows.swap(r, pivot);
            for i in (r + 1)..rows.len() {
                if (rows[i] >> col) & 1 == 1 {
                    rows[i] ^= rows[r];
                }
            }
            r += 1;
        }
    }
    r
}

fn consistent(rows: &[u64], n: usize) -> bool {
    rank(rows.to_vec(), n + 1) == rank(rows.to_vec(), n)
}

/// The affine falsity space of an XNF clause has codimension q relative to
/// the prefix. A consistent q=1 complement is an affine hyperplane, so the
/// clause becomes one parity unit. For q>=2 its complement has full affine
/// hull and yields no additional affine unit. This criterion is already
/// implicit in Beame--Sun (SAT 2026, Definition 3.2 / Algorithm 2).
fn classify(prefix: &[u64], falsity_rows: &[u64], n: usize) -> ClauseUnderPrefix {
    assert!(n < 63);
    assert!(consistent(prefix, n), "decision prefix must be consistent");
    let combined: Vec<u64> = prefix.iter().chain(falsity_rows).copied().collect();
    if !consistent(&combined, n) {
        return ClauseUnderPrefix::Entailed;
    }
    let q = rank(combined, n) - rank(prefix.to_vec(), n);
    match q {
        0 => ClauseUnderPrefix::Conflict,
        1 => ClauseUnderPrefix::Unit,
        _ => ClauseUnderPrefix::NonUnit { quotient_rank: q },
    }
}

#[derive(Clone)]
struct ImplicationDag {
    // Nodes: a (decision), b, c (propagated), bottom (contradiction).
    // Edges indicate *reason dependencies*, which a bare affine span forgets.
    edges: Vec<(usize, usize)>,
}

impl ImplicationDag {
    fn reaches_contradiction_avoiding(&self, excluded: usize) -> bool {
        if excluded == 0 || excluded == 3 {
            return false;
        }
        let mut seen = [false; 4];
        let mut stack = vec![0];
        while let Some(v) = stack.pop() {
            if v == 3 {
                return true;
            }
            if seen[v] || v == excluded {
                continue;
            }
            seen[v] = true;
            for &(from, to) in &self.edges {
                if from == v && to != excluded {
                    stack.push(to);
                }
            }
        }
        false
    }

    fn first_uip(&self) -> usize {
        // A UIP dominates the conflict: every decision-to-conflict path
        // visits it. Trail order here is topological; the latest such node
        // is the classical first UIP. Ignore the contradiction itself.
        (0..3)
            .filter(|&v| !self.reaches_contradiction_avoiding(v))
            .max()
            .expect("decision must dominate the conflict")
    }
}

fn witness() -> (Vec<ClauseUnderPrefix>, ImplicationDag, ImplicationDag) {
    // Both traces: decide a=1, deduce b=1 and c=1, hit ¬b ∨ ¬c.
    // neg(¬b ∨ ¬c) is the affine span of {b=1, c=1}.
    let n = 3;
    let a = 0b001 | (1 << n);
    let b = 0b010 | (1 << n);
    let c = 0b100 | (1 << n);
    let falsity = [b, c];
    let trail = [a, b, c];
    let ranks = (0..=trail.len())
        .map(|i| classify(&trail[..i], &falsity, n))
        .collect();

    // A: ¬a∨b, ¬b∨c, ¬b∨¬c.  Paths both go through b; UIP=b.
    let chain = ImplicationDag {
        edges: vec![(0, 1), (1, 2), (1, 3), (2, 3)],
    };
    // B: ¬a∨b, ¬a∨c, ¬b∨¬c. Only a dominates both paths; UIP=a.
    let fork = ImplicationDag {
        edges: vec![(0, 1), (0, 2), (1, 3), (2, 3)],
    };
    (ranks, chain, fork)
}

/// An independent classical 1-UIP reference for the CNF-embedded witness.
/// Literals are signed one-based variable indices; a,b,c have IDs 1,2,3.
fn resolve_on(clause: &[i8], reason: &[i8], pivot: i8) -> Vec<i8> {
    assert!(clause.contains(&-pivot) && reason.contains(&pivot));
    let mut result: Vec<i8> = clause
        .iter()
        .chain(reason)
        .copied()
        .filter(|&lit| lit != pivot && lit != -pivot)
        .collect();
    result.sort_unstable();
    result.dedup();
    assert!(result.iter().all(|x| !result.contains(&-*x)), "tautological resolvent");
    result
}

fn classical_first_uip_learnt(chain: bool) -> Vec<i8> {
    let b_reason = [-1, 2]; // ¬a ∨ b
    let c_reason = if chain { [-2, 3] } else { [-1, 3] };
    let mut learnt = vec![-2, -3]; // ¬b ∨ ¬c, all at current level
    // Resolve latest propagated variables until only one current-level
    // literal remains. In these traces all a,b,c are at decision level 1.
    for (pivot, reason) in [(3, &c_reason[..]), (2, &b_reason[..])] {
        if learnt.len() == 1 {
            break;
        }
        learnt = resolve_on(&learnt, reason, pivot);
    }
    assert_eq!(learnt.len(), 1);
    learnt
}

fn main() {
    let (profile, chain, fork) = witness();
    println!("WU-001: rank-only parity 1-UIP conjecture FALSIFIED");
    println!("Same trail: a=1, b=1, c=1; same conflict: (!b or !c)");
    println!("Same affine quotient profile: {profile:?}");
    println!("Chain reasons: (!a or b), (!b or c) => UIP=b");
    println!("Fork reasons:  (!a or b), (!a or c) => UIP=a");
    assert_eq!(chain.first_uip(), 1);
    assert_eq!(fork.first_uip(), 0);
    assert_eq!(classical_first_uip_learnt(true), vec![-2]);
    assert_eq!(classical_first_uip_learnt(false), vec![-1]);
    println!("Independent classical 1-UIP learning: chain learns !b; fork learns !a.");
    println!("Consequence: rank profile alone loses essential reason provenance.");
    println!("Boundary: this does NOT refute reason-aware parity UIP definitions.");
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;

    #[test]
    fn same_subspaces_different_first_uips() {
        let (profile, chain, fork) = witness();
        assert_eq!(profile[0], ClauseUnderPrefix::NonUnit { quotient_rank: 2 });
        assert_eq!(profile[1], ClauseUnderPrefix::NonUnit { quotient_rank: 2 });
        assert_eq!(profile[2], ClauseUnderPrefix::Unit);
        assert_eq!(profile[3], ClauseUnderPrefix::Conflict);
        assert_eq!(chain.first_uip(), 1);
        assert_eq!(fork.first_uip(), 0);
        assert_eq!(classical_first_uip_learnt(true), vec![-2]);
        assert_eq!(classical_first_uip_learnt(false), vec![-1]);
    }

    #[test]
    fn replacing_affine_generators_preserves_profile() {
        let n = 3;
        let a = 0b001 | (1 << n);
        let b = 0b010 | (1 << n);
        let c = 0b100 | (1 << n);
        let original = [b, c];
        let nonzero = [b, c, b ^ c];
        for &x in &nonzero {
            for &y in &nonzero {
                if x == y {
                    continue;
                }
                for i in 0..=3 {
                    assert_eq!(
                        classify(&[a, b, c][..i], &original, n),
                        classify(&[a, b, c][..i], &[x, y], n),
                        "generator pair ({x:b},{y:b}), prefix length {i}"
                    );
                }
            }
        }
    }

    #[test]
    fn rank_matches_independent_explicit_span_oracle() {
        let n = 5;
        let mut seed = 0x6179_62f4_384e_ab61u64;
        for _ in 0..4_000 {
            let count = (next(&mut seed) % 9) as usize;
            let rows: Vec<u64> = (0..count).map(|_| next(&mut seed) & 0b11_1111).collect();
            let mut span = HashSet::from([0u64]);
            for &r in &rows {
                let expansion: Vec<_> = span.iter().map(|&v| v ^ r).collect();
                span.extend(expansion);
            }
            let expected_aug_rank = span.len().trailing_zeros() as usize;
            let expected_consistent = !span.contains(&(1 << n));
            assert_eq!(rank(rows.clone(), n + 1), expected_aug_rank);
            assert_eq!(consistent(&rows, n), expected_consistent);
            let projected: Vec<u64> = rows.iter().map(|r| r & ((1 << n) - 1)).collect();
            let mut coefficient_span = HashSet::from([0u64]);
            for &r in &projected {
                let expansion: Vec<_> = coefficient_span.iter().map(|&v| v ^ r).collect();
                coefficient_span.extend(expansion);
            }
            assert_eq!(rank(rows, n), coefficient_span.len().trailing_zeros() as usize);
        }
    }

    #[test]
    fn tautology_conflict_unit_and_nonunit_separated() {
        let n = 3;
        let b0 = 0b010;
        let b1 = b0 | (1 << n);
        let c1 = 0b100 | (1 << n);
        assert_eq!(classify(&[], &[b0, b1], n), ClauseUnderPrefix::Entailed);
        assert_eq!(classify(&[b1], &[b1], n), ClauseUnderPrefix::Conflict);
        assert_eq!(classify(&[], &[b1], n), ClauseUnderPrefix::Unit);
        assert_eq!(classify(&[], &[b1, c1], n), ClauseUnderPrefix::NonUnit { quotient_rank: 2 });
    }

    fn next(state: &mut u64) -> u64 {
        *state ^= *state << 13;
        *state ^= *state >> 7;
        *state ^= *state << 17;
        *state
    }
}
