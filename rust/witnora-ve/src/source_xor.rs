//! Exact source-CNF to bounded (k<=3) XOR extraction.
//!
//! A group of clauses on the same k-variable support is removed only
//! when it contains the ENTIRE CNF blocking the wrong XOR parity.
//! This is an equivalence of complete satisfying-assignment sets,
//! not a heuristic parity guess. Incomplete groups remain in source.

use num_bigint::BigUint;
use num_traits::{One, Zero};
use std::collections::BTreeSet;

use crate::source_preprocess::normalize;

#[derive(Debug, PartialEq, Eq)]
pub struct XorExtraction {
    pub rows: Vec<(BigUint, u32)>,
    pub residual_clauses: Vec<Vec<i32>>,
}

/// Reproduce Python's exact small-k XOR recognition (k=1..3).
/// Rows use arbitrary-precision masks because nvars can reach 256.
pub fn extract_small_xors(
    raw: &[Vec<i32>], nvars: u32,
) -> Result<XorExtraction, String> {
    if nvars > 256 {
        return Err("XOR extractor supports nvars in 0..256".into());
    }
    let canon = normalize(raw.to_vec(), nvars)?;
    let mut clauses: BTreeSet<Vec<i32>> = canon.into_iter().collect();
    let mut supports: BTreeSet<Vec<u32>> = BTreeSet::new();
    for clause in &clauses {
        if (1..=3).contains(&clause.len()) {
            supports.insert(clause.iter().map(|lit| lit.unsigned_abs()).collect());
        }
    }
    let mut rows = Vec::new();
    for support in supports {
        let k = support.len();
        for rhs in 0..=1u32 {
            let mut expected = BTreeSet::new();
            for bits in 0..(1usize << k) {
                if bits.count_ones() % 2 == rhs {
                    continue;
                }
                let mut clause = Vec::with_capacity(k);
                for (index, &v) in support.iter().enumerate() {
                    clause.push(if bits & (1 << index) == 0 {
                        v as i32
                    } else {
                        -(v as i32)
                    });
                }
                expected.insert(clause);
            }
            if expected.is_subset(&clauses) {
                let mut mask = BigUint::zero();
                for &v in &support {
                    mask |= BigUint::one() << ((v - 1) as usize);
                }
                rows.push((mask, rhs));
                for clause in expected {
                    clauses.remove(&clause);
                }
            }
        }
    }
    let mut residual_clauses: Vec<Vec<i32>> = clauses.into_iter().collect();
    residual_clauses.sort_by(|a, b| a.len().cmp(&b.len()).then_with(|| a.cmp(b)));
    Ok(XorExtraction { rows, residual_clauses })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn full_models(clauses: &[Vec<i32>], nvars: usize) -> Vec<usize> {
        (0..(1 << nvars)).filter(|&mask| {
            clauses.iter().all(|clause| clause.iter().any(|&lit| {
                let assignment = mask & (1 << (lit.unsigned_abs() as usize - 1)) != 0;
                assignment == (lit > 0)
            }))
        }).collect()
    }

    fn extracted_models(out: &XorExtraction, nvars: usize) -> Vec<usize> {
        (0..(1 << nvars)).filter(|&mask| {
            out.rows.iter().all(|(row, rhs)| {
                let mut xor = 0u32;
                for v in 0..nvars {
                    if ((row >> v) & BigUint::one()) == BigUint::one()
                        && mask & (1 << v) != 0 {
                        xor ^= 1;
                    }
                }
                xor == *rhs
            }) && out.residual_clauses.iter().all(|clause|
                clause.iter().any(|&lit| {
                    let assignment = mask & (1 << (lit.unsigned_abs() as usize - 1)) != 0;
                    assignment == (lit > 0)
                }))
        }).collect()
    }

    #[test]
    fn exact_parity_and_incomplete_blocks() {
        let parity_two = vec![vec![1, 2], vec![-1, -2]];
        let got = extract_small_xors(&parity_two, 3).unwrap();
        assert_eq!(got.rows, vec![(BigUint::from(3u32), 1u32)]);
        assert!(got.residual_clauses.is_empty());
        let partial = extract_small_xors(&[vec![1, 2]], 3).unwrap();
        assert!(partial.rows.is_empty());
        assert_eq!(partial.residual_clauses, vec![vec![1, 2]]);
        let both = extract_small_xors(&[
            vec![1, 2], vec![1, -2], vec![-1, 2], vec![-1, -2],
        ], 2).unwrap();
        assert_eq!(both.rows.len(), 2);
        assert!(both.residual_clauses.is_empty());
        assert!(full_models(&parity_two, 3) == extracted_models(&got, 3));
        assert!(full_models(&[
            vec![1, 2], vec![1, -2], vec![-1, 2], vec![-1, -2],
        ], 2) == extracted_models(&both, 2));
    }

    #[test]
    fn exact_random_full_model_sets() {
        let mut state = 5112026u64;
        let mut random = || {
            state = state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            (state >> 32) as usize
        };
        for n in 2..=8usize {
            for _ in 0..35 {
                let mut clauses = Vec::new();
                for _ in 0..(random() % 13) {
                    let mut clause = Vec::new();
                    for _ in 0..(random() % 5) {
                        let v = 1 + random() % n;
                        clause.push(if random() & 1 == 0 { v as i32 } else { -(v as i32) });
                    }
                    clauses.push(clause);
                }
                let out = extract_small_xors(&clauses, n as u32).unwrap();
                assert_eq!(full_models(&clauses, n), extracted_models(&out, n));
            }
        }
    }

    #[test]
    fn arbitrary_precision_and_bad_source() {
        let source = vec![vec![256]];
        let got = extract_small_xors(&source, 256).unwrap();
        assert_eq!(got.rows, vec![(BigUint::one() << 255usize, 1)]);
        assert!(got.residual_clauses.is_empty());
        assert!(extract_small_xors(&[vec![0]], 2).is_err());
        assert!(extract_small_xors(&[vec![257]], 256).is_err());
    }
}
