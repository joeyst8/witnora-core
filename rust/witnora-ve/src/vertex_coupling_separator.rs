//! R-051: all two-vertex graph-cut hints in connected articulation-free
//! graphs, using a verified iterative articulation scan for each deletion.
//! These graph-theoretic candidates never certify G14/CNF/Lean conclusions.

use crate::separator_structural_priority::articulation_vertices;
use std::collections::{BTreeMap,BTreeSet};

pub const CLAIM_BOUNDARY:&str=
    "Complete graph-theoretic two-vertex-cut hints only for \
connected graphs with no articulation vertex; no SAT claim.";

#[derive(Clone,Debug,PartialEq,Eq)]
pub struct VertexPairReport {
    pub vertex_count:usize,
    pub articulation_scans:usize,
    pub complete_for_two_vertex_cuts:bool,
    pub candidates:Vec<(i32,i32)>,
}

fn validate_graph(
    graph:&[(i32,Vec<i32>)],
)->Result<BTreeMap<i32,BTreeSet<i32>>,String> {
    let mut adjacency=BTreeMap::<i32,BTreeSet<i32>>::new();
    for (v,neighbors) in graph {
        if adjacency.insert(*v,neighbors.iter().copied().collect()).is_some(){
            return Err("duplicate graph vertex".into());
        }
    }
    for (&v,neighbors) in &adjacency {
        if neighbors.contains(&v) {
            return Err("graph contains a self-loop".into());
        }
        for &other in neighbors {
            if !adjacency.get(&other).is_some_and(|s|s.contains(&v)) {
                return Err(
                    "graph edges must be symmetric and have known endpoints".into()
                );
            }
        }
    }
    Ok(adjacency)
}

fn connected_parts(
    adjacency:&BTreeMap<i32,BTreeSet<i32>>,
)->Vec<Vec<i32>> {
    let mut remaining=adjacency.keys().copied().collect::<BTreeSet<_>>();
    let mut groups=Vec::new();
    while let Some(&start)=remaining.iter().next(){
        remaining.remove(&start);
        let mut part=vec![start];
        let mut stack=vec![start];
        while let Some(v)=stack.pop(){
            for &neighbor in &adjacency[&v]{
                if remaining.remove(&neighbor){
                    part.push(neighbor);
                    stack.push(neighbor);
                }
            }
        }
        part.sort_unstable();
        groups.push(part);
    }
    groups
}

fn packed(adjacency:&BTreeMap<i32,BTreeSet<i32>>)->Vec<(i32,Vec<i32>)>{
    adjacency.iter().map(|(&v,ns)|
        (v,ns.iter().copied().collect())
    ).collect()
}

pub fn vertex_coupling_pairs(
    graph:&[(i32,Vec<i32>)],
)->Result<VertexPairReport,String> {
    let adjacency=validate_graph(graph)?;
    let mut report=VertexPairReport {
        vertex_count:adjacency.len(),articulation_scans:0,
        complete_for_two_vertex_cuts:false,candidates:Vec::new(),
    };
    if adjacency.len()<3 || connected_parts(&adjacency).len()!=1 {
        return Ok(report);
    }
    if !articulation_vertices(&packed(&adjacency))?.is_empty(){
        return Ok(report);
    }
    report.complete_for_two_vertex_cuts=true;
    let mut pairs=BTreeSet::<(i32,i32)>::new();
    for &removed in adjacency.keys(){
        let remainder=adjacency.iter()
            .filter(|(v,_)|**v!=removed)
            .map(|(&v,ns)|{
                let mut neighbors=ns.clone();
                neighbors.remove(&removed);
                (v,neighbors)
            }).collect::<BTreeMap<_,_>>();
        report.articulation_scans+=1;
        for cut in articulation_vertices(&packed(&remainder))? {
            pairs.insert((removed.min(cut),removed.max(cut)));
        }
    }
    report.candidates=pairs.into_iter().collect();
    Ok(report)
}

pub fn prioritized_vertex_pairs(
    graph:&[(i32,Vec<i32>)],
)->Result<Vec<(i32,i32)>,String> {
    let report=vertex_coupling_pairs(graph)?;
    let mut result=report.candidates;
    let mut seen=result.iter().copied().collect::<BTreeSet<_>>();
    let mut vertices=graph.iter().map(|(v,_)|*v).collect::<Vec<_>>();
    vertices.sort_unstable();
    for i in 0..vertices.len() {
        for j in (i+1)..vertices.len(){
            let pair=(vertices[i],vertices[j]);
            if seen.insert(pair) {
                result.push(pair);
            }
        }
    }
    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn four_cycle_has_opposite_vertex_pair_cuts() {
        let graph=vec![
            (1,vec![2,4]),(2,vec![1,3]),
            (3,vec![2,4]),(4,vec![1,3]),
        ];
        let report=vertex_coupling_pairs(&graph).unwrap();
        assert!(report.complete_for_two_vertex_cuts);
        assert_eq!(report.articulation_scans,4);
        assert_eq!(report.candidates,vec![(1,3),(2,4)]);
        let order=prioritized_vertex_pairs(&graph).unwrap();
        assert_eq!(&order[..2],&[(1,3),(2,4)]);
        assert_eq!(order.len(),6);
        assert!(vertex_coupling_pairs(&[(1,vec![1])]).is_err());
    }
}
