//! R-069: planted hard-separator source assembly with frozen Python RNG samples.
//! Synthetic instance construction is not a hardness proof.
use crate::cnf::CanonicalCnf;
use std::collections::BTreeSet;

fn xor_clauses(vars:&[i32],rhs:u32,rows:&mut Vec<Vec<i32>>) {
    let n=vars.len();
    for mask in 0u32..(1u32<<n) {
        if mask.count_ones()%2==rhs {continue;}
        let mut row=vars.iter().enumerate().map(|(i,&v)|
            if (mask>>(n-1-i))&1==1 {-v} else {v}).collect::<Vec<_>>();
        row.sort_unstable();
        rows.push(row);
    }
}

pub fn generate(blocks:i32,core_vars:i32,width:i32,
                samples:&[Vec<Vec<i32>>]) -> Result<Vec<Vec<i32>>,String> {
    if !matches!(blocks,2|4|8) || !matches!(core_vars,18|26) ||
        !matches!(width,2|3) {
        return Err("case outside preregistered stress grid".into());
    }
    if samples.len()!=blocks as usize {return Err("sample block count mismatch".into());}
    let target_samples=if core_vars==18 {76} else {109};
    let boundary=(1..=width).collect::<Vec<_>>();
    let mut rows=Vec::new();
    for (block,sampled) in samples.iter().enumerate() {
        if sampled.len()!=target_samples {return Err("sample count mismatch".into());}
        let start=100+(block as i32)*100;
        let mut vars=boundary.clone();
        vars.extend([start,start+1]);
        xor_clauses(&vars,((width+2)%2) as u32,&mut rows);
        for clause in sampled {
            let support:BTreeSet<i32>=clause.iter().map(|v|v.abs()).collect();
            if clause.len()!=3 || support.len()!=3 ||
                support.iter().any(|&v|v<start || v>=start+core_vars) ||
                !clause.iter().any(|&v|v>0) {
                return Err("invalid planted signed clause".into());
            }
            rows.push(clause.clone());
        }
    }
    Ok(CanonicalCnf::from_signed(&rows)?.clauses)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn grid_and_invalid_rows() {
        let rows=vec![
            vec![vec![100,101,102];76],
            vec![vec![200,201,202];76],
        ];
        assert!(!generate(2,18,2,&rows).unwrap().is_empty());
        assert!(generate(3,18,2,&rows).is_err());
        assert!(generate(2,18,2,&[]).is_err());
        let mut invalid=rows.clone();
        invalid[1][0]=vec![100,101,102];
        assert!(generate(2,18,2,&invalid).is_err());
    }
}
