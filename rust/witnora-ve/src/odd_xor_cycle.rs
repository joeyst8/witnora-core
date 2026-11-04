//! R-041: exact-source binary-XOR odd-cycle discovery.
//! This returns UNVERIFIED candidates only; Lean source-bound verification
//! is a separate trust gate, never implied by graph cycle detection.

use crate::cnf::CanonicalCnf;
use std::collections::{BTreeMap,BTreeSet,VecDeque};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct OddCycle {
    pub start:i32,
    pub steps:Vec<(i32,u32)>,
}

fn pattern_clauses(u:i32,v:i32,rhs:u32)->BTreeSet<Vec<i32>> {
    let mut expected=BTreeSet::new();
    for left in 0..=1u32 {
        for right in 0..=1u32 {
            if left^right==rhs { continue; }
            let mut clause=vec![
                if left==1 {-u} else {u},
                if right==1 {-v} else {v},
            ];
            clause.sort_unstable();
            expected.insert(clause);
        }
    }
    expected
}

fn binary_equations(clauses:&[Vec<i32>])->Vec<(i32,i32,u32)> {
    let existing=clauses.iter().cloned().collect::<BTreeSet<_>>();
    let mut pairs=BTreeSet::new();
    for clause in clauses {
        if clause.len()!=2 { continue; }
        let u=clause[0].abs();
        let v=clause[1].abs();
        if u!=v { pairs.insert((u.min(v),u.max(v))); }
    }
    let mut result=Vec::new();
    for (u,v) in pairs {
        for rhs in 0..=1 {
            if pattern_clauses(u,v,rhs).is_subset(&existing) {
                result.push((u,v,rhs));
            }
        }
    }
    result
}

fn existing_path(
    adj:&BTreeMap<i32,Vec<(i32,u32)>>,
    start:i32,target:i32,
)->Option<Vec<(i32,u32)>> {
    let mut queue=VecDeque::from([start]);
    let mut parent=BTreeMap::<i32,Option<(i32,u32)>>::from([(start,None)]);
    while let Some(node)=queue.pop_front() {
        if node==target { break; }
        let mut nexts=adj.get(&node).cloned().unwrap_or_default();
        nexts.sort_unstable();
        for (neighbor,rhs) in nexts {
            if !parent.contains_key(&neighbor) {
                parent.insert(neighbor,Some((node,rhs)));
                queue.push_back(neighbor);
            }
        }
    }
    if !parent.contains_key(&target) { return None; }
    let mut reversed=Vec::new();
    let mut node=target;
    while node!=start {
        let (prev,rhs)=parent.get(&node).copied().flatten()?;
        reversed.push((node,rhs));
        node=prev;
    }
    reversed.reverse();
    Some(reversed)
}

pub fn discover_odd_xor_cycle(
    source:&[Vec<i32>],
)->Result<Option<OddCycle>,String> {
    let formula=CanonicalCnf::from_signed(source)?;
    let mut adjacency=BTreeMap::<i32,Vec<(i32,u32)>>::new();
    for (u,v,rhs) in binary_equations(&formula.clauses) {
        if let Some(path)=existing_path(&adjacency,u,v) {
            let syndrome=path.iter().fold(0,|acc,(_,bit)|acc^bit);
            if syndrome!=rhs {
                let mut steps=path;
                steps.push((u,rhs));
                return Ok(Some(OddCycle{start:u,steps}));
            }
        }
        adjacency.entry(u).or_default().push((v,rhs));
        adjacency.entry(v).or_default().push((u,rhs));
    }
    Ok(None)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn contradictory_triangle_and_partial_pattern() {
        let source=vec![
            vec![1,-2],vec![-1,2],
            vec![2,-3],vec![-2,3],
            vec![1,3],vec![-1,-3],
        ];
        let cycle=discover_odd_xor_cycle(&source).unwrap().unwrap();
        assert_eq!(cycle.start,2);
        assert_eq!(cycle.steps.last().unwrap().0,2);
        assert_eq!(cycle.steps.iter().map(|(_,bit)|bit).sum::<u32>()%2,1);
        assert!(discover_odd_xor_cycle(&[vec![1,2]]).unwrap().is_none());
    }
}
