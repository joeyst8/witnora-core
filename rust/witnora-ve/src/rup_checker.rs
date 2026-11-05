//! R-014: independent Rust RUP-subset DRAT-style replay checker.
//!
//! This checks RUP additions and deletions, not general DRAT/RAT.
//! It is an empirical independent reference, NOT a replacement for
//! the Lean GeneralRUP trusted proof kernel.

use std::collections::{BTreeMap, BTreeSet};
use crate::cnf::CanonicalCnf;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RupCheck {
    pub verified: bool,
    pub empty_clause_derived: bool,
    pub failed_line: Option<usize>,
    pub error: Option<String>,
    pub warnings: Vec<String>,
}

impl RupCheck {
    fn outcome(verified: bool, empty: bool, failed: Option<usize>,
               error: Option<String>, warnings: Vec<String>) -> Self {
        Self { verified, empty_clause_derived: empty,
               failed_line: failed, error, warnings }
    }
}

fn parse_proof_clause(tokens: &[&str]) -> Result<(bool, Vec<i32>), String> {
    if tokens.is_empty() {
        return Err("empty proof line".into());
    }
    let deletion = tokens[0] == "d";
    let body = if deletion { &tokens[1..] } else { tokens };
    if body.last() != Some(&"0") {
        return Err("proof line missing terminating 0".into());
    }
    let mut literals: BTreeSet<i32> = BTreeSet::new();
    for &token in &body[..body.len() - 1] {
        let lit: i32 = token.parse().map_err(|_| "noninteger RUP literal")?;
        if lit == 0 || lit == i32::MIN {
            return Err("invalid RUP proof literal".into());
        }
        if literals.contains(&-lit) {
            return Err("tautological proof clause is not canonical".into());
        }
        literals.insert(lit);
    }
    Ok((deletion, literals.into_iter().collect()))
}

fn parse_proof(text: &str) -> Result<Vec<(bool, Vec<i32>)>, String> {
    let mut result = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('c') {
            continue;
        }
        result.push(parse_proof_clause(
            &line.split_whitespace().collect::<Vec<_>>())?);
    }
    Ok(result)
}

fn assign(assignment: &mut BTreeMap<u32, bool>, lit: i32) -> bool {
    let key = lit.unsigned_abs();
    let value = lit > 0;
    match assignment.get(&key) {
        Some(&old) => old == value,
        None => { assignment.insert(key, value); true }
    }
}

fn unit_propagation_conflicts(active: &BTreeSet<Vec<i32>>, assumptions: &[i32]) -> bool {
    let mut assignment = BTreeMap::new();
    for &lit in assumptions {
        if !assign(&mut assignment, lit) {
            return true;
        }
    }
    let mut changed = true;
    while changed {
        changed = false;
        for clause in active {
            let mut satisfied = false;
            let mut unassigned = Vec::new();
            for &lit in clause {
                match assignment.get(&lit.unsigned_abs()) {
                    None => unassigned.push(lit),
                    Some(&value) if value == (lit > 0) => {
                        satisfied = true;
                        break;
                    }
                    Some(_) => {}
                }
            }
            if satisfied {
                continue;
            }
            if unassigned.is_empty() {
                return true;
            }
            if unassigned.len() == 1 {
                if !assign(&mut assignment, unassigned[0]) {
                    return true;
                }
                changed = true;
            }
        }
    }
    false
}

/// Replay a RUP-only DRAT-style proof from original source clauses.
/// Textual proof errors become unverified outcomes, matching Python.
pub fn check_rup_text(
    original: &[Vec<i32>],
    proof_text: &str,
    strict_deletions: bool,
) -> Result<RupCheck, String> {
    let normalized = CanonicalCnf::from_signed(original)?;
    let mut active: BTreeSet<Vec<i32>> = normalized.clauses.into_iter().collect();
    let proof = match parse_proof(proof_text) {
        Ok(proof) => proof,
        Err(error) => return Ok(RupCheck::outcome(
            false, false, None, Some(error), vec![])),
    };
    let mut warnings = Vec::new();
    let mut empty_derived = false;
    for (line, (deletion, clause)) in proof.into_iter().enumerate() {
        let line_no = line + 1;
        if deletion {
            if !active.remove(&clause) {
                let message = "deletion clause not present in active database";
                if strict_deletions {
                    return Ok(RupCheck::outcome(false, empty_derived,
                        Some(line_no), Some(message.into()), warnings));
                }
                warnings.push(format!("line {line_no}: {message}"));
            }
            continue;
        }
        let assumptions = clause.iter().map(|lit| -lit).collect::<Vec<_>>();
        if !unit_propagation_conflicts(&active, &assumptions) {
            return Ok(RupCheck::outcome(false, empty_derived,
                Some(line_no), Some("addition is not RUP-checkable".into()), warnings));
        }
        active.insert(clause.clone());
        if clause.is_empty() {
            empty_derived = true;
            return Ok(RupCheck::outcome(
                true, true, None, None, warnings));
        }
    }
    Ok(RupCheck::outcome(false, empty_derived, None,
        Some("empty clause was not derived".into()), warnings))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exact_conflicts_and_missing_additions() {
        let unsat = vec![vec![1], vec![-1]];
        let got = check_rup_text(&unsat, "0\n", false).unwrap();
        assert!(got.verified && got.empty_clause_derived);
        let sat = check_rup_text(&[vec![1]], "0\n", false).unwrap();
        assert!(!sat.verified);
        assert_eq!(sat.failed_line, Some(1));
        let no_goal = check_rup_text(&[], "", false).unwrap();
        assert!(!no_goal.verified);
        assert_eq!(no_goal.error.as_deref(), Some("empty clause was not derived"));
    }

    #[test]
    fn deletion_warning_strictness_and_bad_proofs() {
        let loose = check_rup_text(&[vec![1], vec![-1]],
            "d 2 0\n0\n", false).unwrap();
        assert!(loose.verified);
        assert_eq!(loose.warnings.len(), 1);
        let strict = check_rup_text(&[vec![1], vec![-1]],
            "d 2 0\n0\n", true).unwrap();
        assert!(!strict.verified);
        assert_eq!(strict.failed_line, Some(1));
        assert!(check_rup_text(&[], "1 -1 0\n", false)
                .unwrap().error.unwrap().contains("tautological"));
    }
}
