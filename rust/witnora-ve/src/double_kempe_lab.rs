//! R-100: deterministic two-step Kempe repair with bounded recoloring.
use std::collections::BTreeSet;

pub type Answer=(usize,Vec<usize>,bool,usize,Vec<usize>,Vec<usize>,Option<usize>);

pub fn repair(n:usize,edges:&[(usize,usize)],original:&[usize],
 first_limit:usize,second_limit:usize,total_limit:usize,recolor_nodes:usize)
 ->Result<Answer,String>{
 if [first_limit,second_limit,total_limit,recolor_nodes].contains(&0){
  return Err("positive search budgets required".into());
 }
 if !crate::color_repair_lab::checked(n,edges,original){
  return Err("invalid initial proper coloring".into());
 }
 let original_k=original.iter().max().map_or(0,|&v|v+1);
 let mut attempts=0;
 let mut visited=BTreeSet::from([original.to_vec()]);
 for first in crate::kempe_repair_lab::swaps(n,edges,original)?.into_iter().take(first_limit){
  let first_component=first.2;
  for second in crate::kempe_repair_lab::swaps(n,edges,&first.0)?.into_iter().take(second_limit){
   let colors=second.0;
   if !visited.insert(colors.clone()){continue;}
   attempts+=1;
   let used=colors.iter().copied().collect::<BTreeSet<_>>().into_iter().collect::<Vec<_>>();
   if used.len()<original_k{
    let compressed=colors.iter().map(|c|used.binary_search(c).unwrap()).collect();
    return Ok((used.len(),compressed,true,attempts,first_component,second.2,Some(0)));
   }
   let trial=crate::color_repair_lab::recolor(n,edges,&colors,5,recolor_nodes)?;
   if trial.2{
    return Ok((trial.0,trial.1,true,attempts,first_component,second.2,Some(trial.3)));
   }
   if attempts>=total_limit{break;}
  }
  if attempts>=total_limit{break;}
 }
 Ok((original_k,original.to_vec(),false,attempts,vec![],vec![],None))
}

#[cfg(test)]mod tests{use super::*;#[test]fn empty_moves(){
 let x=repair(1,&[],&[0],2,2,2,10).unwrap();
 assert_eq!(x,(1,vec![0],false,0,vec![],vec![],None));
}}
