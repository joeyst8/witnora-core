//! WU-002: non-CNF counterexample to a coordinate-support 1-UIP graph.
//! Source: Beame--Sun, SAT 2026, Section 8's open parity 1-UIP question.
//! This diagnostic does NOT implement or refute their Algorithm 3.

// Equations are coefficient bits followed by the RHS bit at index n.
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

// Unique coordinates of target in a list of linearly independent equations.
// Echelon elimination is polynomial-time and never enumerates assignments.
fn coordinates(basis: &[u64], target: u64, width: usize) -> Option<u64> {
    assert!(basis.len() < 63 && width < 63);
    let mut pivots: Vec<Option<(u64, u64)>> = vec![None; width];
    for (j, &row) in basis.iter().enumerate() {
        let mut v = row;
        let mut coeffs = 1u64 << j;
        for bit in 0..width {
            if (v >> bit) & 1 == 0 {
                continue;
            }
            if let Some((pivot_row, pivot_coeffs)) = pivots[bit] {
                v ^= pivot_row;
                coeffs ^= pivot_coeffs;
            } else {
                pivots[bit] = Some((v, coeffs));
                break;
            }
        }
        assert!(v != 0, "the trail must contain independent equations");
    }
    let mut v = target;
    let mut coeffs = 0u64;
    for (bit, pivot) in pivots.iter().enumerate() {
        if (v >> bit) & 1 == 0 {
            continue;
        }
        if let Some((pivot_row, pivot_coeffs)) = pivot {
            v ^= pivot_row;
            coeffs ^= pivot_coeffs;
        } else {
            return None;
        }
    }
    if v == 0 { Some(coeffs) } else { None }
}

// A deliberately NAIVE graph: draw a dependency edge when some falsifying
// equation uses the corresponding previous unit as a coordinate. The last
// column for a propagation is its falsifying unit (propagated + 1).
fn propagation_parents(prefix: &[u64], propagated: u64, falsity: &[u64], n: usize) -> Vec<usize> {
    let mut basis = prefix.to_vec();
    basis.push(propagated ^ (1 << n));
    let mut support = 0u64;
    let mut uses_new = false;
    for &f in falsity {
        let decomposition = coordinates(&basis, f, n + 1)
            .expect("reason must be contained in prior units plus negated propagation");
        support |= decomposition;
        uses_new |= (decomposition >> prefix.len()) & 1 == 1;
    }
    assert!(uses_new, "reason must cause a genuinely new propagation");
    (0..prefix.len())
        .filter(|&j| (support >> j) & 1 == 1)
        .collect()
}

fn conflict_parents(trail: &[u64], falsity: &[u64], n: usize) -> Vec<usize> {
    let mut support = 0u64;
    for &f in falsity {
        support |= coordinates(trail, f, n + 1)
            .expect("conflict falsity must be contained in the true trail");
    }
    (0..trail.len())
        .filter(|&j| (support >> j) & 1 == 1)
        .collect()
}

fn first_uip(edges: &[(usize, usize)], conflict: usize) -> usize {
    let reaches_without = |excluded: usize| -> bool {
        if excluded == 0 {
            return false;
        }
        let mut visited = vec![false; conflict + 1];
        let mut stack = vec![0];
        while let Some(v) = stack.pop() {
            if v == conflict {
                return true;
            }
            if visited[v] || v == excluded {
                continue;
            }
            visited[v] = true;
            for &(src, dest) in edges {
                if src == v && dest != excluded {
                    stack.push(dest);
                }
            }
        }
        false
    };
    (0..conflict)
        .filter(|&v| !reaches_without(v))
        .max()
        .expect("the decision must dominate a reachable conflict")
}

#[derive(Debug)]
struct Trace {
    trail: [u64; 4],
    propagation_parents: Vec<usize>,
    conflict_parents: Vec<usize>,
    graph_uip: usize,
}

// Exact non-CNF XNF input, unchanged between traces (four variables):
//   decide a=1
//   R_b: (!a or b)                            -> b=1
//   R_d: (!b or !d)                           -> d=0
//   R_c: (c XOR d=1) OR (b XOR c XOR d=0)    -> c=1 or h=c XOR a=0
//   R_bot: (!b or !c)                        -> contradiction
// R_c's falsity rows are c XOR d=0 and b XOR c XOR d=1; XOR is b=1.
// This really is a parity dependency: it reduces to (!b OR (c XOR d=1)),
// not to a single ordinary CNF clause in the original variables.
fn build_trace(shift_by_a: bool) -> Trace {
    build_trace_with_shift(if shift_by_a { 1 } else { 0 })
}

// Exhaustively cover the eight possible row representatives for the final
// rank-one extension, obtained by adding earlier true units to c=1.
fn build_trace_with_shift(shift: u8) -> Trace {
    let n = 4;
    let a = 0b001 | (1 << n); // a=1
    let b = 0b010 | (1 << n); // b=1
    let d = 0b1000; // d=0
    let c = 0b0100 | (1 << n); // c=1
    assert!(shift < 8);
    let h = c
        ^ (if shift & 1 != 0 { a } else { 0 })
        ^ (if shift & 2 != 0 { b } else { 0 })
        ^ (if shift & 4 != 0 { d } else { 0 });
    let c_zero = c ^ (1 << n);
    let reason_b = [a, b ^ (1 << n)];
    let reason_d = [b, d ^ (1 << n)];
    let reason_c = [c_zero ^ d, b ^ c_zero ^ d];
    let conflict = [b, c];

    assert_eq!(propagation_parents(&[a], b, &reason_b, n), vec![0]);
    assert_eq!(propagation_parents(&[a, b], d, &reason_d, n), vec![1]);
    // It is a valid unit inference: reason falsity has exactly one new
    // quotient dimension relative to the old prefix, for BOTH representatives.
    assert_eq!(rank(vec![a, b, d, reason_c[0], reason_c[1]], n + 1) - rank(vec![a, b, d], n + 1), 1);
    let parents_c = propagation_parents(&[a, b, d], h, &reason_c, n);
    let trail = [a, b, d, h];
    let conflict_parents = conflict_parents(&trail, &conflict, n);
    let mut edges = vec![(0, 1), (1, 2)];
    edges.extend(parents_c.iter().map(|&i| (i, 3)));
    edges.extend(conflict_parents.iter().map(|&i| (i, 4)));
    let graph_uip = first_uip(&edges, 4);
    Trace {
        trail,
        propagation_parents: parents_c,
        conflict_parents,
        graph_uip,
    }
}

fn main() {
    let plain = build_trace(false);
    let gauge = build_trace(true);
    assert_eq!(rank(plain.trail.to_vec(), 5), rank([plain.trail, gauge.trail].concat(), 5));
    assert_eq!(plain.graph_uip, 1);
    assert_eq!(gauge.graph_uip, 0);
    println!("WU-002: coordinate-support 1-UIP gauge invariance FALSIFIED");
    println!("Same non-CNF XNF clauses, same affine trail SPANS and reasons.");
    println!("Propagate c=1:      {plain:?}");
    println!("Propagate c XOR a=0: {gauge:?}");
    println!("The candidate reason intersection K_c is span(b=1) in BOTH cases.");
    println!("Boundary: the different UIPs are from a NAIVE coordinate graph,");
    println!("not from the established CDCL(XOR) algorithm or a semantic UIP.");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn different_graph_uip_under_equivalent_non_cnf_trail() {
        let a = build_trace(false);
        let b = build_trace(true);
        assert_eq!(a.propagation_parents, vec![1, 2]);
        assert_eq!(a.conflict_parents, vec![1, 3]);
        assert_eq!(a.graph_uip, 1);
        assert_eq!(b.propagation_parents, vec![0, 1, 2]);
        assert_eq!(b.conflict_parents, vec![0, 1, 3]);
        assert_eq!(b.graph_uip, 0);
        assert_eq!(rank(a.trail.to_vec(), 5), 4);
        assert_eq!(rank([a.trail, b.trail].concat(), 5), 4);
    }

    #[test]
    fn reason_intersection_is_intrinsic_and_distinguishes_from_coordinate_support() {
        let n = 4;
        let a = 0b001 | (1 << n);
        let b = 0b010 | (1 << n);
        let d = 0b1000;
        let c_zero = 0b0100;
        let f = [c_zero ^ d, b ^ c_zero ^ d];
        let p = [a, b, d];
        // dim(span(F)∩span(P)) = 2+3-4 = 1, and b∈both.
        assert_eq!(rank(f.to_vec(), n + 1), 2);
        assert_eq!(rank(p.to_vec(), n + 1), 3);
        assert_eq!(rank([f.to_vec(), p.to_vec()].concat(), n + 1), 4);
        assert!(coordinates(&f, b, n + 1).is_some());
        assert!(coordinates(&p, b, n + 1).is_some());
        // F changes neither when the propagated row is renamed by adding a
        // previous row nor when the generator pair is rebased.
        let nonzero = [f[0], f[1], f[0] ^ f[1]];
        for &x in &nonzero {
            for &y in &nonzero {
                if x != y {
                    assert_eq!(propagation_parents(&p, 0b0100 | (1 << n), &[x, y], n), vec![1, 2]);
                    assert_eq!(propagation_parents(&p, 0b0101, &[x, y], n), vec![0, 1, 2]);
                }
            }
        }
    }

    #[test]
    fn all_eight_equivalent_propagation_gauges_falsify_graph_invariance() {
        let reference = build_trace_with_shift(0);
        let mut counts = [0usize; 4];
        for shift in 0..8 {
            let trace = build_trace_with_shift(shift);
            assert_eq!(rank([reference.trail, trace.trail].concat(), 5), 4);
            counts[trace.graph_uip] += 1;
        }
        assert_eq!(counts, [4, 4, 0, 0]);
    }

    #[test]
    fn coordinate_extraction_recovers_exact_rows() {
        let n = 5;
        let mut seed = 0x6205_776d_c98a_2b71u64;
        for _ in 0..2_000 {
            let mut basis = Vec::new();
            for _ in 0..5 {
                let row = next(&mut seed) & 63;
                if rank([basis.clone(), vec![row]].concat(), n + 1)
                    > rank(basis.clone(), n + 1)
                {
                    basis.push(row);
                }
            }
            let mask = next(&mut seed) & ((1u64 << basis.len()) - 1);
            let target = basis.iter().enumerate().fold(0u64, |acc, (i, &row)| {
                if (mask >> i) & 1 == 1 { acc ^ row } else { acc }
            });
            assert_eq!(coordinates(&basis, target, n + 1), Some(mask));
        }
    }

    #[test]
    fn xor_reason_cannot_be_one_boolean_cnf_clause() {
        let n = 4;
        let b_true = 0b0010 | (1 << n);
        let cd_zero = 0b1100;
        let f = [cd_zero, b_true ^ cd_zero];
        assert_eq!(rank(f.to_vec(), n + 1), 2);
        // F contains b=1 and no individual assignment for a, c, or d.
        // The falsity set of a single ordinary Boolean CNF clause is an
        // axis-aligned subcube, generated only by fixed-variable equations.
        // F has an extra essential non-axis-aligned relation c XOR d=0.
        let mut fixed_variables = Vec::new();
        for variable in 0..n {
            for rhs in 0..=1u64 {
                let row = (1 << variable) | (rhs << n);
                if coordinates(&f, row, n + 1).is_some() {
                    fixed_variables.push(row);
                }
            }
        }
        assert_eq!(fixed_variables, [b_true]);
        assert_eq!(rank(fixed_variables, n + 1), 1);
    }

    fn next(state: &mut u64) -> u64 {
        *state ^= *state << 13;
        *state ^= *state >> 7;
        *state ^= *state << 17;
        *state
    }
}
