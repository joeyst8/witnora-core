//! Opt-in exact GF(2) XOR equation primitives for the Python reference model.
use std::collections::{BTreeMap,BTreeSet};

/// R-121: canonicalize XOR support by toggling each variable occurrence.
pub fn normalize_variables(variables:&[usize])->Result<Vec<usize>,String>{
 let mut active=BTreeSet::new();
 for &v in variables{
  if v==0{return Err("XOR variable IDs must be positive".into());}
  if !active.insert(v){active.remove(&v);}
 }
 Ok(active.into_iter().collect())
}

/// R-122: exact partial-assignment evaluation, retaining UNKNOWN on missing bits.
pub fn evaluate(variables:&[usize],rhs:u8,assignment:&[(usize,bool)])->Option<bool>{
 let bindings=assignment.iter().copied().collect::<BTreeMap<_,_>>();
 let mut parity=rhs&1;
 for &v in variables{
  parity^=u8::from(*bindings.get(&v)?);
 }
 Some(parity==0)
}

/// R-123: exact GF(2) substitution, returning residual support and RHS.
pub fn substitute(variables:&[usize],rhs:u8,assignment:&[(usize,bool)])
 ->(Vec<usize>,u8){
 let bindings=assignment.iter().copied().collect::<BTreeMap<_,_>>();
 let mut residual=Vec::new();let mut parity=rhs&1;
 for &v in variables{
  if let Some(&bit)=bindings.get(&v){parity^=u8::from(bit);}
  else{residual.push(v);}
 }
 (residual,parity)
}

#[cfg(test)]mod tests{use super::*;#[test]fn normalization(){
 assert_eq!(normalize_variables(&[3,1,3,2,1,7]).unwrap(),vec![2,7]);
 assert_eq!(normalize_variables(&[]).unwrap(),Vec::<usize>::new());
 assert!(normalize_variables(&[1,0]).is_err());
 assert_eq!(evaluate(&[1,2],1,&[(1,true),(2,false)]),Some(true));
 assert_eq!(evaluate(&[1,2],0,&[(1,true)]),None);
 assert_eq!(substitute(&[1,2,3],1,&[(2,true)]),(vec![1,3],0));
}}
