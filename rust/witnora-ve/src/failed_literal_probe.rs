//! R-039: bounded failed-literal probing and assumption conflict detection.
//! This is established SAT inference, preserving SAT/UNSAT but not the
//! exact source model set. Not a new mathematical discovery.

use crate::{cnf::CanonicalCnf, simplifier};
use std::cmp::Reverse;
use std::collections::BTreeMap;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ProbeOutcome {
    pub clauses: Vec<Vec<i32>>,
    pub checked_variables: usize,
    pub forced_literals: Vec<i32>,
    pub both_assumptions_conflict: bool,
    pub source_hash: String,
    pub candidate_hash: String,
}

pub fn unit_conflict(source: &[Vec<i32>], assumed_literal: i32)
    -> Result<bool,String> {
    let formula=CanonicalCnf::from_signed(source)?;
    let mut assigned=BTreeMap::<u32,bool>::new();
    let mut pending=vec![assumed_literal];
    while let Some(lit)=pending.pop() {
        let var=lit.unsigned_abs();
        let value=lit>0;
        if let Some(&old)=assigned.get(&var) {
            if old!=value { return Ok(true); }
            continue;
        }
        assigned.insert(var,value);
        for clause in &formula.clauses {
            let mut undecided=Vec::new();
            let mut satisfied=false;
            for &item in clause {
                match assigned.get(&item.unsigned_abs()) {
                    None => undecided.push(item),
                    Some(&known) if known==(item>0) => {
                        satisfied=true;
                        break;
                    },
                    Some(_) => {},
                }
            }
            if satisfied { continue; }
            if undecided.is_empty() { return Ok(true); }
            if undecided.len()==1 { pending.push(undecided[0]); }
        }
    }
    Ok(false)
}

fn unit_propagation(source: &[Vec<i32>]) -> Result<CanonicalCnf,String> {
    let mut current=CanonicalCnf::from_signed(source)?;
    while let Some(next)=simplifier::unit_step(&current.clauses)? {
        current=CanonicalCnf::from_signed(&next.clauses)?;
        if current.has_empty_clause() {
            return CanonicalCnf::from_signed(&[vec![]]);
        }
    }
    Ok(current)
}

pub fn probe_forced_relations(source: &[Vec<i32>], max_probes: i32)
    -> Result<ProbeOutcome,String> {
    if !(0..=256).contains(&max_probes) {
        return Err("invalid bounded probing budget".into());
    }
    let original=CanonicalCnf::from_signed(source)?;
    let mut occ=original.variables().into_iter()
        .map(|v|(v,0usize)).collect::<BTreeMap<_,_>>();
    for clause in &original.clauses {
        for &lit in clause { *occ.get_mut(&lit.unsigned_abs()).unwrap()+=1; }
    }
    let mut pivots=original.variables();
    pivots.sort_by_key(|v|(Reverse(occ[v]),*v));
    let mut augmented=original.clone();
    let mut forced=Vec::new();
    let mut checked=0usize;
    let mut both=false;
    for pivot in pivots.into_iter().take(max_probes as usize) {
        let positive=unit_conflict(&augmented.clauses,pivot as i32)?;
        let negative=unit_conflict(&augmented.clauses,-(pivot as i32))?;
        checked+=1;
        if positive && negative {
            augmented=CanonicalCnf::from_signed(&[vec![]])?;
            both=true;
            break;
        }
        if positive!=negative {
            let forced_literal=if positive { -(pivot as i32) }
                else { pivot as i32 };
            forced.push(forced_literal);
            let mut raw=augmented.clauses.clone();
            raw.push(vec![forced_literal]);
            augmented=CanonicalCnf::from_signed(&raw)?;
        }
    }
    let simplified=unit_propagation(&augmented.clauses)?;
    Ok(ProbeOutcome{
        clauses:simplified.clauses,
        checked_variables:checked,
        forced_literals:forced,
        both_assumptions_conflict:both,
        source_hash:original.formula_hash(),
        candidate_hash:simplified.formula_hash(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn signed_assumption_and_double_failure() {
        let source=vec![vec![1],vec![-1]];
        assert!(unit_conflict(&source,1).unwrap());
        assert!(unit_conflict(&source,-1).unwrap());
        let result=probe_forced_relations(&source,1).unwrap();
        assert_eq!(result.clauses,vec![vec![]]);
        assert!(result.both_assumptions_conflict);
        assert_eq!(result.checked_variables,1);
    }
    #[test]
    fn bounds_and_zero_probes() {
        assert_eq!(probe_forced_relations(&[],257).unwrap_err(),
            "invalid bounded probing budget");
        assert_eq!(probe_forced_relations(&[vec![1]],0).unwrap()
                .clauses.len(),0);
    }
}
