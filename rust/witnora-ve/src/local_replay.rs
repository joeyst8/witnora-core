//! R-030: independently replay deterministic, non-component CNF proof steps.
//! Scope: UP, PLE, SUB, BCE and VE only. No SAT/UNSAT status claim is made.

use crate::{bce, cnf::CanonicalCnf, simplifier, ve_proof};

#[derive(Clone, Debug)]
pub struct LocalReplayStep {
    pub kind: String,
    pub step_id: usize,
    pub input_hash: String,
    pub output_hash: String,
    pub assigned: Vec<i32>,
    pub removed: Vec<Vec<i32>>,
    pub added: Vec<Vec<i32>>,
    pub subsuming: Vec<i32>,
    pub blocked_literal: i32,
    pub proof_digest: String,
    pub ve_var: i32,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LocalReplayResult {
    pub verified: bool,
    pub final_clauses: Vec<Vec<i32>>,
    pub error: Option<String>,
}

fn equivalent(mut a: Vec<Vec<i32>>, mut b: Vec<Vec<i32>>) -> bool {
    a.sort();
    b.sort();
    a == b
}

fn failure(current: &CanonicalCnf, message: String) -> LocalReplayResult {
    LocalReplayResult {
        verified: false, final_clauses: current.clauses.clone(),
        error: Some(message),
    }
}

pub fn replay(
    source: &[Vec<i32>], steps: &[LocalReplayStep],
    width_cap: i32, expected_final_hash: &str,
) -> Result<LocalReplayResult, String> {
    let mut current = CanonicalCnf::from_signed(source)?;
    for (position, step) in steps.iter().enumerate() {
        if step.step_id != position + 1 {
            return Ok(failure(&current,
                format!("step id mismatch at {}", step.step_id)));
        }
        if step.input_hash != current.formula_hash() {
            return Ok(failure(&current,
                format!("{} input hash mismatch at step {}", step.kind, step.step_id)));
        }
        let check: Result<CanonicalCnf, String> = match step.kind.as_str() {
            "UP" => match simplifier::unit_step(&current.clauses)? {
                None => Err("UP step has no unit clause".into()),
                Some(up) => {
                    let removed = up.satisfied.iter().cloned().chain(
                        up.shortened.iter().map(|pair| pair.0.clone())).collect();
                    let added = up.shortened.iter().map(|pair| pair.1.clone()).collect();
                    if step.assigned != vec![up.literal] {
                        Err("UP assigned literal mismatch".into())
                    } else if !equivalent(step.removed.clone(), removed)
                        || !equivalent(step.added.clone(), added) {
                        Err("UP removed/added clauses mismatch".into())
                    } else {
                        let next = CanonicalCnf { clauses: up.clauses };
                        if step.output_hash != next.formula_hash() {
                            Err("UP output hash mismatch".into())
                        } else { Ok(next) }
                    }
                }
            },
            "PLE" => match simplifier::pure_step(&current.clauses)? {
                None => Err("PLE step has no pure literal".into()),
                Some(ple) => {
                    if step.assigned != vec![ple.literal] {
                        Err("PLE assigned literal mismatch".into())
                    } else if !equivalent(step.removed.clone(), ple.removed) {
                        Err("PLE removed clauses mismatch".into())
                    } else {
                        let next = CanonicalCnf { clauses: ple.clauses };
                        if step.output_hash != next.formula_hash() {
                            Err("PLE output hash mismatch".into())
                        } else { Ok(next) }
                    }
                }
            },
            "SUB" => match current.first_strict_subsumption() {
                None => Err("SUB step has no valid subsumption".into()),
                Some((subsumer, removed)) => {
                    if step.subsuming != subsumer {
                        Err("SUB subsuming clause mismatch".into())
                    } else if step.removed != vec![removed.clone()] {
                        Err("SUB removed clause mismatch".into())
                    } else {
                        let next = current.without_clause(&removed);
                        if step.output_hash != next.formula_hash() {
                            Err("SUB output hash mismatch".into())
                        } else { Ok(next) }
                    }
                }
            },
            "BCE" => match bce::first_blocked_clause(&current.clauses)? {
                None => Err("BCE step has no blocked clause".into()),
                Some((removed, witness)) => {
                    if step.removed != vec![removed.clone()] {
                        Err("BCE removed clause mismatch".into())
                    } else if step.blocked_literal != witness.pivot {
                        Err("BCE blocked literal mismatch".into())
                    } else if step.proof_digest != bce::checked_proof_digest(&witness.checked) {
                        Err("BCE proof digest mismatch".into())
                    } else {
                        let next = current.without_clause(&removed);
                        if step.output_hash != next.formula_hash() {
                            Err("BCE output hash mismatch".into())
                        } else { Ok(next) }
                    }
                }
            },
            "VE" => {
                let ve = ve_proof::eliminate_with_proof(
                    &current.clauses, step.ve_var, width_cap)?;
                if !ve.collapsed {
                    Err("VE replay failed".into())
                } else {
                    let next = CanonicalCnf { clauses: ve.clauses };
                    if step.output_hash != next.formula_hash() {
                        Err("VE output hash mismatch".into())
                    } else if !equivalent(step.removed.clone(), ve.removed) {
                        Err("VE removed clauses mismatch".into())
                    } else if !equivalent(step.added.clone(), ve.added) {
                        Err("VE added resolvents mismatch".into())
                    } else if ve.width_observed > width_cap.max(0) as usize {
                        Err("VE width cap exceeded".into())
                    } else { Ok(next) }
                }
            },
            _ => Err(format!("unknown step type {}", step.kind)),
        };
        match check {
            Ok(next) => current = next,
            Err(error) => return Ok(failure(&current,
                format!("step {}: {error}", step.step_id))),
        }
    }
    if current.formula_hash() != expected_final_hash {
        return Ok(failure(&current, "final formula hash mismatch".into()));
    }
    Ok(LocalReplayResult {
        verified: true, final_clauses: current.clauses, error: None,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn unit_replay_and_wrong_step_hash() {
        let src = vec![vec![1], vec![-1, 2]];
        let before = CanonicalCnf::from_signed(&src).unwrap();
        let up = simplifier::unit_step(&src).unwrap().unwrap();
        let final_formula = CanonicalCnf { clauses: up.clauses.clone() };
        let step = LocalReplayStep {
            kind: "UP".into(), step_id: 1,
            input_hash: before.formula_hash(),
            output_hash: final_formula.formula_hash(), assigned: vec![1],
            removed: vec![vec![1], vec![-1, 2]],
            added: vec![vec![2]], subsuming: vec![],
            blocked_literal: 0, proof_digest: String::new(), ve_var: 0,
        };
        assert!(replay(&src, &[step.clone()], 2, &final_formula.formula_hash())
                .unwrap().verified);
        let mut tampered = step;
        tampered.assigned = vec![-1];
        assert_eq!(replay(&src, &[tampered], 2, &final_formula.formula_hash())
                  .unwrap().error.as_deref(),
                  Some("step 1: UP assigned literal mismatch"));
    }
}
