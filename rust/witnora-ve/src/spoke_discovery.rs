//! R-046: conservative source-bound binary-XOR spoke discovery.
//! These are unverified structural candidates; Lean performs independent
//! source-bound proof checks and is never bypassed by this module.

use crate::cnf::CanonicalCnf;
use crate::odd_xor_cycle::{binary_equations,pattern_clauses};
use std::collections::{BTreeMap,BTreeSet};

#[derive(Clone,Debug,PartialEq,Eq)]
pub struct SourceEquation {
    pub variables:Vec<i32>,
    pub rhs:u32,
    pub source_clauses:Vec<Vec<i32>>,
}

#[derive(Clone,Debug,PartialEq,Eq)]
pub struct SpokePath {
    pub middle:i32,
    pub syndrome:u32,
    pub equations:Vec<SourceEquation>,
}

#[derive(Clone,Debug,PartialEq,Eq)]
pub struct SpokeConflict {
    pub endpoints:(i32,i32),
    pub paths:Vec<SpokePath>,
}

pub fn extract_binary_xor_equations(
    source:&[Vec<i32>],
)->Result<Vec<(i32,i32,u32)>,String> {
    let formula=CanonicalCnf::from_signed(source)?;
    Ok(binary_equations(&formula.clauses))
}

pub fn extract_spoke_paths(
    source:&[Vec<i32>],
)->Result<Vec<(i32,i32,i32,u32,u32)>,String> {
    let equations=extract_binary_xor_equations(source)?;
    let mut edges=BTreeMap::<i32,Vec<(i32,u32)>>::new();
    for (u,v,rhs) in equations {
        edges.entry(u).or_default().push((v,rhs));
        edges.entry(v).or_default().push((u,rhs));
    }
    let mut paths=BTreeSet::new();
    for (middle,neighbors) in edges {
        for first in 0..neighbors.len() {
            for second in (first+1)..neighbors.len() {
                let (u,urhs)=neighbors[first];
                let (v,vrhs)=neighbors[second];
                if u==v { continue; }
                let x=u.min(v);
                let z=u.max(v);
                let (left,right)=if u==x {(urhs,vrhs)} else {(vrhs,urhs)};
                paths.insert((x,z,middle,left,right));
            }
        }
    }
    Ok(paths.into_iter().collect())
}

pub fn discover_parity_spoke_conflicts(
    source:&[Vec<i32>],
)->Result<Vec<SpokeConflict>,String> {
    let equations=extract_binary_xor_equations(source)?;
    let mut edges=BTreeMap::<i32,Vec<(i32,u32,Vec<Vec<i32>>)>>::new();
    for (u,v,rhs) in equations {
        let witness=pattern_clauses(u,v,rhs).into_iter().collect::<Vec<_>>();
        edges.entry(u).or_default().push((v,rhs,witness.clone()));
        edges.entry(v).or_default().push((u,rhs,witness));
    }
    let mut by_endpoints=BTreeMap::<(i32,i32),Vec<SpokePath>>::new();
    for (middle,neighbors) in edges {
        for first in 0..neighbors.len() {
            for second in (first+1)..neighbors.len() {
                let (x,l,source_left)=&neighbors[first];
                let (z,r,source_right)=&neighbors[second];
                if x==z { continue; }
                let endpoints=((*x).min(*z),(*x).max(*z));
                let eq_left=SourceEquation {
                    variables:vec![(*x).min(middle),(*x).max(middle)],
                    rhs:*l,source_clauses:source_left.clone(),
                };
                let eq_right=SourceEquation {
                    variables:vec![middle.min(*z),middle.max(*z)],
                    rhs:*r,source_clauses:source_right.clone(),
                };
                by_endpoints.entry(endpoints).or_default().push(SpokePath {
                    middle,syndrome:l^r,equations:vec![eq_left,eq_right],
                });
            }
        }
    }
    let mut conflicts=Vec::new();
    for (endpoints,paths) in by_endpoints {
        for first in 0..paths.len() {
            for second in (first+1)..paths.len() {
                let a=&paths[first];
                let b=&paths[second];
                if a.middle==b.middle || a.syndrome==b.syndrome {
                    continue;
                }
                conflicts.push(SpokeConflict {
                    endpoints,paths:vec![a.clone(),b.clone()],
                });
            }
        }
    }
    Ok(conflicts)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn odd_two_middle_spokes_are_unverified_candidates() {
        let source=vec![
            vec![1,-3],vec![-1,3],
            vec![2,-3],vec![-2,3],
            vec![1,-4],vec![-1,4],
            vec![2,4],vec![-2,-4],
        ];
        let equations=extract_binary_xor_equations(&source).unwrap();
        assert_eq!(equations.len(),4);
        let paths=extract_spoke_paths(&source).unwrap();
        assert!(paths.contains(&(1,2,3,0,0)));
        assert!(paths.contains(&(1,2,4,0,1)));
        let conflicts=discover_parity_spoke_conflicts(&source).unwrap();
        assert!(conflicts.iter().any(|c|
            c.endpoints==(1,2) &&
            c.paths[0].syndrome!=c.paths[1].syndrome
        ));
        assert!(discover_parity_spoke_conflicts(&[vec![1,2]])
            .unwrap().is_empty());
    }
}
