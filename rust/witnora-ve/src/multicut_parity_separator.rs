//! R-047: bounded 1..3 parity-equation incidence cuts.
//! Purely descriptive, never an audited full-CNF separator or trusted proof.

use crate::cnf::CanonicalCnf;
use crate::parity_separator_fingerprint::{components,exact_xor_supports};
use std::collections::{BTreeMap,BTreeSet};

#[derive(Clone,Debug,PartialEq,Eq)]
pub struct CutCandidate {
    pub variables:Vec<u32>,
    pub size:usize,
    pub components_before:usize,
    pub components_after:usize,
    pub component_equation_indices:Vec<Vec<usize>>,
}

#[derive(Clone,Debug,PartialEq,Eq)]
pub struct MulticutResult {
    pub source_sha256:String,
    pub exact_parity_equations:usize,
    pub candidate_cuts:Vec<CutCandidate>,
    pub smallest_cut_size:Option<usize>,
    pub shared_variables_considered:usize,
    pub trials:usize,
    pub budget_exhausted:bool,
}

pub fn bounded_parity_separators(
    source:&[Vec<i32>],max_cut:i32,max_shared:i32,max_trials:i32,
)->Result<MulticutResult,String> {
    if !(1..=3).contains(&max_cut) || max_shared<1 || max_trials<1 {
        return Err("invalid bounded separator search".into());
    }
    let formula=CanonicalCnf::from_signed(source)?;
    let support_lists=exact_xor_supports(&formula,6);
    let supports=support_lists.iter().map(|s|
        s.iter().copied().collect::<BTreeSet<_>>()
    ).collect::<Vec<_>>();
    let baseline=components(&supports).len();
    let mut incidence=BTreeMap::<u32,usize>::new();
    for support in &supports {
        for &variable in support {
            *incidence.entry(variable).or_default()+=1;
        }
    }
    let mut shared=incidence.iter()
        .filter(|(_,count)| **count>=2)
        .map(|(&v,&n)|(v,n)).collect::<Vec<_>>();
    shared.sort_by(|a,b| b.1.cmp(&a.1).then_with(||a.0.cmp(&b.0)));
    let mut shared=shared.into_iter().take(max_shared as usize)
        .map(|(v,_)|v).collect::<Vec<_>>();
    shared.sort_unstable();
    let mut found=Vec::<CutCandidate>::new();
    let mut trials=0usize;
    let mut exhausted=false;
    for size in 1..=max_cut as usize {
        if size>shared.len(){continue;}
        let mut indices=(0..size).collect::<Vec<_>>();
        loop {
            if trials>=max_trials as usize {
                exhausted=true;
                break;
            }
            trials+=1;
            let cut=indices.iter().map(|&index|shared[index])
                .collect::<Vec<_>>();
            let cut_set=cut.iter().copied().collect::<BTreeSet<_>>();
            let covered=found.iter().any(|prev|
                prev.variables.iter().all(|v|cut_set.contains(v))
            );
            if !covered {
                let reduced=supports.iter().map(|support|
                    support.difference(&cut_set).copied()
                        .collect::<BTreeSet<_>>()
                ).collect::<Vec<_>>();
                let groups=components(&reduced);
                let nonempty=groups.iter().all(|group|
                    group.iter().any(|&i| !reduced[i].is_empty())
                );
                if groups.len()>baseline && nonempty {
                    found.push(CutCandidate {
                        variables:cut,size,
                        components_before:baseline,
                        components_after:groups.len(),
                        component_equation_indices:groups,
                    });
                }
            }
            // Python itertools.combinations yields indices lexicographically.
            let mut advanced=false;
            for pos in (0..size).rev() {
                if indices[pos]<shared.len()-size+pos {
                    indices[pos]+=1;
                    for next in (pos+1)..size {
                        indices[next]=indices[next-1]+1;
                    }
                    advanced=true;
                    break;
                }
            }
            if !advanced {break;}
        }
        if exhausted{break;}
    }
    Ok(MulticutResult {
        source_sha256:formula.formula_hash(),
        exact_parity_equations:supports.len(),
        smallest_cut_size:found.iter().map(|cut|cut.size).min(),
        shared_variables_considered:shared.len(),
        candidate_cuts:found,trials,budget_exhausted:exhausted,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exact_single_and_double_hub_cuts() {
        let source=vec![
            vec![1,-2],vec![-1,2],
            vec![1,-3],vec![-1,3],
        ];
        let result=bounded_parity_separators(&source,3,18,2000).unwrap();
        assert_eq!(result.exact_parity_equations,2);
        assert_eq!(result.smallest_cut_size,Some(1));
        assert_eq!(result.candidate_cuts[0].variables,vec![1]);
        let limited=bounded_parity_separators(&source,3,18,1).unwrap();
        assert_eq!(limited.trials,1);
        assert_eq!(limited.budget_exhausted,false);
        assert!(bounded_parity_separators(&source,0,18,2000).is_err());
    }
}
