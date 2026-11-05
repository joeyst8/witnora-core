//! R-075: exact source-bound sufficient independence check, never SAT search.
use num_bigint::BigUint;
use num_traits::{One,Zero};
use std::collections::{BTreeMap,BTreeSet};

fn root(parent:&mut BTreeMap<i32,i32>,mut v:i32)->i32 {
    while parent[&v]!=v {
        let p=parent[&v];
        let g=parent[&p];
        parent.insert(v,g);
        v=g;
    }
    v
}

pub fn audit(source:&[Vec<i32>],boundary:&[i32],left:&[i32],right:&[i32],
    assignment_decimal:&str)->Result<Option<(bool,usize,usize)>,String> {
    let witness=BigUint::parse_bytes(assignment_decimal.as_bytes(),10)
        .ok_or("invalid Boolean assignment mask")?;
    let mut allowed=BTreeSet::new();
    let mut boundary_mask=BigUint::zero();
    for &v in boundary {
        if !(1..=256).contains(&v) || !allowed.insert(v) {
            return Err("invalid or duplicate boundary variable".into());
        }
        boundary_mask|=BigUint::one()<<((v-1) as usize);
    }
    if (&witness & &boundary_mask)!=witness {
        return Err("witness sets non-boundary variable".into());
    }
    let mut groups=BTreeSet::new();
    for group in [left,right] {
        if group.is_empty() {return Err("empty independence group".into());}
        let mut seen=BTreeSet::new();
        for &v in group {
            if !allowed.contains(&v) || !seen.insert(v) || !groups.insert(v) {
                return Err("overlapping, repeated or nonboundary independence group".into());
            }
        }
    }
    let mut normalized=BTreeSet::<(BigUint,BigUint)>::new();
    for row in source {
        let (mut zeros,mut ones)=(BigUint::zero(),BigUint::zero());
        let mut tautology=false;
        for &lit in row {
            if lit==0 || lit==i32::MIN || !allowed.contains(&(lit.abs())) {
                return Err("invalid signed or nonboundary literal".into());
            }
            let bit=BigUint::one()<<((lit.abs()-1) as usize);
            if lit>0 {
                if (&ones & &bit)!=BigUint::zero() {tautology=true;}
                zeros|=bit;
            } else {
                if (&zeros & &bit)!=BigUint::zero() {tautology=true;}
                ones|=bit;
            }
        }
        if tautology {continue;}
        if (&zeros | &ones)==BigUint::zero() {return Ok(None);}
        normalized.insert((zeros,ones));
    }
    let mut parent=boundary.iter().copied().map(|v|(v,v)).collect::<BTreeMap<_,_>>();
    for (zeros,ones) in &normalized {
        if (&witness & zeros)==BigUint::zero() && (&witness & ones)==*ones {
            return Ok(None);
        }
        let scope=zeros|ones;
        let vertices=boundary.iter().copied().filter(|&v|
            (&scope & (BigUint::one()<<((v-1) as usize)))!=BigUint::zero())
            .collect::<Vec<_>>();
        if let Some(&first)=vertices.first() {
            for &v in vertices.iter().skip(1) {
                let a=root(&mut parent,first);
                let b=root(&mut parent,v);
                if a!=b {parent.insert(b,a);}
            }
        }
    }
    let left_roots=left.iter().map(|&v|root(&mut parent,v)).collect::<BTreeSet<_>>();
    let right_roots=right.iter().map(|&v|root(&mut parent,v)).collect::<BTreeSet<_>>();
    let separated=left_roots.is_disjoint(&right_roots);
    let component_count=boundary.iter().map(|&v|root(&mut parent,v))
        .collect::<BTreeSet<_>>().len();
    Ok(Some((separated,component_count,normalized.len())))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn sufficient_not_necessary_and_invalid_witness() {
        assert_eq!(audit(&[vec![1,2],vec![3,4]],&[1,2,3,4],&[1,2],&[3,4],"15").unwrap(),
            Some((true,2,2)));
        assert_eq!(audit(&[vec![1],vec![2],vec![1,2]],&[1,2],&[1],&[2],"3").unwrap(),
            Some((false,1,3)));
        assert!(audit(&[vec![1]],&[1,2],&[1],&[2],"0").unwrap().is_none());
        assert!(audit(&[],&[1,1],&[1],&[2],"0").is_err());
    }
}
