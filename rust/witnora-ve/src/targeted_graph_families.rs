//! R-060: deterministic graph family constructors for bounded conjecture tests.
//! Constructing examples supplies neither a theorem nor novelty evidence.

use std::collections::BTreeSet;
type Edge = (usize, usize);

pub fn cycle(n: usize) -> (usize, Vec<Edge>) {
    let edges: BTreeSet<Edge> = (0..n).map(|i| {
        let j = (i + 1) % n;
        (i.min(j), i.max(j))
    }).collect();
    (n, edges.into_iter().collect())
}

pub fn wheel(n: usize) -> (usize, Vec<Edge>) {
    let (base_n, edges) = cycle(n - 1);
    let mut edges: BTreeSet<Edge> = edges.into_iter().collect();
    for i in 0..base_n { edges.insert((i, n - 1)); }
    (n, edges.into_iter().collect())
}

pub fn complete_bipartite(a: usize, b: usize) -> (usize, Vec<Edge>) {
    (a + b, (0..a).flat_map(|u| (0..b).map(move |v| (u, a + v))).collect())
}

pub fn mycielski_c5() -> (usize, Vec<Edge>) {
    let (_, base) = cycle(5);
    let mut edges: BTreeSet<Edge> = base.iter().copied().collect();
    for (u, v) in base {
        let a = (u.min(5 + v), u.max(5 + v));
        let b = (v.min(5 + u), v.max(5 + u));
        edges.insert(a);
        edges.insert(b);
    }
    for i in 0..5 { edges.insert((5 + i, 10)); }
    (11, edges.into_iter().collect())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn known_graph_sizes() {
        assert_eq!(cycle(5).1.len(), 5);
        assert_eq!(wheel(6).1.len(), 10);
        assert_eq!(complete_bipartite(3, 4).1.len(), 12);
        assert_eq!(mycielski_c5().1.len(), 20);
    }
}
