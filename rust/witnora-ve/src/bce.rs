//! R-018: deterministic blocked clause elimination proof witnesses.
//!
//! The native algorithm checks every resolvent for a complementary
//! literal pair. Python retains only presentation/digest formatting
//! during migration; no unsupported proof claim is emitted.

use crate::cnf::CanonicalCnf;
use std::collections::BTreeSet;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct BlockedClauseWitness {
    pub pivot: i32,
    /// (other source clause, sorted raw resolvent, tautological)
    pub checked: Vec<(Vec<i32>, Vec<i32>, bool)>,
}

fn is_tautological(literals: &[i32]) -> bool {
    let mut seen = BTreeSet::new();
    for &lit in literals {
        if seen.contains(&-lit) {
            return true;
        }
        seen.insert(lit);
    }
    false
}

fn checked_resolvents(
    formula: &[Vec<i32>],
    clause: &[i32],
    pivot: i32,
) -> Option<BlockedClauseWitness> {
    let mut checked = Vec::new();
    for other in formula {
        if other == clause || !other.contains(&-pivot) {
            continue;
        }
        let mut raw = clause.iter().filter(|&&lit| lit != pivot)
            .chain(other.iter().filter(|&&lit| lit != -pivot))
            .copied().collect::<Vec<_>>();
        raw.sort_unstable();
        let tautological = is_tautological(&raw);
        checked.push((other.clone(), raw, tautological));
        if !tautological {
            return None;
        }
    }
    Some(BlockedClauseWitness { pivot, checked })
}

pub fn blocked_clause_witness(
    source: &[Vec<i32>], target: &[i32], pivot: i32,
) -> Result<Option<BlockedClauseWitness>, String> {
    let formula = CanonicalCnf::from_signed(source)?;
    if pivot == 0 || pivot == i32::MIN {
        return Err("invalid BCE pivot".into());
    }
    let target_cnf = CanonicalCnf::from_signed(&[target.to_vec()])?;
    if target_cnf.clauses.len() != 1 {
        return Err("tautological BCE target clause".into());
    }
    Ok(checked_resolvents(&formula.clauses, &target_cnf.clauses[0], pivot))
}

pub fn first_blocked_clause(
    source: &[Vec<i32>],
) -> Result<Option<(Vec<i32>, BlockedClauseWitness)>, String> {
    let formula = CanonicalCnf::from_signed(source)?;
    let mut candidates = formula.clauses.clone();
    candidates.sort_by(|a,b| b.len().cmp(&a.len()).then_with(||a.cmp(b)));
    for clause in &candidates {
        let mut pivots = clause.clone();
        pivots.sort_by_key(|&lit| (lit.unsigned_abs(), if lit > 0 {0} else {1}));
        for pivot in pivots {
            if let Some(witness) = checked_resolvents(&formula.clauses, clause, pivot) {
                return Ok(Some((clause.clone(), witness)));
            }
        }
    }
    Ok(None)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn blocked_and_unblocked_source_controls() {
        let formula = vec![vec![1, 2], vec![-1, -2]];
        let got = blocked_clause_witness(&formula, &[1, 2], 1)
            .unwrap().unwrap();
        assert_eq!(got.checked.len(), 1);
        assert!(got.checked[0].2);
        let unblocked = blocked_clause_witness(
            &[vec![1, 2], vec![-1, 3]], &[1, 2], 1).unwrap();
        assert!(unblocked.is_none());
        assert!(first_blocked_clause(&[vec![1]]).unwrap().is_some());
    }

    #[test]
    fn validation_and_empty_clauses() {
        assert!(blocked_clause_witness(&[], &[1, -1], 1).is_err());
        assert!(blocked_clause_witness(&[], &[1], 0).is_err());
        assert!(first_blocked_clause(&[]).unwrap().is_none());
    }
}
