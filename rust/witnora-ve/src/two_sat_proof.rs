//! R-021: exact source-compatible 2-SAT SCC proof-event metadata.
//!
//! The node, edge, SCC visit, and assignment order deliberately match
//! Witnora's original Python certificate producer so the unchanged
//! logger can replay the same proof details.

use crate::cnf::CanonicalCnf;
use std::collections::{BTreeMap, BTreeSet};

type SignedGraph = BTreeMap<i32, BTreeSet<i32>>;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct TwoSatProof {
    pub sat: bool,
    pub empty_clause: bool,
    pub conflict_variable: Option<u32>,
    pub edges: Vec<(i32, i32)>,
    pub components: Vec<Vec<i32>>,
    pub assignment: Vec<(u32, bool)>,
    pub node_count: usize,
}

fn add_edge(g: &mut SignedGraph, from: i32, to: i32) {
    g.entry(from).or_default().insert(to);
    g.entry(to).or_default();
}

fn dfs1(node: i32, g: &SignedGraph, seen: &mut BTreeSet<i32>, order: &mut Vec<i32>) {
    seen.insert(node);
    for &next in &g[&node] {
        if !seen.contains(&next) {
            dfs1(next, g, seen, order);
        }
    }
    order.push(node);
}

fn dfs2(node: i32, g: &SignedGraph, comp: &mut BTreeMap<i32,usize>,
        label: usize, nodes: &mut Vec<i32>) {
    comp.insert(node, label);
    nodes.push(node);
    for &next in &g[&node] {
        if !comp.contains_key(&next) {
            dfs2(next, g, comp, label, nodes);
        }
    }
}

pub fn solve_2sat_proof(source: &[Vec<i32>]) -> Result<TwoSatProof, String> {
    let cnf = CanonicalCnf::from_signed(source)?;
    if !cnf.is_2cnf() {
        return Err("formula is not 2-CNF".into());
    }
    if cnf.has_empty_clause() {
        return Ok(TwoSatProof {
            sat:false, empty_clause:true, conflict_variable:None,
            edges:vec![], components:vec![], assignment:vec![], node_count:0,
        });
    }
    let vars = cnf.variables();
    if vars.len() > 256 {
        return Err("native 2-SAT proof universe cap exceeded".into());
    }
    let mut graph = SignedGraph::new();
    for &var in &vars {
        graph.insert(var as i32, BTreeSet::new());
        graph.insert(-(var as i32), BTreeSet::new());
    }
    for clause in &cnf.clauses {
        match clause.as_slice() {
            [a] => add_edge(&mut graph, -*a, *a),
            [a,b] => {
                add_edge(&mut graph, -*a, *b);
                add_edge(&mut graph, -*b, *a);
            }
            [] => {},
            _ => return Err("formula is not 2-CNF".into()),
        }
    }
    let mut reverse = graph.keys().map(|&v| (v,BTreeSet::new()))
        .collect::<SignedGraph>();
    for (src, dsts) in &graph {
        for &dst in dsts {
            reverse.get_mut(&dst).unwrap().insert(*src);
        }
    }
    let mut seen = BTreeSet::new();
    let mut order = Vec::new();
    for &node in graph.keys() {
        if !seen.contains(&node) {
            dfs1(node,&graph,&mut seen,&mut order);
        }
    }
    let mut comp = BTreeMap::new();
    let mut components = Vec::new();
    for &node in order.iter().rev() {
        if comp.contains_key(&node) {
            continue;
        }
        let mut nodes = Vec::new();
        dfs2(node, &reverse, &mut comp, components.len(), &mut nodes);
        nodes.sort();
        components.push(nodes);
    }
    let edges = graph.iter().flat_map(|(&src, dsts)| {
        dsts.iter().map(move |&dst| (src,dst))
    }).collect::<Vec<_>>();
    if let Some(&var) = vars.iter()
        .find(|&&v| comp[&(v as i32)] == comp[&(-(v as i32))])
    {
        return Ok(TwoSatProof {
            sat:false,empty_clause:false,conflict_variable:Some(var),
            edges,components,assignment:vec![],node_count:graph.len(),
        });
    }
    let mut assignment = vars.iter().map(|&v| {
        (v, comp[&(v as i32)] > comp[&(-(v as i32))])
    }).collect::<Vec<_>>();
    let mapped = |rows:&Vec<(u32,bool)>| rows.iter().copied()
        .collect::<BTreeMap<_,_>>();
    if !cnf.satisfied(&mapped(&assignment)) {
        for (_,value) in &mut assignment {
            *value = !*value;
        }
    }
    if !cnf.satisfied(&mapped(&assignment)) {
        return Err("native 2-SAT proof witness failed source verification".into());
    }
    Ok(TwoSatProof {
        sat:true,empty_clause:false, conflict_variable:None,
        edges,components,assignment,node_count:graph.len(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_conflicting_and_sat_source() {
        assert!(solve_2sat_proof(&[]).unwrap().sat);
        let empty = solve_2sat_proof(&[vec![]]).unwrap();
        assert!(!empty.sat && empty.empty_clause);
        let unsat = solve_2sat_proof(&[vec![1],vec![-1]]).unwrap();
        assert_eq!(unsat.conflict_variable, Some(1));
        let sat = solve_2sat_proof(&[vec![1],vec![-1,2]]).unwrap();
        assert!(sat.sat);
        assert_eq!(sat.assignment, vec![(1,true),(2,true)]);
        assert!(sat.node_count == 4);
    }
}
