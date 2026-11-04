//! R-045: observational source-exact XOR separator fingerprint.
//! Detects only complete 2..=6-variable parity clause encodings.
//! A parity-graph separator is NOT a certified CNF separator or Lean proof.

use crate::cnf::CanonicalCnf;
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SeparatorCandidate {
    pub variable: u32,
    pub parity_equations_incident: usize,
    pub components_before: usize,
    pub components_after: usize,
    pub component_equation_indices: Vec<Vec<usize>>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Fingerprint {
    pub source_sha256: String,
    pub parity_equation_supports: Vec<Vec<u32>>,
    pub separator_candidates: Vec<SeparatorCandidate>,
}

fn exact_pattern(support: &[u32], rhs: u32) -> BTreeSet<Vec<i32>> {
    let k = support.len();
    let mut clauses = BTreeSet::new();
    for bits in 0usize..(1usize << k) {
        if bits.count_ones() % 2 == rhs { continue; }
        let mut clause: Vec<i32> = support.iter().enumerate()
            .map(|(i, &var)| {
                if (bits >> i) & 1 == 1 { -(var as i32) }
                else { var as i32 }
            })
            .collect();
        clause.sort_unstable();
        clauses.insert(clause);
    }
    clauses
}

fn exact_xor_supports(formula: &CanonicalCnf, max_k: usize) -> Vec<Vec<u32>> {
    let mut groups = BTreeMap::<Vec<u32>,BTreeSet<Vec<i32>>>::new();
    for clause in &formula.clauses {
        let support = clause.iter().map(|lit| lit.unsigned_abs())
            .collect::<BTreeSet<_>>().into_iter().collect::<Vec<_>>();
        if support.len() != clause.len() { continue; }
        groups.entry(support).or_default().insert(clause.clone());
    }
    let mut equations = Vec::<(Vec<u32>,u32)>::new();
    for (support, group) in groups {
        let k = support.len();
        if k < 2 || k > max_k || group.len() != 1usize << (k - 1) {
            continue;
        }
        for rhs in 0..=1u32 {
            if group == exact_pattern(&support, rhs) {
                equations.push((support.clone(), rhs));
                break;
            }
        }
    }
    equations.sort_unstable();
    equations.into_iter().map(|(support, _rhs)| support).collect()
}

fn components(supports: &[BTreeSet<u32>]) -> Vec<Vec<usize>> {
    let mut remaining = (0..supports.len()).collect::<BTreeSet<usize>>();
    let mut groups = Vec::new();
    while let Some(&start) = remaining.iter().next() {
        remaining.remove(&start);
        let mut group = vec![start];
        let mut queue = vec![start];
        while let Some(current) = queue.pop() {
            let adjacent = remaining.iter().filter(|&&i|
                !supports[current].is_disjoint(&supports[i])
            ).copied().collect::<Vec<_>>();
            for i in adjacent {
                remaining.remove(&i);
                group.push(i);
                queue.push(i);
            }
        }
        group.sort_unstable();
        groups.push(group);
    }
    groups
}

pub fn parity_separator_fingerprint(
    source: &[Vec<i32>], max_k: i32,
) -> Result<Fingerprint,String> {
    if !(2..=6).contains(&max_k) {
        return Err("bounded XOR detection requires arity 2..6".into());
    }
    let formula = CanonicalCnf::from_signed(source)?;
    let supports = exact_xor_supports(&formula, max_k as usize);
    let sets = supports.iter().map(|s| s.iter().copied().collect::<BTreeSet<_>>())
        .collect::<Vec<_>>();
    let base = components(&sets);
    let variables = sets.iter().flat_map(|set| set.iter().copied())
        .collect::<BTreeSet<_>>();
    let mut candidates = Vec::new();
    for variable in variables {
        let incidence = sets.iter().filter(|set| set.contains(&variable)).count();
        if incidence < 2 { continue; }
        let reduced = sets.iter().map(|set| {
            let mut smaller = set.clone();
            smaller.remove(&variable);
            smaller
        }).collect::<Vec<_>>();
        let after = components(&reduced);
        if after.len() > base.len() {
            candidates.push(SeparatorCandidate {
                variable,
                parity_equations_incident: incidence,
                components_before: base.len(),
                components_after: after.len(),
                component_equation_indices: after,
            });
        }
    }
    Ok(Fingerprint {
        source_sha256: formula.formula_hash(),
        parity_equation_supports: supports,
        separator_candidates: candidates,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn exact_source_hub_and_partial_xor_are_observational() {
        let source = vec![
            vec![1,-2],vec![-1,2],
            vec![1,3],vec![-1,-3],
            vec![2,3], // insufficient to claim a third XOR equation
        ];
        let result = parity_separator_fingerprint(&source,6).unwrap();
        assert_eq!(result.parity_equation_supports,vec![vec![1,2],vec![1,3]]);
        assert_eq!(result.separator_candidates.len(),1);
        let hub=&result.separator_candidates[0];
        assert_eq!(hub.variable,1);
        assert_eq!(hub.components_before,1);
        assert_eq!(hub.components_after,2);
        assert_eq!(hub.component_equation_indices,vec![vec![0],vec![1]]);
    }

    #[test]
    fn reject_out_of_bound_detection_and_incomplete_patterns() {
        assert!(parity_separator_fingerprint(&[],1).is_err());
        assert!(parity_separator_fingerprint(&[],7).is_err());
        let result=parity_separator_fingerprint(&[vec![1,2]],6).unwrap();
        assert!(result.parity_equation_supports.is_empty());
    }
}
