//! R-073: benchmark and theorem-example CNF source generators.
use crate::cnf::CanonicalCnf;

fn canonical(rows:Vec<Vec<i32>>)->Result<Vec<Vec<i32>>,String> {
    Ok(CanonicalCnf::from_signed(&rows)?.clauses)
}

fn clique_rows(n:i32,offset:i32)->Result<Vec<Vec<i32>>,String> {
    if n<1 || n>100_000 || offset<0 || (n as i64)+(offset as i64)+1>i32::MAX as i64 {
        return Err("invalid blocked clique dimensions".into());
    }
    let mut out=vec![(1..=n+1).map(|v|v+offset).collect::<Vec<_>>()];
    for i in 1..=n {out.push(vec![-1-offset,-(i+1+offset)]);}
    Ok(out)
}

fn chain_rows(n:i32)->Result<Vec<Vec<i32>>,String> {
    if !(5..=100_000).contains(&n) {return Err("n must be at least 5".into());}
    let mut rows=vec![vec![-3,-1],vec![-4,-3,2],vec![-5,-4],
        vec![2,3],vec![-2,5],vec![1,4]];
    for v in 6..=n {rows.push(vec![-(v-1),v]);rows.push(vec![v-1,-v]);}
    Ok(rows)
}

fn offset_rows(rows:&[Vec<i32>],offset:i32,out:&mut Vec<Vec<i32>>) {
    out.extend(rows.iter().map(|clause|clause.iter().map(|&lit|
        if lit>0 {lit+offset} else {lit-offset}).collect()));
}

/// Options: clique, chain, bce, mixed, conflict, tautology.
pub fn generate(kind:&str,n:i32,count:i32)->Result<Vec<Vec<i32>>,String> {
    let mut rows=Vec::new();
    match kind {
        "clique" => rows=clique_rows(n,0)?,
        "chain" => rows=chain_rows(n)?,
        "bce" => {
            if count<1 || (n as i64+1)*(count as i64)>i32::MAX as i64 {
                return Err("invalid BCE component count".into());
            }
            for k in 0..count {rows.extend(clique_rows(n,k*(n+1))?);}
        }
        "mixed" => {
            let width=n.max(3);
            rows.extend(clique_rows(width,0)?);
            let fixed=vec![vec![1,2],vec![-1,2],vec![1,-2]];
            offset_rows(&fixed,width+1,&mut rows);
            offset_rows(&chain_rows(5)?,width+3,&mut rows);
        }
        "conflict" => rows=vec![vec![1],vec![-1]],
        "tautology" => {
            if n<1 {return Err("n must be at least 1".into());}
            for v in 1..=n {rows.push(vec![v,-v,(v%n)+1]);}
            rows.push(vec![1]);
        }
        _=>return Err("unknown benchmark family".into()),
    }
    canonical(rows)
}

pub fn canonical_samples(rows:&[Vec<i32>])->Result<Vec<Vec<i32>>,String> {
    canonical(rows.to_vec())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn deterministic_family_edges() {
        assert_eq!(generate("clique",3,0).unwrap().len(),4);
        assert_eq!(generate("chain",5,0).unwrap().len(),6);
        assert_eq!(generate("bce",2,3).unwrap().len(),9);
        assert_eq!(generate("conflict",0,0).unwrap().len(),2);
        assert_eq!(generate("tautology",3,0).unwrap(),vec![vec![1]]);
        assert!(generate("clique",0,0).is_err());
    }
}
