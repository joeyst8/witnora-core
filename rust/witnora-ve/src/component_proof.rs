//! R-032: full deterministic incidence-component proof metadata.
//! All fields match the original Python component_details schema.

use crate::{cnf::CanonicalCnf, graph};
use std::collections::BTreeMap;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ComponentRecord {
    pub id: usize,
    pub formula_hash: String,
    pub variables: Vec<u32>,
    pub clauses: Vec<Vec<i32>>,
    pub clause_indices: Vec<usize>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ComponentEvidence {
    pub count: usize,
    pub incidence_edges: Vec<(u32, usize)>,
    pub components: Vec<ComponentRecord>,
}

pub fn component_evidence(source: &[Vec<i32>]) -> Result<ComponentEvidence, String> {
    let formula = CanonicalCnf::from_signed(source)?;
    let canonical = &formula.clauses;
    let clause_index: BTreeMap<_, _> = canonical.iter().enumerate()
        .map(|(i, clause)| (clause.clone(), i)).collect();
    let mut incidence_edges = Vec::new();
    for (i, clause) in canonical.iter().enumerate() {
        let variables = clause.iter().map(|lit| lit.unsigned_abs())
            .collect::<std::collections::BTreeSet<_>>();
        for variable in variables {
            incidence_edges.push((variable, i));
        }
    }
    let components = graph::incidence_components(canonical)?
        .into_iter().enumerate().map(|(id, clauses)| {
            let child = CanonicalCnf::from_signed(&clauses)?;
            let indices = child.clauses.iter().map(|clause| {
                clause_index.get(clause).copied().ok_or_else(
                    || "native component lost original clause".to_string())
            }).collect::<Result<Vec<_>,_>>()?;
            Ok(ComponentRecord {
                id, formula_hash: child.formula_hash(),
                variables: child.variables(),
                clauses: child.clauses,
                clause_indices: indices,
            })
        }).collect::<Result<Vec<_>,String>>()?;
    Ok(ComponentEvidence {
        count: components.len(), incidence_edges, components,
    })
}

/// Verify a logged CD proof record against native source evidence.
/// Returns the first Python-compatible CD error, without claiming full
/// component-state or SAT/UNSAT replay certification.
pub fn verify_evidence(
    source: &[Vec<i32>], output_hash: &str,
    count: usize, edges: &[(u32, usize)],
    logged: &[ComponentRecord],
) -> Result<Option<String>, String> {
    let formula = CanonicalCnf::from_signed(source)?;
    if output_hash != formula.formula_hash() {
        return Ok(Some("CD output hash mismatch".into()));
    }
    let expected = component_evidence(source)?;
    if count != expected.count {
        return Ok(Some("CD component count mismatch".into()));
    }
    if edges != expected.incidence_edges {
        return Ok(Some("CD incidence edges mismatch".into()));
    }
    if logged != expected.components {
        return Ok(Some("CD component contents mismatch".into()));
    }
    Ok(None)
}

/// A valid CD proof produces a set of independently canonicalized child states.
/// Invalid evidence is rejected before any child state is returned.
pub fn verify_evidence_and_children(
    source: &[Vec<i32>], output_hash: &str,
    count: usize, edges: &[(u32, usize)],
    logged: &[ComponentRecord],
) -> Result<(bool, Vec<(String, Vec<Vec<i32>>)>, Option<String>), String> {
    if let Some(reason) = verify_evidence(source, output_hash, count, edges, logged)? {
        return Ok((false, Vec::new(), Some(reason)));
    }
    let mut children = Vec::with_capacity(logged.len());
    for record in logged {
        let child = CanonicalCnf::from_signed(&record.clauses)?;
        children.push((record.id.to_string(), child.clauses));
    }
    Ok((true, children, None))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn disconnected_clause_indices_and_hashes() {
        let source = vec![vec![1,2],vec![3],vec![-2,1],vec![]];
        let got = component_evidence(&source).unwrap();
        assert_eq!(got.count, 3);
        assert_eq!(got.incidence_edges.len(), 5);
        assert_eq!(got.components[0].clauses, vec![vec![]]);
        assert_eq!(got.components[0].clause_indices, vec![0]);
        assert!(got.components.iter().all(|c| c.formula_hash.len()==64));
        let hash = CanonicalCnf::from_signed(&source).unwrap().formula_hash();
        assert_eq!(verify_evidence(&source, &hash, got.count,
            &got.incidence_edges, &got.components).unwrap(), None);
        let (ok, children, error) = verify_evidence_and_children(&source, &hash,
            got.count, &got.incidence_edges, &got.components).unwrap();
        assert!(ok);
        assert_eq!(error, None);
        assert_eq!(children.len(), 3);
        assert_eq!(children[0].0, "0");
        assert_eq!(children[0].1, vec![vec![]]);
        assert_eq!(verify_evidence(&source, &hash, got.count + 1,
            &got.incidence_edges, &got.components).unwrap(),
            Some("CD component count mismatch".into()));
    }
}
