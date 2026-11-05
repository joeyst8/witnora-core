//! R-107: multilinear GF(2) ANF polynomial operations over Boolean variables.
//! Monomial multiplication is set union; coefficient addition is XOR.
use std::collections::{BTreeMap,BTreeSet};
use num_bigint::BigUint;
use num_traits::{One,Zero};

pub type Polynomial=Vec<Vec<usize>>;

fn canonical(poly:&[Vec<usize>])->BTreeSet<Vec<usize>>{
 poly.iter().map(|mon|{
  mon.iter().copied().collect::<BTreeSet<_>>().into_iter().collect()
 }).collect()
}

pub fn xor(left:&[Vec<usize>],right:&[Vec<usize>])->Polynomial{
 let a=canonical(left);let b=canonical(right);
 a.symmetric_difference(&b).cloned().collect()
}

pub fn multiply(left:&[Vec<usize>],right:&[Vec<usize>])->Polynomial{
 let a=canonical(left);let b=canonical(right);
 let mut result=BTreeSet::new();
 for x in &a{for y in &b{
  let merged=x.iter().chain(y.iter()).copied().collect::<BTreeSet<_>>()
   .into_iter().collect::<Vec<_>>();
  if !result.insert(merged.clone()){result.remove(&merged);}
 }}
 result.into_iter().collect()
}

pub fn substitute(poly:&[Vec<usize>],variable:usize,bit:bool)->Polynomial{
 let a=canonical(poly);let mut terms=BTreeSet::new();
 for mon in a{
  let contains=mon.binary_search(&variable).is_ok();
  if contains && !bit{continue;}
  let replaced=if contains{mon.into_iter().filter(|&v|v!=variable).collect()}
               else{mon};
  if !terms.insert(replaced.clone()){terms.remove(&replaced);}
 }
 terms.into_iter().collect()
}

pub fn canonical_equations(equations:&[Polynomial])->Vec<Polynomial>{
 let mut distinct=BTreeSet::new();
 for poly in equations{
  let normalized=canonical(poly).into_iter().collect::<Vec<_>>();
  if !normalized.is_empty(){distinct.insert(normalized);}
 }
 distinct.into_iter().collect()
}

/// R-114: exact polynomial evaluation against an arbitrary-width assignment.
/// Assignment bit zero corresponds to variable 1.
pub fn evaluate(poly:&[Vec<usize>],assignment_bits:&str)->Result<bool,String>{
 let bits=BigUint::parse_bytes(assignment_bits.as_bytes(),10)
     .ok_or("invalid assignment mask")?;
 let mut parity=false;
 for mon in canonical(poly){
  if mon.iter().any(|&v|v==0){
   return Err("variable IDs must be positive".into());
  }
  if mon.iter().all(|&v|((&bits >> (v-1)) & BigUint::one())==BigUint::one()){
   parity=!parity;
  }
 }
 Ok(parity)
}

/// R-108: finite bounded Shannon counter with exact arbitrary-width counts.
pub type CountAnswer=(String,usize,usize,usize);

struct Counter{
 memo:BTreeMap<(Vec<Polynomial>,Vec<usize>),BigUint>,
 calls:usize,hits:usize,maximum:usize,max_states:usize,
}

impl Counter{
 fn solve(&mut self,system:&[Polynomial],remaining:&[usize])->Result<BigUint,String>{
  let current=canonical_equations(system);
  if current.iter().any(|eq|eq.len()==1 && eq[0].is_empty()){
   return Ok(BigUint::zero());
  }
  if current.is_empty(){return Ok(BigUint::one()<<remaining.len());}
  let key=(current.clone(),remaining.to_vec());
  if let Some(cached)=self.memo.get(&key){self.hits+=1;return Ok(cached.clone());}
  if self.calls>=self.max_states{
   return Err(format!("max symbolic states {} exceeded",self.max_states));
  }
  self.calls+=1;
  self.maximum=self.maximum.max(current.len());
  let mut appearances=BTreeMap::<usize,usize>::new();
  for eq in &current{for mon in eq{for &v in mon{
   *appearances.entry(v).or_default()+=1;
  }}}
  let chosen=appearances.iter().max_by_key(|&(&v,&count)|{
   (count,std::cmp::Reverse(v))
  }).map(|(&v,_)|v).ok_or("nontrivial equation lacks variables")?;
  let next_remaining=remaining.iter().copied().filter(|&v|v!=chosen).collect::<Vec<_>>();
  let zero=current.iter().map(|eq|substitute(eq,chosen,false)).collect::<Vec<_>>();
  let one=current.iter().map(|eq|substitute(eq,chosen,true)).collect::<Vec<_>>();
  let count=self.solve(&zero,&next_remaining)?+self.solve(&one,&next_remaining)?;
  self.memo.insert(key,count.clone());
  Ok(count)
 }
}

pub fn count_zeros(equations:&[Polynomial],nvars:usize,max_states:usize)
 ->Result<CountAnswer,String>{
 if max_states<1{return Err("invalid counting bounds".into());}
 if equations.iter().flat_map(|eq|eq.iter()).flat_map(|mon|mon.iter())
   .any(|&v|v<1 || v>nvars){
  return Err("equation uses an out-of-range variable".into());
 }
 let mut counter=Counter{memo:BTreeMap::new(),calls:0,hits:0,
  maximum:0,max_states};
 let remaining=(1..=nvars).collect::<Vec<_>>();
 let result=counter.solve(equations,&remaining)?;
 Ok((result.to_string(),counter.calls,counter.hits,counter.maximum))
}

#[cfg(test)]mod tests{use super::*;#[test]fn boolean_ring(){
 assert_eq!(multiply(&[vec![1]],&[vec![1]]),vec![vec![1]]);
 assert_eq!(multiply(&[vec![1]],&[vec![]]),vec![vec![1]]);
 assert_eq!(xor(&[vec![1]],&[vec![1]]),Vec::<Vec<usize>>::new());
 assert_eq!(substitute(&[vec![1,2],vec![2]],1,true),Vec::<Vec<usize>>::new());
 assert_eq!(substitute(&[vec![1,2],vec![2]],1,false),vec![vec![2]]);
 assert_eq!(count_zeros(&[vec![vec![1]]],1,10).unwrap(),("1".into(),1,0,1));
 assert_eq!(evaluate(&[vec![130],vec![2]],
     &(BigUint::one()<<129usize).to_string()).unwrap(),true);
 assert_eq!(evaluate(&[vec![],vec![1,130]],"0").unwrap(),true);
 assert!(evaluate(&[vec![0]],"0").is_err());
}}
