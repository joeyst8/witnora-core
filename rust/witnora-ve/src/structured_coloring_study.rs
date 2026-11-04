//! R-101: witnessed greedy-clique lower bound, preserving deterministic tie breaks.
use std::collections::BTreeSet;

pub fn greedy_clique(n:usize,edges:&[(usize,usize)])->Result<usize,String>{
 let mut adjacency=vec![BTreeSet::new();n];
 for &(u,v) in edges{
  if u>=n || v>=n || u==v{return Err("invalid simple graph edge".into());}
  adjacency[u].insert(v);adjacency[v].insert(u);
 }
 if n==0{return Ok(0);}
 let mut best=1;
 for start in 0..n{
  let mut candidates=adjacency[start].clone();let mut clique_size=1;
  while !candidates.is_empty(){
   let chosen=*candidates.iter().max_by_key(|&&v|{
    (adjacency[v].intersection(&candidates).count(),adjacency[v].len(),
     std::cmp::Reverse(v))
   }).expect("nonempty candidates");
   clique_size+=1;
   candidates= candidates.intersection(&adjacency[chosen]).copied().collect();
  }
  best=best.max(clique_size);
 }
 Ok(best)
}
#[cfg(test)]mod tests{use super::*;#[test]fn basic(){
 assert_eq!(greedy_clique(0,&[]).unwrap(),0);
 assert_eq!(greedy_clique(3,&[(0,1),(1,2),(0,2)]).unwrap(),3);
 assert_eq!(greedy_clique(4,&[(0,1),(2,3)]).unwrap(),2);
}}
