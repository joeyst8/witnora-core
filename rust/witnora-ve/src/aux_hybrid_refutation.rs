//! W-CROSSDOMAIN-019: exact covariance or GF(2) UNSAT certificates.
//! Both proof types are independently checked; no result means UNKNOWN.

use crate::aux_zero_variance_refutation::{covariance,kernel_certificate,model_count,verify};
use serde_json::{json,Value};
use std::collections::{BTreeMap,BTreeSet};

const N:usize=12;
const STEP:u32=0x9E37_79B9;

#[derive(Clone,Copy,PartialEq,Eq)]
enum Family {Planted,Boundary,EightCore,ParityCycle}
impl Family {
    fn name(self)->&'static str {
        match self {
            Self::Planted=>"fresh_planted_sat_48",
            Self::Boundary=>"fresh_uniform_boundary_48",
            Self::EightCore=>"hidden_eight_core_unsat_56",
            Self::ParityCycle=>"hidden_parity_cycle_unsat_64",
        }
    }
    fn seed(self)->u32 {
        match self {
            Self::Planted=>0xD19C_0DE1,
            Self::Boundary=>0xD19C_0DE2,
            Self::EightCore=>0xD19C_0DE3,
            Self::ParityCycle=>0xD19C_0DE4,
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
        let positive=next(state)&1==0;
        let lit=variable as i32+1;
        clause.push(if positive {lit} else {-lit});
    }
    clause
}

fn source(family:Family,index:usize)->Vec<Vec<i32>> {
    let mut state=family.seed() ^ (index as u32+1).wrapping_mul(STEP);
    let target=match family {Family::EightCore=>56,Family::ParityCycle=>64,_=>48};
    let mut clauses=Vec::with_capacity(target);
    if family==Family::EightCore {
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
    for i in (1..N).rev() {
        let j=next(&mut state) as usize % (i+1);
        permutation.swap(i,j);
    }
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
        let j=next(&mut state) as usize % (i+1);
        clauses.swap(i,j);
    }
    clauses
}

#[derive(Clone)]
struct Equation {vars:[usize;3],rhs:u8,indices:[usize;4]}
impl Equation {
    fn mask(&self)->u16 {
        self.vars.iter().fold(0u16,|acc,&v|acc | (1u16<<(v-1)))
    }
    fn json(&self)->Value {
        json!({"variables":self.vars,"rhs":self.rhs,"clause_indices":self.indices})
    }
}

fn sorted_clause_vars(clause:&[i32])->[usize;3] {
    let mut vars=[0;3];
    for (j,lit) in clause.iter().enumerate(){vars[j]=lit.unsigned_abs() as usize;}
    vars.sort_unstable();
    vars
}

// Index the single assignment to the triple that falsifies each 3-clause.
fn forbidden_pattern(clause:&[i32],vars:[usize;3])->usize {
    let mut bits=0;
    for (j,&v) in vars.iter().enumerate() {
        if clause.iter().any(|&lit|lit==-(v as i32)) {bits|=1<<j;}
    }
    bits
}

fn extract(clauses:&[Vec<i32>])->Vec<Equation> {
    let mut groups:BTreeMap<[usize;3],[Option<usize>;8]>=BTreeMap::new();
    for (i,clause) in clauses.iter().enumerate() {
        let vars=sorted_clause_vars(clause);
        let pattern=forbidden_pattern(clause,vars);
        let entry=groups.entry(vars).or_insert([None;8]);
        if entry[pattern].is_none() {entry[pattern]=Some(i);}
    }
    let mut found=Vec::new();
    for (vars,indices) in groups {
        for rhs in 0u8..=1 {
            let patterns=(0usize..8).filter(|p|p.count_ones() as u8 & 1 !=rhs)
                .collect::<Vec<_>>();
            if patterns.iter().all(|&p|indices[p].is_some()) {
                found.push(Equation{vars,rhs,
                    indices:std::array::from_fn(|j|indices[patterns[j]].unwrap())});
            }
        }
    }
    found
}

fn symmetric_difference(a:&BTreeSet<usize>,b:&BTreeSet<usize>)->BTreeSet<usize> {
    a.symmetric_difference(b).copied().collect()
}

fn verify_xor(clauses:&[Vec<i32>],proof:&[Equation])->Result<(),String> {
    let (mut left,mut right)=(0u16,0u8);
    if proof.is_empty(){return Err("W019 empty XOR contradiction".into());}
    for eq in proof {
        if eq.vars.iter().any(|&v|v==0||v>N) {return Err("W019 variable range".into());}
        let mut got=[false;8];
        for &i in &eq.indices {
            let clause=clauses.get(i).ok_or("W019 bad clause index")?;
            if sorted_clause_vars(clause)!=eq.vars {return Err("W019 wrong triple".into());}
            got[forbidden_pattern(clause,eq.vars)]=true;
        }
        for (i,seen) in got.iter().enumerate() {
            if *seen != ((i.count_ones() as u8&1)!=eq.rhs) {
                return Err("W019 incomplete XOR encoding".into());
            }
        }
        left^=eq.mask();
        right^=eq.rhs;
    }
    if left!=0 || right!=1 {return Err("W019 XOR does not refute".into());}
    Ok(())
}

fn xor_certificate(clauses:&[Vec<i32>])->Result<Option<Vec<Equation>>,String> {
    let equations=extract(clauses);
    let mut basis:BTreeMap<usize,(u16,u8,BTreeSet<usize>)>=BTreeMap::new();
    for (i,eq) in equations.iter().enumerate() {
        let (mut left,mut rhs)=(eq.mask(),eq.rhs);
        let mut support=BTreeSet::from([i]);
        loop {
            if left==0 {
                if rhs==1 {
                    let proof=support.iter().map(|&j|equations[j].clone()).collect::<Vec<_>>();
                    verify_xor(clauses,&proof)?;
                    return Ok(Some(proof));
                }
                break;
            }
            let pivot=left.trailing_zeros() as usize;
            if let Some((row,row_rhs,row_support))=basis.get(&pivot) {
                left^=*row;
                rhs^=*row_rhs;
                support=symmetric_difference(&support,row_support);
            } else {
                basis.insert(pivot,(left,rhs,support));
                break;
            }
        }
    }
    Ok(None)
}

fn family_report(family:Family)->Result<Value,String> {
    let (mut sat,mut covariance_proofs,mut parity_proofs,mut no_proof)=(0,0,0,0);
    let mut controls=Vec::new();
    for index in 0..32 {
        let clauses=source(family,index);
        let models=model_count(&clauses);
        if models>0 {sat+=1;}
        if family==Family::Planted && models==0 {return Err("W019 planted UNSAT".into());}
        if matches!(family,Family::EightCore|Family::ParityCycle) && models>0 {
            return Err("W019 constructed contradiction is SAT".into());
        }
        let k=covariance(&clauses);
        let proof=if let Some(w)=kernel_certificate(&k) {
            verify(&k,&clauses,&w)?;
            if models>0 {return Err("W019 covariance false positive".into());}
            covariance_proofs+=1;
            json!({"kind":"covariance","weights":w.iter().map(|v|v.to_string())
                  .collect::<Vec<_>>()})
        }else if let Some(eqs)=xor_certificate(&clauses)? {
            if models>0 {return Err("W019 parity false positive".into());}
            parity_proofs+=1;
            json!({"kind":"xor","equations":eqs.iter().map(Equation::json).collect::<Vec<_>>()})
        }else {
            no_proof+=1;
            json!({"kind":"none"})
        };
        if [0,1,31].contains(&index) {
            controls.push(json!({"index":index,"source":clauses,"models":models,"proof":proof}));
        }
    }
    Ok(json!({"family":family.name(),"formulas":32,"satisfiable":sat,
        "unsatisfiable":32-sat,"covariance_proofs":covariance_proofs,
        "xor_proofs":parity_proofs,"no_certificate":no_proof,"controls":controls}))
}

pub fn audit()->Result<Value,String> {
    let mut families=Vec::new();
    for family in [Family::Planted,Family::Boundary,Family::EightCore,Family::ParityCycle] {
        families.push(family_report(family)?);
    }
    Ok(json!({"research_id":"W-CROSSDOMAIN-019",
        "scope":"sound incomplete hybrid UNSAT refutation; no SAT speedup claim",
        "families":families}))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn transformed_parity_cycle_has_exact_source_replay() {
        for i in [0,1,31] {
            let c=source(Family::ParityCycle,i);
            let proof=xor_certificate(&c).unwrap().expect("parity core should be detected");
            verify_xor(&c,&proof).unwrap();
            assert_eq!(model_count(&c),0);
        }
    }
}
