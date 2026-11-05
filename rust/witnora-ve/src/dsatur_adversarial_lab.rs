//! R-097: deterministic exact bounded k-coloring decision witness.
//! Backtracking is exponential and a finite witness does not prove novelty.
use std::collections::BTreeSet;

pub fn exact_k_coloring(n:usize,edges:&[(usize,usize)],k:usize)
 ->Result<Option<Vec<usize>>,String>{
 if n>16{return Err("supported n <= 16 and nonnegative k".into());}
 let mut pairs=BTreeSet::new();
 for &(u,v) in edges{
  if u>=v || v>=n || !pairs.insert((u,v)){
   return Err("invalid simple graph".into());
  }
 }
 if n==0{return Ok(Some(Vec::new()));}
 if k==0{return Ok(None);}
 let mut neighbors=vec![Vec::new();n];
 for &(u,v) in edges{neighbors[u].push(v);neighbors[v].push(u);}
 let mut colors=vec![-1i32;n];
 fn search(used:usize,remaining:usize,k:usize,neighbors:&[Vec<usize>],colors:&mut [i32])->bool{
  if remaining==0{return true;}
  let mut best=None;
  for v in 0..colors.len(){if colors[v]>=0{continue;}
   let saturation: BTreeSet<i32>=neighbors[v].iter()
    .filter_map(|&u|(colors[u]>=0).then_some(colors[u])).collect();
   let priority=(saturation.len(),neighbors[v].len(),std::cmp::Reverse(v));
   if best.as_ref().map_or(true,|(_,p)|priority>*p){best=Some((v,priority));}
  }
  let chosen=best.expect("a vertex remains").0;
  let forbidden:BTreeSet<i32>=neighbors[chosen].iter()
   .filter_map(|&u|(colors[u]>=0).then_some(colors[u])).collect();
  for color in 0..(used+1).min(k){
   if forbidden.contains(&(color as i32)){continue;}
   colors[chosen]=color as i32;
   if search(used.max(color+1),remaining-1,k,neighbors,colors){return true;}
   colors[chosen]=-1;
  }
  false
 }
 if search(0,n,k,&neighbors,&mut colors){
  Ok(Some(colors.into_iter().map(|x|x as usize).collect()))
 }else{Ok(None)}
}

#[cfg(test)]mod tests{use super::*;#[test]fn odd_cycle(){
 let edges=[(0,1),(1,2),(2,3),(3,4),(0,4)];
 assert!(exact_k_coloring(5,&edges,2).unwrap().is_none());
 assert!(exact_k_coloring(5,&edges,3).unwrap().is_some());
}}
