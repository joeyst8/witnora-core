//! R-019: native deterministic UP and pure-literal simplifier steps.
//!
//! Returns source-preserving proof event data; Python/Lean certificate
//! loggers remain separate until their ports are verified.

use crate::cnf::CanonicalCnf;
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct UnitStep {
    pub clauses: Vec<Vec<i32>>,
    pub literal: i32,
    pub satisfied: Vec<Vec<i32>>,
    pub shortened: Vec<(Vec<i32>, Vec<i32>)>,
    pub conflict: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PureStep {
    pub clauses: Vec<Vec<i32>>,
    pub literal: i32,
    pub removed: Vec<Vec<i32>>,
}

pub fn unit_step(source: &[Vec<i32>]) -> Result<Option<UnitStep>, String> {
    let formula = CanonicalCnf::from_signed(source)?;
    let Some(literal) = formula.clauses.iter()
        .find(|c| c.len() == 1)
        .map(|c| c[0]) else { return Ok(None); };
    let mut kept = Vec::new();
    let mut satisfied = Vec::new();
    let mut shortened = Vec::new();
    for clause in &formula.clauses {
        if clause.contains(&literal) {
            satisfied.push(clause.clone());
        } else if clause.contains(&-literal) {
            let next = clause.iter().copied()
                .filter(|&v| v != -literal).collect::<Vec<_>>();
            shortened.push((clause.clone(), next.clone()));
            kept.push(next);
        } else {
            kept.push(clause.clone());
        }
    }
    let output = CanonicalCnf::from_signed(&kept)?;
    Ok(Some(UnitStep {
        conflict: output.has_empty_clause(), clauses: output.clauses,
        literal, satisfied, shortened,
    }))
}

pub fn pure_step(source: &[Vec<i32>]) -> Result<Option<PureStep>, String> {
    let formula = CanonicalCnf::from_signed(source)?;
    let mut signs: BTreeMap<u32, BTreeSet<i32>> = BTreeMap::new();
    for clause in &formula.clauses {
        for &lit in clause {
            signs.entry(lit.unsigned_abs()).or_default()
                 .insert(if lit > 0 { 1 } else { -1 });
        }
    }
    let mut pure = Vec::new();
    for (var, signs) in signs {
        if signs.len() == 1 {
            pure.push(if signs.contains(&1) { var as i32 } else { -(var as i32) });
        }
    }
    pure.sort_by_key(|&lit| (lit.unsigned_abs(), if lit > 0 {0} else {1}));
    let Some(literal) = pure.first().copied() else { return Ok(None); };
    let mut kept = Vec::new();
    let mut removed = Vec::new();
    for clause in &formula.clauses {
        if clause.contains(&literal) {
            removed.push(clause.clone());
        } else {
            kept.push(clause.clone());
        }
    }
    Ok(Some(PureStep {
        clauses: CanonicalCnf::from_signed(&kept)?.clauses,
        literal, removed,
    }))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn unit_step_conflict_and_source_events() {
        let got = unit_step(&[vec![1],vec![-1,2],vec![3]]).unwrap().unwrap();
        assert_eq!(got.literal, 1);
        assert_eq!(got.satisfied, vec![vec![1]]);
        assert_eq!(got.shortened, vec![(vec![-1,2],vec![2])]);
        assert_eq!(got.clauses, vec![vec![2],vec![3]]);
        let conflict = unit_step(&[vec![1],vec![-1]]).unwrap().unwrap();
        assert!(conflict.conflict);
        assert_eq!(conflict.clauses, vec![Vec::<i32>::new()]);
        assert!(unit_step(&[vec![1,2]]).unwrap().is_none());
    }

    #[test]
    fn deterministic_pure_literal_order() {
        let got = pure_step(&[vec![1,2],vec![3],vec![-2,4]]).unwrap().unwrap();
        assert_eq!(got.literal, 1);
        assert_eq!(got.removed, vec![vec![1,2]]);
    }
}
