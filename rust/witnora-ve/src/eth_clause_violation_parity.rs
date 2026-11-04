//! R-058: finite clause-violation parity sketches and exact small-domain verifier.
//! Exponential 2^n diagnostic, no generic SAT complexity improvement.

use num_bigint::BigUint;
use num_traits::{One,Zero};
use sha2::{Digest,Sha256};
use std::collections::BTreeSet;

fn check_source(source:&[Vec<i32>],nvars:i64)->Result<(),String>{
    if !(1..=14).contains(&nvars){
        return Err("finite experiment requires 1 <= nvars <= 14".into());
    }
    if source.iter().flat_map(|row|row.iter()).any(|&lit|
        lit==0 || lit.unsigned_abs() as i64>nvars
    ){
        return Err("source literals must have variable IDs in 1..nvars".into());
    }
    Ok(())
}

pub fn source_digest(source:&[Vec<i32>])->String{
    let mut raw=String::from("[");
    for (i,clause) in source.iter().enumerate(){
        if i>0 {raw.push(',');}
        raw.push('[');
        for (j,lit) in clause.iter().enumerate(){
            if j>0 {raw.push(',');}
            raw.push_str(&lit.to_string());
        }
        raw.push(']');
    }
    raw.push(']');
    let mut hasher=Sha256::new();
    hasher.update(raw.as_bytes());
    format!("{:x}",hasher.finalize())
}

pub fn violation_mask(source:&[Vec<i32>],assignment:&BigUint)
    ->Result<BigUint,String>{
    let mut result=BigUint::zero();
    for (j,clause) in source.iter().enumerate(){
        let mut true_clause=false;
        for &lit in clause{
            if lit==0 {return Err("zero literal outside CNF domain".into());}
            let bit=((assignment >> (lit.unsigned_abs() as usize-1))
                &BigUint::one())==BigUint::one();
            if bit==(lit>0){true_clause=true;break;}
        }
        if !true_clause {result|=BigUint::one()<<j;}
    }
    Ok(result)
}

pub fn parity_accepts(violations:&BigUint,rows:&[Vec<usize>])->bool{
    rows.iter().all(|row|{
        row.iter().filter(|&&j|
            ((violations>>j)&BigUint::one())==BigUint::one()
        ).count()%2==0
    })
}

#[derive(Clone,Debug,PartialEq,Eq)]
pub struct FiniteSketch{
    pub rows:Vec<Vec<usize>>,
    pub survivors:Vec<usize>,
    pub satisfying_count:usize,
}

pub fn build_finite_sketch(
    source:&[Vec<i32>],nvars:i64,candidates:&[Vec<usize>],
    max_rows:Option<i64>,
)->Result<FiniteSketch,String>{
    check_source(source,nvars)?;
    if max_rows.is_some_and(|n|n<0){
        return Err("max_rows must be nonnegative".into());
    }
    let mut candidates=candidates.to_vec();
    for row in &candidates{
        let mut prev=None;
        for &col in row{
            if col>=source.len() || prev.is_some_and(|v|col<=v) {
                return Err("invalid candidate parity row".into());
            }
            prev=Some(col);
        }
    }
    candidates.sort_by(|a,b|a.len().cmp(&b.len()).then_with(||a.cmp(b)));
    candidates.dedup();
    let mut states=Vec::new();
    for assignment in 0..(1usize << (nvars as usize)){
        states.push(violation_mask(source,&BigUint::from(assignment))?);
    }
    let mut remaining:Vec<BigUint>=states.into_iter().filter(|s|!s.is_zero()).collect();
    let models=(1usize << (nvars as usize))-remaining.len();
    let mut rows=Vec::new();
    let mut survivors=vec![remaining.len()];
    while !remaining.is_empty(){
        if max_rows.is_some_and(|limit|rows.len() as i64>=limit){
            return Err("row budget exhausted before exact separation".into());
        }
        let mut best_row=None;
        let mut best_mask=BigUint::zero();
        let mut best_rejected=0usize;
        for row in &candidates{
            let mask=row.iter().fold(BigUint::zero(),|mut m,&j|{
                m|=BigUint::one()<<j;m
            });
            let rejected=remaining.iter().filter(|s|{
                (*s & &mask).iter_u32_digits().map(|v|v.count_ones())
                    .sum::<u32>()%2==1
            }).count();
            if rejected>best_rejected{
                best_rejected=rejected;
                best_row=Some(row.clone());
                best_mask=mask;
            }
        }
        let chosen=if let Some(row)=best_row{row}else{
            let first=remaining[0].iter_u32_digits().enumerate()
                .find(|&(_,v)|v!=0).map(|(i,v)|i*32+v.trailing_zeros() as usize)
                .ok_or("unexpected zero remaining violation")?;
            best_mask=BigUint::one()<<first;
            vec![first]
        };
        rows.push(chosen);
        remaining.retain(|s|{
            (&*s & &best_mask).iter_u32_digits().map(|v|v.count_ones())
                .sum::<u32>()%2==0
        });
        survivors.push(remaining.len());
    }
    Ok(FiniteSketch{rows,survivors,satisfying_count:models})
}

pub fn verify_finite_sketch(
    source:&[Vec<i32>],nvars:i64,rows:&[Vec<usize>],
)->bool{
    if check_source(source,nvars).is_err(){return false;}
    for row in rows{
        if row.is_empty() {return false;}
        let mut previous=None;
        for &j in row{
            if j>=source.len() || previous.is_some_and(|v|j<=v){return false;}
            previous=Some(j);
        }
    }
    for assignment in 0..(1usize<<(nvars as usize)){
        let violated=match violation_mask(source,&BigUint::from(assignment)){
            Ok(v)=>v,Err(_)=>return false,
        };
        if violated.is_zero()!=parity_accepts(&violated,rows){return false;}
    }
    true
}

pub fn is_complete_primal(source:&[Vec<i32>],nvars:i64)->bool{
    let mut edges=BTreeSet::new();
    for clause in source{
        for i in 0..clause.len(){
            for j in (i+1)..clause.len(){
                let a=clause[i].unsigned_abs();
                let b=clause[j].unsigned_abs();
                edges.insert((a.min(b),a.max(b)));
            }
        }
    }
    edges.len()==((nvars*(nvars-1))/2).max(0) as usize
}

pub fn decimal_violation(
    source:&[Vec<i32>],assignment:&str,
)->Result<String,String>{
    if assignment.starts_with('-'){return Err("negative assignment".into());}
    let assignment=BigUint::parse_bytes(assignment.as_bytes(),10)
        .ok_or("invalid decimal assignment")?;
    violation_mask(source,&assignment).map(|v|v.to_string())
}

pub fn decimal_parity_accepts(
    violations:&str,rows:&[Vec<usize>],
)->Result<bool,String>{
    if violations.starts_with('-'){return Err("negative violation mask".into());}
    let value=BigUint::parse_bytes(violations.as_bytes(),10)
        .ok_or("invalid decimal violation mask")?;
    Ok(parity_accepts(&value,rows))
}

#[cfg(test)]
mod tests{
    use super::*;
    #[test]
    fn parity_row_fallback_exact_on_units(){
        let source=vec![vec![1],vec![-1]];
        let sketch=build_finite_sketch(&source,1,&[],None).unwrap();
        assert_eq!(sketch.satisfying_count,0);
        assert_eq!(sketch.rows.len(),2);
        assert!(verify_finite_sketch(&source,1,&sketch.rows));
        assert_eq!(source_digest(&source).len(),64);
    }
}
