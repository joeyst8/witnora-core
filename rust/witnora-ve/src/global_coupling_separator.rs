//! R-052: exact two-edge graph-cut witnesses for separator candidate ordering.
//! A graph-only diagnostic; no G14, SAT or Lean proof conclusions.

use std::collections::{BTreeMap, BTreeSet};

pub const CLAIM_BOUNDARY: &str =
    "Exact graph-cut candidates, not G14 recognition, a SAT answer, or a complexity-theory result.";

type Graph = BTreeMap<i32, BTreeSet<i32>>;
type Edge = (i32, i32);

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CutCandidate {
    pub separator: Vec<i32>,
    pub cut_edges: Vec<Edge>,
    pub edge_split_sizes: Vec<usize>,
    pub residual_component_sizes: Vec<usize>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct TwoEdgeCutReport {
    pub vertex_count: usize,
    pub edge_count: usize,
    pub edge_pair_checks: usize,
    pub candidates: Vec<CutCandidate>,
}

fn validate_graph(input: &[(i32, Vec<i32>)]) -> Result<Graph, String> {
    let mut graph = Graph::new();
    for (v, neighbors) in input {
        if graph.insert(*v, neighbors.iter().copied().collect()).is_some() {
            return Err("graph contains repeated vertex keys".into());
        }
    }
    for (&v, neighbors) in &graph {
        if neighbors.contains(&v) {
            return Err("graph contains a self-loop".into());
        }
        for &neighbor in neighbors {
            if !graph.get(&neighbor).is_some_and(|rev| rev.contains(&v)) {
                return Err("graph edges must be symmetric and have known endpoints".into());
            }
        }
    }
    Ok(graph)
}

fn components(
    graph: &Graph,
    omit_vertices: &BTreeSet<i32>,
    omit_edges: &BTreeSet<Edge>,
) -> Vec<Vec<i32>> {
    let mut seen = BTreeSet::<i32>::new();
    let mut result = Vec::new();
    for &root in graph.keys() {
        if omit_vertices.contains(&root) || !seen.insert(root) {
            continue;
        }
        let mut stack = vec![root];
        let mut part = Vec::new();
        while let Some(v) = stack.pop() {
            part.push(v);
            for &neighbor in &graph[&v] {
                if omit_vertices.contains(&neighbor) || seen.contains(&neighbor) {
                    continue;
                }
                let edge = (v.min(neighbor), v.max(neighbor));
                if omit_edges.contains(&edge) {
                    continue;
                }
                seen.insert(neighbor);
                stack.push(neighbor);
            }
        }
        part.sort_unstable();
        result.push(part);
    }
    result
}

pub fn two_edge_cut_boundary_pairs(
    graph_input: &[(i32, Vec<i32>)],
) -> Result<TwoEdgeCutReport, String> {
    let graph = validate_graph(graph_input)?;
    let edges: Vec<Edge> = graph.iter()
        .flat_map(|(&u, neighbors)| neighbors.iter().filter_map(move |&v| {
            (u < v).then_some((u, v))
        }))
        .collect();
    let mut result = TwoEdgeCutReport {
        vertex_count: graph.len(),
        edge_count: edges.len(),
        edge_pair_checks: 0,
        candidates: Vec::new(),
    };
    if graph.is_empty() || components(&graph, &BTreeSet::new(), &BTreeSet::new()).len() != 1 {
        return Ok(result);
    }
    let mut candidates = BTreeMap::<(i32,i32),CutCandidate>::new();
    for i in 0..edges.len() {
        for j in (i+1)..edges.len() {
            result.edge_pair_checks += 1;
            let first = edges[i];
            let second = edges[j];
            let cut = BTreeSet::from([first, second]);
            let pieces = components(&graph, &BTreeSet::new(), &cut);
            if pieces.len() != 2 {
                continue;
            }
            let side: BTreeSet<i32> = pieces[0].iter().copied().collect();
            if [first,second].iter().any(|&(u,v)| side.contains(&u)==side.contains(&v)) {
                continue;
            }
            for part in &pieces {
                let vertices: BTreeSet<i32> = part.iter().copied().collect();
                let mut boundary: Vec<i32> = [first, second].iter()
                    .flat_map(|&(u,v)| [u,v])
                    .filter(|v| vertices.contains(v))
                    .collect();
                boundary.sort_unstable();
                if boundary.len() != 2 || boundary[0] == boundary[1] {
                    continue;
                }
                let key = (boundary[0], boundary[1]);
                if candidates.contains_key(&key) {
                    continue;
                }
                let removed = BTreeSet::from([key.0,key.1]);
                let residual = components(&graph, &removed, &BTreeSet::new());
                if residual.len() <= 1 {
                    continue;
                }
                let mut residual_sizes: Vec<usize> = residual.iter().map(Vec::len).collect();
                residual_sizes.sort_unstable();
                candidates.insert(key, CutCandidate {
                    separator: boundary,
                    cut_edges: vec![first, second],
                    edge_split_sizes: pieces.iter().map(Vec::len).collect(),
                    residual_component_sizes: residual_sizes,
                });
            }
        }
    }
    result.candidates = candidates.into_values().collect();
    result.candidates.sort_by(|a,b| {
        b.residual_component_sizes[0].cmp(&a.residual_component_sizes[0])
            .then_with(|| a.residual_component_sizes.last()
                .cmp(&b.residual_component_sizes.last()))
            .then_with(|| a.separator.cmp(&b.separator))
    });
    Ok(result)
}

pub fn prioritized_global_pairs(
    graph_input: &[(i32, Vec<i32>)],
) -> Result<Vec<Edge>, String> {
    let report = two_edge_cut_boundary_pairs(graph_input)?;
    let mut chosen = BTreeSet::<Edge>::new();
    let mut order = Vec::new();
    for candidate in report.candidates {
        let pair = (candidate.separator[0], candidate.separator[1]);
        if chosen.insert(pair) {
            order.push(pair);
        }
    }
    let mut vertices: Vec<i32> = graph_input.iter().map(|(v,_)| *v).collect();
    vertices.sort_unstable();
    for i in 0..vertices.len() {
        for j in (i+1)..vertices.len() {
            let pair = (vertices[i], vertices[j]);
            if chosen.insert(pair) {
                order.push(pair);
            }
        }
    }
    Ok(order)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn cycle_square_has_exact_symmetric_witnesses() {
        let square=vec![
            (1,vec![2,4]), (2,vec![1,3]),
            (3,vec![2,4]), (4,vec![1,3]),
        ];
        let report=two_edge_cut_boundary_pairs(&square).unwrap();
        assert_eq!(report.vertex_count,4);
        assert_eq!(report.edge_count,4);
        assert_eq!(report.edge_pair_checks,6);
        assert_eq!(report.candidates.len(),2);
        let pairs: Vec<_> = report.candidates.iter()
            .map(|c| c.separator.clone()).collect();
        assert_eq!(pairs,vec![vec![1,3],vec![2,4]]);
        let order=prioritized_global_pairs(&square).unwrap();
        assert_eq!(order.len(),6);
        assert_eq!(order[..2],[(1,3),(2,4)]);
    }
    #[test]
    fn disconnected_and_invalid_fail_closed() {
        let disconnected=vec![(1,vec![]),(2,vec![])];
        let report=two_edge_cut_boundary_pairs(&disconnected).unwrap();
        assert_eq!(report.edge_pair_checks,0);
        assert!(report.candidates.is_empty());
        assert!(two_edge_cut_boundary_pairs(&[(1,vec![1])]).is_err());
        assert!(two_edge_cut_boundary_pairs(&[(1,vec![2]),(2,vec![])]).is_err());
    }
}
