//! R-103: deterministic greedy DSATUR coloring and explicit proper witness.
use std::collections::BTreeSet;

pub fn greedy(n:usize,edges:&[(usize,usize)])->Result<(usize,Vec<usize>),String>{
 let mut neighbors=vec![BTreeSet::new();n];
 for &(u,v) in edges{
  if u>=n || v>=n || u==v{return Err("invalid simple graph edge".into());}
  neighbors[u].insert(v);neighbors[v].insert(u);
 }
 let mut colors=vec![-1isize;n];
 let mut uncolored=(0..n).collect::<BTreeSet<_>>();
 while !uncolored.is_empty(){
  let chosen=*uncolored.iter().max_by_key(|&&v|{
   let saturation=neighbors[v].iter().filter_map(|&u|{
    if colors[u]>=0{Some(colors[u])}else{None}
   }).collect::<BTreeSet<_>>().len();
   (saturation,neighbors[v].len(),std::cmp::Reverse(v))
  }).expect("nonempty remaining vertices");
  let forbidden=neighbors[chosen].iter().filter_map(|&u|{
   if colors[u]>=0{Some(colors[u])}else{None}
  }).collect::<BTreeSet<_>>();
  let mut color=0isize;
  while forbidden.contains(&color){color+=1;}
  colors[chosen]=color;
  uncolored.remove(&chosen);
 }
 if edges.iter().any(|&(u,v)|colors[u]==colors[v]){
  return Err("greedy coloring invalid".into());
 }
 let bound=colors.iter().copied().max().unwrap_or(-1)+1;
 Ok((bound as usize,colors.into_iter().map(|x|x as usize).collect()))
}

#[cfg(test)]mod tests{use super::*;#[test]fn triangle(){
 assert_eq!(greedy(3,&[(0,1),(1,2),(0,2)]).unwrap(),(3,vec![0,1,2]));
 assert_eq!(greedy(0,&[]).unwrap(),(0,vec![]));
}}
