//! R-067: exact hidden-separator CNF generator with Python-frozen label draw.
//! The sampled MT19937 labels are passed in; no Rust RNG equivalence claimed.
use crate::cnf::CanonicalCnf;
use std::collections::{BTreeMap,BTreeSet};

pub fn source_variables(width: i32,cross_noise: bool) -> Result<Vec<i32>,String> {
    if !matches!(width,2|3) {return Err("separator width must be 2 or 3".into());}
    let mut variables=BTreeSet::from([1,2,10,11,20,21,30,31]);
    for v in 3..3+width {variables.insert(v);}
    if cross_noise {variables.insert(32);}
    Ok(variables.into_iter().collect())
}

fn xor_clauses(vars: &[i32],rhs:u32,out:&mut Vec<Vec<i32>>) {
    let n=vars.len();
    for mask in 0u32..(1u32<<n) {
        if mask.count_ones()%2==rhs {continue;}
        let mut row=vars.iter().enumerate().map(|(i,&v)| {
            if (mask>>(n-1-i))&1==1 {-v} else {v}
        }).collect::<Vec<_>>();
        row.sort_unstable();
        out.push(row);
    }
}

pub fn generate(width:i32,cross_noise:bool,labels:&[i32])
    ->Result<Vec<Vec<i32>>,String> {
    let vars=source_variables(width,cross_noise)?;
    if labels.len()!=vars.len() || labels.iter().any(|&v|!(101..=400).contains(&v)) ||
        labels.iter().copied().collect::<BTreeSet<_>>().len()!=labels.len() {
        return Err("invalid frozen label permutation".into());
    }
    let mapping:BTreeMap<i32,i32>=vars.into_iter().zip(labels.iter().copied()).collect();
    let boundary=(3..3+width).collect::<Vec<_>>();
    let mut left=vec![1,2]; left.extend(&boundary);
    let mut right=boundary; right.extend([10,11]);
    let mut rows=Vec::new();
    xor_clauses(&left,0,&mut rows);
    xor_clauses(&right,1,&mut rows);
    rows.extend([vec![1,20,30],vec![-31,10,21]]);
    if cross_noise {rows.push(vec![20,21,32]);}
    for row in &mut rows {
        for lit in row.iter_mut() {
            let v=*mapping.get(&lit.abs()).ok_or("unmapped variable")?;
            *lit=if *lit>0 {v} else {-v};
        }
    }
    Ok(CanonicalCnf::from_signed(&rows)?.clauses)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn widths_and_rejection() {
        for width in [2,3] {
            for noise in [false,true] {
                let vars=source_variables(width,noise).unwrap();
                let labels=(101..101+vars.len() as i32).collect::<Vec<_>>();
                assert!(!generate(width,noise,&labels).unwrap().is_empty());
            }
        }
        assert!(generate(4,false,&[]).is_err());
    }
}
