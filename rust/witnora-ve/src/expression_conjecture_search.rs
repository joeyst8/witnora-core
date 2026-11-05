//! R-088: finite graph-expression grammar, signatures and holdout falsification.
//! Survivors have no theorem or novelty status.
use std::collections::{BTreeMap,BTreeSet};

const ATOMS:&[&str]=&["n","m","alpha","tau","omega","chi","nu","delta","0","1","2"];
const OPS:&[&str]=&["+","-","*","min","max"];

#[derive(Clone)]
struct Expr{op:&'static str,a:&'static str,b:&'static str}
impl Expr{
 fn label(&self)->String{
  match self.op{
   "atom"=>self.a.into(),
   "min"|"max"=>format!("{}({},{})",self.op,self.a,self.b),
   _=>format!("({}{}{})",self.a,self.op,self.b),
  }
 }
 fn complexity(&self)->usize{usize::from(self.op!="atom")}
 fn value(name:&str,row:&BTreeMap<String,i64>)->Result<i64,String>{
  if let Ok(constant)=name.parse::<i64>(){return Ok(constant);}
  row.get(name).copied().ok_or_else(||format!("missing graph metric: {name}"))
 }
 fn evaluate(&self,row:&BTreeMap<String,i64>)->Result<i64,String>{
  let x=Self::value(self.a,row)?;
  if self.op=="atom"{return Ok(x);}
  let y=Self::value(self.b,row)?;
  Ok(match self.op{"+"=>x+y,"-"=>x-y,"*"=>x*y,"min"=>x.min(y),
      "max"=>x.max(y),_=>return Err("unknown operator".into())})
 }
}
fn pool()->Vec<Expr>{
 let mut expressions=ATOMS.iter().map(|&a|Expr{op:"atom",a,b:""}).collect::<Vec<_>>();
 for &op in OPS{
  for (i,&a) in ATOMS.iter().enumerate(){for &b in &ATOMS[i+1..]{
   if ["0","1","2"].contains(&a) || ["0","1","2"].contains(&b){continue;}
   expressions.push(Expr{op,a,b});
   if op=="-"{expressions.push(Expr{op,a:b,b:a});}
  }}
 }
 expressions
}

pub type Rejected=(String,usize,Vec<(usize,usize)>,i64,i64);
pub type Holdout=(usize,Vec<(usize,usize)>,BTreeMap<String,i64>);
pub fn run(training:&[BTreeMap<String,i64>],holdout:&[Holdout],max_candidates:usize)
 ->Result<(usize,usize,Vec<String>,Vec<Rejected>),String>{
 let expressions=pool();
 let mut signatures:BTreeMap<Vec<i64>,Vec<usize>>=BTreeMap::new();
 for (i,e) in expressions.iter().enumerate(){
  let signature=training.iter().map(|row|e.evaluate(row)).collect::<Result<Vec<_>,_>>()?;
  signatures.entry(signature).or_default().push(i);
 }
 let mut candidates=Vec::<(usize,usize)>::new();
 for (signature,equivalent) in signatures{
  if signature.iter().collect::<BTreeSet<_>>().len()<3{continue;}
  for (i,&a) in equivalent.iter().enumerate(){for &b in &equivalent[i+1..]{
   if expressions[a].complexity()+expressions[b].complexity()==0{continue;}
   if expressions[a].label()==expressions[b].label(){continue;}
   candidates.push((a,b));
  }}
 }
 candidates.sort_by_cached_key(|&(a,b)|(
     expressions[a].complexity()+expressions[b].complexity(),
     expressions[a].label(),expressions[b].label()));
 let candidate_count=candidates.len();
 let mut survivors=Vec::new();
 let mut rejected=Vec::new();
 for &(a,b) in candidates.iter().take(max_candidates){
  let name=format!("{} = {}",expressions[a].label(),expressions[b].label());
  let mut failure=None;
  for (n,edges,row) in holdout{
   let left=expressions[a].evaluate(row)?;
   let right=expressions[b].evaluate(row)?;
   if left!=right{failure=Some((*n,edges.clone(),left,right));break;}
  }
  if let Some((n,edges,left,right))=failure{rejected.push((name,n,edges,left,right));}
  else{survivors.push(name);}
 }
 Ok((expressions.len(),candidate_count,survivors,rejected))
}

pub fn evaluate(op:&str,a:&str,b:&str,row:&BTreeMap<String,i64>)->Result<i64,String>{
 let x=Expr::value(a,row)?;
 if op=="atom"{return Ok(x);}
 let y=Expr::value(b,row)?;
 Ok(match op{"+"=>x+y,"-"=>x-y,"*"=>x*y,"min"=>x.min(y),
     "max"=>x.max(y),_=>return Err("unknown operator".into())})
}

#[cfg(test)]
mod tests{
 use super::*;
 #[test]fn arithmetic_and_pool(){
  let row=BTreeMap::from([("n".into(),5),("tau".into(),2)]);
  assert_eq!(evaluate("-","n","tau",&row).unwrap(),3);
  assert_eq!(pool().len(),11+5*28+28);
 }
}
