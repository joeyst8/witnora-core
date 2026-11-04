//! R-078: dense parity geometry; construction is nonenumerative, audit is exponential.
use num_bigint::BigUint;
use num_traits::{One, Zero};
use std::collections::BTreeSet;
use crate::eth_clause_violation_parity::{violation_mask,parity_accepts};

pub fn rows_from_bitmaps(bitmaps:&[String], clause_count:usize)->Result<Vec<Vec<usize>>,String>{
    bitmaps.iter().map(|raw|{
        let bits=BigUint::parse_bytes(raw.as_bytes(),10).ok_or("invalid bitmap")?;
        if (&bits >> clause_count)!=BigUint::zero(){return Err("bitmap exceeds clause count".into());}
        Ok((0..clause_count).filter(|j|((&bits >> *j)&BigUint::one())==BigUint::one()).collect())
    }).collect()
}

pub fn audit(source:&[Vec<i32>],nvars:usize,rows:&[Vec<usize>],max_variables:usize)
 ->Result<(usize,usize,usize,usize,Vec<usize>),String>{
    if nvars>max_variables || nvars>=usize::BITS as usize || nvars>20 {
        return Err("exhaustive audit restricted to small experiments".into());
    }
    let mut models=0;
    let mut false_positives=0;
    let mut singleton=BTreeSet::new();
    for assignment in 0..(1usize<<nvars){
        let mask=violation_mask(source,&BigUint::from(assignment))?;
        if mask.is_zero(){models+=1;continue;}
        let positions:Vec<usize>=mask.iter_u32_digits().enumerate().flat_map(|(word_idx,word)|{
            (0..32).filter(move |bit| ((word>>*bit)&1)==1).map(move |bit|word_idx*32+bit)
        }).collect();
        if positions.len()==1{singleton.insert(positions[0]);}
        if parity_accepts(&mask,rows){false_positives+=1;}
    }
    let total=1usize<<nvars;
    Ok((total,models,total-models,false_positives,singleton.into_iter().collect()))
}

pub fn validate(source:&[Vec<i32>],nvars:usize,clause_count:usize,digest:&str,
    security_bits:usize,rows:&[Vec<usize>])->Result<(),String>{
    if nvars==0 {return Err("nvars must be positive".into());}
    if source.iter().flatten().any(|&lit|lit==0 || lit.unsigned_abs() as usize>nvars){
        return Err("source literal IDs must be in 1..nvars".into());
    }
    if source.len()!=clause_count || crate::eth_clause_violation_parity::source_digest(source)!=digest{
        return Err("source identity mismatch".into());
    }
    if rows.len()!=nvars.checked_add(security_bits).ok_or("incorrect row count")?{
        return Err("incorrect row count".into());
    }
    for row in rows{
        let mut prev=None;
        for &j in row{
            if j>=clause_count{return Err("row references absent clause".into());}
            if prev.is_some_and(|old|j<=old){return Err("noncanonical row IDs".into());}
            prev=Some(j);
        }
    }
    Ok(())
}

pub fn singleton_bound(count:usize,width:usize)->Result<usize,String>{
    if width==0 {return Err("max_row_width must be positive".into());}
    Ok(count/width+usize::from(count%width>0))
}

pub fn row_stats(rows:&[Vec<usize>])->(usize,f64,usize){
    if rows.is_empty(){return (0,0.,0);}
    let sizes:Vec<usize>=rows.iter().map(Vec::len).collect();
    (*sizes.iter().min().unwrap(),sizes.iter().sum::<usize>() as f64/sizes.len() as f64,*sizes.iter().max().unwrap())
}

#[cfg(test)]
mod tests{
 use super::*;
 #[test] fn basic(){
  let source=vec![vec![1],vec![-1]];
  let rows=rows_from_bitmaps(&["1".into(),"2".into()],2).unwrap();
  assert_eq!(rows,vec![vec![0],vec![1]]);
  let d=crate::eth_clause_violation_parity::source_digest(&source);
  validate(&source,1,2,&d,1,&rows).unwrap();
  assert_eq!(audit(&source,1,&rows,14).unwrap(),(2,0,2,0,vec![0,1]));
  assert_eq!(singleton_bound(5,2).unwrap(),3);
 }
}
