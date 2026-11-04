//! R-104: finite graph component, 2-connectivity, Brooks, degeneracy bounds.
use std::collections::BTreeSet;

pub type Answer=(Vec<Vec<usize>>,bool,usize,usize);

pub fn bounds(n:usize,edges:&[(usize,usize)])->Result<Answer,String>{
 let mut neighbors=vec![BTreeSet::new();n];
 for &(u,v) in edges{
  if u>=n || v>=n || u==v{return Err("invalid simple graph edge".into());}
  neighbors[u].insert(v);neighbors[v].insert(u);
 }
 let mut seen=BTreeSet::new();let mut components=Vec::new();
 for start in 0..n{
  if !seen.insert(start){continue;}
  let mut component=Vec::new();let mut queue=vec![start];let mut cursor=0;
  while cursor<queue.len(){
   let u=queue[cursor];cursor+=1;component.push(u);
   for &v in &neighbors[u]{if seen.insert(v){queue.push(v);}}
  }
  component.sort_unstable();components.push(component);
 }
 let mut two_connected=n>=3 && components.len()==1;
 if two_connected{
  for removed in 0..n{
   let root=if removed==0{1}else{0};
   let mut reached=BTreeSet::from([root]);let mut stack=vec![root];
   while let Some(u)=stack.pop(){
    for &v in &neighbors[u]{
     if v!=removed && reached.insert(v){stack.push(v);}
    }
   }
   if reached.len()!=n-1{two_connected=false;break;}
  }
 }
 let mut brooks=0;
 for component in &components{
  let size=component.len();
  let degrees=component.iter().map(|&v|neighbors[v].len()).collect::<Vec<_>>();
  let maximum=degrees.iter().copied().max().unwrap_or(0);
  let local_edges=degrees.iter().sum::<usize>()/2;
  let complete=local_edges==size*(size-1)/2;
  let odd_cycle=size>=3 && size%2==1 && degrees.iter().all(|&d|d==2);
  let local=if complete || odd_cycle{maximum+1}else{maximum};
  brooks=brooks.max(local);
 }
 let mut remaining=(0..n).collect::<BTreeSet<_>>();let mut degeneracy=0;
 while !remaining.is_empty(){
  let chosen=*remaining.iter().min_by_key(|&&v|{
   (neighbors[v].intersection(&remaining).count(),v)
  }).expect("nonempty remaining set");
  degeneracy=degeneracy.max(neighbors[chosen].intersection(&remaining).count());
  remaining.remove(&chosen);
 }
 let deg_bound=if n==0{0}else{degeneracy+1};
 Ok((components,two_connected,brooks,deg_bound))
}

#[cfg(test)]mod tests{use super::*;#[test]fn basic(){
 assert_eq!(bounds(0,&[]).unwrap(),(vec![],false,0,0));
 assert_eq!(bounds(3,&[(0,1),(1,2),(0,2)]).unwrap(),(vec![vec![0,1,2]],true,3,3));
}}
