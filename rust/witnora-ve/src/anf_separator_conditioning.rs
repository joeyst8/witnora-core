//! R-109: arbitrary-width variable-hypergraph residual component sizes.
use num_bigint::BigUint;
use num_traits::{One,Zero};
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

/// R-110: deterministic, budgeted separator selection by balanced components.
pub fn find_separator(equations:&[Vec<Vec<usize>>],nvars:usize,
 max_separator_size:usize,max_candidate_checks:usize)
 ->Result<(Option<Vec<usize>>,usize),String>{
 if max_candidate_checks<1{return Err("invalid separator search bounds".into());}
 let mut scopes=Vec::new();let mut raw_scopes=Vec::new();let mut active=BTreeSet::new();
 for eq in equations{
  let mut vars=BTreeSet::new();let mut scope=BigUint::zero();
  for mon in eq{for &v in mon{
   if v<1 || v>nvars{return Err("equation uses an out-of-range variable".into());}
   vars.insert(v);active.insert(v);
   scope|=BigUint::one()<<(v-1);
  }}
  raw_scopes.push(vars);scopes.push(scope.to_string());
 }
 if component_sizes(&scopes,"0")?.len()!=1{return Ok((None,0));}
 let variables=active.into_iter().collect::<Vec<_>>();
 let degrees=variables.iter().map(|&v|{
  (v,raw_scopes.iter().filter(|row|row.contains(&v)).count())
 }).collect::<BTreeMap<_,_>>();
 let mut checked=0;
 for k in 1..=max_separator_size.min(variables.len()){
  let pool=if k==1 || variables.len()<=32{variables.clone()}
   else{
    let mut pool=variables.clone();
    pool.sort_by_key(|v|(std::cmp::Reverse(degrees[v]),*v));
    pool.truncate(24);pool.sort_unstable();pool
   };
  let mut best:Option<((usize,std::cmp::Reverse<usize>,Vec<usize>),Vec<usize>)>=None;
  fn choose<F:FnMut(&[usize])->bool>(pool:&[usize],k:usize,start:usize,
    selected:&mut Vec<usize>,visit:&mut F)->bool{
   if selected.len()==k{return visit(selected);}
   let need=k-selected.len();
   if pool.len().saturating_sub(start)<need{return true;}
   for i in start..=pool.len()-need{
    selected.push(pool[i]);
    let keep_going=choose(pool,k,i+1,selected,visit);
    selected.pop();
    if !keep_going{return false;}
   }
   true
  }
  let completed=choose(&pool,k,0,&mut vec![],&mut |selected|{
   if checked>=max_candidate_checks{return false;}
   checked+=1;
   let mut removed=BigUint::zero();
   for &v in selected{removed|=BigUint::one()<<(v-1);}
   let sizes=component_sizes(&scopes,&removed.to_string())
    .expect("validated scope masks");
   if sizes.len()>=2{
    let key=(sizes[0],std::cmp::Reverse(sizes.len()),selected.to_vec());
    if best.as_ref().map_or(true,|prior|&key<&prior.0){
     best=Some((key,selected.to_vec()));
    }
   }
   true
  });
  if !completed{return Ok((best.map(|entry|entry.1),checked));}
  if let Some((_,chosen))=best{return Ok((Some(chosen),checked));}
 }
 Ok((None,checked))
}

#[cfg(test)]mod tests{use super::*;#[test]fn sample(){
 assert_eq!(component_sizes(&["3".into(),"12".into()],"0").unwrap(),vec![2,2]);
 assert_eq!(component_sizes(&["3".into(),"6".into()],"2").unwrap(),vec![1,1]);
 assert_eq!(find_separator(&[vec![vec![1,2]],vec![vec![2,3]]],3,1,100).unwrap(),
  (Some(vec![2]),3));
}}
