//! R-096: source-order exact bounded factor-table variable elimination.
//! Exponential in intermediate width, fail-closed on declared work caps.
use num_bigint::BigUint;
use num_traits::{One,Zero};
use std::collections::{BTreeMap,BTreeSet};

#[derive(Clone)]struct Factor{scope:Vec<usize>,table:Vec<BigUint>}
pub type Answer=(String,usize,usize,usize);
fn parse_decimal(s:&str)->Result<BigUint,String>{
 BigUint::parse_bytes(s.as_bytes(),10).ok_or_else(||"invalid nonnegative violation mask".into())
}
pub fn count(clauses:&[(String,String)],variables:&[usize],max_width:usize,max_ops:usize)
 ->Result<Option<Answer>,String>{
 if !(1..=16).contains(&max_width) || max_ops==0{
  return Err("invalid VE width or operation budget".into());
 }
 let active_unique:BTreeSet<usize>=variables.iter().copied().collect();
 if variables.iter().any(|&v|v==0) || active_unique.len()!=variables.len(){
  return Err("duplicate or zero component variable".into());
 }
 let mut allowed=BigUint::zero();
 for &v in variables{allowed|=BigUint::one() << (v-1);}
 let mut factors:Vec<Factor>=Vec::new();
 let mut operations=0usize;let mut maximum_width=0usize;
 for (zero_raw,one_raw) in clauses{
  let zeros=parse_decimal(zero_raw)?;let ones=parse_decimal(one_raw)?;
  let overlap=&zeros & &ones;let support=&zeros | &ones;
  let outside=&support ^ (&support & &allowed);
  if !overlap.is_zero() || !outside.is_zero(){return Err("invalid violation masks".into());}
  if support.is_zero(){return Ok(Some(("0".into(),operations,maximum_width,0)));}
  let scope:Vec<usize>=variables.iter().copied().filter(|&v|((&support>>(v-1))&BigUint::one())==BigUint::one()).collect();
  let width=scope.len();if width>max_width{return Ok(None);}
  maximum_width=maximum_width.max(width);
  let size=1usize<<width;
  if size>max_ops-operations{return Ok(None);}operations+=size;
  let mut table=Vec::with_capacity(size);
  for packed in 0..size{
   let mut assignment=BigUint::zero();
   for (i,&v) in scope.iter().enumerate(){if packed&(1usize<<i)!=0{
    assignment|=BigUint::one()<<(v-1);
   }}
   let violated=(&assignment & &zeros).is_zero() && (&assignment & &ones)==ones;
   table.push(if violated{BigUint::zero()}else{BigUint::one()});
  }
  factors.push(Factor{scope,table});
 }
 let mut active=active_unique;
 for _ in 0..variables.len(){
  let mut choice:Option<(usize,usize,usize,Vec<usize>,Vec<usize>)>=None;
  for &v in &active{
   let ids:Vec<usize>=factors.iter().enumerate().filter_map(|(i,f)|f.scope.contains(&v).then_some(i)).collect();
   let mut scope=BTreeSet::from([v]);
   for &id in &ids{scope.extend(factors[id].scope.iter().copied());}
   let entry=(scope.len(),ids.len(),v,ids,scope.into_iter().collect());
   if choice.as_ref().map_or(true,|best|(entry.0,entry.1,entry.2)<(best.0,best.1,best.2)){
    choice=Some(entry);
   }
  }
  let (width,touched_count,variable,ids,total_scope)=choice.ok_or("no variable selected")?;
  if width>max_width{return Ok(None);}maximum_width=maximum_width.max(width);
  let context:Vec<usize>=total_scope.into_iter().filter(|&v|v!=variable).collect();
  let entries=1usize<<context.len();
  let work=entries*2*touched_count.max(1);
  if work>max_ops-operations{return Ok(None);}operations+=work;
  let mut table=Vec::with_capacity(entries);
  for packed in 0..entries{
   let mut values=BTreeMap::new();
   for (i,&v) in context.iter().enumerate(){values.insert(v,packed&(1usize<<i)!=0);}
   let mut summation=BigUint::zero();
   for x in [false,true]{
    values.insert(variable,x);
    let mut product=BigUint::one();
    for &id in &ids{
     let f=&factors[id];let mut key=0usize;
     for (i,&v) in f.scope.iter().enumerate(){if values[&v]{key|=1usize<<i;}}
     product*=&f.table[key];if product.is_zero(){break;}
    }
    summation+=product;
   }
   table.push(summation);
  }
  for id in ids.into_iter().rev(){factors.remove(id);}
  factors.push(Factor{scope:context,table});
  active.remove(&variable);
 }
 let mut result=BigUint::one();
 for factor in &factors{
  if !factor.scope.is_empty(){return Err("VE left uneliminated variables".into());}
  result*=&factor.table[0];
 }
 Ok(Some((result.to_string(),operations,maximum_width,variables.len())))
}

#[cfg(test)]mod tests{use super::*;#[test]fn one_clause_and_free(){
 let value=count(&[("0".into(),"1".into())],&[1,2],2,100).unwrap().unwrap();
 assert_eq!(value.0,"2");
}}
