//! R-063: deterministic bipartition audit; not an independent graph theorem.
use std::collections::{BTreeSet, VecDeque};

pub fn bipartition(n: usize, edges: &[(usize, usize)]) -> Result<Option<Vec<i32>>, String> {
    if n > 4096 { return Err("vertex budget exceeded".into()); }
    let mut adjacency = vec![BTreeSet::<usize>::new(); n];
    for &(u,v) in edges {
        if u >= n || v >= n { return Err("edge outside graph".into()); }
        adjacency[u].insert(v);
        adjacency[v].insert(u);
    }
    let mut parts = vec![-1; n];
    for root in 0..n {
        if parts[root] >= 0 { continue; }
        parts[root] = 0;
        let mut queue = VecDeque::from([root]);
        while let Some(u) = queue.pop_front() {
            for &v in &adjacency[u] {
                if parts[v] < 0 {
                    parts[v] = 1 - parts[u];
                    queue.push_back(v);
                } else if parts[v] == parts[u] {
                    return Ok(None);
                }
            }
        }
    }
    Ok(Some(parts))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn odd_cycle_and_disconnected() {
        assert_eq!(bipartition(3,&[(0,1),(1,2),(0,2)]),Ok(None));
        assert_eq!(bipartition(4,&[(0,1),(2,3)]),Ok(Some(vec![0,1,0,1])));
        assert_eq!(bipartition(0,&[]),Ok(Some(vec![])));
        assert!(bipartition(3,&[(0,3)]).is_err());
    }
}
