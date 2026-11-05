//! Source-model-equivalent CNF simplification, independent of #SAT counting.
//!
//! Each step uses only Boolean identities:
//!   (A OR x) AND (A OR NOT x)  iff A  (consensus)
//!   unit(l) AND C  iff unit(l) AND C[l := true]  (unit reduction)
//! Every transformation preserves the full assignment set over the
//! original variable universe. This is standard preprocessing, not a
//! novel mathematical result or a trusted Lean proof.

use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, PartialEq, Eq)]
pub struct PreprocessResult {
    pub clauses: Vec<Vec<i32>>,
    pub passes: usize,
    pub consensus_pairs: usize,
    pub original_clauses: usize,
}

pub(crate) fn normalize(mut clauses: Vec<Vec<i32>>, nvars: u32) -> Result<Vec<Vec<i32>>, String> {
    let mut output = Vec::new();
    for mut clause in clauses.drain(..) {
        let mut bits: BTreeMap<u32, i8> = BTreeMap::new();
        let mut tautology = false;
        for lit in clause.drain(..) {
            if lit == 0 || lit == i32::MIN || lit.unsigned_abs() > nvars {
                return Err("literal outside declared source universe".into());
            }
            let (v, sign) = (lit.unsigned_abs(), if lit > 0 { 1 } else { -1 });
            if let Some(previous) = bits.insert(v, sign) {
                if previous != sign {
                    tautology = true;
                }
            }
        }
        if tautology {
            continue;
        }
        output.push(bits.into_iter().map(|(v, sign)| {
            if sign > 0 { v as i32 } else { -(v as i32) }
        }).collect());
    }
    output.sort();
    output.dedup();
    Ok(output)
}

fn propagate_units(clauses: &[Vec<i32>]) -> Vec<Vec<i32>> {
    let mut units: BTreeMap<u32, bool> = BTreeMap::new();
    for clause in clauses {
        if clause.len() == 1 {
            let lit = clause[0];
            let var = lit.unsigned_abs();
            if let Some(previous) = units.insert(var, lit > 0) {
                if previous != (lit > 0) {
                    return vec![vec![]]; // Exact contradiction.
                }
            }
        }
    }
    let mut result = Vec::new();
    for clause in clauses {
        if clause.len() <= 1 {
            result.push(clause.clone());
            continue;
        }
        let mut reduced = Vec::new();
        let mut satisfied = false;
        for &lit in clause {
            match units.get(&lit.unsigned_abs()) {
                Some(&value) if value == (lit > 0) => {
                    satisfied = true;
                    break;
                }
                Some(_) => {} // Falsified literal: remove it.
                None => reduced.push(lit),
            }
        }
        if !satisfied {
            result.push(reduced);
        }
    }
    result
}

/// Replace any collection of *disjoint* complementary clause pairs
/// (A|v),(A|~v) with A. Doing disjoint pairs in a batch is equivalent
/// to sequentially applying the exact Boolean identity.
fn consensus_pass(clauses: &[Vec<i32>]) -> (Vec<Vec<i32>>, usize) {
    let mut candidates: BTreeMap<(Vec<i32>, u32), (Option<usize>, Option<usize>)> =
        BTreeMap::new();
    for (idx, clause) in clauses.iter().enumerate() {
        for (at, &lit) in clause.iter().enumerate() {
            let mut remainder = clause.clone();
            remainder.remove(at);
            let entry = candidates.entry((remainder, lit.unsigned_abs()))
                .or_default();
            if lit > 0 { entry.0 = Some(idx); } else { entry.1 = Some(idx); }
        }
    }
    let mut removed = BTreeSet::new();
    let mut added = Vec::new();
    let mut pairs = 0;
    for ((remainder, _), (positive, negative)) in candidates {
        if let (Some(a), Some(b)) = (positive, negative) {
            if a != b && !removed.contains(&a) && !removed.contains(&b) {
                removed.insert(a);
                removed.insert(b);
                added.push(remainder);
                pairs += 1;
            }
        }
    }
    if pairs == 0 {
        return (clauses.to_vec(), 0);
    }
    let mut result: Vec<Vec<i32>> = clauses.iter().enumerate()
        .filter(|(idx, _)| !removed.contains(idx))
        .map(|(_, c)| c.clone()).collect();
    result.extend(added);
    (result, pairs)
}

/// Lightweight *heuristic* admission check for expensive consensus closure.
/// It conservatively admits all non-binary clauses and any unit/empty clause,
/// and checks whether a binary support contains clauses with a one-sign flip.
/// A false result permits skipping preprocessing but NEVER implies that the
/// source is irreducible by every Boolean method (e.g. deduplication).
/// The count remains exact on either branch. Full source validation occurs
/// even when the admission decision is false.
pub fn source_admission_heuristic(
    source: &[Vec<i32>], nvars: u32,
) -> Result<bool, String> {
    if nvars > 512 {
        return Err("invalid source variable universe".into());
    }
    let mut sign_masks: BTreeMap<(u32, u32), u8> = BTreeMap::new();
    let mut special_clause = false;
    for clause in source {
        for &lit in clause {
            if lit == 0 || lit == i32::MIN || lit.unsigned_abs() > nvars {
                return Err("literal outside declared source universe".into());
            }
        }
        if clause.len() != 2 {
            special_clause = true;
            continue;
        }
        let (a, b) = (clause[0], clause[1]);
        if a.unsigned_abs() == b.unsigned_abs() {
            special_clause = true;
            continue;
        }
        let (first, second) = if a.unsigned_abs() < b.unsigned_abs() {
            (a, b)
        } else {
            (b, a)
        };
        let pattern = ((first < 0) as u8) * 2 + (second < 0) as u8;
        *sign_masks.entry((first.unsigned_abs(), second.unsigned_abs()))
            .or_default() |= 1u8 << pattern;
    }
    if special_clause {
        return Ok(true);
    }
    for &mask in sign_masks.values() {
        // Bit 0 = ++, bit 1 = +-, bit 2 = -+, bit 3 = --.
        // Any edge on this 4-vertex square is a direct consensus pair.
        if (mask & 1 != 0 && mask & 6 != 0)
            || (mask & 8 != 0 && mask & 6 != 0)
        {
            return Ok(true);
        }
    }
    Ok(false)
}

/// Return an exact logically equivalent CNF, or None on resource cap.
///
/// `max_clause_visits` bounds repeated full-clause examination.
/// `max_passes` bounds closure iterations. Neither budget exhaustion
/// nor a synthetic source error is ever treated as UNSAT.
pub fn simplify_source(
    source: &[Vec<i32>], nvars: u32, max_passes: usize,
    max_clause_visits: usize,
) -> Result<Option<PreprocessResult>, String> {
    if nvars > 512 || max_passes == 0 || max_clause_visits == 0 {
        return Err("invalid preprocessing limit or variable universe".into());
    }
    let mut clauses = normalize(source.to_vec(), nvars)?;
    let original_clauses = source.len();
    let mut pairs = 0usize;
    let mut visits = 0usize;
    for round in 0..max_passes {
        if clauses.len() > max_clause_visits.saturating_sub(visits) {
            return Ok(None);
        }
        visits += clauses.len();
        let before = clauses.clone();
        clauses = normalize(propagate_units(&clauses), nvars)?;
        // Empty clause makes CNF UNSAT, so terminate exactly.
        if clauses.iter().any(|clause| clause.is_empty()) {
            return Ok(Some(PreprocessResult {
                clauses: vec![vec![]], passes: round + 1,
                consensus_pairs: pairs, original_clauses,
            }));
        }
        if clauses.len() > max_clause_visits.saturating_sub(visits) {
            return Ok(None);
        }
        visits += clauses.len();
        let (replaced, n) = consensus_pass(&clauses);
        pairs += n;
        clauses = normalize(replaced, nvars)?;
        if clauses == before {
            return Ok(Some(PreprocessResult {
                clauses, passes: round + 1,
                consensus_pairs: pairs, original_clauses,
            }));
        }
    }
    Ok(None)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn models(source: &[Vec<i32>], nvars: usize) -> Vec<usize> {
        (0..(1 << nvars)).filter(|&mask| source.iter().all(|clause|
            clause.iter().any(|&lit| {
                let bit = mask & (1 << (lit.unsigned_abs() as usize - 1)) != 0;
                bit == (lit > 0)
            })
        )).collect()
    }

    #[test]
    fn forcing_64_entailed_units_collapse_to_exact_unit_source() {
        let n = 64usize;
        let mut source: Vec<Vec<i32>> = Vec::new();
        for u in 1..n {
            for v in (u + 1)..=n {
                source.push(vec![u as i32, v as i32]);
                source.push(vec![u as i32, -(v as i32)]);
            }
        }
        for v in 1..n {
            source.push(vec![v as i32]);
        }
        let result = simplify_source(&source, n as u32, 32, 200000).unwrap().unwrap();
        assert_eq!(result.clauses.len(), n - 1);
        assert_eq!(result.clauses, (1..n).map(|v| vec![v as i32]).collect::<Vec<_>>());
    }

    #[test]
    fn randomized_complete_source_model_set_preservation() {
        let mut seed = 30030u64;
        let mut rng = || {
            seed = seed.wrapping_mul(2862933555777941757).wrapping_add(3037000493);
            (seed >> 32) as usize
        };
        for n in 2..=8usize {
            for _ in 0..40 {
                let mut source = Vec::new();
                for _ in 0..(rng() % 11) {
                    let mut clause = Vec::new();
                    for _ in 0..(rng() % 5) {
                        let v = 1 + rng() % n;
                        clause.push(if rng() & 1 == 0 { v as i32 } else { -(v as i32) });
                    }
                    source.push(clause);
                }
                let result = simplify_source(&source, n as u32, 64, 100000).unwrap().unwrap();
                assert_eq!(models(&source, n), models(&result.clauses, n));
            }
        }
    }

    #[test]
    fn contradictory_tautological_and_free_controls() {
        let contradiction = simplify_source(
            &[vec![1], vec![-1], vec![1, -1]], 3, 20, 100,
        ).unwrap().unwrap();
        assert_eq!(contradiction.clauses, vec![Vec::<i32>::new()]);
        let tautological = simplify_source(
            &[vec![1, -1], vec![2, 2]], 3, 20, 100,
        ).unwrap().unwrap();
        assert_eq!(models(&tautological.clauses, 3), models(&[vec![2]], 3));
        assert_eq!(simplify_source(&[], 3, 10, 100).unwrap().unwrap().clauses.len(), 0);
    }

    #[test]
    fn adaptive_admission_selects_forcing_not_parity() {
        let n = 64usize;
        let mut parity = Vec::new();
        let mut forcing = Vec::new();
        for u in 1..n {
            for v in (u + 1)..=n {
                parity.push(vec![u as i32, -(v as i32)]);
                parity.push(vec![-(u as i32), v as i32]);
                forcing.push(vec![u as i32, v as i32]);
                forcing.push(vec![u as i32, -(v as i32)]);
            }
        }
        assert!(!source_admission_heuristic(&parity, n as u32).unwrap());
        assert!(source_admission_heuristic(&forcing, n as u32).unwrap());
        forcing.push(vec![1]);
        assert!(source_admission_heuristic(&forcing, n as u32).unwrap());
        assert!(source_admission_heuristic(&[vec![1, 2, 3]], 3).unwrap());
        assert!(!source_admission_heuristic(&[vec![1, -2], vec![-1, 2]], 2).unwrap());
        assert!(source_admission_heuristic(&[vec![3]], 2).is_err());
        assert!(source_admission_heuristic(&[vec![0, 1]], 2).is_err());
    }

    #[test]
    fn limits_and_bad_source_fail_closed() {
        assert!(simplify_source(&[vec![1, 2], vec![1, -2]], 2, 1, 100)
            .unwrap().is_none());
        assert!(simplify_source(&[vec![1, 2], vec![1, -2]], 2, 100, 1)
            .unwrap().is_none());
        assert!(simplify_source(&[vec![3]], 2, 10, 100).is_err());
        assert!(simplify_source(&[vec![0]], 2, 10, 100).is_err());
    }
}
