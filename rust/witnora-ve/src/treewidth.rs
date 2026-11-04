//! R-017: exact bounded-width primal-graph elimination ordering.
//!
//! Search reproduces Python's deterministic degree-then-ID candidate
//! order, complete fill edges and failed-state memoization. A hard
//! finite search cap produces an ERROR, not a false "no width-c order".

use std::collections::{BTreeMap, BTreeSet};

type Graph = BTreeMap<u32, BTreeSet<u32>>;
type State = (Vec<u32>, Vec<(u32, u32)>);

fn validate_graph(nodes: &[(u32, Vec<u32>)]) -> Result<Graph, String> {
    let mut graph = Graph::new();
    for (v, neighbours) in nodes {
        if *v == 0 || graph.contains_key(v) {
            return Err("duplicate/invalid graph vertex".into());
        }
        let mut neighs = BTreeSet::new();
        for &other in neighbours {
            if other == 0 || other == *v || !neighs.insert(other) {
                return Err("invalid self-loop/duplicate graph neighbour".into());
            }
        }
        graph.insert(*v, neighs);
    }
    for (v, neighbours) in &graph {
        for other in neighbours {
            if !graph.get(other).is_some_and(|n| n.contains(v)) {
                return Err("graph is not a symmetric simple graph".into());
            }
        }
    }
    Ok(graph)
}

fn state(graph: &Graph) -> State {
    let nodes = graph.keys().copied().collect();
    let mut edges = Vec::new();
    for (v, neighbours) in graph {
        for &other in neighbours {
            if *v < other {
                edges.push((*v, other));
            }
        }
    }
    (nodes, edges)
}

fn eliminate(graph: &Graph, variable: u32) -> Graph {
    let mut next = graph.clone();
    let neighbours: Vec<u32> = graph[&variable].iter().copied().collect();
    next.remove(&variable);
    for &a in &neighbours {
        if let Some(row) = next.get_mut(&a) {
            row.remove(&variable);
        }
    }
    for (i, &a) in neighbours.iter().enumerate() {
        for &b in &neighbours[i+1..] {
            next.get_mut(&a).unwrap().insert(b);
            next.get_mut(&b).unwrap().insert(a);
        }
    }
    next
}

fn width_of_order(graph: &Graph, order: &[u32]) -> Option<usize> {
    let order_set: BTreeSet<_> = order.iter().copied().collect();
    if order.len() != graph.len() || order_set.len() != graph.len()
        || order_set != graph.keys().copied().collect()
    {
        return None;
    }
    let mut current = graph.clone();
    let mut max_width = 0;
    for &v in order {
        max_width = max_width.max(current.get(&v)?.len());
        current = eliminate(&current, v);
    }
    if current.is_empty() { Some(max_width) } else { None }
}

fn search(graph: &Graph, cap: usize, failed: &mut BTreeSet<State>,
          explored: &mut usize, max_states: usize) -> Result<Option<Vec<u32>>, String> {
    if graph.is_empty() {
        return Ok(Some(vec![]));
    }
    let signature = state(graph);
    if failed.contains(&signature) {
        return Ok(None);
    }
    *explored += 1;
    if *explored > max_states {
        return Err("native treewidth search budget exhausted".into());
    }
    let mut candidates: Vec<_> = graph.iter()
        .filter(|(_, n)| n.len() <= cap)
        .map(|(&v, n)| (n.len(), v)).collect();
    candidates.sort_unstable();
    for (_, v) in candidates {
        if let Some(rest) = search(&eliminate(graph, v), cap, failed,
                                   explored, max_states)? {
            let mut order = vec![v];
            order.extend(rest);
            return Ok(Some(order));
        }
    }
    failed.insert(signature);
    Ok(None)
}

pub fn find_elimination_order(
    nodes: &[(u32, Vec<u32>)], width_cap: usize,
    max_states: usize,
) -> Result<Option<Vec<u32>>, String> {
    if width_cap > 4 || max_states == 0 {
        return Err("Witnora exact treewidth width/budget unsupported".into());
    }
    let graph = validate_graph(nodes)?;
    let mut failed = BTreeSet::new();
    let mut explored = 0;
    let result = search(&graph, width_cap, &mut failed,
                        &mut explored, max_states)?;
    if let Some(ref order) = result {
        if width_of_order(&graph, order).is_none_or(|w| w > width_cap) {
            return Err("native treewidth output failed independent width check".into());
        }
    }
    Ok(result)
}

pub fn verify_elimination_order(
    nodes: &[(u32, Vec<u32>)], order: &[u32],
) -> Result<Option<usize>, String> {
    let graph = validate_graph(nodes)?;
    Ok(width_of_order(&graph, order))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn undirected(n: u32, edges: &[(u32, u32)]) -> Vec<(u32, Vec<u32>)> {
        let mut g: Graph = (1..=n).map(|v|(v, BTreeSet::new())).collect();
        for &(a,b) in edges {
            g.get_mut(&a).unwrap().insert(b);
            g.get_mut(&b).unwrap().insert(a);
        }
        g.into_iter().map(|(a, b)|(a,b.into_iter().collect())).collect()
    }

    #[test]
    fn path_cycle_and_clique_widths() {
        let path = undirected(5, &[(1,2),(2,3),(3,4),(4,5)]);
        let order = find_elimination_order(&path, 1, 10000).unwrap().unwrap();
        assert_eq!(verify_elimination_order(&path, &order).unwrap(), Some(1));
        let cycle = undirected(4, &[(1,2),(2,3),(3,4),(4,1)]);
        assert!(find_elimination_order(&cycle, 1, 10000).unwrap().is_none());
        assert!(find_elimination_order(&cycle, 2, 10000).unwrap().is_some());
        let clique = undirected(5, &[(1,2),(1,3),(1,4),(1,5),
            (2,3),(2,4),(2,5),(3,4),(3,5),(4,5)]);
        assert!(find_elimination_order(&clique, 3, 10000).unwrap().is_none());
        assert!(find_elimination_order(&clique, 4, 10000).unwrap().is_some());
    }

    #[test]
    fn invalid_graphs_and_budget_refusal() {
        assert!(find_elimination_order(&[(1,vec![2])], 1, 10000).is_err());
        assert!(find_elimination_order(&[(1,vec![])], 5, 10000).is_err());
        assert!(find_elimination_order(&[(1,vec![])], 0, 0).is_err());
    }
}
