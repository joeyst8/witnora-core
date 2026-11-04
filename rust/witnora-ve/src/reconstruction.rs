//! R-029: SAT witness reconstruction with exact Python failure semantics.
//! This is a witness producer, not a standalone UNSAT proof checker.

use crate::cnf::CanonicalCnf;
use std::collections::BTreeMap;

#[derive(Clone, Debug)]
pub struct ReconstructionStep {
    pub kind: String,
    pub assigned: Vec<i32>,
    pub bce_removed: Vec<i32>,
    pub bce_pivot: i32,
    pub bce_opposites: Vec<Vec<i32>>,
    pub ve_var: i32,
    pub ve_removed: Vec<Vec<i32>>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ReconstructionOutcome {
    pub ok: bool,
    pub assignment: BTreeMap<u32, bool>,
    pub error: Option<String>,
}

fn literal_satisfied(literal: i32, assignment: &BTreeMap<u32, bool>) -> bool {
    let value = *assignment.get(&literal.unsigned_abs()).unwrap_or(&false);
    if literal > 0 { value } else { !value }
}

fn clause_satisfied_default_false(
    clause: &[i32], assignment: &BTreeMap<u32, bool>,
) -> bool {
    clause.iter().any(|&lit| literal_satisfied(lit, assignment))
}

fn failure(assignment: &BTreeMap<u32, bool>, error: String) -> ReconstructionOutcome {
    ReconstructionOutcome { ok: false, assignment: assignment.clone(), error: Some(error) }
}

fn normalize_clause(raw: &[i32]) -> Result<Vec<i32>, String> {
    let cnf = CanonicalCnf::from_signed(&[raw.to_vec()])?;
    if cnf.clauses.len() != 1 {
        return Err("tautological reconstruction clause".into());
    }
    Ok(cnf.clauses[0].clone())
}

pub fn reconstruct(
    original: &[Vec<i32>],
    steps: &[ReconstructionStep],
    final_assignment: &[(u32, bool)],
) -> Result<ReconstructionOutcome, String> {
    let formula = CanonicalCnf::from_signed(original)?;
    let mut assignment = BTreeMap::new();
    for &(var, value) in final_assignment {
        if assignment.insert(var, value).is_some() {
            return Err("duplicate final assignment variable".into());
        }
    }
    for step in steps.iter().rev() {
        match step.kind.as_str() {
            "2SAT_SOLVE" | "TREEWIDTH_SOLVE" | "SUB" | "CD" => {}
            "UP" | "PLE" => {
                let Some(&lit) = step.assigned.first() else {
                    return Ok(failure(&assignment, format!("{} missing assigned literal", step.kind)));
                };
                if lit == 0 || lit == i32::MIN {
                    return Err("invalid reconstruction assigned literal".into());
                }
                let var = lit.unsigned_abs();
                let desired = lit > 0;
                if assignment.get(&var).is_some_and(|&old| old != desired) {
                    return Ok(failure(&assignment, format!("inconsistent assignment for variable {var}")));
                }
                assignment.insert(var, desired);
            }
            "BCE" => {
                let clause = normalize_clause(&step.bce_removed)?;
                let pivot = step.bce_pivot;
                if pivot == 0 || pivot == i32::MIN {
                    return Err("invalid BCE reconstruction pivot".into());
                }
                if !clause_satisfied_default_false(&clause, &assignment) {
                    assignment.insert(pivot.unsigned_abs(), pivot > 0);
                }
                if !clause_satisfied_default_false(&clause, &assignment) {
                    return Ok(failure(&assignment,
                        "BCE removed clause remains unsatisfied".into()));
                }
                for raw in &step.bce_opposites {
                    let other = normalize_clause(raw)?;
                    if !clause_satisfied_default_false(&other, &assignment) {
                        return Ok(failure(&assignment,
                            "BCE opposite clause was falsified".into()));
                    }
                }
            }
            "VE" => {
                let var = step.ve_var;
                if var <= 0 {
                    return Err("invalid VE reconstruction variable".into());
                }
                let mut desired: Option<bool> = None;
                let mut removed = Vec::new();
                for raw in &step.ve_removed {
                    let clause = normalize_clause(raw)?;
                    let pos = clause.contains(&var);
                    let neg = clause.contains(&-var);
                    if !pos && !neg {
                        return Ok(failure(&assignment, "VE log contains unrelated clause".into()));
                    }
                    let rest = clause.iter().copied().filter(|lit| lit.unsigned_abs() != var as u32)
                        .collect::<Vec<_>>();
                    if !clause_satisfied_default_false(&rest, &assignment) {
                        let needed = pos;
                        if desired.is_some_and(|old| old != needed) {
                            return Ok(failure(&assignment, "VE reconstruction sign conflict".into()));
                        }
                        desired = Some(needed);
                    }
                    removed.push(clause);
                }
                let key = var as u32;
                if let Some(value) = desired {
                    if assignment.get(&key).is_some_and(|&old| old != value) {
                        return Ok(failure(&assignment,
                            format!("VE assignment conflict for variable {var}")));
                    }
                    assignment.insert(key, value);
                } else {
                    assignment.entry(key).or_insert(false);
                }
                for clause in &removed {
                    if !clause_satisfied_default_false(clause, &assignment) {
                        return Ok(failure(&assignment,
                            "VE removed clause remains unsatisfied".into()));
                    }
                }
            }
            other => {
                return Ok(failure(&assignment,
                    format!("unsupported reconstruction step {other}")));
            }
        }
    }

    for variable in formula.variables() {
        assignment.entry(variable).or_insert(false);
    }
    if !formula.satisfied(&assignment) {
        return Ok(failure(&assignment,
            "reconstructed assignment does not satisfy original formula".into()));
    }
    Ok(ReconstructionOutcome { ok: true, assignment, error: None })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn up_ve_bce_and_failure_controls() {
        let step = ReconstructionStep {
            kind: "UP".into(), assigned: vec![1],
            bce_removed: vec![], bce_pivot: 0,
            bce_opposites: vec![], ve_var: 0, ve_removed: vec![],
        };
        let r = reconstruct(&[vec![1]], &[step.clone()], &[]).unwrap();
        assert!(r.ok);
        assert_eq!(r.assignment[&1], true);
        let fail = reconstruct(&[vec![-1]], &[step], &[]).unwrap();
        assert!(!fail.ok);
        assert_eq!(fail.error.as_deref(),
                   Some("reconstructed assignment does not satisfy original formula"));
        let ve = ReconstructionStep {
            kind: "VE".into(), assigned: vec![], bce_removed: vec![],
            bce_pivot: 0, bce_opposites: vec![], ve_var: 2,
            ve_removed: vec![vec![1, 2]],
        };
        let restored = reconstruct(&[vec![1, 2]], &[ve], &[(1, false)]).unwrap();
        assert!(restored.ok);
        assert_eq!(restored.assignment[&2], true);
        let bce = ReconstructionStep {
            kind: "BCE".into(), assigned: vec![], bce_removed: vec![1],
            bce_pivot: 1, bce_opposites: vec![], ve_var: 0,
            ve_removed: vec![],
        };
        assert!(reconstruct(&[vec![1]], &[bce], &[]).unwrap().ok);
    }
}
