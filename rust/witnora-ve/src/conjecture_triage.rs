//! R-061: conservative fixed-grammar conjecture identity normalization.
//! No output from this module constitutes a theorem or novelty claim.

use std::collections::BTreeSet;
use std::collections::BTreeMap;

pub type Adversarial=(usize,Vec<(usize,usize)>,BTreeMap<String,i64>);
pub type Falsified=(String,usize,Vec<(usize,usize)>,i64,i64);

fn eval_label(label:&str,row:&BTreeMap<String,i64>)->Result<i64,String>{
 if label.starts_with("min(") || label.starts_with("max("){
  let op=&label[..3];
  if !label.ends_with(')'){return Err("candidate absent from generated expression grammar".into());}
  let (a,b)=label[4..label.len()-1].split_once(',')
     .ok_or("candidate absent from generated expression grammar")?;
  return crate::expression_conjecture_search::evaluate(op,a,b,row);
 }
 if label.starts_with('(') && label.ends_with(')'){
  let inner=&label[1..label.len()-1];
  for op in ['+','-','*']{
   if let Some((a,b))=inner.split_once(op){
    return crate::expression_conjecture_search::evaluate(&op.to_string(),a,b,row);
   }
  }
 }
 if ["n","m","alpha","tau","omega","chi","nu","delta","0","1","2"].contains(&label){
  return crate::expression_conjecture_search::evaluate("atom",label,"",row);
 }
 Err("candidate absent from generated expression grammar".into())
}

pub fn triage(survivors:&[String],adversarial:&[Adversarial])
 ->Result<(Vec<String>,Vec<String>,Vec<Falsified>),String>{
 let known=known_identity_keys();
 let mut catalog=Vec::new();let mut unclassified=Vec::new();let mut falsified=Vec::new();
 for statement in survivors{
  if known.contains(&identity_key(statement)?){catalog.push(statement.clone());continue;}
  let (a,b)=statement.split_once(" = ")
   .ok_or("candidate absent from generated expression grammar")?;
  let mut witness=None;
  for (n,edges,row) in adversarial{
   let lhs=eval_label(a,row)?;let rhs=eval_label(b,row)?;
   if lhs!=rhs{witness=Some((*n,edges.clone(),lhs,rhs));break;}
  }
  if let Some((n,edges,lhs,rhs))=witness{
   falsified.push((statement.clone(),n,edges,lhs,rhs));
  }else{unclassified.push(statement.clone());}
 }
 catalog.sort();unclassified.sort();Ok((catalog,unclassified,falsified))
}

pub fn normalize_expression(expr: &str) -> Result<String, String> {
    let expr = expr.trim();
    for op in ['+', '*'] {
        if expr.starts_with('(') && expr.ends_with(')') && expr.matches(op).count() == 1 {
            let inner = &expr[1..expr.len() - 1];
            let (a, b) = inner.split_once(op).ok_or("malformed binary expression")?;
            let mut parts = [a, b];
            parts.sort();
            return Ok(format!("({}{}{})", parts[0], op, parts[1]));
        }
    }
    for op in ["min", "max"] {
        if expr.starts_with(&format!("{op}(")) && expr.ends_with(')') {
            let inner = &expr[op.len() + 1..expr.len() - 1];
            let mut parts = inner.split(',');
            let a = parts.next().ok_or("malformed binary function")?;
            let b = parts.next().ok_or("malformed binary function")?;
            if parts.next().is_some() { return Err("malformed binary function".into()); }
            let mut sorted = [a, b];
            sorted.sort();
            return Ok(format!("{op}({},{})", sorted[0], sorted[1]));
        }
    }
    Ok(expr.to_owned())
}

pub fn identity_key(statement: &str) -> Result<(String, String), String> {
    let (left, right) = statement.split_once(" = ")
        .ok_or("statement requires ' = ' delimiter")?;
    let mut sides = [normalize_expression(left)?, normalize_expression(right)?];
    sides.sort();
    Ok((sides[0].clone(), sides[1].clone()))
}

pub fn known_identity_keys() -> BTreeSet<(String, String)> {
    let mut catalog: Vec<String> = [
        "n = (alpha+tau)", "alpha = (n-tau)", "tau = (n-alpha)",
        "chi = max(omega,chi)", "alpha = min(n,alpha)",
        "chi = min(n,chi)", "delta = min(n,delta)",
        "delta = min(m,delta)", "m = max(m,delta)",
        "m = max(m,nu)", "m = max(m,tau)",
    ].iter().map(|s|s.to_string()).collect();
    for metric in ["alpha", "tau", "omega", "chi", "nu", "delta"] {
        catalog.push(format!("{metric} = min(n,{metric})"));
        catalog.push(format!("n = max(n,{metric})"));
    }
    catalog.iter().map(|s|identity_key(s).expect("static identity catalog"))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn symmetric_and_fail_closed() {
        assert_eq!(normalize_expression(" (tau+alpha) ").unwrap(), "(alpha+tau)");
        assert_eq!(normalize_expression("max(n,alpha)").unwrap(), "max(alpha,n)");
        assert_eq!(identity_key("n = (tau+alpha)").unwrap(),
                   identity_key("(alpha+tau) = n").unwrap());
        assert!(normalize_expression("min(a,b,c)").is_err());
        assert!(known_identity_keys().contains(&identity_key("n = (tau+alpha)").unwrap()));
    }
}
