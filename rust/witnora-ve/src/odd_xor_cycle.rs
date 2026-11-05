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

/// W-CROSSDOMAIN-002: signed-graph balance/cycle-space diagnostic.
/// Only applies when the entire canonical source is made of complete
/// binary-XOR CNF gadgets. This is not a general #SAT verifier.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct BinaryXorTopology {
    pub variables: usize,
    pub equation_edges: usize,
    pub components: usize,
    pub cycle_space_dimension: usize,
    pub inconsistent_cycle_candidate: bool,
    pub exact_model_count_if_pure: String,
}

pub fn pure_binary_xor_topology(
    source: &[Vec<i32>], nvars: usize,
) -> Result<Option<BinaryXorTopology>, String> {
    if nvars > 32 { return Err("binary topology diagnostic supports <=32 variables".into()); }
    let formula = CanonicalCnf::from_signed(source)?;
    if formula.max_var() as usize > nvars {
        return Err("source variable exceeds declared universe".into());
    }
    let equations = binary_equations(&formula.clauses);
    let mut accounted = BTreeSet::<Vec<i32>>::new();
    for &(u, v, rhs) in &equations {
        accounted.extend(pattern_clauses(u, v, rhs));
    }
    let original = formula.clauses.iter().cloned().collect::<BTreeSet<_>>();
    if accounted != original { return Ok(None); }

    fn root(parents: &mut [usize], mut index: usize) -> usize {
        while parents[index] != index {
            let parent = parents[index];
            parents[index] = parents[parent];
            index = parents[index];
        }
        index
    }
    let mut parents = (0..nvars).collect::<Vec<_>>();
    let mut components = nvars;
    for &(u, v, _) in &equations {
        let a = root(&mut parents, u as usize - 1);
        let b = root(&mut parents, v as usize - 1);
        if a != b {
            parents[b] = a;
            components -= 1;
        }
    }
    // Multi-edges are intentional: opposite RHS on the same support give
    // an inconsistent length-two cycle and one independent cycle relation.
    let cycle_space_dimension = equations.len() - (nvars - components);
    let inconsistent = discover_odd_xor_cycle(&formula.clauses)?.is_some();
    let model_count = if inconsistent { 0u64 } else { 1u64 << components };
    Ok(Some(BinaryXorTopology {
        variables: nvars,
        equation_edges: equations.len(),
        components,
        cycle_space_dimension,
        inconsistent_cycle_candidate: inconsistent,
        exact_model_count_if_pure: model_count.to_string(),
    }))
}

pub(crate) fn pattern_clauses(u:i32,v:i32,rhs:u32)->BTreeSet<Vec<i32>> {
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

pub(crate) fn binary_equations(clauses:&[Vec<i32>])->Vec<(i32,i32,u32)> {
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

    #[test]
    fn signed_graph_cycle_space_matches_independent_source_truth_tables() {
        let families: &[(&[(i32, i32)], usize)] = &[
            (&[(1, 2), (2, 3), (1, 3)], 3),
            (&[(1, 2), (2, 3), (3, 4), (1, 4)], 4),
            (&[(1, 2), (2, 3), (1, 3), (1, 4), (4, 5), (1, 5)], 5),
            (&[(1, 2), (1, 2)], 3),
        ];
        for &(edges, n) in families {
            for bits in 0..(1usize << edges.len()) {
                let mut clauses = Vec::new();
                for (index, &(u, v)) in edges.iter().enumerate() {
                    clauses.extend(pattern_clauses(u, v, ((bits >> index) & 1) as u32));
                }
                let answer = pure_binary_xor_topology(&clauses, n).unwrap().unwrap();
                let oracle = (0..(1usize << n)).filter(|&assignment| {
                    clauses.iter().all(|clause| clause.iter().any(|&lit| {
                        let value = assignment & (1usize << (lit.unsigned_abs() as usize - 1)) != 0;
                        value == (lit > 0)
                    }))
                }).count();
                assert_eq!(answer.exact_model_count_if_pure, oracle.to_string());
                assert_eq!(answer.inconsistent_cycle_candidate, oracle == 0);
                assert_eq!(answer.cycle_space_dimension,
                           answer.equation_edges - (n - answer.components));
            }
        }
        assert!(pure_binary_xor_topology(&[vec![1, 2]], 2).unwrap().is_none());
        assert!(pure_binary_xor_topology(&[vec![1]], 2).unwrap().is_none());
    }

    #[test]
    fn cycle_diagnostic_matches_native_gaussian_and_finite_source_oracle() {
        // W-CROSSDOMAIN-003: deterministically generated complete source-CNF
        // gadgets, including duplicate supports and contradictory labels.
        // The Gaussian implementation is a distinct GF(2) algorithm.
        let mut state = 0x52917u64;
        let mut next = || {
            state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
            state >> 32
        };
        for n in 2..=8usize {
            for trial in 0..64usize {
                let mut clauses = Vec::new();
                let mut equations = Vec::<(Vec<usize>,u8)>::new();
                for _ in 0..(n + trial % (n + 2)) {
                    let u = (next() as usize % n) + 1;
                    let mut v = (next() as usize % (n - 1)) + 1;
                    if v >= u { v += 1; }
                    let rhs = (next() & 1) as u8;
                    clauses.extend(pattern_clauses(u as i32, v as i32, rhs as u32));
                    equations.push((vec![u, v], rhs));
                }
                let routed = pure_binary_xor_topology(&clauses, n).unwrap().unwrap();
                let gaussian_contradiction = crate::xor_equations::gaussian(&equations).0;
                let direct_count = (0..(1usize << n)).filter(|&assignment| {
                    clauses.iter().all(|clause| clause.iter().any(|&lit| {
                        let bit = assignment & (1usize << (lit.unsigned_abs() as usize - 1)) != 0;
                        bit == (lit > 0)
                    }))
                }).count();
                assert_eq!(routed.inconsistent_cycle_candidate, gaussian_contradiction);
                assert_eq!(routed.exact_model_count_if_pure, direct_count.to_string());
            }
        }
    }

    #[test]
    fn mixed_sources_fail_closed_before_any_pure_xor_count() {
        let mut source = Vec::new();
        source.extend(pattern_clauses(1, 2, 0));
        source.extend(pattern_clauses(2, 3, 0));
        assert_eq!(pure_binary_xor_topology(&source, 3).unwrap().unwrap()
                   .exact_model_count_if_pure, "2");

        for additional in [vec![1], vec![-1], vec![1, 3], vec![]] {
            let mut mixed = source.clone();
            mixed.push(additional);
            assert!(pure_binary_xor_topology(&mixed, 3).unwrap().is_none());
        }
        assert!(pure_binary_xor_topology(&[vec![1, 2]], 3).unwrap().is_none());
        assert!(pure_binary_xor_topology(&[vec![4]], 3).is_err());
    }
}
