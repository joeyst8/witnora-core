//! W-CROSSDOMAIN-008: exact Fourier projection of source-clause violation
//! weight profiles onto GF(2) parity syndromes. This is standard character
//! orthogonality / MacWilliams-style sum-product algebra, not a #SAT theorem.

use std::collections::{BTreeMap, BTreeSet};

fn root(parent: &mut [usize], mut v: usize) -> usize {
    while parent[v] != v {
        let next = parent[v];
        parent[v] = parent[next];
        v = parent[v];
    }
    v
}

fn hadamard(values: &mut [i64]) -> Result<(), String> {
    let mut stride = 1usize;
    while stride < values.len() {
        for block in (0..values.len()).step_by(stride * 2) {
            for offset in 0..stride {
                let left = values[block + offset];
                let right = values[block + offset + stride];
                values[block + offset] = left.checked_add(right)
                    .ok_or("Fourier transform addition overflow")?;
                values[block + offset + stride] = left.checked_sub(right)
                    .ok_or("Fourier transform subtraction overflow")?;
            }
        }
        stride *= 2;
    }
    Ok(())
}

/// Return the exact coefficient at each number of violated CNF source clauses,
/// restricted to assignments whose clause-violation mask has parity `rhs`
/// under the given zero-based clause-index rows. Rows may have duplicates:
/// duplicate indices cancel in GF(2). All arithmetic and caps are explicit.
///
/// Each disconnected primal component supplies a weight/syndrome histogram;
/// Walsh-Hadamard on syndrome converts XOR convolution into multiplication.
pub fn fourier_parity_violation_profile(
    source: &[Vec<i32>], nvars: usize, rows: &[Vec<usize>], rhs: &[bool],
    max_component_variables: usize,
) -> Result<Vec<u64>, String> {
    if nvars > 32 || source.len() > 64 || rows.len() != rhs.len()
        || rows.len() > 8 || max_component_variables == 0
        || max_component_variables > 14 {
        return Err("unsupported source/parity/component cap".into());
    }
    let modes = 1usize << rows.len();
    let mut column_syndrome = vec![0usize; source.len()];
    for (index, row) in rows.iter().enumerate() {
        for &clause_id in row {
            if clause_id >= source.len() {
                return Err("parity row references a missing source clause".into());
            }
            column_syndrome[clause_id] ^= 1usize << index;
        }
    }
    let mut target_syndrome = 0usize;
    for (index, &bit) in rhs.iter().enumerate() {
        if bit { target_syndrome |= 1usize << index; }
    }

    let mut parent = (0..nvars).collect::<Vec<_>>();
    let mut supported = Vec::new();
    let mut empty_count = 0usize;
    let mut empty_syndrome = 0usize;
    for (index, clause) in source.iter().enumerate() {
        if clause.is_empty() {
            empty_count += 1;
            empty_syndrome ^= column_syndrome[index];
            continue;
        }
        let mut support = BTreeSet::new();
        for &literal in clause {
            if literal == 0 || literal == i32::MIN
                || literal.unsigned_abs() as usize > nvars {
                return Err("literal outside source variable universe".into());
            }
            support.insert(literal.unsigned_abs() as usize - 1);
        }
        let first = *support.iter().next().ok_or("unexpected empty support")?;
        for &variable in support.iter().skip(1) {
            let a = root(&mut parent, first);
            let b = root(&mut parent, variable);
            if a != b { parent[b] = a; }
        }
        supported.push((index, clause, first));
    }

    let mut components: BTreeMap<usize, Vec<usize>> = BTreeMap::new();
    for variable in 0..nvars {
        components.entry(root(&mut parent, variable))
            .or_default().push(variable);
    }
    let mut grouped: BTreeMap<usize, Vec<(usize, &Vec<i32>)>> = BTreeMap::new();
    for &(index, clause, first) in &supported {
        grouped.entry(root(&mut parent, first))
            .or_default().push((index, clause));
    }

    // Global polynomial in transformed syndrome coordinates, with coefficients
    // indexed [number of nonempty-clause violations][Fourier frequency].
    let mut global = vec![vec![1i64; modes]];
    for (component, variables) in components {
        if variables.len() > max_component_variables {
            return Err("component exceeds exact enumeration cap".into());
        }
        let clauses = grouped.remove(&component).unwrap_or_default();
        let mut local = vec![vec![0i64; modes]; clauses.len() + 1];
        for assignment in 0..(1usize << variables.len()) {
            let mut weight = 0usize;
            let mut syndrome = 0usize;
            for &(source_index, clause) in &clauses {
                let satisfied = clause.iter().any(|&literal| {
                    let variable = literal.unsigned_abs() as usize - 1;
                    let position = variables.binary_search(&variable)
                        .expect("validated component contains clause scope");
                    let value = assignment & (1usize << position) != 0;
                    value == (literal > 0)
                });
                if !satisfied {
                    weight += 1;
                    syndrome ^= column_syndrome[source_index];
                }
            }
            local[weight][syndrome] = local[weight][syndrome].checked_add(1)
                .ok_or("local histogram overflow")?;
        }
        for coefficients in &mut local { hadamard(coefficients)?; }
        let mut product = vec![vec![0i64; modes]; global.len() + local.len() - 1];
        for (i, left) in global.iter().enumerate() {
            for (j, right) in local.iter().enumerate() {
                for frequency in 0..modes {
                    let term = left[frequency].checked_mul(right[frequency])
                        .ok_or("transformed polynomial multiplication overflow")?;
                    product[i + j][frequency] = product[i + j][frequency]
                        .checked_add(term)
                        .ok_or("transformed polynomial addition overflow")?;
                }
            }
        }
        global = product;
    }

    // Inverse Fourier *at the requested syndrome only*, including the fixed
    // syndrome of every empty clause. Exact divisibility is mandatory.
    let selected = target_syndrome ^ empty_syndrome;
    let mut answer = vec![0u64; source.len() + 1];
    for (degree, coefficients) in global.iter().enumerate() {
        let mut numerator = 0i64;
        for (frequency, &coefficient) in coefficients.iter().enumerate() {
            numerator = if ((frequency & selected).count_ones() & 1) == 0 {
                numerator.checked_add(coefficient)
            } else {
                numerator.checked_sub(coefficient)
            }.ok_or("Fourier projection overflow")?;
        }
        let denominator = modes as i64;
        if numerator % denominator != 0 {
            return Err("nonintegral Fourier projection".into());
        }
        let count = numerator / denominator;
        if count < 0 { return Err("negative Fourier projection".into()); }
        answer[degree + empty_count] = count as u64;
    }
    Ok(answer)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::aux_violation_tensors::{factorized_violation_profile, weight_profile};

    #[test]
    fn parity_free_reduces_to_independent_factorized_source_polynomial() {
        let source = vec![vec![1, 2], vec![], vec![-1], vec![3, -3]];
        assert_eq!(fourier_parity_violation_profile(&source, 3, &[], &[], 3).unwrap(),
                   factorized_violation_profile(&source, 3, 3).unwrap());
    }

    #[test]
    fn globally_coupled_twelve_clause_even_odd_parity_is_analytic() {
        let source = (0..12).map(|i| vec![2 * i + 1, 2 * i + 2])
            .collect::<Vec<_>>();
        let row = vec![(0..12).collect::<Vec<_>>()];
        let even = fourier_parity_violation_profile(&source, 24, &row, &[false], 2).unwrap();
        let odd = fourier_parity_violation_profile(&source, 24, &row, &[true], 2).unwrap();
        let mut choose = 1u64;
        for degree in 0..=12usize {
            let expected = choose * 3u64.pow((12 - degree) as u32);
            assert_eq!(even[degree], if degree % 2 == 0 {expected} else {0});
            assert_eq!(odd[degree], if degree % 2 == 1 {expected} else {0});
            if degree < 12 { choose = choose * (12 - degree) as u64 / (degree + 1) as u64; }
        }
        assert_eq!(even[0], 3u64.pow(12));
        assert_eq!(odd[0], 0);
    }

    #[test]
    fn finite_truth_table_matches_for_redundant_and_conflicting_parity_rows() {
        let source = vec![vec![], vec![1], vec![-1, 2], vec![2], vec![1, -1]];
        for rows in [vec![vec![], vec![0, 0]], vec![vec![0, 1, 3], vec![1, 3]],
                     vec![vec![0], vec![0]], vec![vec![0, 2, 2]]] {
            for target in 0..(1usize << rows.len()) {
                let rhs = (0..rows.len()).map(|i| target & (1 << i) != 0)
                    .collect::<Vec<_>>();
                let mut expected = vec![0u64; source.len() + 1];
                for assignment in 0..(1usize << 2) {
                    let violations = source.iter().map(|clause| !clause.iter().any(|&lit| {
                        let value = assignment & (1usize << (lit.unsigned_abs() as usize - 1)) != 0;
                        value == (lit > 0)
                    })).collect::<Vec<_>>();
                    if rows.iter().zip(&rhs).all(|(row, &bit)|
                        row.iter().filter(|&&index| violations[index]).count() % 2 == bit as usize) {
                        expected[violations.iter().filter(|&&v| v).count()] += 1;
                    }
                }
                assert_eq!(fourier_parity_violation_profile(&source, 2, &rows, &rhs, 2)
                           .unwrap(), expected);
            }
        }
        assert_eq!(fourier_parity_violation_profile(&source, 2, &[], &[], 2).unwrap(),
                   weight_profile(&source, 2, &[], 14).unwrap());
    }

    #[test]
    fn strict_validation_and_empty_source() {
        assert_eq!(fourier_parity_violation_profile(&[], 0, &[vec![]], &[false], 1)
                   .unwrap(), vec![1]);
        assert_eq!(fourier_parity_violation_profile(&[], 0, &[vec![]], &[true], 1)
                   .unwrap(), vec![0]);
        assert!(fourier_parity_violation_profile(&[vec![1]], 1, &[vec![1]], &[false], 1).is_err());
        assert!(fourier_parity_violation_profile(&[vec![0]], 1, &[], &[], 1).is_err());
        assert!(fourier_parity_violation_profile(&[vec![1]], 1, &[vec![0]], &[], 1).is_err());
    }

    #[test]
    fn identical_energy_profiles_can_have_distinct_triangle_syndrome_spectra() {
        // W-CROSSDOMAIN-009 exhaustive six-variable seven-clause witness;
        // both source formulas have the identical indexed primal graph.
        let source_a = vec![vec![1,2], vec![-1,3], vec![-1,4], vec![-2,-3],
                            vec![-2,5], vec![-4,6], vec![-5,-6]];
        let source_b = vec![vec![1,2], vec![1,3], vec![-1,4], vec![-2,-3],
                            vec![-2,5], vec![-4,6], vec![-5,-6]];
        let energy = vec![2,22,30,10,0,0,0,0];
        assert_eq!(fourier_parity_violation_profile(&source_a, 6, &[], &[], 6).unwrap(),
                   energy);
        assert_eq!(fourier_parity_violation_profile(&source_b, 6, &[], &[], 6).unwrap(),
                   energy);
        let cycle = vec![vec![0,1,3]];
        assert_eq!(fourier_parity_violation_profile(&source_a, 6, &cycle, &[false], 6)
                   .unwrap(), vec![2,12,2,0,0,0,0,0]);
        assert_eq!(fourier_parity_violation_profile(&source_b, 6, &cycle, &[false], 6)
                   .unwrap(), vec![2,16,10,4,0,0,0,0]);
    }
}
