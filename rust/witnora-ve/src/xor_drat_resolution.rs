//! R-132: exact signed-clause resolvent helper for XOR-to-DRAT export.
use std::collections::BTreeSet;

pub fn resolve_fast(a:&[i64],b:&[i64],pivot:i64)->Option<Vec<i64>>{
 let negative_pivot=pivot.checked_neg()?;
 let mut literals=a.iter().copied().collect::<BTreeSet<_>>();
 literals.remove(&pivot);
 for &lit in b{
  if lit==negative_pivot{continue;}
  if literals.contains(&lit.checked_neg()?){return None;}
  literals.insert(lit);
 }
 for &lit in &literals{
  if literals.contains(&lit.checked_neg()?){return None;}
 }
 Some(literals.into_iter().collect())
}

#[cfg(test)]mod tests{use super::*;#[test]fn resolvent(){
 assert_eq!(resolve_fast(&[1,2],&[-1,3],1),Some(vec![2,3]));
 assert_eq!(resolve_fast(&[1,2],&[-1,-2],1),None);
}}
