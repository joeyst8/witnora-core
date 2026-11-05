//! R-133: deterministic sparse GF(2) elimination schedule with min-fill scoring.
//! The result is an algebraic row-operation trace, never a DRAT proof by itself.
use std::collections::{BTreeMap,BTreeSet};

type Row=(BTreeSet<usize>,u8);
type Op=(usize,usize,String,String,Option<String>,Vec<usize>,u8,usize);
type RowKey=(usize,Vec<usize>,u8,String);
type Score=(usize,usize,usize,usize,usize,usize,RowKey);
pub type ScheduleAnswer=(Vec<usize>,Vec<Op>,usize,usize,Option<usize>);

fn row_sort_key(id:&str,rows:&BTreeMap<String,Row>)->RowKey{
 let (vars,rhs)=&rows[id];
 (vars.len(),vars.iter().copied().collect(),*rhs,id.to_string())
}

fn row_key(row:&Row)->(Vec<usize>,u8){
 (row.0.iter().copied().collect(),row.1)
}

fn xor_rows(left:&Row,right:&Row)->Row{
 (left.0.symmetric_difference(&right.0).copied().collect(),left.1^right.1)
}

struct Candidate{
 score:Score,
 variable:usize,
 rows:BTreeMap<String,Row>,
 ops:Vec<Op>,
 peak:usize,
 next_index:usize,
}

pub fn schedule(equations:&[(Vec<usize>,u8)])->ScheduleAnswer{
 let mut active=BTreeMap::<String,Row>::new();
 for (index,(vars,rhs)) in equations.iter().enumerate(){
  let support=vars.iter().copied().collect::<BTreeSet<_>>();
  if !support.is_empty() || *rhs!=0{
   active.insert(format!("input_{index:04}"),(support,*rhs&1));
  }
 }
 let mut order=Vec::new();let mut operations=Vec::new();
 let initial_width=active.values().map(|r|r.0.len()).max().unwrap_or(0);
 let mut peak_width=initial_width;
 let mut contradiction_seen=active.values().any(|r|r.0.is_empty() && r.1==1);
 let mut final_width=if contradiction_seen{Some(0)}else{None};
 let mut next_row_index=0usize;
 while !active.is_empty() && !contradiction_seen{
  let variables=active.values().flat_map(|r|r.0.iter().copied())
      .collect::<BTreeSet<_>>();
  if variables.is_empty(){break;}
  let mut best:Option<Candidate>=None;
  for variable in variables{
   let mut containing=active.iter().filter(|(_,r)|r.0.contains(&variable))
       .map(|(id,_)|id.clone()).collect::<Vec<_>>();
   if containing.is_empty(){continue;}
   let mut not_containing=active.iter().filter(|(_,r)|!r.0.contains(&variable))
       .map(|(id,r)|(id.clone(),r.clone())).collect::<BTreeMap<_,_>>();
   containing.sort_by_key(|id|row_sort_key(id,&active));
   for pivot_id in &containing{
    let pivot=&active[pivot_id];
    let mut candidate_rows=not_containing.clone();
    let mut seen=candidate_rows.values().map(row_key).collect::<BTreeSet<_>>();
    let mut generated=Vec::<Op>::new();
    let mut local_peak=candidate_rows.values().map(|r|r.0.len()).max().unwrap_or(0);
    let mut local_contradiction=false;
    let mut local_next_index=next_row_index;
    let mut others=containing.iter().filter(|id|*id!=pivot_id)
        .cloned().collect::<Vec<_>>();
    others.sort_by_key(|id|row_sort_key(id,&active));
    for other_id in others{
     let merged=xor_rows(pivot,&active[&other_id]);
     let width=merged.0.len();local_peak=local_peak.max(width);
     let mut result_id=None;
     if width==0 && merged.1==1{
      local_contradiction=true;
      let name=format!("row_{local_next_index:04}");local_next_index+=1;
      candidate_rows.insert(name.clone(),(BTreeSet::new(),1));
      result_id=Some(name);
     }else if width>0 || merged.1!=0{
      let key=row_key(&merged);
      if seen.insert(key.clone()){
       let name=format!("row_{local_next_index:04}");local_next_index+=1;
       candidate_rows.insert(name.clone(),merged.clone());
       result_id=Some(name);
      }else{
       result_id=candidate_rows.iter().find(|(_,r)|row_key(r)==key)
           .map(|(id,_)|id.clone());
      }
     }
     generated.push((operations.len()+generated.len(),variable,pivot_id.clone(),
         other_id,result_id,merged.0.iter().copied().collect(),merged.1,width));
     if local_contradiction{break;}
    }
    let score=(if local_contradiction{0}else{1},local_peak,
      generated.iter().filter(|op|op.4.is_some()).count(),
      candidate_rows.values().map(|r|r.0.len()).sum(),
      containing.len(),variable,row_sort_key(pivot_id,&active));
    let candidate=Candidate{score,variable,rows:candidate_rows,
         ops:generated,peak:local_peak,next_index:local_next_index};
    if best.as_ref().is_none_or(|prior|candidate.score<prior.score){
     best=Some(candidate);
    }
   }
  }
  let Some(selected)=best else{break;};
  order.push(selected.variable);
  // Python's reference scans *all* recorded result IDs, including reused
  // input_#### IDs, when advancing the next generated row index.  Preserve
  // that historical certificate-label behavior for exact trace parity.
  let reused_index=selected.ops.iter().filter_map(|op|op.4.as_deref())
      .filter_map(|name|name.split_once('_').and_then(|(_,digits)|digits.parse::<usize>().ok()))
      .map(|index|index+1).max().unwrap_or(0);
  operations.extend(selected.ops);
  active=selected.rows;
  peak_width=peak_width.max(selected.peak);
  next_row_index=selected.next_index.max(reused_index);
  if active.values().any(|r|r.0.is_empty() && r.1==1){
   contradiction_seen=true;final_width=Some(0);
  }
 }
 let already=order.iter().copied().collect::<BTreeSet<_>>();
 let remaining=active.values().flat_map(|r|r.0.iter().copied())
     .filter(|v|!already.contains(v)).collect::<BTreeSet<_>>();
 order.extend(remaining);
 (order,operations,initial_width,peak_width,final_width)
}

#[cfg(test)]mod tests{use super::*;#[test]fn simple(){
 let result=schedule(&[(vec![1,2],1),(vec![2,3],0)]);
 assert!(!result.0.is_empty());
 assert_eq!(result.2,2);
 assert_eq!(schedule(&[(vec![],1)]).4,Some(0));
}}
