//! W-CROSSDOMAIN-020: covariance, XOR and one-step binary-resolution baselines.
//! Each sound certificate format is tested independently on hidden 3-CNFs.

use crate::aux_hybrid_refutation::{xor_certificate,verify_xor,Equation};
use crate::aux_zero_variance_refutation::{covariance,kernel_certificate,model_count,verify};
use serde_json::{json,Value};
use std::collections::BTreeMap;

const N:usize=12;
const STEP:u32=0x9E37_79B9;

#[derive(Clone,Copy,PartialEq,Eq)]
enum Family {Planted,Boundary,DisguisedTwoSat,FullEight,ParityCycle}
impl Family {
    fn name(self)->&'static str {
        match self {
            Self::Planted=>"fresh_planted_sat_48",
            Self::Boundary=>"fresh_uniform_boundary_48",
            Self::DisguisedTwoSat=>"disguised_2sat_unsat_56",
            Self::FullEight=>"full_eight_unsat_56",
            Self::ParityCycle=>"parity_cycle_unsat_64",
        }
    }
    fn seed(self)->u32 {
        match self {
            Self::Planted=>0xD20C_0DE1,
            Self::Boundary=>0xD20C_0DE2,
            Self::DisguisedTwoSat=>0xD20C_0DE3,
            Self::FullEight=>0xD20C_0DE4,
            Self::ParityCycle=>0xD20C_0DE5,
        }
    }
}

fn next(state:&mut u32)->u32 {
    *state^=*state<<13;
    *state^=*state>>17;
    *state^=*state<<5;
    *state
}

fn random_clause(state:&mut u32)->Vec<i32> {
    let mut seen=[false;N];
    let mut clause=Vec::new();
    while clause.len()<3 {
        let variable=next(state) as usize % N;
        if seen[variable] {continue;}
        seen[variable]=true;
        let lit=variable as i32+1;
        clause.push(if next(state)&1==0 {lit} else {-lit});
    }
    clause
}

fn source(family:Family,index:usize)->Vec<Vec<i32>> {
    let mut state=family.seed() ^ (index as u32+1).wrapping_mul(STEP);
    let target=match family {
        Family::Planted|Family::Boundary=>48,
        Family::DisguisedTwoSat|Family::FullEight=>56,
        Family::ParityCycle=>64,
    };
    let mut clauses=Vec::with_capacity(target);
    if family==Family::DisguisedTwoSat {
        for a in 0..=1 {
            for b in 0..=1 {
                let x=if a==0 {1} else {-1};
                let y=if b==0 {2} else {-2};
                let padding=3+a*2+b;
                clauses.push(vec![x,y,padding]);
                clauses.push(vec![x,y,-padding]);
            }
        }
    }
    if family==Family::FullEight {
        for bits in 0..8 {
            clauses.push((0..3).map(|j| {
                let lit=j+1;
                if bits&(1<<j)!=0 {-lit} else {lit}
            }).collect());
        }
    }
    if family==Family::ParityCycle {
        for (vars,desired) in [([1i32,2,3],0u32),([1,4,5],0),
                               ([2,4,6],0),([3,5,6],1)] {
            for bits in 0u32..8 {
                if bits.count_ones()&1==desired {continue;}
                clauses.push(vars.iter().enumerate().map(|(j,&v)| {
                    if bits&(1u32<<j)!=0 {-v} else {v}
                }).collect());
            }
        }
    }
    while clauses.len()<target {
        let clause=random_clause(&mut state);
        if family==Family::Planted && clause.iter().all(|&lit|lit>0) {continue;}
        clauses.push(clause);
    }
    let mut permutation:[i32;N]=std::array::from_fn(|i|i as i32+1);
    for i in (1..N).rev(){let j=next(&mut state) as usize%(i+1);permutation.swap(i,j);}
    let flips:[bool;N]=std::array::from_fn(|_|next(&mut state)&1!=0);
    for clause in &mut clauses {
        for lit in clause {
            let v=lit.unsigned_abs() as usize-1;
            let mapped=permutation[v];
            let negative=(*lit<0)^flips[v];
            *lit=if negative {-mapped} else {mapped};
        }
    }
    for i in (1..clauses.len()).rev() {
        let j=next(&mut state) as usize%(i+1);
        clauses.swap(i,j);
    }
    clauses
}

#[derive(Clone)]
struct Resolvent {pair:[i32;2],premises:[usize;2]}
impl Resolvent {
    fn json(&self)->Value {
        json!({"binary_clause":self.pair,"source_indices":self.premises})
    }
}

// Exactly one resolution step: (a|b|z),(a|b|!z) derives (a|b).
fn binary_resolvents(clauses:&[Vec<i32>])->Vec<Resolvent> {
    let mut groups:BTreeMap<([i32;2],usize),[Option<usize>;2]>=BTreeMap::new();
    for (i,clause) in clauses.iter().enumerate() {
        for eliminated in 0..3 {
            let lit=clause[eliminated];
            let mut other=[0i32;2];
            let mut j=0;
            for (k,&value) in clause.iter().enumerate() {
                if k!=eliminated {other[j]=value;j+=1;}
            }
            other.sort_unstable();
            let polarity=if lit>0 {0} else {1};
            let entry=groups.entry((other,lit.unsigned_abs() as usize))
                .or_insert([None;2]);
            if entry[polarity].is_none(){entry[polarity]=Some(i);}
        }
    }
    let mut unique:BTreeMap<[i32;2],[usize;2]>=BTreeMap::new();
    for ((pair,_),source) in groups {
        if let (Some(a),Some(b))=(source[0],source[1]) {
            unique.entry(pair).or_insert([a,b]);
        }
    }
    unique.into_iter().map(|(pair,premises)|Resolvent{pair,premises}).collect()
}

fn verify_resolvents(source:&[Vec<i32>],binary:&[Resolvent])->Result<(),String> {
    for r in binary {
        let mut extra=[0i32;2];
        for (j,&index) in r.premises.iter().enumerate() {
            let clause=source.get(index).ok_or("W020 resolution source index")?;
            if r.pair.iter().any(|lit|!clause.contains(lit)) {
                return Err("W020 invalid binary resolvent".into());
            }
            let remain=clause.iter().find(|lit|!r.pair.contains(lit))
                .ok_or("W020 absent resolution pivot")?;
            extra[j]=*remain;
        }
        if extra[0]!=-extra[1] || extra[0]==0 {
            return Err("W020 resolution noncomplementary pivot".into());
        }
    }
    Ok(())
}

fn node(lit:i32)->usize {
    let v=lit.unsigned_abs() as usize-1;
    2*v+usize::from(lit>0)
}

// Polynomial 2-SAT reachability: the implications entail a contradiction
// iff a variable and its complement are mutually reachable.
fn binary_unsat(binary:&[Resolvent])->bool {
    let size=2*N;
    let mut reach=vec![vec![false;size];size];
    for (i,row) in reach.iter_mut().enumerate(){row[i]=true;}
    for r in binary {
        let [a,b]=r.pair;
        reach[node(-a)][node(b)]=true;
        reach[node(-b)][node(a)]=true;
    }
    for k in 0..size {
        for i in 0..size {
            if reach[i][k] {
                for j in 0..size {
                    if reach[k][j] {reach[i][j]=true;}
                }
            }
        }
    }
    (0..N).any(|v|reach[2*v][2*v+1]&&reach[2*v+1][2*v])
}

fn family_report(family:Family)->Result<Value,String> {
    let (mut sat,mut cov_hits,mut xor_hits,mut res_hits)=(0,0,0,0);
    let (mut cov_only_vs_xor,mut cov_unique_vs_both,mut xor_unique_vs_both)=(0,0,0);
    let mut controls=Vec::new();
    for index in 0..32 {
        let clauses=source(family,index);
        let models=model_count(&clauses);
        if models>0 {sat+=1;}
        if family==Family::Planted && models==0 {return Err("W020 planted UNSAT".into());}
        if matches!(family,Family::DisguisedTwoSat|Family::FullEight|Family::ParityCycle)
            && models>0 {return Err("W020 planted contradiction SAT".into());}
        let k=covariance(&clauses);
        let cov=kernel_certificate(&k);
        if let Some(ref w)=cov {verify(&k,&clauses,w)?;cov_hits+=1;}
        let xor:Option<Vec<Equation>>=xor_certificate(&clauses)?;
        if let Some(ref eqs)=xor {verify_xor(&clauses,eqs)?;xor_hits+=1;}
        let resolvents=binary_resolvents(&clauses);
        verify_resolvents(&clauses,&resolvents)?;
        let resolved=binary_unsat(&resolvents);
        if resolved {res_hits+=1;}
        if (cov.is_some()||xor.is_some()||resolved)&&models>0 {
            return Err("W020 unsound UNSAT certificate".into());
        }
        if cov.is_some() && xor.is_none(){cov_only_vs_xor+=1;}
        if cov.is_some() && xor.is_none() && !resolved {cov_unique_vs_both+=1;}
        if xor.is_some() && cov.is_none() && !resolved {xor_unique_vs_both+=1;}
        if [0,1,31].contains(&index) {
            controls.push(json!({"index":index,"source":clauses,"models":models,
                "covariance_weights":cov.map(|weights|weights.iter()
                    .map(|w|w.to_string()).collect::<Vec<_>>()),
                "xor_equations":xor.map(|eqs|eqs.iter().map(Equation::json)
                    .collect::<Vec<_>>()),
                "binary_resolvents":resolvents.iter().map(Resolvent::json)
                    .collect::<Vec<_>>(),"resolution_unsat":resolved}));
        }
    }
    Ok(json!({"family":family.name(),"formulas":32,
        "satisfiable":sat,"unsatisfiable":32-sat,
        "covariance_proofs":cov_hits,"xor_proofs":xor_hits,
        "resolution_proofs":res_hits,
        "covariance_without_xor":cov_only_vs_xor,
        "covariance_unique_against_xor_and_resolution":cov_unique_vs_both,
        "xor_unique_against_covariance_and_resolution":xor_unique_vs_both,
        "controls":controls}))
}

pub fn audit()->Result<Value,String> {
    let mut families=Vec::new();
    for family in [Family::Planted,Family::Boundary,Family::DisguisedTwoSat,
                   Family::FullEight,Family::ParityCycle] {
        families.push(family_report(family)?);
    }
    Ok(json!({"research_id":"W-CROSSDOMAIN-020",
        "scope":"sound incomplete separated refutation formats; no solver speedup",
        "families":families}))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn disguised_two_sat_separates_covariance_from_four_pattern_xor() {
        for i in [0,1,31] {
            let clauses=source(Family::DisguisedTwoSat,i);
            let k=covariance(&clauses);
            let w=kernel_certificate(&k).expect("eight-clause zero variance core");
            verify(&k,&clauses,&w).unwrap();
            assert!(xor_certificate(&clauses).unwrap().is_none());
            let derived=binary_resolvents(&clauses);
            verify_resolvents(&clauses,&derived).unwrap();
            assert!(binary_unsat(&derived));
        }
    }
}
