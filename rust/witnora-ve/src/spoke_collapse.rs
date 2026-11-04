//! R-071: exact generated parity-spoke CNF and source-bound classification.
//! This implements a restricted recognizer, not a general SAT solver.
use crate::cnf::CanonicalCnf;
use std::collections::BTreeSet;

pub type Spoke=(i32,i32,i32); // (middle, left parity, right parity)
pub type Verdict=(String,Vec<usize>,Vec<i32>,Vec<(i32,bool)>);

pub fn generate(spokes:&[Spoke])->Result<Vec<Vec<i32>>,String> {
    let mut mids=BTreeSet::new();
    let mut rows=Vec::new();
    for &(mid,left,right) in spokes {
        if mid<3 || !matches!(left,0|1) || !matches!(right,0|1) ||
            !mids.insert(mid) {
            return Err("invalid or repeated parity spoke".into());
        }
        for (rhs,first,second) in [(left,1,mid),(right,mid,2)] {
            for x in 0..=1 {
                for y in 0..=1 {
                    if (x^y)==rhs {continue;}
                    rows.push(vec![if x==1 {-first} else {first},
                                   if y==1 {-second} else {second}]);
                }
            }
        }
    }
    Ok(CanonicalCnf::from_signed(&rows)?.clauses)
}

pub fn classify(source:&[Vec<i32>],spokes:&[Spoke])->Verdict {
    let unsupported=||("UNSUPPORTED".into(),vec![],vec![],vec![]);
    if spokes.is_empty() {return unsupported();}
    let expected=match generate(spokes) {Ok(x)=>x,Err(_)=>return unsupported()};
    let given=match CanonicalCnf::from_signed(source) {
        Ok(x)=>x.clauses,Err(_)=>return unsupported(),
    };
    if given!=expected {return unsupported();}
    let signature=spokes[0].1^spokes[0].2;
    for (idx,&(_,left,right)) in spokes.iter().enumerate().skip(1) {
        let other=left^right;
        if signature!=other {
            return ("UNSAT_BY_SPOKE_SYNDROME".into(),vec![0,idx],
                    vec![signature,other],vec![]);
        }
    }
    let mut assignment=vec![(1,false),(2,signature!=0)];
    assignment.extend(spokes.iter().map(|&(mid,left,_)|(mid,left!=0)));
    ("SAT_WITH_WITNESS".into(),vec![],vec![],assignment)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn exact_spoke_controls() {
        let same=[(3,0,0),(4,1,1)];
        let f=generate(&same).unwrap();
        assert_eq!(f.len(),8);
        assert_eq!(classify(&f,&same).0,"SAT_WITH_WITNESS");
        let conflicting=[(3,0,0),(4,1,0)];
        let g=generate(&conflicting).unwrap();
        assert_eq!(classify(&g,&conflicting).1,vec![0,1]);
        assert_eq!(classify(&f,&conflicting).0,"UNSUPPORTED");
        assert_eq!(classify(&g,&[(3,0,0),(3,1,0)]).0,"UNSUPPORTED");
        assert!(generate(&[(2,0,1)]).is_err());
        assert!(generate(&[(3,2,0)]).is_err());
    }
}
