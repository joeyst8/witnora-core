//! R-010: native exact 2-SAT decision and satisfying assignment.
//!
//! Kosaraju SCC over the signed implication graph. No heuristic
//! SAT decisions, no Python fallback. Unlike #SAT counting, this
//! returns a satisfying assignment or an UNSAT decision only.

use std::collections::BTreeSet;

fn index(lit: i32) -> usize {
    let v = (lit.unsigned_abs() - 1) as usize;
    2 * v + if lit < 0 { 1 } else { 0 }
}

fn dfs_order(node: usize, edges: &[Vec<usize>], seen: &mut [bool], order: &mut Vec<usize>) {
    seen[node] = true;
    for &next in &edges[node] {
        if !seen[next] {
            dfs_order(next, edges, seen, order);
        }
    }
    order.push(node);
}

fn dfs_component(node: usize, edges: &[Vec<usize>], comp: &mut [usize], label: usize) {
    comp[node] = label;
    for &next in &edges[node] {
        if comp[next] == usize::MAX {
            dfs_component(next, edges, comp, label);
        }
    }
}

/// SAT: Some(0-indexed variable assignment); UNSAT: None.
/// Errors: invalid source literals or source is not 2-CNF.
/// Variables absent from the formula still receive arbitrary Booleans.
pub fn solve_2sat(
    source: &[Vec<i32>], nvars: u32,
) -> Result<Option<Vec<bool>>, String> {
    if nvars > 256 {
        return Err("R-010 supports nvars in 0..256".into());
    }
    let nodes = 2 * nvars as usize;
    let mut normalized: Vec<Vec<i32>> = Vec::new();
    let mut has_empty = false;
    for raw in source {
        let mut signs: BTreeSet<i32> = BTreeSet::new();
        let mut tautology = false;
        for &lit in raw {
            if lit == 0 || lit.unsigned_abs() > nvars {
                return Err("2-SAT source literal out of range".into());
            }
            if signs.contains(&-lit) {
                tautology = true;
            }
            signs.insert(lit);
        }
        if tautology {
            continue;
        }
        if signs.len() > 2 {
            return Err("source is not 2-CNF".into());
        }
        if signs.is_empty() {
            has_empty = true;
        } else {
            normalized.push(signs.into_iter().collect());
        }
    }

    if has_empty { return Ok(None); }
    let mut edges: Vec<BTreeSet<usize>> = vec![BTreeSet::new(); nodes];
    for clause in &normalized {
        let a = index(clause[0]);
        if clause.len() == 1 {
            edges[a ^ 1].insert(a);
        } else {
            let b = index(clause[1]);
            edges[a ^ 1].insert(b);
            edges[b ^ 1].insert(a);
        }
    }
    let graph: Vec<Vec<usize>> =
        edges.iter().map(|neigh| neigh.iter().copied().collect()).collect();
    let mut reverse = vec![Vec::new(); nodes];
    for (src, neighbours) in graph.iter().enumerate() {
        for &dst in neighbours {
            reverse[dst].push(src);
        }
    }
    for neighbours in &mut reverse {
        neighbours.sort_unstable();
    }

    let mut seen = vec![false; nodes];
    let mut order = Vec::with_capacity(nodes);
    for node in 0..nodes {
        if !seen[node] {
            dfs_order(node, &graph, &mut seen, &mut order);
        }
    }
    let mut comp = vec![usize::MAX; nodes];
    let mut next_label = 0;
    for &node in order.iter().rev() {
        if comp[node] == usize::MAX {
            dfs_component(node, &reverse, &mut comp, next_label);
            next_label += 1;
        }
    }
    let mut assignment = Vec::with_capacity(nvars as usize);
    for v in 0..(nvars as usize) {
        if comp[2 * v] == comp[2 * v + 1] {
            return Ok(None);
        }
        assignment.push(comp[2 * v] > comp[2 * v + 1]);
    }

    // Machine-check the witness against every normalized input clause.
    if !normalized.iter().all(|clause| clause.iter().any(|&lit| {
        let value = assignment[(lit.unsigned_abs() - 1) as usize];
        value == (lit > 0)
    })) {
        return Err("native 2-SAT witness failed source verification".into());
    }
    Ok(Some(assignment))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn truth_table_sat(source: &[Vec<i32>], nvars: u32) -> bool {
        (0..(1u32 << nvars)).any(|mask| source.iter().all(|clause| {
            clause.iter().any(|&lit| {
                ((mask >> (lit.unsigned_abs() - 1)) & 1 != 0) == (lit > 0)
            })
        }))
    }

    #[test]
    fn basic_empty_units_and_contradictions() {
        assert_eq!(solve_2sat(&[], 0).unwrap(), Some(vec![]));
        assert_eq!(solve_2sat(&[vec![]], 2).unwrap(), None);
        assert_eq!(solve_2sat(&[vec![1], vec![-1]], 2).unwrap(), None);
        assert_eq!(solve_2sat(&[vec![1]], 2).unwrap().unwrap()[0], true);
        assert_eq!(solve_2sat(&[vec![-1]], 2).unwrap().unwrap()[0], false);
        assert!(solve_2sat(&[vec![1, -1]], 2).unwrap().is_some());
        assert_eq!(solve_2sat(&[vec![1, 1, 1]], 2).unwrap().unwrap()[0], true);
    }

    #[test]
    fn reject_nonlinear_invalid_and_undeclared_sources() {
        assert!(solve_2sat(&[vec![1, 2, 3]], 3).is_err());
        assert!(solve_2sat(&[vec![0]], 1).is_err());
        assert!(solve_2sat(&[vec![5]], 4).is_err());
        assert!(solve_2sat(&[], 257).is_err());
    }

    #[test]
    fn random_2800_exact_sat_decisions_and_witnesses() {
        let mut state = 10102026u64;
        let mut next = || {
            state = state.wrapping_mul(6364136223846793005)
                         .wrapping_add(1442695040888963407);
            (state >> 32) as u32
        };
        for n in 1..=8u32 {
            for _ in 0..350 {
                let mut clauses = Vec::new();
                for _ in 0..(next() % 16) {
                    let mut clause = Vec::new();
                    for _ in 0..(next() % 3) {
                        let v = 1 + next() % n;
                        clause.push(if next() & 1 == 0 { v as i32 } else { -(v as i32) });
                    }
                    clauses.push(clause);
                }
                let brute = truth_table_sat(&clauses, n);
                let got = solve_2sat(&clauses, n).unwrap();
                assert_eq!(got.is_some(), brute,
                           "n={n} clauses={clauses:?}");
                if let Some(assignment) = got {
                    assert!(clauses.iter().all(|clause| clause.iter().any(|&lit| {
                        assignment[(lit.unsigned_abs() - 1) as usize] == (lit > 0)
                    })));
                }
            }
        }
    }
}
