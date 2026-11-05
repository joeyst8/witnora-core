//! R-008: One-call native exact CNF source-to-count composition.
//!
//! This links the previously differential-checked Rust kernels for
//! source normalization, small XOR extraction, affine projection,
//! sparse Fourier expansion, and right-hand Walsh inclusion-exclusion.
//! The result is exact or None on a declared finite resource cap.
//! Only the bounded inclusion-exclusion coefficient family is admitted.

use num_bigint::{BigInt, BigUint};
use num_traits::{One, Zero};
use std::collections::BTreeSet;

use crate::left_affine::project_and_expand;
use crate::right_walsh::right_walsh_coefficients;
use crate::source_preprocess::{simplify_source, source_admission_heuristic};
use crate::source_xor::extract_small_xors;

#[derive(Debug, PartialEq, Eq)]
pub struct FusedSourceCount {
    pub models: BigUint,
    pub extracted_affine_rows: usize,
    pub residual_clauses: usize,
    pub boundary_variables: usize,
    pub internal_variables: usize,
    pub internal_free_variables: usize,
    pub left_fourier_terms: usize,
    pub right_violation_terms: usize,
    pub right_components: usize,
    pub source_preprocess_skipped: bool,
    pub source_preprocess_passes: usize,
    pub right_subset_operations: u64,
}

/// Return a normalized violation pattern for the residual right CNF.
/// None denotes an explicit empty clause / contradictory CNF.
/// The source XOR extractor already validates and canonicalizes clauses.
fn violation_patterns(
    residual: &[Vec<i32>],
) -> Option<Vec<(BigUint, BigUint)>> {
    let mut out = Vec::with_capacity(residual.len());
    for clause in residual {
        if clause.is_empty() {
            return None;
        }
        let mut zeros = BigUint::zero();
        let mut ones = BigUint::zero();
        for &lit in clause {
            let bit = BigUint::one() << ((lit.unsigned_abs() - 1) as usize);
            if lit > 0 { zeros |= bit; } else { ones |= bit; }
        }
        out.push((zeros, ones));
    }
    Some(out)
}

/// End-to-end exact count over nvars original source variables.
/// All flags and budgets are explicit; the native route never falls
/// back to Python or estimates a count.
///
/// `preprocess` is one of: none, rust_consensus, rust_adaptive.
pub fn count_fused_source(
    source: &[Vec<i32>],
    nvars: u32,
    preprocess: &str,
    max_preprocess_passes: usize,
    max_preprocess_clause_visits: usize,
    max_spectrum_terms: usize,
    max_inclusion_subsets: usize,
    max_coefficient_operations: u64,
) -> Result<Option<FusedSourceCount>, String> {
    if nvars > 256 || max_spectrum_terms == 0
        || max_coefficient_operations == 0
    {
        return Err("invalid fused source universe or counting budget".into());
    }
    let (normalized, skipped, passes) = match preprocess {
        "none" => (source.to_vec(), true, 0),
        "rust_consensus" => {
            let Some(out) = simplify_source(
                source, nvars, max_preprocess_passes,
                max_preprocess_clause_visits,
            )? else { return Ok(None); };
            (out.clauses, false, out.passes)
        }
        "rust_adaptive" => {
            let admitted = source_admission_heuristic(source, nvars)?;
            if !admitted {
                if source.len() > max_preprocess_clause_visits
                    || max_preprocess_passes == 0
                    || max_preprocess_clause_visits == 0
                {
                    return Ok(None);
                }
                (source.to_vec(), true, 0)
            } else {
                let Some(out) = simplify_source(
                    source, nvars, max_preprocess_passes,
                    max_preprocess_clause_visits,
                )? else { return Ok(None); };
                (out.clauses, false, out.passes)
            }
        }
        _ => return Err("unknown exact fused source preprocessor".into()),
    };

    let extracted = extract_small_xors(&normalized, nvars)?;
    let boundary: Vec<u32> = extracted.residual_clauses.iter()
        .flat_map(|clause| clause.iter().map(|lit| lit.unsigned_abs()))
        .collect::<BTreeSet<_>>()
        .into_iter().collect();
    let bset: BTreeSet<u32> = boundary.iter().copied().collect();
    let internal: Vec<u32> = (1..=nvars)
        .filter(|v| !bset.contains(v)).collect();
    let Some(left) = project_and_expand(
        &extracted.rows, &internal, &boundary, max_spectrum_terms,
    )? else { return Ok(None); };

    let modes: Vec<BigUint> = left.spectrum.iter()
        .map(|(mode, _, _)| mode.clone()).collect();
    let normalized_right = violation_patterns(&extracted.residual_clauses);
    let Some(right) = right_walsh_coefficients(
        normalized_right.as_deref(), &boundary, &modes,
        max_inclusion_subsets, max_coefficient_operations,
    )? else { return Ok(None); };
    if right.coefficients.len() != left.spectrum.len() {
        return Err("native source Walsh spectrum dimensions disagree".into());
    }

    // All fractions are dyadic. A common positive power-of-two
    // denominator exists, so the exact model count is an integer
    // obtained by multiplying by 2^|boundary| after contraction.
    let left_den = left.spectrum.first()
        .map(|(_, _, d)| d.clone()).unwrap_or_else(BigUint::one);
    let right_den = right.coefficients.iter()
        .map(|(_, den)| den).max().cloned().unwrap_or_else(BigUint::one);
    let target_den = &left_den * &right_den;
    let mut numerator = BigInt::zero();
    for ((_, lnum, lden), (rnum, rden)) in left.spectrum.iter()
        .zip(&right.coefficients)
    {
        if lnum.is_zero() || rnum.is_zero() { continue; }
        let current_den = lden * rden;
        if (&target_den % &current_den) != BigUint::zero() {
            return Err("non-dyadic Fourier denominator invariant".into());
        }
        let factor = &target_den / &current_den;
        numerator += lnum * rnum * BigInt::from(factor);
    }
    numerator <<= boundary.len();
    let denominator = BigInt::from(target_den);
    if numerator < BigInt::zero() || (&numerator % &denominator) != BigInt::zero() {
        return Err("fused exact source count is not a nonnegative integer".into());
    }
    let models = (&numerator / &denominator).to_biguint()
        .ok_or_else(|| "negative fused model count".to_string())?;
    Ok(Some(FusedSourceCount {
        models,
        extracted_affine_rows: extracted.rows.len(),
        residual_clauses: extracted.residual_clauses.len(),
        boundary_variables: boundary.len(),
        internal_variables: internal.len(),
        internal_free_variables: left.internal_free,
        left_fourier_terms: left.spectrum.len(),
        right_violation_terms: right.compatible_terms,
        right_components: right.components,
        source_preprocess_skipped: skipped,
        source_preprocess_passes: passes,
        right_subset_operations: right.subset_operations,
    }))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn models(source: &[Vec<i32>], nvars: usize) -> usize {
        (0..(1usize << nvars)).filter(|&mask| source.iter().all(
            |clause| clause.iter().any(|&lit| {
                let bit = mask & (1usize << (lit.unsigned_abs() as usize - 1)) != 0;
                bit == (lit > 0)
            })
        )).count()
    }

    fn count(source: &[Vec<i32>], n: u32, mode: &str) -> Option<FusedSourceCount> {
        count_fused_source(source, n, mode, 64, 1000000, 512, 8192, 10000000)
            .unwrap()
    }

    #[test]
    fn empty_unsat_and_explicit_variables() {
        assert_eq!(count(&[], 0, "none").unwrap().models, BigUint::one());
        assert_eq!(count(&[], 4, "rust_adaptive").unwrap().models,
                   BigUint::from(16u32));
        assert_eq!(count(&[vec![]], 4, "none").unwrap().models,
                   BigUint::zero());
        assert_eq!(count(&[vec![1], vec![-1]], 4, "rust_consensus")
                   .unwrap().models, BigUint::zero());
        assert_eq!(count(&[vec![1, -1]], 4, "none").unwrap().models,
                   BigUint::from(16u32));
    }

    #[test]
    fn seeded_random_full_source_truth_tables() {
        let mut seed = 8082026u64;
        let mut next = || {
            seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            (seed >> 32) as usize
        };
        for n in 2..=8usize {
            for _ in 0..30 {
                let mut source = Vec::new();
                for _ in 0..(next() % 9) {
                    let mut clause = Vec::new();
                    for _ in 0..(next() % 5) {
                        let v = 1 + next() % n;
                        clause.push(if next() & 1 == 0 { v as i32 } else { -(v as i32) });
                    }
                    source.push(clause);
                }
                let expected = BigUint::from(models(&source, n));
                for mode in ["none", "rust_consensus", "rust_adaptive"] {
                    let got = count(&source, n as u32, mode).unwrap();
                    assert_eq!(got.models, expected,
                               "n={n} mode={mode} source={source:?}");
                }
            }
        }
    }

    #[test]
    fn forcing_64_recover_and_fail_closed_caps() {
        let n = 64i32;
        let mut source = Vec::new();
        for u in 1..n {
            for v in (u + 1)..=n {
                source.push(vec![u, v]);
                source.push(vec![u, -v]);
            }
        }
        for v in 1..n { source.push(vec![v]); }
        let out = count(&source, n as u32, "rust_adaptive").unwrap();
        assert_eq!(out.models, BigUint::from(2u32));
        assert!(out.residual_clauses < source.len());
        assert!(count_fused_source(&source, 64, "rust_consensus", 1, 1000000,
                                   512, 8192, 1000000).unwrap().is_none());
        assert!(count_fused_source(&[vec![1, 2]], 2, "none", 64, 1000, 512,
                                   1, 100000).unwrap().is_none());
        assert!(count_fused_source(&[vec![3]], 2, "none", 64, 1000, 512,
                                   8192, 100000).is_err());
    }
}
