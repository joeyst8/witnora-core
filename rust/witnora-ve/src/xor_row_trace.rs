//! R-151/R-152: bounded full XOR row-trace proof candidate assembly.
//! This is not a proof verifier; independent DRAT/RUP gates retain authority.
use std::collections::{BTreeMap, BTreeSet};
use std::time::Instant;

pub type TraceOperation = (String, String, Option<String>, Vec<usize>, u8);
pub type Answer = (Option<String>, Option<String>, usize, usize, usize);

fn fail(reason: &str, count: usize, width: usize, bytes: usize) -> Answer {
    (None, Some(reason.to_string()), count, width, bytes)
}

#[allow(clippy::too_many_arguments)]
pub fn refute(
    original: &[Vec<i64>],
    source: &[(Vec<usize>, u8, Vec<Vec<i64>>)],
    trace: &[TraceOperation],
    max_clauses: usize, max_bytes: usize, timeout_seconds: Option<f64>,
) -> Answer {
    let mut active = original.iter().cloned().collect::<BTreeSet<_>>();
    let rows = crate::xor_row_sources::source_rows(source);
    let support = crate::xor_row_sources::source_union(
        &source.iter().map(|(_,_,clauses)| clauses.clone()).collect::<Vec<_>>());
    if !support.iter().all(|c| active.contains(c)) {
        return fail("DETECTED_XOR_SOURCE_CLAUSE_MISSING_FROM_ORIGINAL",0,0,0);
    }
    let mut values = BTreeMap::<String,(Vec<usize>,u8)>::new();
    let mut encodings = BTreeMap::<String,Vec<Vec<i64>>>::new();
    for (name, clauses, variables, rhs) in rows {
        values.insert(name.clone(), (variables,rhs));
        encodings.insert(name,clauses);
    }
    let started = Instant::now();
    let expired = || timeout_seconds.is_some_and(|t| started.elapsed().as_secs_f64()>t);
    let mut lines = Vec::<String>::new();
    let mut count = 0;
    let mut width = 0;
    let mut bytes = 0;
    for (left_id,right_id,result_id,result_variables,result_rhs) in trace {
        if expired() { return fail("SKIPPED_TIME_CAP",count,width,bytes); }
        let all = values.iter().map(|(id,(vars,rhs))| (id.clone(),vars.clone(),*rhs))
            .collect::<Vec<_>>();
        if let Some(reason) = crate::xor_row_validation::validate(
            &all,left_id,right_id,result_variables,*result_rhs) {
            return fail(&reason,count,width,bytes);
        }
        let target_vars = result_variables.iter().copied().collect::<BTreeSet<_>>();
        if result_id.is_none() && target_vars.is_empty() && result_rhs&1==0 {
            continue;
        }
        let Some(left_value)=values.get(left_id) else{unreachable!()};
        let Some(right_value)=values.get(right_id) else{unreachable!()};
        let Ok(expected) = crate::xor_equations::canonical_xor_cnf(
            &target_vars.iter().copied().collect::<Vec<_>>(),*result_rhs,16)
        else { return fail("ROW_OPERATION_ENCODING_DERIVATION_FAILED",count,width,bytes); };
        let Some(left_encoding)=encodings.get(left_id) else{unreachable!()};
        let Some(right_encoding)=encodings.get(right_id) else{unreachable!()};
        let active_clauses=active.iter().cloned().collect::<Vec<_>>();
        let (new_count,new_bytes,new_width,error,added_lines,added_clauses) =
            crate::xor_row_derivation::derive(left_encoding,right_encoding,
                &left_value.0,&right_value.0,&expected,&active_clauses,
                count,bytes,width,max_clauses,max_bytes,timeout_seconds,
                started.elapsed().as_secs_f64());
        count=new_count;bytes=new_bytes;width=new_width;
        if let Some(reason)=error { return fail(&reason,count,width,bytes); }
        lines.extend(added_lines);
        active.extend(added_clauses);
        let Some(id)=result_id else {
            return fail("ROW_OPERATION_RESULT_ID_MISSING",count,width,bytes);
        };
        values.insert(id.clone(),(target_vars.iter().copied().collect(),result_rhs&1));
        encodings.insert(id.clone(),expected);
        if target_vars.is_empty() && result_rhs&1==1 {
            return (Some(lines.join("\n")+"\n"),None,count,width,bytes);
        }
    }
    fail("ROW_OPERATION_TRACE_DID_NOT_DERIVE_EMPTY",count,width,bytes)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn contradictory_source_rows() {
        let source=vec![
            (vec![1],0,vec![vec![-1]]),
            (vec![1],1,vec![vec![1]])];
        let trace=vec![("input_0000".to_string(),"input_0001".to_string(),
            Some("result_0".to_string()),vec![],1)];
        let out=refute(&[vec![-1],vec![1]],&source,&trace,10,100,None);
        assert_eq!(out,(Some("0\n".to_string()),None,1,0,2));
    }
}
