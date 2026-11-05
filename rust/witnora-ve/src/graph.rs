//! R-016: native canonical-CNF primal graph and incidence components.
//!
//! Deterministic incidence decomposition preserves clause ordering
//! and isolates empty clauses as separate components.

use std::collections::{BTreeMap, BTreeSet, VecDeque};
use crate::cnf::CanonicalCnf;

pub fn primal_variables_and_edges(
    source: &[Vec<i32>],
) -> Result<(Vec<u32>, Vec<(u32, u32)>), String> {
    let cnf = CanonicalCnf::from_signed(source)?;
    let variables = cnf.variables();
    let mut edges = BTreeSet::new();
    for clause in cnf.clauses {
        let vars: Vec<_> = clause.iter().map(|lit| lit.unsigned_abs())
            .collect::<BTreeSet<_>>().into_iter().collect();
        for (i, &a) in vars.iter().enumerate() {
            for &b in &vars[i+1..] {
                edges.insert((a, b));
            }
        }
    }
    Ok((variables, edges.into_iter().collect()))
}

/// Components are ordered by their first canonical clause index.
pub fn incidence_components(
    source: &[Vec<i32>],
) -> Result<Vec<Vec<Vec<i32>>>, String> {
    let cnf = CanonicalCnf::from_signed(source)?;
    let clauses = cnf.clauses;
    let mut var_to_clauses: BTreeMap<u32, Vec<usize>> = BTreeMap::new();
    for (i, clause) in clauses.iter().enumerate() {
        for &lit in clause {
            var_to_clauses.entry(lit.unsigned_abs()).or_default().push(i);
        }
    }

    let mut seen_clause = vec![false; clauses.len()];
    let mut components = Vec::new();
    for start in 0..clauses.len() {
        if seen_clause[start] {
            continue;
        }
        let mut queue = VecDeque::from([start]);
        let mut seen_vars = BTreeSet::new();
        let mut ids = Vec::new();
        seen_clause[start] = true;
        while let Some(i) = queue.pop_front() {
            ids.push(i);
            for &lit in &clauses[i] {
                let var = lit.unsigned_abs();
                if !seen_vars.insert(var) {
                    continue;
                }
                if let Some(neighbours) = var_to_clauses.get(&var) {
                    for &j in neighbours {
                        if !seen_clause[j] {
                            seen_clause[j] = true;
                            queue.push_back(j);
                        }
                    }
                }
            }
        }
        ids.sort_unstable();
        components.push(ids.into_iter().map(|i| clauses[i].clone()).collect());
    }
    Ok(components)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn graph_edges_and_empty_clause_component() {
        let src = vec![vec![1, 2, 3], vec![-3, 4], vec![7], vec![]];
        let (vars, edges) = primal_variables_and_edges(&src).unwrap();
        assert_eq!(vars, vec![1, 2, 3, 4, 7]);
        assert_eq!(edges, vec![(1,2), (1,3), (2,3), (3,4)]);
        let components = incidence_components(&src).unwrap();
        assert_eq!(components.len(), 3);
        assert_eq!(components[0], vec![Vec::<i32>::new()]);
        assert_eq!(components[1].len(), 2);
        assert_eq!(components[2], vec![vec![7]]);
    }

    #[test]
    fn empty_and_isolated_components() {
        assert!(incidence_components(&[]).unwrap().is_empty());
        assert_eq!(incidence_components(&[vec![1], vec![2]]).unwrap().len(), 2);
    }
}
