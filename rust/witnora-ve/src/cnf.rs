//! R-011: canonical immutable-style CNF algebra matching Python cnf.py.
//!
//! Clause literals are ordered using signed-integer ordering,
//! clauses are lexicographically ordered, duplicate clauses vanish,
//! and tautological clauses are discarded. An empty clause is retained.

use std::collections::{BTreeMap, BTreeSet};
use sha2::{Digest, Sha256};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CanonicalCnf {
    pub clauses: Vec<Vec<i32>>,
}

impl CanonicalCnf {
    pub fn from_signed(source: &[Vec<i32>]) -> Result<Self, String> {
        let mut clauses: BTreeSet<Vec<i32>> = BTreeSet::new();
        for raw in source {
            let mut literals: BTreeSet<i32> = BTreeSet::new();
            let mut tautology = false;
            for &lit in raw {
                if lit == 0 || lit == i32::MIN {
                    return Err("invalid canonical CNF literal".into());
                }
                if literals.contains(&-lit) {
                    tautology = true;
                }
                literals.insert(lit);
            }
            if !tautology {
                clauses.insert(literals.into_iter().collect());
            }
        }
        Ok(Self { clauses: clauses.into_iter().collect() })
    }

    pub fn variables(&self) -> Vec<u32> {
        self.clauses.iter()
            .flat_map(|c| c.iter().map(|lit| lit.unsigned_abs()))
            .collect::<BTreeSet<u32>>().into_iter().collect()
    }

    pub fn max_var(&self) -> u32 {
        self.variables().into_iter().max().unwrap_or(0)
    }

    pub fn is_2cnf(&self) -> bool {
        self.clauses.iter().all(|c| c.len() <= 2)
    }

    pub fn has_empty_clause(&self) -> bool {
        self.clauses.iter().any(Vec::is_empty)
    }

    pub fn canonical_dimacs(&self) -> String {
        let mut out = format!("p cnf {} {}\n", self.max_var(), self.clauses.len());
        for clause in &self.clauses {
            for lit in clause {
                out.push_str(&format!("{lit} "));
            }
            out.push_str("0\n");
        }
        out
    }

    pub fn formula_hash(&self) -> String {
        let digest = Sha256::digest(self.canonical_dimacs().as_bytes());
        digest.iter().map(|byte| format!("{byte:02x}")).collect()
    }

    pub fn clause_satisfied(clause: &[i32], assignment: &BTreeMap<u32, bool>) -> bool {
        clause.iter().any(|&lit| {
            assignment.get(&lit.unsigned_abs()).is_some_and(|&value| value == (lit > 0))
        })
    }

    pub fn satisfied(&self, assignment: &BTreeMap<u32, bool>) -> bool {
        self.clauses.iter().all(|c| Self::clause_satisfied(c, assignment))
    }

    pub fn without_clause(&self, target: &[i32]) -> Self {
        let clauses = self.clauses.iter().filter(|c| c.as_slice() != target)
            .cloned().collect();
        Self { clauses }
    }

    pub fn first_strict_subsumption(&self) -> Option<(Vec<i32>, Vec<i32>)> {
        for a in &self.clauses {
            for b in &self.clauses {
                if a.len() >= b.len() {
                    continue;
                }
                if a.iter().all(|lit| b.binary_search(lit).is_ok()) {
                    return Some((a.clone(), b.clone()));
                }
            }
        }
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonical_signed_order_and_exact_dimacs() {
        let src = vec![vec![3, -2, 1, 1], vec![2, -2],
                       vec![-4, 4, 5], vec![], vec![3, -2, 1]];
        let cnf = CanonicalCnf::from_signed(&src).unwrap();
        assert_eq!(cnf.clauses, vec![vec![], vec![-2, 1, 3]]);
        assert_eq!(cnf.canonical_dimacs(), "p cnf 3 2\n0\n-2 1 3 0\n");
        assert_eq!(cnf.formula_hash().len(), 64);
        assert!(cnf.has_empty_clause());
        assert!(!cnf.is_2cnf());
    }

    #[test]
    fn satisfaction_variable_universe_and_subsumption() {
        let cnf = CanonicalCnf::from_signed(&[
            vec![1], vec![1, 2], vec![-2, 3],
        ]).unwrap();
        assert_eq!(cnf.variables(), vec![1, 2, 3]);
        assert_eq!(cnf.first_strict_subsumption(),
                   Some((vec![1], vec![1, 2])));
        assert!(cnf.satisfied(&BTreeMap::from([(1, true), (2, false), (3, false)])));
        assert!(!cnf.satisfied(&BTreeMap::from([(1, false), (2, true), (3, false)])));
        assert_eq!(cnf.without_clause(&[1]).clauses.len(), 2);
    }

    #[test]
    fn reject_zero_and_signed_min() {
        assert!(CanonicalCnf::from_signed(&[vec![0]]).is_err());
        assert!(CanonicalCnf::from_signed(&[vec![i32::MIN]]).is_err());
    }

    #[test]
    fn seeded_random_1600_exact_normalizations() {
        let mut state = 110112026u64;
        let mut next = || {
            state = state.wrapping_mul(6364136223846793005)
                         .wrapping_add(1442695040888963407);
            (state >> 32) as u32
        };
        for n in 1..=8u32 {
            for _ in 0..200 {
                let mut clauses = Vec::new();
                for _ in 0..(next() % 12) {
                    let mut clause = Vec::new();
                    for _ in 0..(next() % 5) {
                        let v = 1 + next() % n;
                        clause.push(if next() % 2 == 0 { v as i32 } else { -(v as i32) });
                    }
                    clauses.push(clause);
                }
                let c = CanonicalCnf::from_signed(&clauses).unwrap();
                let d = CanonicalCnf::from_signed(&c.clauses).unwrap();
                assert_eq!(c, d, "normalization idempotence failed");
                let literals = c.clauses.iter().flatten().collect::<BTreeSet<_>>();
                assert!(!literals.contains(&&0));
            }
        }
    }
}
