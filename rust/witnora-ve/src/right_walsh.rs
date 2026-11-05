//! Exact CNF Walsh coefficient batch computation by component-wise
//! inclusion-exclusion. All coefficients are rational dyadics, represented
//! with arbitrary-precision integer numerators and power-of-two denominator.
//! This is standard inclusion-exclusion, not a new solver theorem.

use num_bigint::{BigInt, BigUint};
use num_traits::{One, Zero};
use std::collections::BTreeMap;

#[derive(Clone, Debug)]
struct Clause { zeros: BigUint, ones: BigUint }

#[derive(Debug, PartialEq, Eq)]
pub struct WalshBatch {
    pub coefficients: Vec<(BigInt, BigUint)>,
    pub compatible_terms: usize,
    pub components: usize,
    pub subset_operations: u64,
}

fn bit_count(x: &BigUint) -> usize {
    x.to_u32_digits().iter().map(|digit| digit.count_ones() as usize).sum()
}

fn variables(x: &BigUint) -> Vec<usize> {
    let mut ids = Vec::new();
    for (i, word) in x.to_u32_digits().iter().copied().enumerate() {
        let mut w = word;
        while w != 0 {
            let bit = w.trailing_zeros() as usize;
            ids.push(i * 32 + bit + 1);
            w &= w - 1;
        }
    }
    ids
}

fn find(parent: &mut [usize], v: usize) -> usize {
    if parent[v] != v {
        parent[v] = find(parent, parent[v]);
    }
    parent[v]
}

fn union(parent: &mut [usize], a: usize, b: usize) {
    let ra = find(parent, a);
    let rb = find(parent, b);
    if ra != rb { parent[rb] = ra; }
}

/// Exact Fourier coefficients of the indicator of a boundary CNF.
///
/// The clause pair (zeros,ones) describes the one assignment pattern
/// violating that clause; the masks must be disjoint and nonempty.
/// None as the clauses argument represents an explicit empty clause,
/// i.e. the constantly-false CNF. Some(empty) is constantly true.
/// The optional result signals a strict subset/operation cap refusal.
pub fn right_walsh_coefficients(
    normalized: Option<&[(BigUint, BigUint)]>,
    boundary: &[u32],
    modes: &[BigUint],
    max_subsets: usize,
    max_operations: u64,
) -> Result<Option<WalshBatch>, String> {
    if max_operations == 0 || boundary.len() > 256 {
        return Err("invalid native Walsh operation cap or boundary size".into());
    }
    let mut allowed = BigUint::zero();
    for &v in boundary {
        if v == 0 || v > 256 {
            return Err("invalid boundary ID".into());
        }
        let bit = BigUint::one() << ((v - 1) as usize);
        if (&allowed & &bit) != BigUint::zero() {
            return Err("duplicate boundary ID".into());
        }
        allowed |= bit;
    }
    for mode in modes {
        if (mode & &allowed) != *mode {
            return Err("Walsh mode outside declared boundary".into());
        }
    }
    let Some(source) = normalized else {
        return Ok(Some(WalshBatch {
            coefficients: modes.iter().map(|_| (BigInt::zero(), BigUint::one())).collect(),
            compatible_terms: 0, components: 1, subset_operations: 0,
        }));
    };
    if source.is_empty() {
        return Ok(Some(WalshBatch {
            coefficients: modes.iter().map(|mode| (
                if mode.is_zero() { BigInt::one() } else { BigInt::zero() },
                BigUint::one(),
            )).collect(),
            compatible_terms: 0, components: 0, subset_operations: 0,
        }));
    }

    let mut parent: Vec<usize> = (0..=256).collect();
    let mut clauses = Vec::with_capacity(source.len());
    for (z, o) in source {
        if !(z & o).is_zero() {
            return Err("conflicting forced zero/one bits in a clause".into());
        }
        let scope = z | o;
        if scope.is_zero() || (&scope & &allowed) != scope {
            return Err("invalid empty or nonboundary violation pattern".into());
        }
        let vars = variables(&scope);
        for &v in vars.iter().skip(1) { union(&mut parent, vars[0], v); }
        clauses.push(Clause { zeros: z.clone(), ones: o.clone() });
    }

    let mut groups: BTreeMap<usize, Vec<Clause>> = BTreeMap::new();
    let mut scopes: BTreeMap<usize, BigUint> = BTreeMap::new();
    for clause in clauses {
        let scope = &clause.zeros | &clause.ones;
        let first = variables(&scope)[0];
        let root = find(&mut parent, first);
        scopes.entry(root).or_insert_with(BigUint::zero);
        *scopes.get_mut(&root).unwrap() |= &scope;
        groups.entry(root).or_default().push(clause);
    }

    let mut remaining = max_subsets;
    let mut total_terms = 0usize;
    let mut total_ops = 0u64;
    let mut denominator_exponent = 0usize;
    let mut per_mode: Vec<BigInt> = modes.iter().map(|_| BigInt::one()).collect();
    let mut union_scope = BigUint::zero();
    let group_count = groups.len();

    for (root, group) in groups {
        let Some(subsets) = 1usize.checked_shl(group.len() as u32) else {
            return Ok(None);
        };
        if subsets > remaining {
            return Ok(None);
        }
        remaining -= subsets;
        let required = (subsets as u64).saturating_mul(modes.len() as u64);
        if required > max_operations.saturating_sub(total_ops) {
            return Ok(None);
        }
        total_ops += required;
        let scope = &scopes[&root];
        let width = bit_count(scope);
        denominator_exponent += width;
        union_scope |= scope;
        let local_modes: Vec<BigUint> = modes.iter().map(|m| m & scope).collect();
        let mut numerators: Vec<BigInt> = modes.iter().map(|_| BigInt::zero()).collect();

        for selected in 0..subsets {
            let mut zeros = BigUint::zero();
            let mut ones = BigUint::zero();
            let mut valid = true;
            for (i, clause) in group.iter().enumerate() {
                if selected & (1 << i) == 0 { continue; }
                zeros |= &clause.zeros;
                ones |= &clause.ones;
                if !(&zeros & &ones).is_zero() {
                    valid = false;
                    break;
                }
            }
            if !valid { continue; }
            total_terms += 1;
            let forced = &zeros | &ones;
            let weight = BigInt::one() << (width - bit_count(&forced));
            let selected_odd = selected.count_ones() & 1 != 0;
            for (index, m) in local_modes.iter().enumerate() {
                if (m & &forced) != *m { continue; }
                let odd = bit_count(&(m & &ones)) & 1 != 0;
                if selected_odd ^ odd {
                    numerators[index] -= &weight;
                } else {
                    numerators[index] += &weight;
                }
            }
        }
        for (result, next) in per_mode.iter_mut().zip(numerators) {
            *result *= next;
        }
    }
    let denominator = BigUint::one() << denominator_exponent;
    let coefficients = modes.iter().zip(per_mode).map(|(m, numerator)| {
        if (m & &union_scope) != *m {
            (BigInt::zero(), BigUint::one())
        } else {
            (numerator, denominator.clone())
        }
    }).collect();
    Ok(Some(WalshBatch {
        coefficients, compatible_terms: total_terms,
        components: group_count, subset_operations: total_ops,
    }))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn eval_cnf(source: &[(BigUint, BigUint)], mask: &BigUint) -> bool {
        source.iter().all(|(z, o)| {
            !((mask & z).is_zero() && (mask & o) == *o)
        })
    }

    fn brute_numerator(source: &[(BigUint, BigUint)], n: usize, mode: &BigUint) -> BigInt {
        let mut total = BigInt::zero();
        for packed in 0..(1usize << n) {
            let assignment = BigUint::from(packed);
            if eval_cnf(source, &assignment) {
                if bit_count(&(&assignment & mode)) & 1 == 0 { total += 1; }
                else { total -= 1; }
            }
        }
        total
    }

    #[test]
    fn empty_unsat_and_inconsistent_masks() {
        let vars = [1, 2];
        let modes = [BigUint::zero(), BigUint::one()];
        let empty = right_walsh_coefficients(Some(&[]), &vars, &modes, 4, 100)
            .unwrap().unwrap();
        assert_eq!(empty.coefficients[0], (BigInt::one(), BigUint::one()));
        assert_eq!(empty.coefficients[1], (BigInt::zero(), BigUint::one()));
        let unsat = right_walsh_coefficients(None, &vars, &modes, 4, 100)
            .unwrap().unwrap();
        assert!(unsat.coefficients.iter().all(|(n, _)| n.is_zero()));
        let bad = [(BigUint::one(), BigUint::one())];
        assert!(right_walsh_coefficients(Some(&bad), &vars, &modes, 4, 100).is_err());
    }

    #[test]
    fn signed_and_disconnected_component_brute_coefficients() {
        let cases: Vec<(usize, Vec<(BigUint, BigUint)>)> = vec![
            (3, vec![(1u32.into(), 0u32.into())]),
            (3, vec![(1u32.into(), 2u32.into())]),
            (4, vec![(1u32.into(), 2u32.into()), (4u32.into(), 8u32.into())]),
            (3, vec![(1u32.into(), 0u32.into()), (0u32.into(), 1u32.into())]),
        ];
        for (n, clauses) in cases {
            let boundary: Vec<u32> = (1..=n as u32).collect();
            let modes: Vec<BigUint> = (0..(1usize << n)).map(BigUint::from).collect();
            let out = right_walsh_coefficients(
                Some(&clauses), &boundary, &modes, 256, 1_000_000,
            ).unwrap().unwrap();
            for (mode, (num, denom)) in modes.iter().zip(out.coefficients.iter()) {
                assert_eq!(
                    num * BigInt::from(1u32 << n),
                    brute_numerator(&clauses, n, mode) * BigInt::from(denom.clone())
                );
            }
        }
    }

    #[test]
    fn random_small_full_walsh_spectra_and_caps() {
        let mut state = 322206u64;
        let mut next = || {
            state = state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            (state >> 32) as usize
        };
        for n in 2..=7usize {
            let boundary: Vec<u32> = (1..=n as u32).collect();
            for _ in 0..35 {
                let mut source = Vec::new();
                for _ in 0..(next() % 6) {
                    let mut z = BigUint::zero();
                    let mut o = BigUint::zero();
                    for _ in 0..(1 + next() % 3) {
                        let v = 1 + next() % n;
                        let bit = BigUint::one() << (v - 1);
                        if (&z & &bit).is_zero() && (&o & &bit).is_zero() {
                            if next() & 1 == 0 { z |= bit; }
                            else { o |= bit; }
                        }
                    }
                    if !(&z | &o).is_zero() { source.push((z, o)); }
                }
                let modes: Vec<BigUint> = (0..(1usize << n)).map(BigUint::from).collect();
                let Some(out) = right_walsh_coefficients(
                    Some(&source), &boundary, &modes, 1024, 1_000_000,
                ).unwrap() else { continue };
                for (mode, (num, denom)) in modes.iter().zip(out.coefficients.iter()) {
                    assert_eq!(
                        num * BigInt::from(1u32 << n),
                        brute_numerator(&source, n, mode) * BigInt::from(denom.clone())
                    );
                }
            }
        }
        let source = vec![(1u32.into(), 0u32.into())];
        assert!(right_walsh_coefficients(Some(&source), &[1], &[BigUint::zero()], 1, 100)
            .unwrap().is_none());
        assert!(right_walsh_coefficients(Some(&source), &[1], &[BigUint::zero()], 8, 1)
            .unwrap().is_none());
    }

    #[test]
    fn huge_variable_masks_are_exact() {
        let z = BigUint::one() << 255usize;
        let modes = vec![BigUint::zero(), z.clone()];
        let out = right_walsh_coefficients(
            Some(&[(z.clone(), BigUint::zero())]), &[256], &modes, 2, 100,
        ).unwrap().unwrap();
        assert_eq!(out.coefficients,
                   vec![(BigInt::one(), 2u32.into()), (BigInt::from(-1), 2u32.into())]);
    }
}
