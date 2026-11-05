//! R-139–R-141: exact DRAT clause formatting and bounded emission accounting.
//! No clause is accepted as a proof unless the separate RUP/DRAT verifier checks it.

pub fn clause_line(clause:&[i64])->String{
 if clause.is_empty(){return "0".to_owned();}
 let mut text=clause.iter().map(i64::to_string).collect::<Vec<_>>().join(" ");
 text.push_str(" 0");text
}

pub fn line_size(clause:&[i64])->usize{clause_line(clause).len()+1}

pub type EmitDecision=(usize,usize,usize,Option<String>,bool);
pub fn emit(clause:&[i64],already_active:bool,emitted:usize,bytes:usize,
 max_width:usize,max_clauses:usize,max_bytes:usize)->EmitDecision{
 let width=max_width.max(clause.len());
 if already_active{return(emitted,bytes,width,None,false);}
 if emitted>=max_clauses{
  return(emitted,bytes,width,Some("SKIPPED_PROOF_SIZE_CAP".into()),false);
 }
 let Some(next_bytes)=bytes.checked_add(line_size(clause)) else{
  return(emitted,bytes,width,Some("SKIPPED_PROOF_BYTES_CAP".into()),false);
 };
 if next_bytes>max_bytes{
  return(emitted,bytes,width,Some("SKIPPED_PROOF_BYTES_CAP".into()),false);
 }
 (emitted+1,next_bytes,width,None,true)
}

#[cfg(test)]mod tests{use super::*;
 #[test]fn exact_line_and_accounting(){
  assert_eq!(clause_line(&[]),"0");assert_eq!(line_size(&[]),2);
  assert_eq!(clause_line(&[-100,2]),"-100 2 0");
  assert_eq!(line_size(&[-100,2]),9);
  assert_eq!(emit(&[],false,0,0,0,1,2),(1,2,0,None,true));
  assert_eq!(emit(&[],false,1,2,0,1,20),
    (1,2,0,Some("SKIPPED_PROOF_SIZE_CAP".into()),false));
  assert_eq!(emit(&[],false,0,0,0,1,1),
    (0,0,0,Some("SKIPPED_PROOF_BYTES_CAP".into()),false));
 }
}
