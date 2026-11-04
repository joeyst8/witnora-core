//! R-098: bounded, incomplete local recoloring with exact visit accounting.
use std::collections::BTreeSet;
pub type Answer=(usize,Vec<usize>,bool,usize,bool);

pub fn checked(n:usize,edges:&[(usize,usize)],colors:&[usize])->bool{
 colors.len()==n && edges.iter().all(|&(u,v)|u<n && v<n && colors[u]!=colors[v])
}
pub fn recolor(n:usize,edges:&[(usize,usize)],initial:&[usize],
 max_changed:usize,max_nodes:usize)->Result<Answer,String>{
 if !checked(n,edges,initial){return Err("not a proper initial coloring".into());}
 if max_nodes<1{return Err("invalid budgets".into());}
 let k=initial.iter().max().map_or(0,|&x|x+1);
 if k<=1{return Ok((k,initial.to_vec(),false,0,false));}
 let mut adjacency=vec![BTreeSet::new();n];
 for &(u,v) in edges{adjacency[u].insert(v);adjacency[v].insert(u);}
 let mut order=(0..n).collect::<Vec<_>>();
 order.sort_by_key(|&v|(initial[v]!=k-1,std::cmp::Reverse(adjacency[v].len()),v));
 let mut result=vec![-1isize;n];let mut nodes=0usize;let mut exhausted=false;
 fn visit(index:usize,changed:usize,n:usize,max_changed:usize,max_nodes:usize,
   k:usize,initial:&[usize],order:&[usize],adjacency:&[BTreeSet<usize>],
   result:&mut [isize],nodes:&mut usize,exhausted:&mut bool)->bool{
  *nodes+=1;
  if *nodes>max_nodes{*exhausted=true;return false;}
  if index==n{return true;}
  let v=order[index];let original=initial[v];
  let mut choices=(0..k-1).collect::<Vec<_>>();
  choices.sort_by_key(|&c|(c!=original,c));
  for color in choices{
   let extra=usize::from(color!=original);
   if changed+extra>max_changed{continue;}
   if adjacency[v].iter().any(|&u|result[u]==color as isize){continue;}
   result[v]=color as isize;
   if visit(index+1,changed+extra,n,max_changed,max_nodes,k,initial,order,adjacency,result,nodes,exhausted){return true;}
   result[v]=-1;
   if *exhausted{return false;}
  }
  false
 }
 let found=visit(0,0,n,max_changed,max_nodes,k,initial,&order,
  &adjacency,&mut result,&mut nodes,&mut exhausted);
 if found{
  Ok((k-1,result.into_iter().map(|x|x as usize).collect(),true,nodes,exhausted))
 }else{Ok((k,initial.to_vec(),false,nodes,exhausted))}
}
#[cfg(test)]mod tests{use super::*;#[test]fn single_color(){
 assert_eq!(recolor(1,&[],&[0],5,10).unwrap(),(1,vec![0],false,0,false));
}}
