//! R-109: arbitrary-width variable-hypergraph residual component sizes.
use num_bigint::BigUint;
use std::collections::{BTreeMap,BTreeSet};

fn bits(value:&BigUint)->Vec<usize>{
 let mut result=Vec::new();
 for (word_index,mut word) in value.to_u64_digits().into_iter().enumerate(){
  while word!=0{
   let offset=word.trailing_zeros() as usize;
   result.push(word_index*64+offset);
   word&=word-1;
  }
 }
 result
}

fn root(parent:&mut BTreeMap<usize,usize>,bit:usize)->usize{
 let p=parent[&bit];
 if p==bit{return bit;}
 let r=root(parent,p);parent.insert(bit,r);r
}

pub fn component_sizes(scopes:&[String],removed:&str)->Result<Vec<usize>,String>{
 let removed_mask=BigUint::parse_bytes(removed.as_bytes(),10)
  .ok_or("invalid removed mask")?;
 let removed_bits=bits(&removed_mask).into_iter().collect::<BTreeSet<_>>();
 let mut parent=BTreeMap::<usize,usize>::new();
 for scope in scopes{
  let mask=BigUint::parse_bytes(scope.as_bytes(),10)
   .ok_or("invalid scope mask")?;
  let remainder=bits(&mask).into_iter().filter(|v|!removed_bits.contains(v))
   .collect::<Vec<_>>();
  if let Some(&anchor)=remainder.first(){
   parent.entry(anchor).or_insert(anchor);
   for &v in remainder.iter().skip(1){
    parent.entry(v).or_insert(v);
    let ra=root(&mut parent,anchor);let rb=root(&mut parent,v);
    if ra!=rb{parent.insert(rb,ra);}
   }
  }
 }
 let mut sizes=BTreeMap::<usize,usize>::new();
 for bit in parent.keys().copied().collect::<Vec<_>>(){
  let r=root(&mut parent,bit);*sizes.entry(r).or_default()+=1;
 }
 let mut result=sizes.into_values().collect::<Vec<_>>();
 result.sort_unstable_by(|a,b|b.cmp(a));
 Ok(result)
}

#[cfg(test)]mod tests{use super::*;#[test]fn sample(){
 assert_eq!(component_sizes(&["3".into(),"12".into()],"0").unwrap(),vec![2,2]);
 assert_eq!(component_sizes(&["3".into(),"6".into()],"2").unwrap(),vec![1,1]);
}}
