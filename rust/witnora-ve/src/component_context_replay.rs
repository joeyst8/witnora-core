//! R-035: single-root CD plus component-context local step replay.
//! This is a deliberately bounded proof-transition stream checker, not
//! final SAT/UNSAT or recursive/nested certificate certification.

use crate::{cnf::CanonicalCnf, component_proof::{self, ComponentRecord},
            local_replay::{self, LocalReplayResult, LocalReplayStep}};
use std::collections::BTreeMap;

#[derive(Clone, Debug)]
pub struct ContextLocalStep {
    pub component_id: Option<String>,
    pub step: LocalReplayStep,
}

fn reject(source: &CanonicalCnf, error: String) -> LocalReplayResult {
    LocalReplayResult {
        verified: false, final_clauses: source.clauses.clone(),
        error: Some(error),
    }
}

pub fn replay_single_root_cd(
    source: &[Vec<i32>], root_input_hash: &str, root_output_hash: &str,
    component_count: usize, incidence_edges: &[(u32, usize)],
    component_records: &[ComponentRecord], steps: &[ContextLocalStep],
    width_cap: i32, final_hash: &str,
) -> Result<LocalReplayResult, String> {
    let original = CanonicalCnf::from_signed(source)?;
    if root_input_hash != original.formula_hash() {
        return Ok(reject(&original, "CD input hash mismatch at step 1".into()));
    }
    let (ok, children, error) = component_proof::verify_evidence_and_children(
        source, root_output_hash, component_count, incidence_edges,
        component_records,
    )?;
    if !ok {
        return Ok(reject(&original, format!("step 1: {}",
            error.unwrap_or_else(|| "CD evidence mismatch".into()))));
    }
    let mut root = original.clone();
    let mut states = BTreeMap::<String, CanonicalCnf>::new();
    for (id, clauses) in children {
        states.insert(id, CanonicalCnf::from_signed(&clauses)?);
    }

    for (position, event) in steps.iter().enumerate() {
        let expected_id = position + 2;
        if event.step.step_id != expected_id {
            return Ok(reject(&original,
                format!("step id mismatch at {}", event.step.step_id)));
        }
        if event.step.kind == "CD" {
            return Ok(reject(&original,
                "nested CD is outside single-root replay scope".into()));
        }
        let current = match &event.component_id {
            Some(id) => match states.get(id) {
                Some(state) => state.clone(),
                None => return Ok(reject(&original,
                    format!("step {}: component {} is missing", expected_id, id))),
            },
            None if !states.is_empty() => return Ok(reject(&original,
                format!("step {}: component-local step missing component_id",
                    expected_id))),
            None => root.clone(),
        };
        if event.step.input_hash != current.formula_hash() {
            return Ok(reject(&original, format!(
                "{} input hash mismatch at step {}",
                event.step.kind, expected_id)));
        }
        let mut step = event.step.clone();
        step.step_id = 1;
        let out = local_replay::replay(
            &current.clauses, &[step], width_cap, &event.step.output_hash,
        )?;
        if !out.verified {
            let error = out.error.unwrap_or_else(|| "local replay failed".into());
            let suffix = error.strip_prefix("step 1: ").unwrap_or(&error);
            return Ok(reject(&original,
                format!("step {}: {}", expected_id, suffix)));
        }
        let next = CanonicalCnf::from_signed(&out.final_clauses)?;
        if let Some(id) = &event.component_id {
            states.insert(id.clone(), next);
        } else {
            root = next;
        }
    }

    let final_state = if states.is_empty() {
        root
    } else {
        let joined = states.values().flat_map(|state| state.clauses.clone())
            .collect::<Vec<_>>();
        CanonicalCnf::from_signed(&joined)?
    };
    if final_state.formula_hash() != final_hash {
        return Ok(reject(&original, "final formula hash mismatch".into()));
    }
    Ok(LocalReplayResult {
        verified: true, final_clauses: final_state.clauses, error: None,
    })
}

/// Verify a local root-proof prefix, then one CD and component-scoped suffix.
/// Global step numbering and first-error prefixes follow Python's stream.
pub fn replay_prefixed_root_cd(
    source: &[Vec<i32>], prefix: &[LocalReplayStep],
    cd_step_id: usize, cd_input_hash: &str, cd_output_hash: &str,
    count: usize, edges: &[(u32, usize)], records: &[ComponentRecord],
    suffix: &[ContextLocalStep], width_cap: i32, final_hash: &str,
) -> Result<LocalReplayResult, String> {
    let original = CanonicalCnf::from_signed(source)?;
    if cd_step_id != prefix.len() + 1 {
        return Ok(reject(&original,
            format!("step id mismatch at {}", cd_step_id)));
    }
    for (position, event) in suffix.iter().enumerate() {
        if event.step.step_id != cd_step_id + position + 1 {
            return Ok(reject(&original,
                format!("step id mismatch at {}", event.step.step_id)));
        }
    }
    let expected_prefix_hash = prefix.last()
        .map(|event| event.output_hash.clone())
        .unwrap_or_else(|| original.formula_hash());
    let replayed = local_replay::replay(
        source, prefix, width_cap, &expected_prefix_hash,
    )?;
    if !replayed.verified {
        return Ok(replayed);
    }
    let before_cd = CanonicalCnf::from_signed(&replayed.final_clauses)?;
    if cd_input_hash != before_cd.formula_hash() {
        return Ok(reject(&original, format!(
            "CD input hash mismatch at step {}", cd_step_id)));
    }
    let shifted = suffix.iter().enumerate().map(|(position, event)| {
        let mut next = event.clone();
        next.step.step_id = position + 2;
        next
    }).collect::<Vec<_>>();
    let mut result = replay_single_root_cd(
        &before_cd.clauses, cd_input_hash, cd_output_hash,
        count, edges, records, &shifted, width_cap, final_hash,
    )?;
    if let Some(error) = result.error.take() {
        let adjusted = if let Some(tail) =
            error.strip_prefix("CD input hash mismatch at step 1") {
            format!("CD input hash mismatch at step {}{}", cd_step_id, tail)
        } else if let Some((number, tail)) =
            error.strip_prefix("step ").and_then(|s| s.split_once(':')) {
            if let Ok(relative) = number.parse::<usize>() {
                format!("step {}:{}", relative + prefix.len(), tail)
            } else {
                error
            }
        } else if let Some((head, number)) = error.rsplit_once(" at step ") {
            if let Ok(relative) = number.parse::<usize>() {
                format!("{} at step {}", head, relative + prefix.len())
            } else {
                error
            }
        } else {
            error
        };
        result.error = Some(adjusted);
    }
    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn root_cd_and_child_state_integrity() {
        let source = vec![vec![1], vec![2]];
        let root = CanonicalCnf::from_signed(&source).unwrap();
        let cd = component_proof::component_evidence(&source).unwrap();
        let out = replay_single_root_cd(&source, &root.formula_hash(),
            &root.formula_hash(), cd.count, &cd.incidence_edges,
            &cd.components, &[], 3, &root.formula_hash()).unwrap();
        assert!(out.verified);
        assert_eq!(out.final_clauses, root.clauses);
        let denied = replay_single_root_cd(&source, &root.formula_hash(),
            &root.formula_hash(), cd.count + 1, &cd.incidence_edges,
            &cd.components, &[], 3, &root.formula_hash()).unwrap();
        assert_eq!(denied.error.as_deref(),
            Some("step 1: CD component count mismatch"));
    }
}
