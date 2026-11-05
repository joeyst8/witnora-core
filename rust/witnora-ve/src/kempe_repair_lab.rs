//! R-099: exact two-color connected-component Kempe swaps.
use std::collections::BTreeSet;
pub type Variant=(Vec<usize>,Vec<usize>,Vec<usize>);

pub fn swaps(n:usize,edges:&[(usize,usize)],initial:&[usize])
 ->Result<Vec<Variant>,String>{
 if !crate::color_repair_lab::checked(n,edges,initial){
  return Err("invalid initial coloring".into());
 }
 let mut neighbors=vec![BTreeSet::new();n];
 for &(u,v) in edges{neighbors[u].insert(v);neighbors[v].insert(u);}
 let k=initial.iter().max().map_or(0,|&v|v+1);
 let mut variants=Vec::new();
 let mut seen_colorings=BTreeSet::from([initial.to_vec()]);
 for a in 0..k{for b in a+1..k{
  let eligible:BTreeSet<usize>=(0..n).filter(|&v|initial[v]==a || initial[v]==b).collect();
  let mut seen=BTreeSet::new();
  for &start in &eligible{
   if seen.contains(&start){continue;}
   let mut component=BTreeSet::from([start]);let mut todo=vec![start];seen.insert(start);
   while let Some(last)=todo.pop(){
    for &v in neighbors[last].intersection(&eligible){
     if seen.insert(v){component.insert(v);todo.push(v);}
    }
   }
   let mut result=initial.to_vec();
   for &v in &component{result[v]=if initial[v]==a{b}else{a};}
   if !seen_colorings.insert(result.clone()){continue;}
   if !crate::color_repair_lab::checked(n,edges,&result){
    return Err("Kempe swap violated proper coloring".into());
   }
   variants.push((result,vec![a,b],component.into_iter().collect()));
  }
 }}
 Ok(variants)
}
#[cfg(test)]mod tests{use super::*;#[test]fn simple_swap(){
 let x=swaps(2,&[(0,1)],&[0,1]).unwrap();assert_eq!(x.len(),1);
 assert_eq!(x[0].0,vec![1,0]);
}}
