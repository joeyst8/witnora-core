//! R-089: exact bounded graph invariants and finite conjecture screening.
use std::collections::BTreeMap;

pub type Metrics=BTreeMap<String,i64>;
pub type Holdout=(usize,Vec<(usize,usize)>,Metrics);
pub type Rejected=(String,usize,Vec<(usize,usize)>,Metrics);
const KEYS:[&str;8]=["n","m","alpha","tau","omega","chi","nu","delta"];

pub fn metrics(n:usize,edges:&[(usize,usize)])->Result<Metrics,String>{
 if n>11 || edges.iter().any(|&(u,v)|u>=v || v>=n){return Err("invalid bounded simple graph".into());}
 let mut neighbors=vec![0usize;n];
 for &(u,v) in edges{neighbors[u]|=1<<v;neighbors[v]|=1<<u;}
 let total=1usize<<n;
 let mut independent=vec![false;total];independent[0]=true;
 for mask in 1..total{
  let v=mask.trailing_zeros() as usize;let rest=mask & (mask-1);
  independent[mask]=independent[rest] && neighbors[v]&rest==0;
 }
 let alpha=(0..total).filter(|&m|independent[m]).map(|m|m.count_ones() as usize).max().unwrap_or(0);
 let omega=(0..total).filter(|&mask|(0..n).all(|v| mask&(1<<v)==0 || (neighbors[v] & (mask^(1<<v)))==(mask^(1<<v))))
    .map(|m|m.count_ones() as usize).max().unwrap_or(0);
 fn chromatic(mask:usize,n:usize,independent:&[bool],memo:&mut [Option<usize>])->usize{
  if mask==0{return 0;}if let Some(k)=memo[mask]{return k;}
  let anchor=mask & mask.wrapping_neg();let mut sub=mask;let mut best=n+1;
  while sub>0{if sub&anchor!=0 && independent[sub]{best=best.min(1+chromatic(mask^sub,n,independent,memo));}sub=(sub-1)&mask;}
  memo[mask]=Some(best);best
 }
 fn matching(mask:usize,neighbors:&[usize],memo:&mut [Option<usize>])->usize{
  if mask==0{return 0;}if let Some(k)=memo[mask]{return k;}
  let v=mask.trailing_zeros() as usize;let rest=mask & (mask-1);
  let mut best=matching(rest,neighbors,memo);let mut possible=neighbors[v]&rest;
  while possible>0{let other=possible & possible.wrapping_neg();possible^=other;
   best=best.max(1+matching(rest^other,neighbors,memo));}
  memo[mask]=Some(best);best
 }
 let chi=chromatic(total-1,n,&independent,&mut vec![None;total]);
 let nu=matching(total-1,&neighbors,&mut vec![None;total]);
 Ok([("n",n),("m",edges.len()),("alpha",alpha),("tau",n-alpha),
      ("omega",omega),("chi",chi),("nu",nu),
      ("delta",neighbors.iter().map(|x|x.count_ones() as usize).max().unwrap_or(0))]
    .into_iter().map(|(k,v)|(k.into(),v as i64)).collect())
}

fn templates()->Vec<(bool,usize,usize,usize)>{
 let mut result=Vec::new();
 for a in 0..8{for b in 0..8{if a!=b{result.push((true,a,b,0));}}}
 for a in 0..8{for b in a+1..8{for c in 0..8{if c!=a && c!=b{result.push((false,a,b,c));}}}}
 result
}
fn value(row:&Metrics,key:&str)->Result<i64,String>{row.get(key).copied().ok_or_else(||format!("missing graph metric: {key}"))}
fn holds(t:(bool,usize,usize,usize),row:&Metrics)->Result<bool,String>{
 let (_,a,b,c)=t;let a=value(row,KEYS[a])?;let b=value(row,KEYS[b])?;
 if t.0{Ok(a<=b)}else{Ok(a+b==value(row,KEYS[c])?)}
}
fn name(t:(bool,usize,usize,usize))->String{
 let (_,a,b,c)=t;
 if t.0{format!("{} <= {}",KEYS[a],KEYS[b])}
 else{format!("{} + {} = {}",KEYS[a],KEYS[b],KEYS[c])}
}
pub fn run(training:&[Metrics],holdout:&[Holdout])
 ->Result<(usize,usize,Vec<String>,Vec<Rejected>),String>{
 let all=templates();let mut selected=Vec::new();
 for &t in &all{if training.iter().map(|row|holds(t,row)).collect::<Result<Vec<_>,_>>()?.iter().all(|&b|b){selected.push(t);}}
 let mut survivors=Vec::new();let mut rejected=Vec::new();
 for &t in &selected{
  let mut failure=None;
  for (n,edges,row) in holdout{if !holds(t,row)?{failure=Some((*n,edges.clone(),row.clone()));break;}}
  if let Some((n,edges,row))=failure{rejected.push((name(t),n,edges,row));}
  else{survivors.push(name(t));}
 }
 survivors.sort();Ok((all.len(),selected.len(),survivors,rejected))
}

#[cfg(test)]mod tests{use super::*;#[test]fn empty_and_triangle(){
 let empty=metrics(0,&[]).unwrap();assert_eq!(empty["chi"],0);
 let triangle=metrics(3,&[(0,1),(0,2),(1,2)]).unwrap();
 assert_eq!((triangle["alpha"],triangle["omega"],triangle["chi"],triangle["nu"]),(1,3,3,1));
 assert_eq!(templates().len(),56+28*6);
}}
