//! R-105: bounded constructive coloring by minimum cover/nonedge matching.
use std::collections::BTreeSet;

pub type Answer=(usize,Vec<usize>,Vec<Vec<usize>>,Vec<usize>);

fn nonedge_matching(mask:usize,neighbors:&[usize],
 memo:&mut [Option<Vec<(usize,usize)>>])->Vec<(usize,usize)>{
 if mask==0{return vec![];}
 if let Some(x)=&memo[mask]{return x.clone();}
 let bit=mask & (!mask+1);let u=bit.trailing_zeros() as usize;
 let rest=mask^bit;
 let mut best=nonedge_matching(rest,neighbors,memo);
 let mut options=rest & !neighbors[u];
 while options!=0{
  let partner_bit=options & (!options+1);options^=partner_bit;
  let v=partner_bit.trailing_zeros() as usize;
  let suffix=nonedge_matching(rest^partner_bit,neighbors,memo);
  let mut candidate=Vec::with_capacity(suffix.len()+1);
  candidate.push((u,v));candidate.extend(suffix);
  if candidate.len()>best.len() || (candidate.len()==best.len() && candidate<best){
   best=candidate;
  }
 }
 memo[mask]=Some(best.clone());best
}

pub fn matching_bound(n:usize,edges:&[(usize,usize)])->Result<Answer,String>{
 if n>11{return Err("bounded study only".into());}
 let mut edge_set=BTreeSet::new();let mut neighbors=vec![0usize;n];
 for &(u,v) in edges{
  if u>=v || v>=n || !edge_set.insert((u,v)){
   return Err("invalid simple graph".into());
  }
  neighbors[u]|=1<<v;neighbors[v]|=1<<u;
 }
 let full=(1usize<<n)-1;
 let mut independent=vec![false;1<<n];independent[0]=true;
 for mask in 1usize..1<<n{
  let bit=mask & (!mask+1);let v=bit.trailing_zeros() as usize;
  let rest=mask^bit;
  independent[mask]=independent[rest] && (neighbors[v]&rest)==0;
 }
 let mut memo=vec![None;1<<n];
 let mut best:Option<(usize,usize,usize,Vec<(usize,usize)>)>=None;
 for cover in 0..1<<n{
  let outside=full^cover;
  if !independent[outside]{continue;}
  let matching=nonedge_matching(cover,&neighbors,&mut memo);
  let count=cover.count_ones() as usize;
  let bound=count-matching.len()+usize::from(outside!=0);
  let trial=(bound,count,cover,matching);
  if best.as_ref().map_or(true,|prior|&trial<prior){best=Some(trial);}
 }
 let (bound,_,cover,matching)=best.ok_or("missing coloring witness")?;
 let mut colors=vec![usize::MAX;n];let mut next=0;
 for &(u,v) in &matching{colors[u]=next;colors[v]=next;next+=1;}
 for u in 0..n{
  if cover&(1<<u)!=0 && colors[u]==usize::MAX{colors[u]=next;next+=1;}
 }
 if full^cover!=0{
  for (u,color) in colors.iter_mut().enumerate(){
   if cover&(1<<u)==0{*color=next;}
  }
  next+=1;
 }
 if next!=bound || colors.contains(&usize::MAX) ||
    edges.iter().any(|&(u,v)|colors[u]==colors[v]){
  return Err("invalid constructed coloring".into());
 }
 Ok((bound,(0..n).filter(|&u|cover&(1<<u)!=0).collect(),
  matching.into_iter().map(|(u,v)|vec![u,v]).collect(),colors))
}

#[cfg(test)]mod tests{use super::*;#[test]fn cases(){
 assert_eq!(matching_bound(0,&[]).unwrap(),(0,vec![],vec![],vec![]));
 let x=matching_bound(3,&[(0,1),(0,2),(1,2)]).unwrap();
 assert_eq!(x.0,3);
}}
