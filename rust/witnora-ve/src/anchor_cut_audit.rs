//! R-065: full-source primal reachability after deleting a candidate cut.
//! A structural check, not a Lean certificate or SAT proof.
use std::collections::{BTreeMap, BTreeSet, VecDeque};

pub fn anchors_separated(
    clauses: &[Vec<i32>], cut: &[u32], left: u32, right: u32,
) -> Result<bool, String> {
    if clauses.iter().flatten().any(|&lit|lit==0) {
        return Err("zero literal outside CNF domain".into());
    }
    let excluded: BTreeSet<u32> = cut.iter().copied().collect();
    if excluded.contains(&left) || excluded.contains(&right) { return Ok(false); }
    let mut neighbors: BTreeMap<u32,BTreeSet<u32>> = BTreeMap::new();
    for clause in clauses {
        let vars: BTreeSet<u32> = clause.iter().map(|lit|lit.unsigned_abs())
            .filter(|v|!excluded.contains(v)).collect();
        for &v in &vars {
            neighbors.entry(v).or_default().extend(vars.iter().copied().filter(|&x|x!=v));
        }
    }
    let mut reached = BTreeSet::from([left]);
    let mut queue = VecDeque::from([left]);
    while let Some(current) = queue.pop_front() {
        if let Some(next) = neighbors.get(&current) {
            for &v in next {
                if reached.insert(v) { queue.push_back(v); }
            }
        }
    }
    Ok(!reached.contains(&right))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn cut_and_shared_clause() {
        let cnf=vec![vec![1,2],vec![-2,3]];
        assert_eq!(anchors_separated(&cnf,&[2],1,3),Ok(true));
        assert_eq!(anchors_separated(&cnf,&[],1,3),Ok(false));
        assert_eq!(anchors_separated(&cnf,&[1],1,3),Ok(false));
    }
}
