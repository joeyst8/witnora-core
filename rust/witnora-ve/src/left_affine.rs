//! Exact GF(2) affine projection and sparse Walsh/Fourier expansion.
//!
//! This is standard Boolean linear algebra. Arbitrary-precision integer
//! numerators with a common 2^rank denominator avoid floating-point
//! rounding. Inconsistent rows yield an empty spectrum; budget refusal
//! yields None, never a fabricated count.

use num_bigint::{BigInt, BigUint};
use num_traits::{One, Zero};
use std::collections::BTreeMap;

#[derive(Debug, PartialEq, Eq)]
pub struct LeftAffineSpectrum {
    /// None iff the affine system is inconsistent.
    pub projected_rows: Option<Vec<(BigUint, u32)>>,
    pub internal_free: usize,
    pub spectrum: Vec<(BigUint, BigInt, BigUint)>,
}

fn variable_mask(variables: &[u32]) -> Result<BigUint, String> {
    if variables.len() > 256 {
        return Err("too many affine variables".into());
    }
    let mut mask = BigUint::zero();
    for &v in variables {
        if v == 0 || v > 256 {
            return Err("invalid GF(2) variable ID".into());
        }
        let bit = BigUint::one() << ((v - 1) as usize);
        if !(&mask & &bit).is_zero() {
            return Err("duplicate GF(2) variable ID".into());
        }
        mask |= bit;
    }
    Ok(mask)
}

/// Exact projection of internal variables followed by a budgeted sparse
/// boundary Walsh expansion. The expansion is the NUMBER of compatible
/// internal assignments per boundary assignment, not a probability.
/// The optional return is *only* a spectrum-size budget refusal.
pub fn project_and_expand(
    source_rows: &[(BigUint, u32)],
    internals: &[u32],
    boundary: &[u32],
    max_terms: usize,
) -> Result<Option<LeftAffineSpectrum>, String> {
    let i_mask = variable_mask(internals)?;
    let b_mask = variable_mask(boundary)?;
    if !(&i_mask & &b_mask).is_zero() {
        return Err("internal and boundary variable overlap".into());
    }
    let allowed = &i_mask | &b_mask;
    let mut internal_vars = internals.to_vec();
    let mut boundary_vars = boundary.to_vec();
    internal_vars.sort_unstable();
    boundary_vars.sort_unstable();

    let mut internal_pivots: BTreeMap<u32, (BigUint, u32)> = BTreeMap::new();
    let mut residual = Vec::new();
    for (support, rhs) in source_rows {
        if *rhs > 1 || (support & &allowed) != *support {
            return Err("invalid affine row or undeclared variable".into());
        }
        let mut mask = support.clone();
        let mut parity = *rhs;
        let mut pivoted = false;
        for &v in &internal_vars {
            let bit = BigUint::one() << ((v - 1) as usize);
            if (&mask & &bit).is_zero() {
                continue;
            }
            if let Some((older, value)) = internal_pivots.get(&v) {
                mask ^= older;
                parity ^= value;
            } else {
                internal_pivots.insert(v, (mask, parity));
                pivoted = true;
                break;
            }
        }
        if !pivoted {
            residual.push((mask, parity));
        }
    }

    let free = internals.len() - internal_pivots.len();
    let mut boundary_pivots: BTreeMap<u32, (BigUint, u32)> = BTreeMap::new();
    for (mut mask, mut parity) in residual {
        let mut pivoted = false;
        for &v in &boundary_vars {
            let bit = BigUint::one() << ((v - 1) as usize);
            if (&mask & &bit).is_zero() {
                continue;
            }
            if let Some((older, value)) = boundary_pivots.get(&v) {
                mask ^= older;
                parity ^= value;
            } else {
                boundary_pivots.insert(v, (mask, parity));
                pivoted = true;
                break;
            }
        }
        if !pivoted && parity != 0 {
            return Ok(Some(LeftAffineSpectrum {
                projected_rows: None,
                internal_free: free,
                spectrum: Vec::new(),
            }));
        }
    }

    if max_terms == 0 {
        return Err("max Fourier terms must be positive".into());
    }
    let projected_rows: Vec<(BigUint, u32)> =
        boundary_pivots.into_values().collect();
    let mut numerators: BTreeMap<BigUint, BigInt> = BTreeMap::new();
    numerators.insert(BigUint::zero(), BigInt::one() << free);
    let mut denominator = BigUint::one();

    for (support, rhs) in &projected_rows {
        let mut next: BTreeMap<BigUint, BigInt> = BTreeMap::new();
        for (mode, coef) in &numerators {
            *next.entry(mode.clone()).or_insert_with(BigInt::zero) += coef;
            let shifted = mode ^ support;
            let entry = next.entry(shifted).or_insert_with(BigInt::zero);
            if *rhs == 0 { *entry += coef; } else { *entry -= coef; }
        }
        next.retain(|_, value| !value.is_zero());
        if next.len() > max_terms {
            return Ok(None);
        }
        numerators = next;
        denominator <<= 1usize;
    }
    Ok(Some(LeftAffineSpectrum {
        projected_rows: Some(projected_rows),
        internal_free: free,
        spectrum: numerators.into_iter().map(|(mode, num)| (
            mode, num, denominator.clone(),
        )).collect(),
    }))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn parity(mask: &BigUint, assignment: usize) -> u32 {
        let both = mask & BigUint::from(assignment);
        both.to_u32_digits().iter().map(|x| x.count_ones()).sum::<u32>() & 1
    }

    fn brute_internal_completions(
        rows: &[(BigUint, u32)], nb: usize, ni: usize, boundary: usize,
    ) -> usize {
        (0..(1usize << ni)).filter(|i| {
            let assignment = boundary | (i << nb);
            rows.iter().all(|(mask, rhs)| parity(mask, assignment) == *rhs)
        }).count()
    }

    #[test]
    fn known_projection_free_internal_and_contradictions() {
        let rows = vec![
            (BigUint::from((1u32 << 12) | 3), 0),
            (BigUint::from((1u32 << 12) | 12), 0),
        ];
        let out = project_and_expand(
            &rows, &[13, 14], &(1..=12).collect::<Vec<_>>(), 16,
        ).unwrap().unwrap();
        assert_eq!(out.internal_free, 1);
        assert_eq!(out.projected_rows,
                   Some(vec![(BigUint::from(15u32), 0)]));
        assert_eq!(out.spectrum, vec![
            (BigUint::zero(), BigInt::from(2), BigUint::from(2u32)),
            (BigUint::from(15u32), BigInt::from(2), BigUint::from(2u32)),
        ]);
        let contradiction = project_and_expand(
            &[(BigUint::from(3u32), 0), (BigUint::from(3u32), 1)],
            &[], &[1, 2], 2,
        ).unwrap().unwrap();
        assert_eq!(contradiction.projected_rows, None);
        assert!(contradiction.spectrum.is_empty());
    }

    #[test]
    fn randomized_exact_internal_completion_fourier_differentials() {
        let mut seed = 700700u64;
        let mut next = || {
            seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            (seed >> 32) as usize
        };
        for nb in 1..=5usize {
            for ni in 0..=2usize {
                for _ in 0..35 {
                    let internals: Vec<u32> = ((nb + 1)..=(nb + ni)).map(|v| v as u32).collect();
                    let boundary: Vec<u32> = (1..=nb as u32).collect();
                    let mut rows = Vec::new();
                    for _ in 0..(next() % 8) {
                        let mut support = BigUint::zero();
                        for v in 1..=(nb + ni) {
                            if next() & 1 == 0 {
                                support |= BigUint::one() << (v - 1);
                            }
                        }
                        rows.push((support, (next() & 1) as u32));
                    }
                    let out = project_and_expand(
                        &rows, &internals, &boundary, 256,
                    ).unwrap().unwrap();
                    for b in 0..(1usize << nb) {
                        let expected = brute_internal_completions(&rows, nb, ni, b);
                        if out.projected_rows.is_none() {
                            assert_eq!(expected, 0);
                            continue;
                        }
                        let denominator = out.spectrum.first().unwrap().2.clone();
                        let mut numerator = BigInt::zero();
                        for (mode, num, den) in &out.spectrum {
                            assert_eq!(*den, denominator);
                            if parity(mode, b) == 0 { numerator += num; }
                            else { numerator -= num; }
                        }
                        assert_eq!(
                            numerator,
                            BigInt::from(expected) * BigInt::from(denominator.clone())
                        );
                    }
                }
            }
        }
    }

    #[test]
    fn caps_bad_inputs_and_variable_256() {
        let rows = vec![(BigUint::one(), 0), (BigUint::from(2u32), 0)];
        assert!(project_and_expand(&rows, &[], &[1, 2], 2).unwrap().is_none());
        assert!(project_and_expand(&[], &[1], &[1], 2).is_err());
        assert!(project_and_expand(&[(BigUint::from(4u32), 0)], &[], &[1, 2], 2).is_err());
        assert!(project_and_expand(&[(BigUint::from(1u32), 2)], &[], &[1], 2).is_err());
        let high = BigUint::one() << 255usize;
        let out = project_and_expand(&[(high.clone(), 1)], &[], &[256], 2)
            .unwrap().unwrap();
        assert_eq!(out.spectrum.len(), 2);
        assert_eq!(out.spectrum[0], (BigUint::zero(), BigInt::one(), 2u32.into()));
        assert_eq!(out.spectrum[1], (high, BigInt::from(-1), 2u32.into()));
    }
}
