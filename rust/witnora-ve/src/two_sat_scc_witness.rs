//! R-037: native, source-attributed SCC contradiction paths for 2-CNF.
//! Mirrors the original Python BFS tie-break, edge provenance, and
//! resolution-derived complementary unit clauses.

use crate::cnf::CanonicalCnf;
use std::collections::{BTreeMap, BTreeSet, VecDeque};

type Graph = BTreeMap<i32, BTreeSet<i32>>;
type Sources = BTreeMap<(i32, i32), Vec<i32>>;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ProofEdge {
    pub source: i32,
    pub target: i32,
    pub clause: Vec<i32>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SccResolutionProof {
    pub variable: u32,
    pub path_pos_to_neg: Vec<ProofEdge>,
    pub path_neg_to_pos: Vec<ProofEdge>,
    pub derived_clauses: Vec<Vec<i32>>,
}

fn implication_graph(source: &[Vec<i32>]) -> Result<(Graph, Sources), String> {
    let cnf = CanonicalCnf::from_signed(source)?;
    if !cnf.is_2cnf() {
        return Err("2-SAT SCC proof extraction requires clauses of width <= 2".into());
    }
    let mut graph = Graph::new();
    for var in cnf.variables() {
        graph.insert(var as i32, BTreeSet::new());
        graph.insert(-(var as i32), BTreeSet::new());
    }
    let mut sources = Sources::new();
    for clause in cnf.clauses {
        let edges = match clause.as_slice() {
            [] => continue,
            [lit] => vec![(-*lit, *lit)],
            [a,b] => vec![(-*a, *b), (-*b, *a)],
            _ => unreachable!(),
        };
        for (from, to) in edges {
            graph.entry(from).or_default().insert(to);
            graph.entry(to).or_default();
            sources.insert((from,to), clause.clone());
        }
    }
    Ok((graph,sources))
}

fn shortest_path(graph: &Graph, start: i32, target: i32) -> Option<Vec<i32>> {
    let mut pending = VecDeque::from([start]);
    let mut parent = BTreeMap::<i32,Option<i32>>::from([(start,None)]);
    while let Some(node) = pending.pop_front() {
        if node == target {
            let mut path = Vec::new();
            let mut cursor = Some(node);
            while let Some(at) = cursor {
                path.push(at);
                cursor = *parent.get(&at)?;
            }
            path.reverse();
            return Some(path);
        }
        if let Some(nexts) = graph.get(&node) {
            for &next in nexts {
                if !parent.contains_key(&next) {
                    parent.insert(next,Some(node));
                    pending.push_back(next);
                }
            }
        }
    }
    None
}

fn annotated_path(nodes: &[i32], sources: &Sources) -> Result<Vec<ProofEdge>, String> {
    let mut path = Vec::new();
    for pair in nodes.windows(2) {
        let (from,to) = (pair[0],pair[1]);
        let clause = sources.get(&(from,to)).ok_or_else(|| {
            format!("implication edge {}->{} has no source clause", from,to)
        })?;
        path.push(ProofEdge{source:from,target:to,clause:clause.clone()});
    }
    if path.is_empty() {
        return Err("2-SAT SCC path must contain at least one implication edge".into());
    }
    Ok(path)
}

fn derived_clauses(path: &[ProofEdge]) -> Result<Vec<Vec<i32>>, String> {
    let mut current = path[0].clause.clone();
    if path.len() == 1 { return Ok(vec![current]); }
    let mut derived = Vec::new();
    for edge in path.iter().skip(1) {
        let pivot = edge.source;
        if current.binary_search(&pivot).is_err() {
            return Err("path resolution pivot missing from current clause".into());
        }
        if edge.clause.binary_search(&-pivot).is_err() {
            return Err("path resolution pivot complement missing from edge clause".into());
        }
        let mut next = BTreeSet::<i32>::new();
        for &lit in current.iter().filter(|&&lit| lit != pivot)
            .chain(edge.clause.iter().filter(|&&lit| lit != -pivot)) {
            if next.contains(&-lit) {
                return Err("path resolution generated tautological intermediate clause".into());
            }
            next.insert(lit);
        }
        current = next.into_iter().collect();
        derived.push(current.clone());
    }
    Ok(derived)
}

pub fn build_2sat_scc_resolution_proof(
    source: &[Vec<i32>], requested_variable: Option<i32>,
) -> Result<SccResolutionProof, String> {
    let (graph,sources) = implication_graph(source)?;
    let variables = graph.keys().map(|v| v.unsigned_abs())
        .collect::<BTreeSet<_>>();
    let candidates = match requested_variable {
        Some(var) => vec![var],
        None => variables.into_iter().map(|v| v as i32).collect(),
    };
    for var in candidates {
        if var <= 0 { continue; }
        let pos = match shortest_path(&graph,var,-var) {
            Some(path) => path, None => continue,
        };
        let neg = match shortest_path(&graph,-var,var) {
            Some(path) => path, None => continue,
        };
        let pos_edges = annotated_path(&pos,&sources)?;
        let neg_edges = annotated_path(&neg,&sources)?;
        let pos_derived = derived_clauses(&pos_edges)?;
        let neg_derived = derived_clauses(&neg_edges)?;
        if pos_derived.is_empty() || neg_derived.is_empty() {
            return Err("2-SAT SCC paths did not derive clauses".into());
        }
        if pos_derived.last() != Some(&vec![-var]) {
            return Err("positive-to-negative SCC path did not derive negative unit".into());
        }
        if neg_derived.last() != Some(&vec![var]) {
            return Err("negative-to-positive SCC path did not derive positive unit".into());
        }
        let mut derived = pos_derived;
        derived.extend(neg_derived);
        return Ok(SccResolutionProof {
            variable: var as u32,
            path_pos_to_neg: pos_edges,
            path_neg_to_pos: neg_edges,
            derived_clauses: derived,
        });
    }
    Err("no mutually reachable variable/negation pair found".into())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn incompatible_units_and_short_resolution_chain() {
        let direct = build_2sat_scc_resolution_proof(
            &[vec![1],vec![-1]],None).unwrap();
        assert_eq!(direct.variable,1);
        assert_eq!(direct.derived_clauses,vec![vec![-1],vec![1]]);
        let chain = build_2sat_scc_resolution_proof(
            &[vec![1,2],vec![-1,2],vec![1,-2],vec![-1,-2]],None).unwrap();
        assert_eq!(chain.variable,1);
        assert_eq!(chain.derived_clauses.last(),Some(&vec![1]));
    }

    #[test]
    fn satisfiable_and_non_two_cnf_rejected() {
        assert_eq!(build_2sat_scc_resolution_proof(
            &[vec![1,2]],None).unwrap_err(),
            "no mutually reachable variable/negation pair found");
        assert_eq!(build_2sat_scc_resolution_proof(
            &[vec![1,2,3]],None).unwrap_err(),
            "2-SAT SCC proof extraction requires clauses of width <= 2");
    }
}
