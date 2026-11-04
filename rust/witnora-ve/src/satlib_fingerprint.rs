//! R-070: deterministic structural metrics, without any novelty or proof claim.
use crate::cnf::CanonicalCnf;
use std::collections::{BTreeMap, BTreeSet};

/// (variables, clauses, max width, unit, binary, ternary, primal components,
/// maximum variable occurrences, mixed-polarity variable count).
pub fn structural_metrics(source: &[Vec<i32>])
    -> Result<(usize,usize,usize,usize,usize,usize,usize,usize,usize),String> {
    let cnf=CanonicalCnf::from_signed(source)?;
    let mut occurrences=BTreeMap::<u32,(usize,bool,bool)>::new();
    let mut adjacency=BTreeMap::<u32,BTreeSet<u32>>::new();
    let (mut max_width,mut unit,mut binary,mut ternary)=(0,0,0,0);
    for row in &cnf.clauses {
        max_width=max_width.max(row.len());
        match row.len() {1=>unit+=1,2=>binary+=1,3=>ternary+=1,_=>()}
        let vars=row.iter().map(|x|x.unsigned_abs()).collect::<Vec<_>>();
        for &lit in row {
            let entry=occurrences.entry(lit.unsigned_abs()).or_default();
            entry.0+=1;
            if lit>0 {entry.1=true;} else {entry.2=true;}
        }
        for &v in &vars {
            let neighbors=adjacency.entry(v).or_default();
            neighbors.extend(vars.iter().copied().filter(|&other|other!=v));
        }
    }
    let mixed=occurrences.values().filter(|(_,pos,neg)|*pos&&*neg).count();
    let max_occ=occurrences.values().map(|x|x.0).max().unwrap_or(0);
    let mut remaining=adjacency.keys().copied().collect::<BTreeSet<_>>();
    let mut components=0;
    while let Some(start)=remaining.pop_first() {
        components+=1;
        let mut stack=vec![start];
        while let Some(v)=stack.pop() {
            for &neighbor in &adjacency[&v] {
                if remaining.remove(&neighbor) {stack.push(neighbor);}
            }
        }
    }
    Ok((occurrences.len(),cnf.clauses.len(),max_width,unit,binary,ternary,
        components,max_occ,mixed))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn empty_disconnected_and_mixed() {
        assert_eq!(structural_metrics(&[]).unwrap(),(0,0,0,0,0,0,0,0,0));
        assert_eq!(structural_metrics(&[vec![1,2],vec![-1],vec![4,5]]).unwrap(),
            (4,3,2,1,2,0,2,2,1));
        assert_eq!(structural_metrics(&[vec![],vec![1]]).unwrap(),
            (1,2,1,1,0,0,1,1,0));
    }
}
