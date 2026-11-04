//! Exact, bounded source-CNF model counting by indexed variable elimination.
//!
//! This is conventional sum-product factor elimination. Its runtime is
//! exponential in the largest intermediate factor width. A budget failure
//! returns Ok(None), never an invented model count.
//!
//! This crate is a performance candidate. Lean checks separate certificates;
//! native Rust code does not constitute a formal proof.

pub mod source_preprocess;
pub mod source_xor;
pub mod right_walsh;
pub mod left_affine;
pub mod fused_source;
pub mod two_sat;
pub mod cnf;
pub mod dimacs_evidence;
pub mod rup_witness;
pub mod rup_checker;

use num_bigint::BigUint;
use num_traits::{One, Zero};
use std::cmp::Reverse;
use std::collections::{BTreeMap, BTreeSet, BinaryHeap};

#[derive(Clone, Debug)]
struct Factor {
    scope: Vec<u32>,
    table: Vec<BigUint>,
}

#[derive(Debug, PartialEq, Eq)]
pub struct CountResult {
    pub models: BigUint,
    pub operations: u64,
    pub max_factor_variables: usize,
    pub eliminated_variables: usize,
}

fn score(
    variable: u32,
    incidence: &BTreeMap<u32, BTreeSet<usize>>,
    factors: &BTreeMap<usize, Factor>,
) -> (usize, usize) {
    let mut union = BTreeSet::from([variable]);
    let relevant = &incidence[&variable];
    for id in relevant {
        union.extend(factors[id].scope.iter().copied());
    }
    (union.len(), relevant.len())
}

/// Count assignments satisfying CNF over precisely the listed variables.
/// Input literal sign has the usual CNF meaning; all IDs must be listed.
/// Component variables need not be contiguous or start at 1.
///
/// The width/operation caps mirror the Python indexed reference.
pub fn count_component(
    clauses: &[Vec<i32>],
    component_variables: &[u32],
    max_factor_variables: usize,
    max_operations: u64,
) -> Result<Option<CountResult>, String> {
    if !(1..=16).contains(&max_factor_variables) || max_operations < 1 {
        return Err("invalid width or operation cap".into());
    }
    if component_variables.len() > 512 {
        return Err("more than 512 variables not supported".into());
    }
    let mut active: BTreeSet<u32> = BTreeSet::new();
    for &v in component_variables {
        if v == 0 || v > i32::MAX as u32 || !active.insert(v) {
            return Err("invalid or repeated variable ID".into());
        }
    }

    let mut factors: BTreeMap<usize, Factor> = BTreeMap::new();
    let mut incidence: BTreeMap<u32, BTreeSet<usize>> =
        active.iter().map(|&v| (v, BTreeSet::new())).collect();
    let mut next_id: usize = 0;
    let mut operations: u64 = 0;
    let mut maximum_width: usize = 0;

    for clause in clauses {
        let mut violation_bits: BTreeMap<u32, bool> = BTreeMap::new();
        let mut tautology = false;
        for &lit in clause {
            if lit == 0 || lit == i32::MIN {
                return Err("invalid zero or minimum signed literal".into());
            }
            let variable = lit.unsigned_abs();
            if !active.contains(&variable) {
                return Err(format!("literal {lit} outside component universe"));
            }
            // To violate a positive literal, its variable must be false.
            // To violate a negative literal, its variable must be true.
            let forbidden = lit < 0;
            match violation_bits.insert(variable, forbidden) {
                Some(other) if other != forbidden => tautology = true,
                _ => {}
            }
        }
        if tautology {
            continue;
        }
        if violation_bits.is_empty() {
            return Ok(Some(CountResult {
                models: BigUint::zero(), operations, max_factor_variables: maximum_width,
                eliminated_variables: 0,
            }));
        }
        let scope: Vec<u32> = violation_bits.keys().copied().collect();
        let width = scope.len();
        if width > max_factor_variables {
            return Ok(None);
        }
        maximum_width = maximum_width.max(width);
        let entries = 1usize << width;
        if (entries as u64) > max_operations.saturating_sub(operations) {
            return Ok(None);
        }
        operations += entries as u64;
        let mut table = Vec::with_capacity(entries);
        for packed in 0..entries {
            let violated = scope.iter().enumerate().all(|(i, v)| {
                (packed & (1usize << i) != 0) == violation_bits[v]
            });
            table.push(if violated { BigUint::zero() } else { BigUint::one() });
        }
        factors.insert(next_id, Factor { scope: scope.clone(), table });
        for &v in &scope {
            incidence.get_mut(&v).unwrap().insert(next_id);
        }
        next_id += 1;
    }

    let mut versions: BTreeMap<u32, u64> = active.iter().map(|&v| (v, 0)).collect();
    let mut heap: BinaryHeap<Reverse<(usize, usize, u32, u64)>> = BinaryHeap::new();
    for &v in &active {
        let (width, touched) = score(v, &incidence, &factors);
        heap.push(Reverse((width, touched, v, 0)));
    }

    let mut constant = BigUint::one();
    let variable_count = component_variables.len();

    for _ in 0..variable_count {
        let (scored_width, variable) = loop {
            let Some(Reverse((width, _touched, v, stamp))) = heap.pop() else {
                return Err("priority queue unexpectedly empty".into());
            };
            if active.contains(&v) && versions[&v] == stamp {
                break (width, v);
            }
        };
        let ids: Vec<usize> = incidence[&variable].iter().copied().collect();
        let touched: Vec<&Factor> = ids.iter().map(|id| &factors[id]).collect();
        let mut union = BTreeSet::from([variable]);
        for factor in &touched {
            union.extend(factor.scope.iter().copied());
        }
        if union.len() != scored_width {
            return Err("stale elimination priority score".into());
        }
        if union.len() > max_factor_variables {
            return Ok(None);
        }
        maximum_width = maximum_width.max(union.len());
        let context: Vec<u32> = union.into_iter().filter(|&v| v != variable).collect();
        let entries = 1usize << context.len();
        let work = (entries as u64) * 2 * touched.len().max(1) as u64;
        if work > max_operations.saturating_sub(operations) {
            return Ok(None);
        }
        operations += work;
        let context_positions: BTreeMap<u32, usize> =
            context.iter().enumerate().map(|(i, &v)| (v, i)).collect();
        let mut values = Vec::with_capacity(entries);

        for packed in 0..entries {
            let mut sum = BigUint::zero();
            for selected in [false, true] {
                let mut product = BigUint::one();
                for factor in &touched {
                    let mut key = 0usize;
                    for (position, &v) in factor.scope.iter().enumerate() {
                        let bit = if v == variable {
                            selected
                        } else {
                            packed & (1usize << context_positions[&v]) != 0
                        };
                        if bit {
                            key |= 1usize << position;
                        }
                    }
                    product *= &factor.table[key];
                    if product.is_zero() {
                        break;
                    }
                }
                sum += product;
            }
            values.push(sum);
        }

        let mut affected: BTreeSet<u32> = BTreeSet::new();
        for id in ids {
            let factor = factors.remove(&id).unwrap();
            for u in factor.scope {
                incidence.get_mut(&u).unwrap().remove(&id);
                if u != variable {
                    affected.insert(u);
                }
            }
        }

        if context.is_empty() {
            constant *= &values[0];
        } else {
            factors.insert(next_id, Factor { scope: context.clone(), table: values });
            for &u in &context {
                incidence.get_mut(&u).unwrap().insert(next_id);
                affected.insert(u);
            }
            next_id += 1;
        }
        active.remove(&variable);
        incidence.remove(&variable);
        for u in affected {
            if active.contains(&u) {
                let stamp = versions.get_mut(&u).unwrap();
                *stamp += 1;
                let (width, touched) = score(u, &incidence, &factors);
                heap.push(Reverse((width, touched, u, *stamp)));
            }
        }
    }
    if factors.values().any(|f| !f.scope.is_empty()) {
        return Err("active factors survived variable elimination".into());
    }
    for factor in factors.values() {
        constant *= &factor.table[0];
    }
    Ok(Some(CountResult {
        models: constant,
        operations,
        max_factor_variables: maximum_width,
        eliminated_variables: variable_count,
    }))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn brute(source: &[Vec<i32>], n: usize) -> usize {
        (0usize..(1 << n)).filter(|&mask| {
            source.iter().all(|clause| clause.iter().any(|&lit| {
                let bit = mask & (1 << (lit.unsigned_abs() as usize - 1)) != 0;
                bit == (lit > 0)
            }))
        }).count()
    }

    fn fibonacci(n: usize) -> BigUint {
        let (mut a, mut b) = (BigUint::zero(), BigUint::one());
        for _ in 0..n {
            (a, b) = (b.clone(), a + &b);
        }
        a
    }

    #[test]
    fn chain_256_exact_bigint() {
        let n: usize = 256;
        let clauses: Vec<Vec<i32>> = (1..n)
            .map(|i| vec![i as i32, (i + 1) as i32]).collect();
        let vars: Vec<u32> = (1..=n as u32).collect();
        let answer = count_component(&clauses, &vars, 3, 100000).unwrap().unwrap();
        assert_eq!(answer.models, fibonacci(n + 2));
        assert!(answer.max_factor_variables <= 3);
    }

    #[test]
    fn empty_and_unsat_components() {
        let vars = [1, 3, 8];
        let empty = count_component(&[], &vars, 1, 100).unwrap().unwrap();
        assert_eq!(empty.models, BigUint::from(8u8));
        let unsat = count_component(&[vec![1], vec![-1]], &vars, 2, 100).unwrap().unwrap();
        assert_eq!(unsat.models, BigUint::zero());
        let empty_clause = count_component(&[vec![]], &vars, 2, 100).unwrap().unwrap();
        assert_eq!(empty_clause.models, BigUint::zero());
    }

    #[test]
    fn signed_random_bruteforce_differentials() {
        let mut state = 19021u64;
        let mut rand = || {
            state = state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            (state >> 32) as usize
        };
        for n in 3..=8usize {
            let vars: Vec<u32> = (1..=n as u32).collect();
            for _ in 0..40 {
                let mut clauses = Vec::new();
                for _ in 0..(rand() % 11) {
                    let k = 1 + rand() % 3;
                    let mut clause = Vec::new();
                    for _ in 0..k {
                        let v = 1 + rand() % n;
                        clause.push(if rand() & 1 == 0 { v as i32 } else { -(v as i32) });
                    }
                    clauses.push(clause);
                }
                let r = count_component(&clauses, &vars, 8, 1000000).unwrap().unwrap();
                assert_eq!(r.models, BigUint::from(brute(&clauses, n) as u64));
            }
        }
    }

    #[test]
    fn finite_caps_and_source_validation() {
        let vars: Vec<u32> = (1..=16).collect();
        let ring: Vec<Vec<i32>> = (1..=16).map(|i| {
            vec![i as i32, ((i % 16) + 1) as i32]
        }).collect();
        assert!(count_component(&ring, &vars, 2, 100000).unwrap().is_none());
        assert!(count_component(&ring, &vars, 3, 4).unwrap().is_none());
        assert!(count_component(&[vec![17]], &vars, 3, 100).is_err());
        assert!(count_component(&[], &[1, 1], 3, 100).is_err());
        assert!(count_component(&[], &vars, 0, 100).is_err());
    }

    #[test]
    fn tautologies_do_not_change_counts() {
        let vars = [1, 2, 3];
        let answer = count_component(&[vec![1, -1], vec![2, 2]], &vars, 3, 100).unwrap().unwrap();
        assert_eq!(answer.models, BigUint::from(4u8));
    }
}

#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use pyo3::exceptions::PyValueError;

/// In-process Rust arithmetic entry point. BigUint travels as decimal
/// text, avoiding a lossy 64-bit Python integer conversion.
#[cfg(feature = "python")]
#[pyfunction]
fn count_component_native(
    clauses: Vec<Vec<i32>>,
    component_variables: Vec<u32>,
    max_factor_variables: usize,
    max_operations: u64,
) -> PyResult<Option<(String, u64, usize, usize)>> {
    let answer = count_component(
        &clauses, &component_variables, max_factor_variables, max_operations,
    ).map_err(PyValueError::new_err)?;
    Ok(answer.map(|result| (
        result.models.to_string(), result.operations,
        result.max_factor_variables, result.eliminated_variables,
    )))
}

#[cfg(feature = "python")]
#[pyfunction]
fn simplify_source_native(
    clauses: Vec<Vec<i32>>, nvars: u32,
    max_passes: usize, max_clause_visits: usize,
) -> PyResult<Option<(Vec<Vec<i32>>, usize, usize)>> {
    let answer = source_preprocess::simplify_source(
        &clauses, nvars, max_passes, max_clause_visits,
    ).map_err(PyValueError::new_err)?;
    Ok(answer.map(|result| (
        result.clauses, result.passes, result.consensus_pairs,
    )))
}

/// The adaptive option skips expensive normalization when the cheap
/// binary-sign heuristic sees no direct consensus opportunity. It returns
/// pass_count=0 for the exact no-op path. This changes only performance:
/// the original source is retained unchanged if the heuristic rejects.
#[cfg(feature = "python")]
#[pyfunction]
fn simplify_source_adaptive_native(
    clauses: Vec<Vec<i32>>, nvars: u32,
    max_passes: usize, max_clause_visits: usize,
) -> PyResult<Option<(Vec<Vec<i32>>, usize, usize)>> {
    if max_passes == 0 || max_clause_visits == 0 || nvars > 512 {
        return Err(PyValueError::new_err("invalid preprocessing bounds"));
    }
    let admitted = source_preprocess::source_admission_heuristic(&clauses, nvars)
        .map_err(PyValueError::new_err)?;
    if !admitted {
        if clauses.len() > max_clause_visits {
            return Ok(None);
        }
        return Ok(Some((clauses, 0, 0)));
    }
    let answer = source_preprocess::simplify_source(
        &clauses, nvars, max_passes, max_clause_visits,
    ).map_err(PyValueError::new_err)?;
    Ok(answer.map(|result| (
        result.clauses, result.passes, result.consensus_pairs,
    )))
}

/// Exact source-CNF extraction of complete k-XOR blocks, k<=3.
/// Arbitrary-precision bit masks are returned as decimal strings.
#[cfg(feature = "python")]
#[pyfunction]
fn extract_small_xors_native(
    clauses: Vec<Vec<i32>>, nvars: u32,
) -> PyResult<(Vec<(String, u32)>, Vec<Vec<i32>>)> {
    let answer = source_xor::extract_small_xors(&clauses, nvars)
        .map_err(PyValueError::new_err)?;
    Ok((
        answer.rows.into_iter().map(|(mask, rhs)| (mask.to_string(), rhs)).collect(),
        answer.residual_clauses,
    ))
}

/// Exact batched right CNF Walsh coefficients using inclusion-exclusion.
/// Every coefficient is returned as a signed numerator and positive
/// denominator in decimal text; there is no floating point approximation.
#[cfg(feature = "python")]
#[pyfunction]
fn right_walsh_native(
    clauses: Option<Vec<(String, String)>>,
    boundary: Vec<u32>,
    modes: Vec<String>,
    max_subsets: usize,
    max_operations: u64,
) -> PyResult<Option<(Vec<(String, String)>, usize, usize, u64)>> {
    let parse = |s: &str| {
        BigUint::parse_bytes(s.as_bytes(), 10)
            .ok_or_else(|| PyValueError::new_err("invalid decimal Walsh mask"))
    };
    let clauses = clauses.map(|rows| rows.into_iter()
        .map(|(z, o)| Ok((parse(&z)?, parse(&o)?)))
        .collect::<PyResult<Vec<_>>>()).transpose()?;
    let modes = modes.iter().map(|m| parse(m)).collect::<PyResult<Vec<_>>>()?;
    let answer = right_walsh::right_walsh_coefficients(
        clauses.as_deref(), &boundary, &modes, max_subsets, max_operations,
    ).map_err(PyValueError::new_err)?;
    Ok(answer.map(|got| (
        got.coefficients.into_iter().map(|(num, den)| (num.to_string(), den.to_string())).collect(),
        got.compatible_terms, got.components, got.subset_operations,
    )))
}

/// Native exact affine GF(2) projection and sparse Fourier expansion.
/// The optional outer result is budget refusal. The optional projected
/// rows distinguish a contradictory system from a satisfiable one.
#[cfg(feature = "python")]
#[pyfunction]
fn affine_spectrum_native(
    rows: Vec<(String, u32)>,
    internals: Vec<u32>,
    boundary: Vec<u32>,
    max_terms: usize,
) -> PyResult<Option<(Option<Vec<(String, u32)>>, usize,
                       Vec<(String, String, String)>)>> {
    let mut parsed = Vec::with_capacity(rows.len());
    for (mask, rhs) in rows {
        let support = BigUint::parse_bytes(mask.as_bytes(), 10)
            .ok_or_else(|| PyValueError::new_err("invalid GF2 affine decimal mask"))?;
        parsed.push((support, rhs));
    }
    let result = left_affine::project_and_expand(
        &parsed, &internals, &boundary, max_terms,
    ).map_err(PyValueError::new_err)?;
    Ok(result.map(|answer| (
        answer.projected_rows.map(|rs| rs.into_iter()
            .map(|(mask, rhs)| (mask.to_string(), rhs)).collect()),
        answer.internal_free,
        answer.spectrum.into_iter()
            .map(|(mode, num, den)| (mode.to_string(), num.to_string(), den.to_string()))
            .collect(),
    )))
}

/// Fully native source-CNF exact counting with one PyO3 boundary.
/// The model count is transported as decimal text to avoid truncation.
#[cfg(feature = "python")]
#[pyfunction]
fn count_source_native(
    clauses: Vec<Vec<i32>>, nvars: u32, preprocess: &str,
    max_preprocess_passes: usize, max_preprocess_clause_visits: usize,
    max_spectrum_terms: usize, max_inclusion_subsets: usize,
    max_coefficient_operations: u64,
) -> PyResult<Option<(String, usize, usize, usize, usize, usize,
                       usize, usize, usize, bool, usize, u64)>> {
    let got = fused_source::count_fused_source(
        &clauses, nvars, preprocess, max_preprocess_passes,
        max_preprocess_clause_visits, max_spectrum_terms,
        max_inclusion_subsets, max_coefficient_operations,
    ).map_err(PyValueError::new_err)?;
    Ok(got.map(|out| (
        out.models.to_string(), out.extracted_affine_rows,
        out.residual_clauses, out.boundary_variables,
        out.internal_variables, out.internal_free_variables, out.left_fourier_terms,
        out.right_violation_terms, out.right_components,
        out.source_preprocess_skipped, out.source_preprocess_passes,
        out.right_subset_operations,
    )))
}

#[cfg(feature = "python")]
#[pyfunction]
fn solve_two_sat_native(
    clauses: Vec<Vec<i32>>, nvars: u32,
) -> PyResult<Option<Vec<bool>>> {
    two_sat::solve_2sat(&clauses, nvars).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn canonical_cnf_native(
    clauses: Vec<Vec<i32>>,
) -> PyResult<(Vec<Vec<i32>>, String, Vec<u32>, bool)> {
    let normalized = cnf::CanonicalCnf::from_signed(&clauses)
        .map_err(PyValueError::new_err)?;
    Ok((
        normalized.clauses.clone(), normalized.canonical_dimacs(),
        normalized.variables(), normalized.is_2cnf(),
    ))
}

#[cfg(feature = "python")]
#[pyfunction]
fn first_subsumption_native(
    clauses: Vec<Vec<i32>>,
) -> PyResult<Option<(Vec<i32>, Vec<i32>)>> {
    let normalized = cnf::CanonicalCnf::from_signed(&clauses)
        .map_err(PyValueError::new_err)?;
    Ok(normalized.first_strict_subsumption())
}

#[cfg(feature = "python")]
#[pyfunction]
fn parse_dimacs_evidence_native(
    text: String,
) -> PyResult<(Vec<Vec<i32>>, Vec<Vec<i32>>, Vec<i32>, Vec<String>, String)> {
    let parsed = dimacs_evidence::parse_text_evidence(&text)
        .map_err(PyValueError::new_err)?;
    Ok((
        parsed.canonical.clauses.clone(), parsed.raw_clauses,
        parsed.literal_stream, parsed.literal_spellings,
        parsed.canonical.canonical_dimacs(),
    ))
}

#[cfg(feature = "python")]
#[pyfunction]
fn indexed_rup_witness_native(
    database: Vec<Vec<i32>>, target_clause: Vec<i32>, max_units: usize,
) -> PyResult<Option<Vec<i32>>> {
    rup_witness::indexed_unit_conflict_witness(
        &database, &target_clause, max_units,
    ).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn check_rup_subset_native(
    original: Vec<Vec<i32>>, proof_text: String, strict_deletions: bool,
) -> PyResult<(bool, bool, Option<usize>, Option<String>, Vec<String>)> {
    let result = rup_checker::check_rup_text(
        &original, &proof_text, strict_deletions,
    ).map_err(PyValueError::new_err)?;
    Ok((result.verified, result.empty_clause_derived, result.failed_line,
        result.error, result.warnings))
}

#[cfg(feature = "python")]
#[pymodule]
fn witnora_ve(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(count_component_native, module)?)?;
    module.add_function(wrap_pyfunction!(simplify_source_native, module)?)?;
    module.add_function(wrap_pyfunction!(simplify_source_adaptive_native, module)?)?;
    module.add_function(wrap_pyfunction!(extract_small_xors_native, module)?)?;
    module.add_function(wrap_pyfunction!(right_walsh_native, module)?)?;
    module.add_function(wrap_pyfunction!(affine_spectrum_native, module)?)?;
    module.add_function(wrap_pyfunction!(count_source_native, module)?)?;
    module.add_function(wrap_pyfunction!(solve_two_sat_native, module)?)?;
    module.add_function(wrap_pyfunction!(canonical_cnf_native, module)?)?;
    module.add_function(wrap_pyfunction!(first_subsumption_native, module)?)?;
    module.add_function(wrap_pyfunction!(parse_dimacs_evidence_native, module)?)?;
    module.add_function(wrap_pyfunction!(indexed_rup_witness_native, module)?)?;
    module.add_function(wrap_pyfunction!(check_rup_subset_native, module)?)?;
    Ok(())
}
