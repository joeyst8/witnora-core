//! R-077: explicit finite auxiliary violation tensor bridge and local scopes.
//! Exponential oracle strictly bounded; no general contraction algorithm.
use crate::eth_clause_violation_parity::{violation_mask,parity_accepts};
use num_bigint::BigUint;
use num_traits::Zero;
use std::collections::{BTreeMap, BTreeSet};

pub fn local_scopes(source:&[Vec<i32>],nvars:usize,rows:&[Vec<usize>])
    ->Result<Vec<Vec<usize>>,String> {
    let mut out=Vec::new();
    for (j,clause) in source.iter().enumerate() {
        let mut scope=clause.iter().map(|lit|lit.unsigned_abs() as usize)
            .collect::<BTreeSet<_>>();
        scope.insert(nvars+j+1);
        out.push(scope.into_iter().collect());
    }
    for row in rows {
        if row.iter().any(|&j|j>=source.len()) {return Err("invalid parity row".into());}
        out.push(row.iter().map(|&j|nvars+j+1).collect::<BTreeSet<_>>()
            .into_iter().collect());
    }
    Ok(out)
}

pub fn direct_scopes(source:&[Vec<i32>],rows:&[Vec<usize>])
    ->Result<Vec<Vec<usize>>,String> {
    let mut out=Vec::new();
    for row in rows {
        let mut scope=BTreeSet::new();
        for &j in row {
            let clause=source.get(j).ok_or("invalid parity row")?;
            scope.extend(clause.iter().map(|lit|lit.unsigned_abs() as usize));
        }
        out.push(scope.into_iter().collect());
    }
    Ok(out)
}

pub fn exact_source_models(source:&[Vec<i32>],nvars:usize,max_variables:usize)
    ->Result<u64,String> {
    if nvars>max_variables || nvars>14 {return Err("exhaustive model oracle restricted".into());}
    let mut count=0;
    for x in 0..(1usize<<nvars) {
        if violation_mask(source,&BigUint::from(x))?.is_zero() {count+=1;}
    }
    Ok(count)
}

pub fn weight_profile(source:&[Vec<i32>],nvars:usize,rows:&[Vec<usize>],
    max_variables:usize)->Result<Vec<u64>,String> {
    if nvars>max_variables || nvars>14 {return Err("exhaustive auxiliary bridge restricted".into());}
    if rows.iter().flatten().any(|&j|j>=source.len()) {return Err("invalid sparse row".into());}
    let mut coefficients=vec![0u64;source.len()+1];
    for x in 0..(1usize<<nvars) {
        let violations=violation_mask(source,&BigUint::from(x))?;
        if parity_accepts(&violations,rows) {
            let weight=violations.iter_u32_digits().map(|d|d.count_ones() as usize).sum::<usize>();
            coefficients[weight]+=1;
        }
    }
    Ok(coefficients)
}

/// W-CROSSDOMAIN-006: exact source-CNF violation-energy polynomial using
/// disconnected primal-graph components. P(q) = sum_x q^(violated clauses).
/// This is established factor-graph/sum-product mathematics, not a novel
/// general counting algorithm. No parity rows are imposed in this variant.
pub fn factorized_violation_profile(
    source: &[Vec<i32>], nvars: usize, max_component_variables: usize,
) -> Result<Vec<u64>, String> {
    if nvars > 32 || source.len() > 64 || max_component_variables == 0
        || max_component_variables > 14 {
        return Err("unsupported component/variable/column cap".into());
    }
    let mut parent = (0..nvars).collect::<Vec<_>>();
    fn root(parent: &mut [usize], mut v: usize) -> usize {
        while parent[v] != v {
            let next = parent[v];
            parent[v] = parent[next];
            v = parent[v];
        }
        v
    }
    let mut supports = Vec::new();
    let mut empty_clauses = 0usize;
    for clause in source {
        if clause.is_empty() { empty_clauses += 1; continue; }
        let mut support = BTreeSet::new();
        for &lit in clause {
            if lit == 0 || lit == i32::MIN || lit.unsigned_abs() as usize > nvars {
                return Err("literal outside source variable universe".into());
            }
            support.insert(lit.unsigned_abs() as usize - 1);
        }
        let first = *support.iter().next().ok_or("unexpected empty support")?;
        for &v in support.iter().skip(1) {
            let a = root(&mut parent, first);
            let b = root(&mut parent, v);
            if a != b { parent[b] = a; }
        }
        supports.push((clause, first));
    }
    let mut variables: BTreeMap<usize, Vec<usize>> = BTreeMap::new();
    for v in 0..nvars {
        variables.entry(root(&mut parent, v)).or_default().push(v);
    }
    let mut clauses: BTreeMap<usize, Vec<&Vec<i32>>> = BTreeMap::new();
    for &(clause, first) in &supports {
        clauses.entry(root(&mut parent, first)).or_default().push(clause);
    }
    let mut global = vec![1u64];
    for (component, vars) in variables {
        if vars.len() > max_component_variables {
            return Err("component exceeds exact enumeration cap".into());
        }
        let local_clauses = clauses.remove(&component).unwrap_or_default();
        let mut local = vec![0u64; local_clauses.len() + 1];
        for assignment in 0..(1usize << vars.len()) {
            let mut violations = 0;
            for clause in &local_clauses {
                let satisfied = clause.iter().any(|&lit| {
                    let var = lit.unsigned_abs() as usize - 1;
                    let position = vars.binary_search(&var).expect("component scopes validated");
                    let value = assignment & (1usize << position) != 0;
                    value == (lit > 0)
                });
                if !satisfied { violations += 1; }
            }
            local[violations] = local[violations].checked_add(1)
                .ok_or("local coefficient overflow")?;
        }
        let mut product = vec![0u64; global.len() + local.len() - 1];
        for (i, &left) in global.iter().enumerate() {
            for (j, &right) in local.iter().enumerate() {
                product[i + j] = product[i + j]
                    .checked_add(left.checked_mul(right).ok_or("coefficient multiplication overflow")?)
                    .ok_or("coefficient addition overflow")?;
            }
        }
        global = product;
    }
    let mut result = vec![0u64; source.len() + 1];
    for (degree, coefficient) in global.into_iter().enumerate() {
        result[degree + empty_clauses] = coefficient;
    }
    Ok(result)
}

/// W-CROSSDOMAIN-007: exact cutset conditioning over one-based source-variable
/// IDs. Pin separator assignments, remove each fixed variable from the source
/// universe, factor each residual polynomial, and sum branch coefficients.
/// Established cutset-conditioning mathematics; no general treewidth guarantee.
pub fn conditioned_violation_profile(
    source: &[Vec<i32>], nvars: usize, separator: &[usize],
    max_component_variables: usize, max_separator_variables: usize,
) -> Result<Vec<u64>, String> {
    if nvars > 32 || source.len() > 64 || max_separator_variables > 8
        || separator.len() > max_separator_variables {
        return Err("unsupported separator/variable/column cap".into());
    }
    let mut separator_positions = BTreeMap::new();
    for (position, &variable) in separator.iter().enumerate() {
        if variable == 0 || variable > nvars
            || separator_positions.insert(variable, position).is_some() {
            return Err("separator must contain distinct in-range one-based IDs".into());
        }
    }
    for clause in source {
        for &literal in clause {
            if literal == 0 || literal == i32::MIN
                || literal.unsigned_abs() as usize > nvars {
                return Err("literal outside source variable universe".into());
            }
        }
    }
    let mut remap = vec![0usize; nvars + 1];
    let mut residual_nvars = 0usize;
    for original in 1..=nvars {
        if !separator_positions.contains_key(&original) {
            residual_nvars += 1;
            remap[original] = residual_nvars;
        }
    }
    let mut answer = vec![0u64; source.len() + 1];
    for assignment in 0..(1usize << separator.len()) {
        let mut residual = Vec::with_capacity(source.len());
        for clause in source {
            let mut remaining = Vec::new();
            let mut satisfied_by_separator = false;
            for &literal in clause {
                let original = literal.unsigned_abs() as usize;
                if let Some(&position) = separator_positions.get(&original) {
                    let fixed_value = (assignment & (1usize << position)) != 0;
                    if fixed_value == (literal > 0) {
                        satisfied_by_separator = true;
                        break;
                    }
                } else {
                    let new_id = remap[original] as i32;
                    remaining.push(if literal > 0 {new_id} else {-new_id});
                }
            }
            if !satisfied_by_separator { residual.push(remaining); }
        }
        let local = factorized_violation_profile(
            &residual, residual_nvars, max_component_variables)?;
        for (degree, coefficient) in local.into_iter().enumerate() {
            answer[degree] = answer[degree].checked_add(coefficient)
                .ok_or("conditional coefficient addition overflow")?;
        }
    }
    Ok(answer)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn zero_coefficient_and_locality() {
        let source=vec![vec![1],vec![2]];
        let rows=vec![vec![0,1]];
        assert_eq!(exact_source_models(&source,2,14).unwrap(),1);
        assert_eq!(weight_profile(&source,2,&rows,14).unwrap(),vec![1,0,1]);
        assert_eq!(local_scopes(&source,2,&rows).unwrap(),
            vec![vec![1,3],vec![2,4],vec![3,4]]);
        assert_eq!(direct_scopes(&source,&rows).unwrap(),vec![vec![1,2]]);
    }

    #[test]
    fn factorized_profile_matches_independent_small_exhaustive_oracle() {
        let mut state = 91u64;
        let mut next = || {
            state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
            state >> 32
        };
        for n in 1..=8usize {
            for _ in 0..64 {
                let mut source = Vec::new();
                for _ in 0..(n + 3) {
                    let width = next() as usize % 4;
                    let mut clause = Vec::new();
                    for _ in 0..width {
                        let variable = (next() as usize % n + 1) as i32;
                        clause.push(if next() & 1 == 0 { variable } else { -variable });
                    }
                    source.push(clause);
                }
                let expected = weight_profile(&source, n, &[], 14).unwrap();
                let actual = factorized_violation_profile(&source, n, 14).unwrap();
                assert_eq!(actual, expected);
            }
        }
    }

    #[test]
    fn twelve_independent_binary_clauses_match_analytic_partition_polynomial() {
        let source = (0..12).map(|j| vec![(2*j+1) as i32, (2*j+2) as i32])
            .collect::<Vec<_>>();
        let coefficients = factorized_violation_profile(&source, 24, 2).unwrap();
        let mut choose = 1u64;
        for k in 0..=12usize {
            let expected = choose * 3u64.pow((12-k) as u32);
            assert_eq!(coefficients[k], expected, "degree {k}");
            if k < 12 { choose = choose * (12-k) as u64 / (k+1) as u64; }
        }
        assert_eq!(coefficients[0], 3u64.pow(12));
        assert!(factorized_violation_profile(&source, 24, 1).is_err());
    }

    #[test]
    fn empty_clauses_and_unused_variables_are_counted_exactly() {
        assert_eq!(factorized_violation_profile(&[vec![], vec![]], 0, 2).unwrap(),
                   vec![0, 0, 1]);
        assert_eq!(factorized_violation_profile(&[vec![], vec![1,-1], vec![2]], 2, 2)
                       .unwrap(), vec![0, 2, 2, 0]);
        assert_eq!(factorized_violation_profile(&[], 32, 1).unwrap(),
                   vec![1u64 << 32]);
    }

    #[test]
    fn connected_star_cutset_has_exact_analytic_polynomial() {
        let source = (2..=25).map(|leaf| vec![1, leaf]).collect::<Vec<_>>();
        assert!(factorized_violation_profile(&source, 25, 1).is_err());
        let profile = conditioned_violation_profile(&source, 25, &[1], 1, 1).unwrap();
        let mut choose = 1u64;
        for degree in 0..=24usize {
            let expected = choose + if degree == 0 {1u64 << 24} else {0};
            assert_eq!(profile[degree], expected);
            if degree < 24 { choose = choose * (24-degree) as u64 / (degree+1) as u64; }
        }
        assert_eq!(profile[0], (1u64 << 24) + 1);
    }

    #[test]
    fn conditioned_polynomial_matches_exhaustive_source_oracle() {
        let mut state = 137u64;
        let mut next = || {
            state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
            state >> 32
        };
        for n in 1..=8usize {
            for _ in 0..48 {
                let mut source = Vec::new();
                for _ in 0..(n + 3) {
                    let width = next() as usize % 4;
                    source.push((0..width).map(|_| {
                        let variable = (next() as usize % n + 1) as i32;
                        if next() & 1 == 0 { variable } else { -variable }
                    }).collect::<Vec<_>>());
                }
                let separator = if n == 1 {vec![1]} else {vec![2, 1]};
                let expected = weight_profile(&source, n, &[], 14).unwrap();
                let actual = conditioned_violation_profile(&source, n, &separator, 14, 2).unwrap();
                assert_eq!(actual, expected);
            }
        }
    }

    #[test]
    fn conditioned_polynomial_rejects_invalid_separator() {
        assert!(conditioned_violation_profile(&[vec![1]], 1, &[1,1], 1, 2).is_err());
        assert!(conditioned_violation_profile(&[vec![1]], 1, &[2], 1, 1).is_err());
        assert!(conditioned_violation_profile(&[vec![0]], 1, &[1], 1, 1).is_err());
        assert!(conditioned_violation_profile(&[vec![1]], 1, &[1], 1, 0).is_err());
    }
}
