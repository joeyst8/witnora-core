//! R-091 finite conditional and transformed graph conjecture screening.
//! Empirical survivors do not establish universal mathematical validity.
use std::collections::BTreeMap;
pub type Metrics=BTreeMap<String,i64>;
pub type Record=(usize,Vec<(usize,usize)>,Metrics,Metrics,Metrics,BTreeMap<String,bool>);
pub type Falsified=(String,usize,Vec<(usize,usize)>);
type Template=(&'static str,&'static str,&'static str,&'static str);
const CONDITIONS:[&str;4]=["connected","bipartite","triangle_free","tree"];
const RELATIONS:[&str;5]=["chi<=2","omega<=2","tau==nu","m>=n-1","alpha>=2"];
const TRANSFORM_METRICS:[&str;6]=["alpha","tau","omega","chi","nu","delta"];

fn templates()->Vec<Template>{
 let mut t=Vec::new();
 for a in CONDITIONS{for b in RELATIONS{t.push(("conditional",a,b,""));}}
 for a in ["complement","delete_vertex_0"]{for b in TRANSFORM_METRICS{
  for c in ["le","ge","eq"]{t.push(("transform",a,b,c));}
 }}
 t.push(("cross","alpha","omega","complement"));
 t.push(("cross","omega","alpha","complement"));t
}
fn val(m:&Metrics,key:&str)->Result<i64,String>{
 m.get(key).copied().ok_or_else(||format!("missing metric: {key}"))
}
fn relation(name:&str,m:&Metrics)->Result<bool,String>{
 Ok(match name{
  "chi<=2"=>val(m,"chi")?<=2,
  "omega<=2"=>val(m,"omega")?<=2,
  "tau==nu"=>val(m,"tau")?==val(m,"nu")?,
  "m>=n-1"=>val(m,"m")?>=val(m,"n")?-1,
  "alpha>=2"=>val(m,"alpha")?>=2,
  _=>return Err("unknown relation".into()),
 })
}
fn transform<'a>(r:&'a Record,name:&str)->Result<&'a Metrics,String>{
 match name{"complement"=>Ok(&r.3),"delete_vertex_0"=>Ok(&r.4),
  _=>Err("unknown transform".into())}
}
fn applicable(r:&Record,name:&str)->Result<bool,String>{
 r.5.get(name).copied().ok_or_else(||format!("missing condition: {name}"))
}
fn holds(t:Template,r:&Record)->Result<bool,String>{
 let (kind,a,b,c)=t;
 Ok(match kind{
  "conditional"=>!applicable(r,a)? || relation(b,&r.2)?,
  "cross"=>val(&r.2,a)?==val(&r.3,b)?,
  "transform"=>{let lhs=val(transform(r,a)?,b)?;let rhs=val(&r.2,b)?;
   match c{"le"=>lhs<=rhs,"ge"=>lhs>=rhs,"eq"=>lhs==rhs,
    _=>return Err("unknown direction".into())}},
  _=>return Err("unknown template".into()),
 })
}
fn nonvacuous(t:Template,training:&[Record])->Result<bool,String>{
 let (kind,a,b,_)=t;
 match kind{
  "conditional"=>{
   let mut yes=0;let mut no=0;let mut outside_failure=false;
   for r in training{if applicable(r,a)?{yes+=1;}else{
    no+=1;if !relation(b,&r.2)?{outside_failure=true;}
   }}
   Ok(yes>=20 && no>=20 && outside_failure)
  },
  "transform"=>{
   let mut differing=0;
   for r in training{if val(transform(r,a)?,b)?!=val(&r.2,b)?{differing+=1;}}
   Ok(differing>=20)
  },
  _=>Ok(true),
 }
}
fn statement(t:Template)->String{
 let (kind,a,b,c)=t;
 match kind{
  "conditional"=>format!("if {a}(G) then {b}"),
  "transform"=>format!("{b}({a}(G)) {} {b}(G)",match c{"le"=>"<=","ge"=>">=",_=>"="}),
  _=>format!("{a}(G) = {b}(complement(G))"),
 }
}
pub fn run(training:&[Record],holdout:&[Record])
 ->Result<(usize,usize,Vec<String>,Vec<Falsified>),String>{
 let all=templates();let mut candidates=Vec::new();
 for &t in &all{if nonvacuous(t,training)?{
  let mut passes=true;for row in training{if !holds(t,row)?{passes=false;break;}}
  if passes{candidates.push(t);}
 }}
 let mut survivors=Vec::new();let mut falsified=Vec::new();
 for t in &candidates{
  let mut witness=None;
  for r in holdout{if !holds(*t,r)?{witness=Some((r.0,r.1.clone()));break;}}
  if let Some((n,edges))=witness{falsified.push((statement(*t),n,edges));}
  else{survivors.push(statement(*t));}
 }
 survivors.sort();Ok((all.len(),candidates.len(),survivors,falsified))
}

#[cfg(test)]mod tests{use super::*;#[test]fn grammar_size(){assert_eq!(templates().len(),58);}}
