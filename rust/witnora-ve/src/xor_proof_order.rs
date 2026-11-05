//! R-135/R-136: preserve the Gaussian trace's pivot order and width metadata.
//! Metadata does not establish propositional proof validity; the DRAT gate does.
use std::collections::BTreeSet;

pub fn proof_order(pivots:&[usize],variables:&[usize])->Vec<usize>{
 let present=pivots.iter().copied().collect::<BTreeSet<_>>();
 let mut out=pivots.to_vec();
 out.extend(variables.iter().copied().filter(|v|!present.contains(v)));
 out
}

pub fn gaussian_stats(pivots:&[usize],variables:&[usize],
 trace_widths:&[usize],detected_widths:&[usize],unsat:bool)
 ->(Vec<usize>,usize,usize,Option<usize>){
 let initial=detected_widths.iter().copied().max().unwrap_or(0);
 let peak=initial.max(trace_widths.iter().copied().max().unwrap_or(0));
 (proof_order(pivots,variables),initial,peak,if unsat{Some(0)}else{None})
}

#[cfg(test)]mod tests{use super::*;
 #[test]fn preserve_duplicates_and_order(){
  assert_eq!(proof_order(&[3,1,3],&[1,2,3,4]),vec![3,1,3,2,4]);
  assert_eq!(gaussian_stats(&[2],&[1,2],&[1,5],&[3,4],true),
     (vec![2,1],4,5,Some(0)));
 }
}
