//! R-077: explicit finite auxiliary violation tensor bridge and local scopes.
//! Exponential oracle strictly bounded; no general contraction algorithm.
use crate::eth_clause_violation_parity::{violation_mask,parity_accepts};
use num_bigint::BigUint;
use num_traits::Zero;
use std::collections::BTreeSet;

pub fn local_scopes(source:&[Vec<i32>],nvars:usize,rows:&[Vec<usize>])
    ->Result<Vec<Vec<usize>>,String> {
    let mut out=Vec::new();
    for (j,clause) in source.iter().enumerate() {
        let mut scope=clause.iter().map(|lit|lit.unsigned_abs() as usize)
            .collect::<BTreeSet<_>>();
        scope.insert(nvars+j+1);
        out.push(scope.into_iter().collect());
    }
    for row in rows {
        if row.iter().any(|&j|j>=source.len()) {return Err("invalid parity row".into());}
        out.push(row.iter().map(|&j|nvars+j+1).collect::<BTreeSet<_>>()
            .into_iter().collect());
    }
    Ok(out)
}

pub fn direct_scopes(source:&[Vec<i32>],rows:&[Vec<usize>])
    ->Result<Vec<Vec<usize>>,String> {
    let mut out=Vec::new();
    for row in rows {
        let mut scope=BTreeSet::new();
        for &j in row {
            let clause=source.get(j).ok_or("invalid parity row")?;
            scope.extend(clause.iter().map(|lit|lit.unsigned_abs() as usize));
        }
        out.push(scope.into_iter().collect());
    }
    Ok(out)
}

pub fn exact_source_models(source:&[Vec<i32>],nvars:usize,max_variables:usize)
    ->Result<u64,String> {
    if nvars>max_variables || nvars>14 {return Err("exhaustive model oracle restricted".into());}
    let mut count=0;
    for x in 0..(1usize<<nvars) {
        if violation_mask(source,&BigUint::from(x))?.is_zero() {count+=1;}
    }
    Ok(count)
}

pub fn weight_profile(source:&[Vec<i32>],nvars:usize,rows:&[Vec<usize>],
    max_variables:usize)->Result<Vec<u64>,String> {
    if nvars>max_variables || nvars>14 {return Err("exhaustive auxiliary bridge restricted".into());}
    if rows.iter().flatten().any(|&j|j>=source.len()) {return Err("invalid sparse row".into());}
    let mut coefficients=vec![0u64;source.len()+1];
    for x in 0..(1usize<<nvars) {
        let violations=violation_mask(source,&BigUint::from(x))?;
        if parity_accepts(&violations,rows) {
            let weight=violations.iter_u32_digits().map(|d|d.count_ones() as usize).sum::<usize>();
            coefficients[weight]+=1;
        }
    }
    Ok(coefficients)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn zero_coefficient_and_locality() {
        let source=vec![vec![1],vec![2]];
        let rows=vec![vec![0,1]];
        assert_eq!(exact_source_models(&source,2,14).unwrap(),1);
        assert_eq!(weight_profile(&source,2,&rows,14).unwrap(),vec![1,0,1]);
        assert_eq!(local_scopes(&source,2,&rows).unwrap(),
            vec![vec![1,3],vec![2,4],vec![3,4]]);
        assert_eq!(direct_scopes(&source,&rows).unwrap(),vec![vec![1,2]]);
    }
}
