//! R-102: finite graph-coloring selector features and frozen rule predicates.
use std::collections::BTreeMap;

pub type Signals=(isize,usize,isize,usize,usize,usize);

pub fn signals(n:usize,edges:&[(usize,usize)],colors:&[isize])->Result<Signals,String>{
 let k=colors.iter().copied().max().unwrap_or(-1)+1;
 let clique=crate::structured_coloring_study::greedy_clique(n,edges)?;
 let mut counts=BTreeMap::<isize,usize>::new();
 for &color in colors{*counts.entry(color).or_default()+=1;}
 let last_size=if k!=0{*counts.get(&(k-1)).unwrap_or(&0)}else{0};
 let min_class=counts.values().copied().min().unwrap_or(0);
 let singleton=counts.values().filter(|&&v|v==1).count();
 Ok((k,clique,k-clique as isize,last_size,min_class,singleton))
}

pub fn triggers(rule:&str,k:isize,gap:isize,last_size:usize,min_class:usize,singleton:usize)
 ->Result<bool,String>{
 let g=gap>0;
 let result=match rule{
  "uncertified"=>g,
  "gap_ge_2"=>gap>=2,
  "gap_ge_3"=>gap>=3,
  "uncertified_last_le_1"=>g && last_size<=1,
  "uncertified_last_le_2"=>g && last_size<=2,
  "uncertified_last_le_3"=>g && last_size<=3,
  "uncertified_singleton"=>g && singleton>=1,
  "uncertified_minclass_le_2"=>g && min_class<=2,
  "uncertified_k_ge_4"=>g && k>=4,
  "uncertified_last_le_2_or_singleton"=>g && (last_size<=2 || singleton>=1),
  _=>return Err("unknown selector".into()),
 };
 Ok(result)
}

/// R-106: count true/false candidate decisions without changing any rule.
pub fn confusion(rule:&str,rows:&[(bool,isize,isize,usize,usize,usize)])
 ->Result<(usize,usize,usize,usize,usize,usize),String>{
 let positives=rows.iter().filter(|r|r.0).count();
 let mut selected=0;let mut true_positive=0;
 for &(failure,k,gap,last_size,min_class,singleton) in rows{
  if triggers(rule,k,gap,last_size,min_class,singleton)?{
   selected+=1;
   if failure{true_positive+=1;}
  }
 }
 Ok((rows.len(),positives,selected,true_positive,
     positives-true_positive,selected-true_positive))
}

#[cfg(test)]mod tests{use super::*;#[test]fn signals_and_rules(){
 assert_eq!(signals(3,&[(0,1),(1,2)],&[0,1,0]).unwrap(),(2,2,0,1,1,1));
 assert_eq!(triggers("uncertified",2,0,1,1,1).unwrap(),false);
 assert_eq!(triggers("gap_ge_2",5,2,1,1,2).unwrap(),true);
 assert_eq!(confusion("uncertified",&[(true,3,1,1,1,1),
  (false,2,0,1,1,1)]).unwrap(),(2,1,1,1,0,0));
}}
