//! R-142: deterministic bounded resolution proof generation for XOR-CNF support.
//! The emitted proof is only a *candidate*; RUP/drat-trim still verify it.
use std::collections::BTreeSet;
use std::time::Instant;

pub type Answer=(Option<String>,Option<String>,usize,usize,usize);

fn fail(reason:&str,emitted:usize,width:usize,bytes:usize)->Answer{
 (None,Some(reason.to_string()),emitted,width,bytes)
}

pub fn refute(original:&[Vec<i64>],support:&[Vec<i64>],order:&[usize],
 max_clauses:usize,max_bytes:usize,timeout_seconds:Option<f64>)->Answer{
 let active=original.iter().cloned().collect::<BTreeSet<_>>();
 let mut focus=support.iter().cloned().collect::<BTreeSet<_>>();
 if !focus.is_subset(&active){
  return fail("DETECTED_XOR_SOURCE_CLAUSE_MISSING_FROM_ORIGINAL",0,0,0);
 }
 if focus.contains(&Vec::<i64>::new()){
  return(Some("0\n".to_owned()),None,1,0,2);
 }
 let started=Instant::now();
 let expired=||timeout_seconds.is_some_and(|seconds|{
  started.elapsed().as_secs_f64()>seconds
 });
 let mut lines=Vec::<String>::new();let mut emitted=0usize;
 let mut bytes=0usize;let mut width=0usize;
 for &variable in order{
  if expired(){return fail("SKIPPED_TIME_CAP",emitted,width,bytes);}
  let Ok(pivot)=i64::try_from(variable) else{continue;};
  let positive=focus.iter().filter(|clause|clause.contains(&pivot))
      .cloned().collect::<Vec<_>>();
  let negative=focus.iter().filter(|clause|clause.contains(&-pivot))
      .cloned().collect::<Vec<_>>();
  if positive.is_empty() && negative.is_empty(){continue;}
  for left in &positive{
   for right in &negative{
    let Some(resolvent)=crate::xor_drat_resolution::resolve_fast(left,right,pivot)
    else{continue;};
    width=width.max(resolvent.len());
    if focus.contains(&resolvent){continue;}
    if emitted>=max_clauses{
     return fail("SKIPPED_PROOF_SIZE_CAP",emitted,width,bytes);
    }
    let Some(next_bytes)=bytes.checked_add(crate::xor_proof_emit::line_size(&resolvent))
    else{return fail("SKIPPED_PROOF_BYTES_CAP",emitted,width,bytes);};
    if next_bytes>max_bytes{
     return fail("SKIPPED_PROOF_BYTES_CAP",emitted,width,bytes);
    }
    lines.push(crate::xor_proof_emit::clause_line(&resolvent));
    emitted+=1;bytes=next_bytes;
    focus.insert(resolvent.clone());
    if resolvent.is_empty(){
     return(Some(lines.join("\n")+"\n"),None,emitted,width,bytes);
    }
    if expired(){return fail("SKIPPED_TIME_CAP",emitted,width,bytes);}
   }
  }
  for clause in positive.iter().chain(negative.iter()){
   focus.remove(clause);
  }
 }
 fail("VARIABLE_ELIMINATION_DID_NOT_DERIVE_EMPTY",emitted,width,bytes)
}

#[cfg(test)]mod tests{use super::*;
 #[test]fn contradictory_units(){
  assert_eq!(refute(&[vec![1],vec![-1]],&[vec![1],vec![-1]],&[1],20,40,None),
    (Some("0\n".into()),None,1,0,2));
  assert_eq!(refute(&[vec![1]],&[vec![1],vec![-1]],&[1],20,40,None).1,
    Some("DETECTED_XOR_SOURCE_CLAUSE_MISSING_FROM_ORIGINAL".into()));
 }
}
