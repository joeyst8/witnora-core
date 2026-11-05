//! R-076: source-bound conditional structural independence certificate.
//! Inconclusive means neither dependence nor UNSAT.
use crate::cnf::CanonicalCnf;
use crate::crc_structural_independence::audit;
use num_bigint::BigUint;
use num_traits::{One,Zero};
use std::collections::BTreeSet;

pub fn conditioned(source:&[Vec<i32>],boundary:&[i32],left:&[i32],right:&[i32],
    separator:&[i32],assignment_decimal:&str)
    ->Result<Option<(bool,String,usize,usize,usize)>,String> {
    let witness=BigUint::parse_bytes(assignment_decimal.as_bytes(),10)
        .ok_or("invalid full boundary assignment mask")?;
    let allowed=boundary.iter().copied().collect::<BTreeSet<_>>();
    let sep=separator.iter().copied().collect::<BTreeSet<_>>();
    if sep.len()!=separator.len() || !sep.is_subset(&allowed) {
        return Err("invalid separator variables".into());
    }
    if left.iter().any(|v|sep.contains(v)) || right.iter().any(|v|sep.contains(v)) {
        return Err("groups overlap separator".into());
    }
    let original=audit(source,boundary,left,right,assignment_decimal)?;
    if original.is_none() {return Ok(None);}
    let canonical=CanonicalCnf::from_signed(source)?;
    if canonical.clauses.iter().any(Vec::is_empty) {return Ok(None);}
    let mut condition=BigUint::zero();
    let mut sep_mask=BigUint::zero();
    for &v in separator {
        let bit=BigUint::one()<<((v-1) as usize);
        sep_mask|=&bit;
        if (&witness & &bit)!=BigUint::zero() {condition|=bit;}
    }
    let mut residual=Vec::new();
    for row in &canonical.clauses {
        let satisfied=row.iter().any(|&lit| {
            let v=lit.abs();
            if !sep.contains(&v) {return false;}
            let bit=BigUint::one()<<((v-1) as usize);
            ((&condition & bit)!=BigUint::zero())==(lit>0)
        });
        if satisfied {continue;}
        let remaining=row.iter().copied().filter(|lit|!sep.contains(&lit.abs()))
            .collect::<Vec<_>>();
        if remaining.is_empty() {return Ok(None);}
        residual.push(remaining);
    }
    let vars=boundary.iter().copied().filter(|v|!sep.contains(v)).collect::<Vec<_>>();
    let full_condition=&witness & (&sep_mask);
    let remaining_witness=&witness ^ &full_condition;
    let sub=audit(&residual,&vars,left,right,&remaining_witness.to_string())?;
    Ok(sub.map(|(separated,components,_)|
        (separated,condition.to_string(),components,canonical.clauses.len(),residual.len())))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn conditioned_separates_a_bridge() {
        let source=vec![vec![1,2],vec![-2,3]];
        let got=conditioned(&source,&[1,2,3],&[1],&[3],&[2],"7").unwrap().unwrap();
        assert!(got.0);
        assert_eq!(got.1,"2");
        assert_eq!(got.3,2);
    }
}
