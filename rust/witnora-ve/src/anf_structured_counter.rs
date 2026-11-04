//! R-111: exact, budgeted ANF zero counting with component decomposition.
//! Independent of Python's implementation; all counts use BigUint.
use num_bigint::BigUint;
use num_traits::{One,Zero};
use std::collections::{BTreeMap,BTreeSet};

type Poly=Vec<BigUint>;
type System=Vec<Poly>;
pub type Answer=(String,usize,usize,usize,usize,usize,usize,usize);

fn set_bits(mask:&BigUint)->BTreeSet<usize>{
 let mut result=BTreeSet::new();
 for (word_id,mut word) in mask.to_u64_digits().into_iter().enumerate(){
  while word!=0{
   let bit=word.trailing_zeros() as usize;
   result.insert(64*word_id+bit);
   word&=word-1;
  }
 }
 result
}

fn compile(equations:&[Vec<Vec<usize>>])->System{
 equations.iter().map(|eq|{
  eq.iter().map(|mon|{
   mon.iter().fold(BigUint::zero(),|mut mask,&v|{
    mask|=BigUint::one()<<(v-1);mask
   })
  }).collect::<BTreeSet<_>>().into_iter().collect()
 }).collect()
}

fn canonical(system:&[Poly])->System{
 system.iter().filter(|eq|!eq.is_empty()).cloned()
  .collect::<BTreeSet<_>>().into_iter().collect()
}

fn root(parent:&mut BTreeMap<usize,usize>,bit:usize)->usize{
 let p=parent[&bit];
 if p==bit{return bit;}
 let r=root(parent,p);parent.insert(bit,r);r
}

fn groups(system:&System)->(Vec<(System,BTreeSet<usize>)>,BTreeSet<usize>){
 let mut parent=BTreeMap::<usize,usize>::new();
 let mut scopes=Vec::new();let mut active=BTreeSet::new();
 for eq in system{
  let mut scope=BTreeSet::new();
  for mon in eq{scope.extend(set_bits(mon));}
  active.extend(scope.iter().copied());
  if let Some(&first)=scope.iter().next(){
   parent.entry(first).or_insert(first);
   for &v in scope.iter().skip(1){
    parent.entry(v).or_insert(v);
    let ra=root(&mut parent,first);let rb=root(&mut parent,v);
    if ra!=rb{parent.insert(rb,ra);}
   }
  }
  scopes.push(scope);
 }
 let mut gathered=BTreeMap::<usize,(System,BTreeSet<usize>)>::new();
 for (eq,scope) in system.iter().zip(scopes.iter()){
  let &first=scope.iter().next().expect("nonconstant equation scope");
  let r=root(&mut parent,first);
  let item=gathered.entry(r).or_default();
  item.0.push(eq.clone());item.1.extend(scope.iter().copied());
 }
 (gathered.into_values().collect(),active)
}

struct Counter{
 memo:BTreeMap<(System,Vec<usize>),BigUint>,
 cofactors:BTreeMap<(Poly,usize,bool),Poly>,
 states:usize,memo_hits:usize,cofactor_hits:usize,
 splits:usize,forced:usize,maximum:usize,max_states:usize,
}

impl Counter{
 fn cofactor(&mut self,poly:&Poly,variable:usize,value:bool)->Poly{
  let key=(poly.clone(),variable,value);
  if let Some(x)=self.cofactors.get(&key){
   self.cofactor_hits+=1;return x.clone();
  }
  let bit=BigUint::one()<<variable;
  let mut terms=BTreeSet::new();
  for mon in poly{
   let contains=(mon & &bit)!=BigUint::zero();
   if contains && !value{continue;}
   let replaced=if contains{mon ^ &bit}else{mon.clone()};
   if !terms.insert(replaced.clone()){terms.remove(&replaced);}
  }
  let out=terms.into_iter().collect::<Vec<_>>();
  self.cofactors.insert(key,out.clone());out
 }

 fn forced_unit(poly:&Poly)->Option<(usize,bool)>{
  if poly.len()==1{
   let bits=set_bits(&poly[0]);
   if bits.len()==1{return Some((*bits.iter().next().unwrap(),false));}
  }
  if poly.len()==2 && poly[0].is_zero(){
   let bits=set_bits(&poly[1]);
   if bits.len()==1{return Some((*bits.iter().next().unwrap(),true));}
  }
  None
 }

 fn solve(&mut self,system:&[Poly],remaining:&BTreeSet<usize>)->Result<BigUint,String>{
  let current=canonical(system);
  if current.iter().any(|eq|eq.len()==1 && eq[0].is_zero()){
   return Ok(BigUint::zero());
  }
  if current.is_empty(){return Ok(BigUint::one()<<remaining.len());}
  let key=(current.clone(),remaining.iter().copied().collect::<Vec<_>>());
  if let Some(value)=self.memo.get(&key){self.memo_hits+=1;return Ok(value.clone());}
  if self.states>=self.max_states{
   return Err(format!("max symbolic states {} exceeded",self.max_states));
  }
  self.states+=1;
  self.maximum=self.maximum.max(current.len());
  for eq in &current{
   if let Some((variable,value))=Self::forced_unit(eq){
    if !remaining.contains(&variable){
     return Err("forced variable outside remaining set".into());
    }
    self.forced+=1;
    let mut next=remaining.clone();next.remove(&variable);
    let transformed=current.iter().map(|p|self.cofactor(p,variable,value))
     .collect::<Vec<_>>();
    let answer=self.solve(&transformed,&next)?;
    self.memo.insert(key,answer.clone());
    return Ok(answer);
   }
  }
  let (components,active)=groups(&current);
  if !active.is_subset(remaining){return Err("unexpected active variable".into());}
  let free=remaining.difference(&active).count();
  if components.len()>1{
   self.splits+=1;
   let mut answer=BigUint::one()<<free;
   for (part,scope) in &components{
    answer*=self.solve(part,scope)?;
    if answer.is_zero(){break;}
   }
   self.memo.insert(key,answer.clone());return Ok(answer);
  }
  if free>0{
   let answer=(BigUint::one()<<free)*self.solve(&current,&active)?;
   self.memo.insert(key,answer.clone());return Ok(answer);
  }
  let mut appearances=BTreeMap::<usize,usize>::new();
  for eq in &current{for mon in eq{for v in set_bits(mon){
   *appearances.entry(v).or_default()+=1;
  }}}
  let chosen=appearances.iter().max_by_key(|&(&v,&count)|{
   (count,std::cmp::Reverse(v))
  }).map(|(&v,_)|v).ok_or("nontrivial equation lacks variables")?;
  let mut next=remaining.clone();next.remove(&chosen);
  let left=current.iter().map(|p|self.cofactor(p,chosen,false))
   .collect::<Vec<_>>();
  let right=current.iter().map(|p|self.cofactor(p,chosen,true))
   .collect::<Vec<_>>();
  let answer=self.solve(&left,&next)?+self.solve(&right,&next)?;
  self.memo.insert(key,answer.clone());Ok(answer)
 }
}

pub fn count(equations:&[Vec<Vec<usize>>],nvars:usize,max_states:usize)
 ->Result<Answer,String>{
 if max_states<1{return Err("invalid counting bounds".into());}
 if equations.iter().flat_map(|eq|eq.iter()).flat_map(|mon|mon.iter())
  .any(|&v|v<1 || v>nvars){
  return Err("equation uses an out-of-range variable".into());
 }
 let compiled=compile(equations);
 let remaining=(0..nvars).collect::<BTreeSet<_>>();
 let mut c=Counter{memo:BTreeMap::new(),cofactors:BTreeMap::new(),
  states:0,memo_hits:0,cofactor_hits:0,splits:0,forced:0,
  maximum:0,max_states};
 let answer=c.solve(&compiled,&remaining)?;
 Ok((answer.to_string(),c.states,c.memo_hits,c.cofactor_hits,
     c.cofactors.len(),c.splits,c.forced,c.maximum))
}

#[cfg(test)]mod tests{use super::*;#[test]fn simple(){
 assert_eq!(count(&[vec![vec![1]]],1,10).unwrap(),
  ("1".into(),1,0,0,1,0,1,1));
 assert_eq!(count(&[],100,10).unwrap().0,(BigUint::one()<<100).to_string());
}}
