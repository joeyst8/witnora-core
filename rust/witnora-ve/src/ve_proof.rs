//! R-020: exact bounded-width variable-elimination proof events.
//!
//! This is Davis-Putnam resolution on source clauses, not model-counting
//! variable elimination. Every generated and discarded resolvent is
//! returned so the legacy proof logger can be compared exactly.

use crate::cnf::CanonicalCnf;
use std::collections::BTreeSet;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ResolutionPair {
    pub positive: Vec<i32>,
    pub negative: Vec<i32>,
    pub resolvent: Vec<i32>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct VeProofStep {
    pub clauses: Vec<Vec<i32>>,
    pub collapsed: bool,
    pub width_observed: usize,
    pub refusal_resolvent: Option<Vec<i32>>,
    pub discarded: Vec<ResolutionPair>,
    pub generated: Vec<ResolutionPair>,
    pub added: Vec<Vec<i32>>,
    pub removed: Vec<Vec<i32>>,
}

fn has_tautology(literals: &[i32]) -> bool {
    let mut seen = BTreeSet::new();
    for &lit in literals {
        if seen.contains(&-lit) {
            return true;
        }
        seen.insert(lit);
    }
    false
}

pub fn eliminate_with_proof(
    source: &[Vec<i32>], variable: i32, width_cap: i32,
) -> Result<VeProofStep, String> {
    let formula = CanonicalCnf::from_signed(source)?;
    if variable == i32::MIN {
        return Err("invalid variable-elimination pivot".into());
    }
    let positive: Vec<_> = formula.clauses.iter()
        .filter(|c| c.contains(&variable)).cloned().collect();
    let negative: Vec<_> = formula.clauses.iter()
        .filter(|c| c.contains(&-variable)).cloned().collect();
    let mut removed = positive.iter().chain(negative.iter())
        .cloned().collect::<Vec<_>>();
    removed.sort();
    let kept: Vec<_> = formula.clauses.iter()
        .filter(|c| !c.contains(&variable) && !c.contains(&-variable))
        .cloned().collect();

    let mut resolvents = BTreeSet::new();
    let mut discarded = Vec::new();
    let mut generated = Vec::new();
    let mut max_resolvent_len = 0;

    for a in &positive {
        for b in &negative {
            let mut raw = a.iter().filter(|&&lit| lit != variable)
                .chain(b.iter().filter(|&&lit| lit != -variable))
                .copied().collect::<Vec<_>>();
            raw.sort_unstable();
            let pair = ResolutionPair {
                positive: a.clone(), negative: b.clone(),
                resolvent: raw.clone(),
            };
            if has_tautology(&raw) {
                discarded.push(pair);
                continue;
            }
            let normalized = CanonicalCnf::from_signed(&[raw])?;
            if normalized.clauses.len() != 1 {
                return Err("unexpected tautological canonical resolvent".into());
            }
            let resolvent = normalized.clauses[0].clone();
            max_resolvent_len = max_resolvent_len.max(resolvent.len());
            if resolvent.len() as i64 > width_cap as i64 {
                return Ok(VeProofStep {
                    clauses: formula.clauses, collapsed: false,
                    width_observed: max_resolvent_len,
                    refusal_resolvent: Some(resolvent),
                    discarded, generated,
                    added: vec![], removed,
                });
            }
            resolvents.insert(resolvent.clone());
            generated.push(ResolutionPair {
                positive: a.clone(), negative: b.clone(),
                resolvent,
            });
        }
    }
    let added = resolvents.into_iter().collect::<Vec<_>>();
    let mut output = kept;
    output.extend(added.clone());
    let out = CanonicalCnf::from_signed(&output)?;
    Ok(VeProofStep {
        clauses: out.clauses, collapsed: true,
        width_observed: max_resolvent_len,
        refusal_resolvent: None,
        discarded, generated, added, removed,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn width_refusals_and_exact_resolvents() {
        let source = vec![vec![1,2],vec![-1,3],vec![4]];
        let out = eliminate_with_proof(&source, 1, 2).unwrap();
        assert!(out.collapsed);
        assert_eq!(out.added, vec![vec![2,3]]);
        assert_eq!(out.removed, vec![vec![-1,3],vec![1,2]]);
        let refusal = eliminate_with_proof(&source, 1, 1).unwrap();
        assert!(!refusal.collapsed);
        assert_eq!(refusal.refusal_resolvent, Some(vec![2,3]));
        assert_eq!(refusal.clauses, CanonicalCnf::from_signed(&source).unwrap().clauses);
    }

    #[test]
    fn zero_negative_caps_and_no_occurrence() {
        let source = vec![vec![1],vec![-1]];
        let got = eliminate_with_proof(&source, 1, 0).unwrap();
        assert!(got.collapsed);
        assert_eq!(got.clauses, vec![vec![]]);
        assert!(!eliminate_with_proof(&source, 1, -1).unwrap().collapsed);
        assert!(eliminate_with_proof(&source, 3, 0).unwrap().collapsed);
    }
}
