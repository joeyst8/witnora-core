//! R-048: experimental graph-invariant DP elimination policies.
//! Min-fill, XOR-boundary and max-release are scheduling heuristics; exact
//! resolution is established mathematics, not a new proof or runtime bound.

use crate::cnf::CanonicalCnf;
use crate::spoke_discovery::extract_binary_xor_equations;
use crate::two_ply_lookahead::elimination_options;
use std::collections::{BTreeMap,BTreeSet};

#[derive(Clone,Debug,PartialEq,Eq)]
pub struct GraphInvariants {
    pub degree:BTreeMap<u32,usize>,
    pub fill:BTreeMap<u32,usize>,
    pub xor_degree:BTreeMap<u32,usize>,
}

pub fn graph_invariants(formula:&CanonicalCnf)->GraphInvariants {
    let variables=formula.variables();
    let mut neighbors=variables.iter().map(|&v|
        (v,BTreeSet::<u32>::new())
    ).collect::<BTreeMap<_,_>>();
    for clause in &formula.clauses {
        let support=clause.iter().map(|lit|lit.unsigned_abs())
            .collect::<BTreeSet<_>>().into_iter().collect::<Vec<_>>();
        for i in 0..support.len() {
            for j in (i+1)..support.len() {
                let (a,b)=(support[i],support[j]);
                neighbors.get_mut(&a).unwrap().insert(b);
                neighbors.get_mut(&b).unwrap().insert(a);
            }
        }
    }
    let mut xor_degree=variables.iter().map(|&v|(v,0usize))
        .collect::<BTreeMap<_,_>>();
    for (u,v,_) in extract_binary_xor_equations(&formula.clauses)
        .expect("canonical CNF has valid source literals")
    {
        *xor_degree.get_mut(&(u as u32)).unwrap()+=1;
        *xor_degree.get_mut(&(v as u32)).unwrap()+=1;
    }
    let mut degree=BTreeMap::new();
    let mut fill=BTreeMap::new();
    for (&v,adjacent) in &neighbors {
        let vertices=adjacent.iter().copied().collect::<Vec<_>>();
        let mut missing=0usize;
        for i in 0..vertices.len() {
            for j in (i+1)..vertices.len() {
                if !neighbors[&vertices[i]].contains(&vertices[j]) {
                    missing+=1;
                }
            }
        }
        degree.insert(v,vertices.len());
        fill.insert(v,missing);
    }
    GraphInvariants {degree,fill,xor_degree}
}

pub fn eliminate_with_policy(
    formula:&CanonicalCnf,policy:&str,max_pairs:i32,max_clause_growth:i32,
)->Result<CanonicalCnf,String> {
    if !matches!(policy,"min_fill"|"xor_boundary"|"max_release") {
        return Err("unknown invariant-guided elimination policy".into());
    }
    let stats=graph_invariants(formula);
    let mut best:Option<((i64,i64,i64),u32,CanonicalCnf)>=None;
    for (pivot,reduced) in elimination_options(
        formula,max_pairs,max_clause_growth,
    ) {
        let v=pivot;
        let nclauses=reduced.clauses.len() as i64;
        let degree=stats.degree[&v] as i64;
        let fill=stats.fill[&v] as i64;
        let xor=stats.xor_degree[&v] as i64;
        let priority=match policy {
            "min_fill" => (fill,degree,nclauses),
            "xor_boundary" => (xor,fill,nclauses),
            "max_release" => (
                nclauses-formula.clauses.len() as i64,fill,degree,
            ),
            _ => unreachable!(),
        };
        if best.as_ref().is_none_or(|(p,bv,_)|
            (priority,v)<(*p,*bv)
        ) {
            best=Some((priority,v,reduced));
        }
    }
    Ok(best.map(|(_,_,candidate)|candidate)
        .unwrap_or_else(||formula.clone()))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn graph_triangle_and_exact_policy_semantics() {
        let formula=CanonicalCnf::from_signed(&[
            vec![1,2],vec![-1,3],vec![2,3],
        ]).unwrap();
        let stats=graph_invariants(&formula);
        assert_eq!(stats.degree[&1],2);
        assert_eq!(stats.fill[&1],0);
        assert_eq!(stats.xor_degree[&1],0);
        for policy in ["min_fill","xor_boundary","max_release"] {
            let result=eliminate_with_policy(&formula,policy,12,2).unwrap();
            assert!(!result.clauses.is_empty());
            assert!(result.variables().len()<=formula.variables().len());
        }
        assert!(eliminate_with_policy(&formula,"nope",12,2).is_err());
        assert_eq!(
            eliminate_with_policy(&formula,"min_fill",-1,2).unwrap(),
            formula
        );
    }
}
