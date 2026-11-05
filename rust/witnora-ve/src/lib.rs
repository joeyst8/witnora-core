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
pub mod graph;
pub mod treewidth;
pub mod bce;
pub mod simplifier;
pub mod ve_proof;
pub mod two_sat_proof;
pub mod two_sat_scc_witness;
pub mod order_experiments;
pub mod failed_literal_probe;
pub mod scaling_families;
pub mod odd_xor_cycle;
pub mod two_ply_lookahead;
pub mod adaptive_lookahead;
pub mod selective_lookahead;
pub mod parity_separator_fingerprint;
pub mod spoke_discovery;
pub mod multicut_parity_separator;
pub mod structural_operator_invention;
pub mod cost_sensitive_gate;
pub mod separator_structural_priority;
pub mod vertex_coupling_separator;
pub mod global_coupling_separator;
pub mod gf2_sparse_row_basis;
pub mod g5_elimination_activity;
pub mod g5_boundary_path_signal;
pub mod sparse_parity_checks;
pub mod eth_clause_violation_parity;
pub mod symbolic_implication;
pub mod targeted_graph_families;
pub mod conjecture_triage;
pub mod proof_trace_metadata;
pub mod bipartite_audit;
pub mod incremental_xor_screen;
pub mod anchor_cut_audit;
pub mod parity_cut_width;
pub mod hidden_separator_generator;
pub mod hard_separator_generator;
pub mod satlib_fingerprint;
pub mod spoke_collapse;
pub mod ood_sat_families;
pub mod benchmark_families;
pub mod parity_compression;
pub mod crc_structural_independence;
pub mod crc_conditional_independence;
pub mod aux_violation_tensors;
pub mod constraint_geometry;
pub mod geometry_aware_parity;
pub mod claim_boundary;
pub mod crc_independence_audit;
pub mod crc_defect_oracle;
pub mod crc_shannon_oracle;
pub mod crc_conflict_oracle;
pub mod crc_orbit_oracle;
pub mod crc_separator_discovery;
pub mod crc_cutset_count;
pub mod expression_conjecture_search;
pub mod graph_conjecture_lab;
pub mod conditional_graph_conjectures;
pub mod lean_numeric_certificate_export;
pub mod lean_ascii_certificate_export;
pub mod lean_color_certificate_export;
pub mod crc_variable_elimination;
pub mod dsatur_adversarial_lab;
pub mod color_repair_lab;
pub mod kempe_repair_lab;
pub mod double_kempe_lab;
pub mod structured_coloring_study;
pub mod color_selector_lab;
pub mod nonedge_matching_dsatur;
pub mod nonedge_graph_bounds;
pub mod nonedge_matching_bound;
pub mod violation_image_anf;
pub mod anf_separator_conditioning;
pub mod anf_structured_counter;
pub mod xor_equations;
pub mod xor_drat_resolution;
pub mod xor_sparse_schedule;
pub mod xor_proof_order;
pub mod xor_proof_emit;
pub mod xor_ve_refutation;
pub mod certificate_json;
pub mod bundle_manifest;
pub mod reconstruction;
pub mod local_replay;
pub mod component_proof;
pub mod component_context_replay;

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
fn symbolic_bound_path_native(smaller: &str, larger: &str) -> Option<Vec<String>> {
    symbolic_implication::bound_path(smaller, larger)
}

#[cfg(feature = "python")]
#[pyfunction]
fn symbolic_normalize_native(op: &str, a: &str, b: &str, label: &str) -> (String, Vec<String>) {
    symbolic_implication::normalize(op, a, b, label)
}

#[cfg(feature = "python")]
#[pyfunction]
fn symbolic_derive_pair_native(
    left:(String,String,String,String),right:(String,String,String,String),
) -> (String,String,Vec<String>,String) {
    symbolic_implication::derive_pair(
        (&left.0,&left.1,&left.2,&left.3),
        (&right.0,&right.1,&right.2,&right.3))
}

#[cfg(feature = "python")]
#[pyfunction]
fn symbolic_known_axioms_native() -> Vec<String> {
    symbolic_implication::known_axioms()
}

#[cfg(feature = "python")]
#[pyfunction]
fn targeted_graph_family_native(
    family: &str, a: usize, b: usize,
) -> PyResult<(usize, Vec<(usize, usize)>)> {
    match family {
        "cycle" if a >= 3 && a <= 100 => Ok(targeted_graph_families::cycle(a)),
        "wheel" if a >= 4 && a <= 100 => Ok(targeted_graph_families::wheel(a)),
        "bipartite" if a >= 1 && b >= 1 && a <= 100 && b <= 100 =>
            Ok(targeted_graph_families::complete_bipartite(a, b)),
        "mycielski_c5" => Ok(targeted_graph_families::mycielski_c5()),
        _ => Err(PyValueError::new_err("invalid bounded graph family")),
    }
}

#[cfg(feature = "python")]
#[pyfunction]
fn conjecture_normalize_native(expr: &str) -> PyResult<String> {
    conjecture_triage::normalize_expression(expr).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn conjecture_identity_key_native(statement: &str) -> PyResult<(String, String)> {
    conjecture_triage::identity_key(statement).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn conjecture_known_identities_native() -> Vec<(String, String)> {
    conjecture_triage::known_identity_keys().into_iter().collect()
}

#[cfg(feature = "python")]
#[pyfunction]
fn native_unsat_trace_metadata_supported_native(
    format: Option<String>, replayed: bool, external: Option<String>,
    lrat_frat: Option<String>, reason: Option<String>,
) -> bool {
    proof_trace_metadata::is_supported(format.as_deref(), replayed,
        external.as_deref(), lrat_frat.as_deref(), reason.as_deref())
}

#[cfg(feature = "python")]
#[pyfunction]
fn bipartition_audit_native(
    n: usize, edges: Vec<(usize, usize)>,
) -> PyResult<Option<Vec<i32>>> {
    bipartite_audit::bipartition(n, &edges).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn possible_two_xor_patterns_native(clauses: Vec<Vec<i32>>) -> PyResult<bool> {
    incremental_xor_screen::possible_two_xor_patterns(&clauses)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn full_cnf_anchors_separated_native(
    clauses: Vec<Vec<i32>>, cut: Vec<u32>, left: u32, right: u32,
) -> PyResult<bool> {
    anchor_cut_audit::anchors_separated(&clauses, &cut, left, right)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn independent_parity_cut_width_native(
    supports: Vec<Vec<u32>>, limit: usize,
) -> PyResult<Option<usize>> {
    parity_cut_width::independent_parity_cut_width(&supports,limit)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn make_hidden_separator_native(
    width:i32,cross_noise:bool,labels:Vec<i32>,
) -> PyResult<Vec<Vec<i32>>> {
    hidden_separator_generator::generate(width,cross_noise,&labels)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn make_hard_separator_case_native(
    blocks:i32,core_vars:i32,width:i32,samples:Vec<Vec<Vec<i32>>>,
) -> PyResult<Vec<Vec<i32>>> {
    hard_separator_generator::generate(blocks,core_vars,width,&samples)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn satlib_structural_metrics_native(source:Vec<Vec<i32>>)
    ->PyResult<(usize,usize,usize,usize,usize,usize,usize,usize,usize)> {
    satlib_fingerprint::structural_metrics(&source).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn spoke_cnf_native(spokes:Vec<(i32,i32,i32)>)->PyResult<Vec<Vec<i32>>> {
    spoke_collapse::generate(&spokes).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn collapse_spokes_native(source:Vec<Vec<i32>>,spokes:Vec<(i32,i32,i32)>)
    ->PyResult<spoke_collapse::Verdict> {
    Ok(spoke_collapse::classify(&source,&spokes))
}

#[cfg(feature = "python")]
#[pyfunction]
fn ood_pigeonhole_native(pigeons:i32,holes:i32)->PyResult<Vec<Vec<i32>>> {
    ood_sat_families::pigeonhole(pigeons,holes).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn ood_graph_coloring_native(vertices:i32,edges:Vec<(i32,i32)>,colors:i32)
    ->PyResult<Vec<Vec<i32>>> {
    ood_sat_families::graph_coloring(vertices,&edges,colors).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn ood_tseitin_complete_native(vertices:i32,contradictory:bool)
    ->PyResult<Vec<Vec<i32>>> {
    ood_sat_families::tseitin_complete_graph(vertices,contradictory)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn ood_n_queens_native(n:i32)->PyResult<Vec<Vec<i32>>> {
    ood_sat_families::n_queens(n).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn ood_planted_samples_native(n:i32,witness:Vec<bool>,rows:Vec<Vec<i32>>)
    ->PyResult<Vec<Vec<i32>>> {
    ood_sat_families::planted_from_samples(n,&witness,&rows)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn benchmark_family_native(kind:String,n:i32,count:i32)->PyResult<Vec<Vec<i32>>> {
    benchmark_families::generate(&kind,n,count).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn benchmark_sampled_clauses_native(rows:Vec<Vec<i32>>)->PyResult<Vec<Vec<i32>>> {
    benchmark_families::canonical_samples(&rows).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn parity_compress_native(source:Vec<Vec<i32>>)
    ->PyResult<parity_compression::Compression> {
    parity_compression::compress(&source).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn parity_reconstruct_native(roots:Vec<(i32,i32)>,offsets:Vec<(i32,u32)>,
    values:Vec<(i32,u32)>)->PyResult<Vec<(i32,u32)>> {
    parity_compression::reconstruct(&roots,&offsets,&values).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn parity_rewrite_native(source:Vec<Vec<i32>>,roots:Vec<(i32,i32)>,
    offsets:Vec<(i32,u32)>)->PyResult<Vec<Vec<i32>>> {
    parity_compression::rewrite(&source,&roots,&offsets).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn crc_structural_independence_native(source:Vec<Vec<i32>>,boundary:Vec<i32>,
    left:Vec<i32>,right:Vec<i32>,assignment_decimal:String)
    ->PyResult<Option<(bool,usize,usize)>> {
    crc_structural_independence::audit(&source,&boundary,&left,&right,
        &assignment_decimal).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn crc_conditional_independence_native(source:Vec<Vec<i32>>,boundary:Vec<i32>,
    left:Vec<i32>,right:Vec<i32>,separator:Vec<i32>,assignment_decimal:String)
    ->PyResult<Option<(bool,String,usize,usize,usize)>> {
    crc_conditional_independence::conditioned(&source,&boundary,&left,&right,
        &separator,&assignment_decimal).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn aux_local_scopes_native(source:Vec<Vec<i32>>,nvars:usize,rows:Vec<Vec<usize>>)
    ->PyResult<Vec<Vec<usize>>> {
    aux_violation_tensors::local_scopes(&source,nvars,&rows).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn aux_direct_scopes_native(source:Vec<Vec<i32>>,rows:Vec<Vec<usize>>)
    ->PyResult<Vec<Vec<usize>>> {
    aux_violation_tensors::direct_scopes(&source,&rows).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn aux_exact_models_native(source:Vec<Vec<i32>>,nvars:usize,max_variables:usize)
    ->PyResult<u64> {
    aux_violation_tensors::exact_source_models(&source,nvars,max_variables)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn aux_weight_profile_native(source:Vec<Vec<i32>>,nvars:usize,rows:Vec<Vec<usize>>,
    max_variables:usize)->PyResult<Vec<u64>> {
    aux_violation_tensors::weight_profile(&source,nvars,&rows,max_variables)
        .map_err(PyValueError::new_err)
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
#[pyfunction]
fn primal_graph_native(
    clauses: Vec<Vec<i32>>,
) -> PyResult<(Vec<u32>, Vec<(u32, u32)>)> {
    graph::primal_variables_and_edges(&clauses).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn incidence_components_native(
    clauses: Vec<Vec<i32>>,
) -> PyResult<Vec<Vec<Vec<i32>>>> {
    graph::incidence_components(&clauses).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn treewidth_order_native(
    graph: Vec<(u32, Vec<u32>)>, width_cap: usize, max_states: usize,
) -> PyResult<Option<Vec<u32>>> {
    treewidth::find_elimination_order(
        &graph, width_cap, max_states,
    ).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn verify_treewidth_order_native(
    graph: Vec<(u32, Vec<u32>)>, order: Vec<u32>,
) -> PyResult<Option<usize>> {
    treewidth::verify_elimination_order(&graph, &order)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn blocked_clause_witness_native(
    source: Vec<Vec<i32>>, clause: Vec<i32>, pivot: i32,
) -> PyResult<Option<(i32, Vec<(Vec<i32>, Vec<i32>, bool)>)>> {
    bce::blocked_clause_witness(&source, &clause, pivot)
        .map(|got| got.map(|w| (w.pivot, w.checked)))
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn first_blocked_clause_native(
    source: Vec<Vec<i32>>,
) -> PyResult<Option<(Vec<i32>, i32, Vec<(Vec<i32>, Vec<i32>, bool)>)>> {
    bce::first_blocked_clause(&source)
        .map(|got| got.map(|(clause, w)| (clause, w.pivot, w.checked)))
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn unit_step_native(
    source: Vec<Vec<i32>>,
) -> PyResult<Option<(Vec<Vec<i32>>, i32, Vec<Vec<i32>>,
                      Vec<(Vec<i32>, Vec<i32>)>, bool)>> {
    simplifier::unit_step(&source)
        .map(|got| got.map(|out| (
            out.clauses, out.literal, out.satisfied,
            out.shortened, out.conflict,
        )))
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn pure_step_native(
    source: Vec<Vec<i32>>,
) -> PyResult<Option<(Vec<Vec<i32>>, i32, Vec<Vec<i32>>)>> {
    simplifier::pure_step(&source)
        .map(|got| got.map(|out| (
            out.clauses, out.literal, out.removed,
        )))
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn eliminate_with_proof_native(
    source: Vec<Vec<i32>>, variable: i32, width_cap: i32,
) -> PyResult<(Vec<Vec<i32>>, bool, usize, Option<Vec<i32>>,
               Vec<(Vec<i32>, Vec<i32>, Vec<i32>)>,
               Vec<(Vec<i32>, Vec<i32>, Vec<i32>)>,
               Vec<Vec<i32>>, Vec<Vec<i32>>)> {
    let step = ve_proof::eliminate_with_proof(
        &source, variable, width_cap,
    ).map_err(PyValueError::new_err)?;
    let as_tuple = |pair: ve_proof::ResolutionPair| {
        (pair.positive, pair.negative, pair.resolvent)
    };
    Ok((
        step.clauses, step.collapsed, step.width_observed,
        step.refusal_resolvent,
        step.discarded.into_iter().map(as_tuple).collect(),
        step.generated.into_iter().map(as_tuple).collect(),
        step.added, step.removed,
    ))
}

#[cfg(feature = "python")]
#[pyfunction]
fn solve_two_sat_proof_native(
    source: Vec<Vec<i32>>,
) -> PyResult<(bool, bool, Option<u32>, Vec<(i32,i32)>,
               Vec<Vec<i32>>, Vec<(u32,bool)>, usize)> {
    let out = two_sat_proof::solve_2sat_proof(&source)
        .map_err(PyValueError::new_err)?;
    Ok((out.sat, out.empty_clause, out.conflict_variable,
        out.edges, out.components, out.assignment, out.node_count))
}

#[cfg(feature = "python")]
#[pyfunction]
fn canonical_cnf_hash_native(clauses: Vec<Vec<i32>>) -> PyResult<String> {
    let cnf = cnf::CanonicalCnf::from_signed(&clauses)
        .map_err(PyValueError::new_err)?;
    Ok(cnf.formula_hash())
}

#[cfg(feature = "python")]
#[pyfunction]
fn blocked_clause_digest_native(
    rows: Vec<(Vec<i32>, Vec<i32>, bool)>,
) -> PyResult<String> {
    Ok(bce::checked_proof_digest(&rows))
}

/// R-024: build the canonical certificate step record in Rust.
#[cfg(feature = "python")]
#[pyfunction]
fn build_step_record_native(
    py: Python<'_>, step_id: usize, step_type: String,
    input_clauses: Vec<Vec<i32>>, output_clauses: Vec<Vec<i32>>,
    details: Py<PyAny>, removed_clauses: Vec<Vec<i32>>,
    added_clauses: Vec<Vec<i32>>, assigned_literals: Vec<i32>,
    reconstruction_data: Py<PyAny>,
) -> PyResult<Py<PyAny>> {
    use pyo3::types::PyDict;
    if step_id == 0 {
        return Err(PyValueError::new_err("certificate step id must be positive"));
    }
    let input = cnf::CanonicalCnf::from_signed(&input_clauses)
        .map_err(PyValueError::new_err)?;
    let output = cnf::CanonicalCnf::from_signed(&output_clauses)
        .map_err(PyValueError::new_err)?;
    let record = PyDict::new(py);
    record.set_item("step_id", step_id)?;
    record.set_item("type", step_type)?;
    record.set_item("input_formula_hash", input.formula_hash())?;
    record.set_item("output_formula_hash", output.formula_hash())?;
    record.set_item("details", details)?;
    record.set_item("removed_clauses", removed_clauses)?;
    record.set_item("added_clauses", added_clauses)?;
    record.set_item("assigned_literals", assigned_literals)?;
    record.set_item("reconstruction_data", reconstruction_data)?;
    Ok(record.into_any().unbind())
}

#[cfg(feature = "python")]
#[pyfunction]
fn stable_certificate_json_native(value: &Bound<'_, PyAny>) -> PyResult<(String, String)> {
    certificate_json::stable_json(value)
}

#[cfg(feature = "python")]
#[pyfunction]
fn certificate_file_digests_native(
    files: Vec<(String, String)>,
) -> PyResult<Vec<(String, String)>> {
    bundle_manifest::file_digests(&files).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn compact_certificate_hash_native(value: &Bound<'_, PyAny>) -> PyResult<(String, String)> {
    certificate_json::compact_certificate_hash(value)
}

#[cfg(feature = "python")]
#[pyfunction]
fn verify_certificate_file_digests_native(
    expected: Vec<(String, String)>, files: Vec<(String, String)>,
) -> PyResult<Option<String>> {
    bundle_manifest::first_digest_failure(&expected, &files)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn reconstruct_assignment_native(
    source: Vec<Vec<i32>>,
    steps: Vec<(String, Vec<i32>, Vec<i32>, i32, Vec<Vec<i32>>, i32, Vec<Vec<i32>>)>,
    final_assignment: Vec<(u32, bool)>,
) -> PyResult<(bool, Vec<(u32, bool)>, Option<String>)> {
    let steps = steps.into_iter().map(
        |(kind, assigned, bce_removed, bce_pivot, bce_opposites, ve_var, ve_removed)| {
            reconstruction::ReconstructionStep {
                kind, assigned, bce_removed, bce_pivot, bce_opposites,
                ve_var, ve_removed,
            }
        },
    ).collect::<Vec<_>>();
    let out = reconstruction::reconstruct(&source, &steps, &final_assignment)
        .map_err(PyValueError::new_err)?;
    Ok((out.ok, out.assignment.into_iter().collect(), out.error))
}

#[cfg(feature = "python")]
#[pyfunction]
fn replay_local_certificate_native(
    source: Vec<Vec<i32>>,
    steps: Vec<(String, usize, String, String, Vec<i32>,
                Vec<Vec<i32>>, Vec<Vec<i32>>,
                (Vec<i32>, i32, String, i32),
                (Vec<u32>, Vec<(u32, u32)>, String, Vec<(u32, bool)>))>,
    width_cap: i32, final_hash: String,
) -> PyResult<(bool, Vec<Vec<i32>>, Option<String>)> {
    let events = steps.into_iter().map(
        |(kind, step_id, input_hash, output_hash, assigned, removed, added,
           (subsuming, blocked_literal, proof_digest, ve_var),
           (tree_order, primal_edges, two_sat_status, two_sat_assignment))| {
            local_replay::LocalReplayStep {
                kind, step_id, input_hash, output_hash, assigned, removed,
                added, subsuming, blocked_literal, proof_digest, ve_var,
                tree_order, primal_edges, two_sat_status, two_sat_assignment,
            }
        },
    ).collect::<Vec<_>>();
    let out = local_replay::replay(&source, &events, width_cap, &final_hash)
        .map_err(PyValueError::new_err)?;
    Ok((out.verified, out.final_clauses, out.error))
}

#[cfg(feature = "python")]
#[pyfunction]
fn component_evidence_native(
    source: Vec<Vec<i32>>,
) -> PyResult<(usize, Vec<(u32, usize)>,
               Vec<(usize, String, Vec<u32>, Vec<Vec<i32>>, Vec<usize>)>)> {
    let out = component_proof::component_evidence(&source)
        .map_err(PyValueError::new_err)?;
    let components = out.components.into_iter().map(|c| (
        c.id, c.formula_hash, c.variables, c.clauses, c.clause_indices,
    )).collect();
    Ok((out.count, out.incidence_edges, components))
}

#[cfg(feature = "python")]
#[pyfunction]
fn verify_component_evidence_native(
    source: Vec<Vec<i32>>,
    output_hash: String,
    count: usize,
    edges: Vec<(u32, usize)>,
    logged: Vec<(usize, String, Vec<u32>, Vec<Vec<i32>>, Vec<usize>)>,
) -> PyResult<Option<String>> {
    let records = logged.into_iter().map(
        |(id, formula_hash, variables, clauses, clause_indices)| {
            component_proof::ComponentRecord {
                id, formula_hash, variables, clauses, clause_indices,
            }
        }
    ).collect::<Vec<_>>();
    component_proof::verify_evidence(&source, &output_hash, count, &edges, &records)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn verify_cd_children_native(
    source: Vec<Vec<i32>>,
    output_hash: String,
    count: usize,
    edges: Vec<(u32, usize)>,
    logged: Vec<(usize, String, Vec<u32>, Vec<Vec<i32>>, Vec<usize>)>,
) -> PyResult<(bool, Vec<(String, Vec<Vec<i32>>)>, Option<String>)> {
    let records = logged.into_iter().map(
        |(id, formula_hash, variables, clauses, clause_indices)| {
            component_proof::ComponentRecord {
                id, formula_hash, variables, clauses, clause_indices,
            }
        }
    ).collect::<Vec<_>>();
    component_proof::verify_evidence_and_children(
        &source, &output_hash, count, &edges, &records,
    ).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn replay_root_component_certificate_native(
    source: Vec<Vec<i32>>, root_input_hash: String,
    root_output_hash: String, component_count: usize,
    incidence_edges: Vec<(u32, usize)>,
    component_records: Vec<(usize, String, Vec<u32>, Vec<Vec<i32>>, Vec<usize>)>,
    events: Vec<(Option<String>,
        (String, usize, String, String, Vec<i32>,
         Vec<Vec<i32>>, Vec<Vec<i32>>,
         (Vec<i32>, i32, String, i32),
         (Vec<u32>, Vec<(u32, u32)>, String, Vec<(u32, bool)>)))>,
    width_cap: i32, final_hash: String,
) -> PyResult<(bool, Vec<Vec<i32>>, Option<String>)> {
    let records = component_records.into_iter().map(
        |(id, formula_hash, variables, clauses, clause_indices)| {
            component_proof::ComponentRecord {
                id, formula_hash, variables, clauses, clause_indices,
            }
        }
    ).collect::<Vec<_>>();
    let steps = events.into_iter().map(|(component_id, packed)| {
        let (kind, step_id, input_hash, output_hash, assigned, removed,
             added, (subsuming, blocked_literal, proof_digest, ve_var),
             (tree_order, primal_edges, two_sat_status, two_sat_assignment)) =
             packed;
        component_context_replay::ContextLocalStep {
            component_id,
            step: local_replay::LocalReplayStep {
                kind, step_id, input_hash, output_hash, assigned, removed,
                added, subsuming, blocked_literal, proof_digest, ve_var,
                tree_order, primal_edges, two_sat_status, two_sat_assignment,
            },
        }
    }).collect::<Vec<_>>();
    let out = component_context_replay::replay_single_root_cd(
        &source, &root_input_hash, &root_output_hash, component_count,
        &incidence_edges, &records, &steps, width_cap, &final_hash,
    ).map_err(PyValueError::new_err)?;
    Ok((out.verified, out.final_clauses, out.error))
}

#[cfg(feature = "python")]
#[pyfunction]
fn replay_prefixed_component_certificate_native(
    source: Vec<Vec<i32>>,
    prefix: Vec<(String, usize, String, String, Vec<i32>,
                 Vec<Vec<i32>>, Vec<Vec<i32>>,
                 (Vec<i32>, i32, String, i32),
                 (Vec<u32>, Vec<(u32, u32)>, String, Vec<(u32, bool)>))>,
    cd_step_id: usize, cd_input_hash: String, cd_output_hash: String,
    count: usize, edges: Vec<(u32, usize)>,
    records: Vec<(usize, String, Vec<u32>, Vec<Vec<i32>>, Vec<usize>)>,
    suffix: Vec<(Option<String>,
                 (String, usize, String, String, Vec<i32>,
                  Vec<Vec<i32>>, Vec<Vec<i32>>,
                  (Vec<i32>, i32, String, i32),
                  (Vec<u32>, Vec<(u32, u32)>, String, Vec<(u32, bool)>)))>,
    width_cap: i32, final_hash: String,
) -> PyResult<(bool, Vec<Vec<i32>>, Option<String>)> {
    let unpack = |packed: (
        String, usize, String, String, Vec<i32>, Vec<Vec<i32>>,
        Vec<Vec<i32>>, (Vec<i32>, i32, String, i32),
        (Vec<u32>, Vec<(u32,u32)>, String, Vec<(u32,bool)>),
    )| {
        let (kind, step_id, input_hash, output_hash, assigned, removed,
             added, (subsuming, blocked_literal, proof_digest, ve_var),
             (tree_order, primal_edges, two_sat_status, two_sat_assignment))
            = packed;
        local_replay::LocalReplayStep {
            kind, step_id, input_hash, output_hash, assigned, removed,
            added, subsuming, blocked_literal, proof_digest, ve_var,
            tree_order, primal_edges, two_sat_status, two_sat_assignment,
        }
    };
    let events = prefix.into_iter().map(unpack).collect::<Vec<_>>();
    let scoped = suffix.into_iter().map(|(component_id, step)| {
        component_context_replay::ContextLocalStep {
            component_id, step: unpack(step),
        }
    }).collect::<Vec<_>>();
    let full_records = records.into_iter().map(
        |(id, formula_hash, variables, clauses, clause_indices)| {
            component_proof::ComponentRecord {
                id, formula_hash, variables, clauses, clause_indices,
            }
        }
    ).collect::<Vec<_>>();
    let out = component_context_replay::replay_prefixed_root_cd(
        &source, &events, cd_step_id, &cd_input_hash, &cd_output_hash,
        count, &edges, &full_records, &scoped, width_cap, &final_hash,
    ).map_err(PyValueError::new_err)?;
    Ok((out.verified, out.final_clauses, out.error))
}

#[cfg(feature = "python")]
#[pyfunction]
fn build_2sat_scc_resolution_native(
    source: Vec<Vec<i32>>, requested_variable: Option<i32>,
) -> PyResult<(u32, Vec<(i32,i32,Vec<i32>)>,
               Vec<(i32,i32,Vec<i32>)>, Vec<Vec<i32>>)> {
    let proof = two_sat_scc_witness::build_2sat_scc_resolution_proof(
        &source, requested_variable,
    ).map_err(PyValueError::new_err)?;
    let packed = |edges: Vec<two_sat_scc_witness::ProofEdge>| {
        edges.into_iter().map(|edge|
            (edge.source, edge.target, edge.clause)).collect::<Vec<_>>()
    };
    Ok((proof.variable,packed(proof.path_pos_to_neg),
        packed(proof.path_neg_to_pos),proof.derived_clauses))
}

#[cfg(feature = "python")]
#[pyfunction]
fn factor_elimination_order_native(
    scopes: Vec<Vec<i32>>, nvars: i32, nsource: i32,
    mode: String, beam: i32,
) -> PyResult<(usize, usize, Vec<i32>)> {
    let result=order_experiments::elimination_order(
        &scopes,nvars,nsource,&mode,beam,
    ).map_err(PyValueError::new_err)?;
    Ok((result.induced_width,result.added_fill_edges,result.order))
}

#[cfg(feature = "python")]
#[pyfunction]
fn replay_factor_elimination_width_native(
    scopes: Vec<Vec<i32>>, nvars: i32, order: Vec<i32>,
) -> PyResult<usize> {
    order_experiments::replay_elimination_width(&scopes,nvars,&order)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn unit_conflict_native(
    source: Vec<Vec<i32>>, assumed_literal: i32,
) -> PyResult<bool> {
    failed_literal_probe::unit_conflict(&source,assumed_literal)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn probe_forced_relations_native(
    source: Vec<Vec<i32>>, max_probes: i32,
) -> PyResult<(Vec<Vec<i32>>, usize, Vec<i32>, bool, String, String)> {
    let result=failed_literal_probe::probe_forced_relations(&source,max_probes)
        .map_err(PyValueError::new_err)?;
    Ok((result.clauses,result.checked_variables,result.forced_literals,
        result.both_assumptions_conflict,result.source_hash,
        result.candidate_hash))
}

#[cfg(feature = "python")]
#[pyfunction]
fn make_separator_scaling_case_native(
    blocks_per_side: i32, width: i32,
) -> PyResult<(Vec<Vec<i32>>,i32,i32,i32,Vec<i32>)> {
    let x=scaling_families::make_scaling_case(blocks_per_side,width)
        .map_err(PyValueError::new_err)?;
    Ok((x.clauses,x.width,x.blocks_per_side,x.parity_equations,
        x.expected_boundary))
}

#[cfg(feature = "python")]
#[pyfunction]
fn discover_odd_xor_cycle_native(
    source:Vec<Vec<i32>>,
) -> PyResult<Option<(i32,Vec<(i32,u32)>)>> {
    Ok(odd_xor_cycle::discover_odd_xor_cycle(&source)
        .map_err(PyValueError::new_err)?
        .map(|cycle|(cycle.start,cycle.steps)))
}


#[cfg(feature = "python")]
#[pyfunction]
fn elimination_options_native(
    source: Vec<Vec<i32>>, max_pairs: i32, growth_budget: i32,
) -> PyResult<Vec<(u32, Vec<Vec<i32>>)>> {
    let cnf = cnf::CanonicalCnf::from_signed(&source).map_err(PyValueError::new_err)?;
    Ok(two_ply_lookahead::elimination_options(&cnf, max_pairs, growth_budget)
        .into_iter().map(|(pivot, result)| (pivot, result.clauses)).collect())
}

#[cfg(feature = "python")]
#[pyfunction]
fn two_ply_pivot_native(
    source: Vec<Vec<i32>>, max_pairs: i32,
    growth_budget: i32, beam_width: i32,
) -> PyResult<Vec<Vec<i32>>> {
    let cnf = cnf::CanonicalCnf::from_signed(&source).map_err(PyValueError::new_err)?;
    Ok(two_ply_lookahead::two_ply_pivot(&cnf, max_pairs, growth_budget, beam_width)
        .map_err(PyValueError::new_err)?.clauses)
}


#[cfg(feature = "python")]
#[pyfunction]
fn adaptive_pivot_native(
    source: Vec<Vec<i32>>, max_pairs: i32, growth_budget: i32,
    beam_width: i32, expansion_budget: i32, max_depth: i32,
    ambiguity_margin: f64,
) -> PyResult<(Vec<Vec<i32>>, String, usize, usize, f64, f64)> {
    let cnf = cnf::CanonicalCnf::from_signed(&source).map_err(PyValueError::new_err)?;
    let out = adaptive_lookahead::adaptive_pivot(
        &cnf, max_pairs, growth_budget, beam_width, expansion_budget,
        max_depth, ambiguity_margin,
    ).map_err(PyValueError::new_err)?;
    Ok((out.formula.clauses, out.mode.to_string(), out.expanded, out.depth,
        out.baseline_score, out.candidate_score))
}


#[cfg(feature = "python")]
#[pyfunction]
fn cheap_pivot_features_native(
    source: Vec<Vec<i32>>, max_pairs: i32,
) -> PyResult<(usize, usize, usize, usize)> {
    let cnf = cnf::CanonicalCnf::from_signed(&source).map_err(PyValueError::new_err)?;
    let f = selective_lookahead::cheap_pivot_features(&cnf, max_pairs);
    Ok((f.viable_mixed_pivots, f.pure_pivots, f.variables, f.clauses))
}

#[cfg(feature = "python")]
#[pyfunction]
fn selective_pivot_native(
    source: Vec<Vec<i32>>, max_pairs: i32, min_mixed_pivots: i32,
    max_vars: i32, max_clauses: i32, expansion_budget: i32,
) -> PyResult<(Vec<Vec<i32>>, usize, usize, usize, usize, String, usize)> {
    let cnf = cnf::CanonicalCnf::from_signed(&source).map_err(PyValueError::new_err)?;
    let out = selective_lookahead::selective_pivot(
        &cnf, max_pairs, min_mixed_pivots, max_vars,
        max_clauses, expansion_budget,
    ).map_err(PyValueError::new_err)?;
    Ok((out.formula.clauses, out.features.viable_mixed_pivots,
        out.features.pure_pivots, out.features.variables,
        out.features.clauses, out.mode.to_string(), out.expanded))
}


#[cfg(feature = "python")]
#[pyfunction]
fn parity_separator_fingerprint_native(
    source: Vec<Vec<i32>>, max_k: i32,
) -> PyResult<(String, Vec<Vec<u32>>,
               Vec<(u32,usize,usize,usize,Vec<Vec<usize>>)>)> {
    let result=parity_separator_fingerprint::parity_separator_fingerprint(
        &source,max_k,
    ).map_err(PyValueError::new_err)?;
    let candidates=result.separator_candidates.into_iter().map(|c| (
        c.variable,c.parity_equations_incident,c.components_before,
        c.components_after,c.component_equation_indices,
    )).collect();
    Ok((result.source_sha256,result.parity_equation_supports,candidates))
}


#[cfg(feature = "python")]
#[pyfunction]
fn extract_binary_xor_equations_native(
    source: Vec<Vec<i32>>,
) -> PyResult<Vec<(i32,i32,u32)>> {
    spoke_discovery::extract_binary_xor_equations(&source)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn extract_spoke_paths_native(
    source: Vec<Vec<i32>>,
) -> PyResult<Vec<(i32,i32,i32,u32,u32)>> {
    spoke_discovery::extract_spoke_paths(&source)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn discover_parity_spoke_conflicts_native(
    source: Vec<Vec<i32>>,
) -> PyResult<Vec<((i32,i32),Vec<(i32,u32,Vec<(Vec<i32>,u32,Vec<Vec<i32>>)>)>)>> {
    let conflicts=spoke_discovery::discover_parity_spoke_conflicts(&source)
        .map_err(PyValueError::new_err)?;
    Ok(conflicts.into_iter().map(|conflict| (
        conflict.endpoints,
        conflict.paths.into_iter().map(|path| (
            path.middle,path.syndrome,
            path.equations.into_iter().map(|eq|
                (eq.variables,eq.rhs,eq.source_clauses)
            ).collect(),
        )).collect(),
    )).collect())
}


#[cfg(feature = "python")]
#[pyfunction]
fn bounded_parity_separators_native(
    source:Vec<Vec<i32>>,max_cut:i32,max_shared:i32,max_trials:i32,
) -> PyResult<(String,usize,
               Vec<(Vec<u32>,usize,usize,usize,Vec<Vec<usize>>)>,
               Option<usize>,usize,usize,bool)> {
    let out=multicut_parity_separator::bounded_parity_separators(
        &source,max_cut,max_shared,max_trials,
    ).map_err(PyValueError::new_err)?;
    let cuts=out.candidate_cuts.into_iter().map(|c|(
        c.variables,c.size,c.components_before,c.components_after,
        c.component_equation_indices,
    )).collect();
    Ok((out.source_sha256,out.exact_parity_equations,cuts,
        out.smallest_cut_size,out.shared_variables_considered,
        out.trials,out.budget_exhausted))
}


#[cfg(feature = "python")]
#[pyfunction]
fn graph_invariants_native(
    source:Vec<Vec<i32>>,
) -> PyResult<Vec<(u32,usize,usize,usize)>> {
    let formula=cnf::CanonicalCnf::from_signed(&source)
        .map_err(PyValueError::new_err)?;
    let stats=structural_operator_invention::graph_invariants(&formula);
    Ok(formula.variables().into_iter().map(|v|(
        v,stats.degree[&v],stats.fill[&v],stats.xor_degree[&v],
    )).collect())
}

#[cfg(feature = "python")]
#[pyfunction]
fn eliminate_with_policy_native(
    source:Vec<Vec<i32>>,policy:String,
    max_pairs:i32,max_clause_growth:i32,
) -> PyResult<Vec<Vec<i32>>> {
    let formula=cnf::CanonicalCnf::from_signed(&source)
        .map_err(PyValueError::new_err)?;
    Ok(structural_operator_invention::eliminate_with_policy(
        &formula,&policy,max_pairs,max_clause_growth,
    ).map_err(PyValueError::new_err)?.clauses)
}


#[cfg(feature = "python")]
#[pyfunction]
fn choose_threshold_native(
    rows:Vec<(i32,i32,i32,f64,f64,f64,f64)>,cost_weight:f64,
) -> PyResult<(i32,f64,usize,usize,f64)> {
    let observations=rows.into_iter().map(|(
        mixed_pivots,variables,clauses,
        adaptive_score,greedy_score,adaptive_ms,greedy_ms,
    )|cost_sensitive_gate::Observation {
        mixed_pivots,variables,clauses,adaptive_score,greedy_score,
        adaptive_ms,greedy_ms,
    }).collect::<Vec<_>>();
    let out=cost_sensitive_gate::choose_threshold(
        &observations,cost_weight,
    ).map_err(PyValueError::new_err)?;
    Ok((out.threshold,out.train_utility,
        out.selected_train_cases,out.train_cases,out.cost_weight))
}

#[cfg(feature = "python")]
#[pyfunction]
fn cost_sensitive_pivot_native(
    source:Vec<Vec<i32>>,threshold:i32,max_pairs:i32,
) -> PyResult<(Vec<Vec<i32>>,usize,usize,usize,usize,String,usize)> {
    let out=cost_sensitive_gate::cost_sensitive_pivot(
        &source,threshold,max_pairs,
    ).map_err(PyValueError::new_err)?;
    Ok((out.formula.clauses,
        out.features.viable_mixed_pivots,out.features.pure_pivots,
        out.features.variables,out.features.clauses,
        out.mode.to_string(),out.expanded))
}


#[cfg(feature = "python")]
#[pyfunction]
fn articulation_vertices_native(
    graph:Vec<(i32,Vec<i32>)>,
) -> PyResult<Vec<i32>> {
    separator_structural_priority::articulation_vertices(&graph)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn prioritized_singletons_native(
    graph:Vec<(i32,Vec<i32>)>,
) -> PyResult<Vec<i32>> {
    separator_structural_priority::prioritized_singletons(&graph)
        .map_err(PyValueError::new_err)
}


#[cfg(feature = "python")]
#[pyfunction]
fn vertex_coupling_pairs_native(
    graph:Vec<(i32,Vec<i32>)>,
) -> PyResult<(usize,usize,bool,Vec<(i32,i32)>)> {
    let out=vertex_coupling_separator::vertex_coupling_pairs(&graph)
        .map_err(PyValueError::new_err)?;
    Ok((out.vertex_count,out.articulation_scans,
        out.complete_for_two_vertex_cuts,out.candidates))
}

#[cfg(feature = "python")]
#[pyfunction]
fn prioritized_vertex_pairs_native(
    graph:Vec<(i32,Vec<i32>)>,
) -> PyResult<Vec<(i32,i32)>> {
    vertex_coupling_separator::prioritized_vertex_pairs(&graph)
        .map_err(PyValueError::new_err)
}


#[cfg(feature = "python")]
#[pyfunction]
fn two_edge_cut_boundary_pairs_native(
    graph: Vec<(i32,Vec<i32>)>,
) -> PyResult<(usize,usize,usize,Vec<(Vec<i32>,Vec<(i32,i32)>,Vec<usize>,Vec<usize>)>)> {
    let report=global_coupling_separator::two_edge_cut_boundary_pairs(&graph)
        .map_err(PyValueError::new_err)?;
    let candidates=report.candidates.into_iter().map(|row| (
        row.separator,row.cut_edges,row.edge_split_sizes,row.residual_component_sizes
    )).collect();
    Ok((report.vertex_count,report.edge_count,report.edge_pair_checks,candidates))
}

#[cfg(feature = "python")]
#[pyfunction]
fn prioritized_global_pairs_native(
    graph: Vec<(i32,Vec<i32>)>,
) -> PyResult<Vec<(i32,i32)>> {
    global_coupling_separator::prioritized_global_pairs(&graph)
        .map_err(PyValueError::new_err)
}


#[cfg(feature = "python")]
#[pyfunction]
fn sparse_row_mask_native(
    row:Vec<i64>,
) -> PyResult<String> {
    gf2_sparse_row_basis::row_mask_decimal(&row).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn build_sparse_parity_basis_native(
    clause_count:i64, max_row_width:i64, rows:Vec<Vec<i64>>, ordering:String,
) -> PyResult<(Vec<usize>,Vec<Vec<usize>>,Vec<String>)> {
    let cert=gf2_sparse_row_basis::build_sparse_parity_basis(
        clause_count,max_row_width,&rows,&ordering,
    ).map_err(PyValueError::new_err)?;
    Ok((
        cert.selected_indices,
        cert.rows,
        cert.expansions.iter().map(ToString::to_string).collect(),
    ))
}

#[cfg(feature = "python")]
#[pyfunction]
fn verify_sparse_parity_basis_native(
    clause_count:i64,
    max_row_width:i64,
    rows:Vec<Vec<i64>>,
    cert_clause_count:i64,
    cert_original_row_count:i64,
    selected_indices:Vec<usize>,
    retained_rows:Vec<Vec<i64>>,
    expansions:Vec<String>,
    ordering:String,
) -> PyResult<()> {
    gf2_sparse_row_basis::verify_sparse_parity_basis(
        clause_count,max_row_width,&rows,
        cert_clause_count,cert_original_row_count,
        &selected_indices,&retained_rows,&expansions,&ordering,
    ).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn sparse_accepts_masks_native(
    mask:String, rows:Vec<Vec<i64>>,
) -> PyResult<bool> {
    gf2_sparse_row_basis::accepts_masks_decimal(&mask,&rows)
        .map_err(PyValueError::new_err)
}


#[cfg(feature = "python")]
#[pyfunction]
fn g5_activity_native(
    operations:Vec<g5_elimination_activity::Operation>,variables:Vec<i64>,
) -> PyResult<(Vec<i64>,Vec<(i64,usize)>,Vec<(i64,usize)>,usize,Vec<i64>)> {
    let report=g5_elimination_activity::activity_from_g5_operations(&operations,&variables)
        .map_err(PyValueError::new_err)?;
    Ok((report.ranked_variables,report.touches,report.cancellations,
        report.xor_operations,report.top_pair))
}

#[cfg(feature = "python")]
#[pyfunction]
fn g5_ranked_pairs_native(
    ranked:Vec<i64>,limit:Option<i64>,
) -> PyResult<Vec<(i64,i64)>> {
    g5_elimination_activity::ranked_pair_candidates(&ranked,limit)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn g5_cross_merge_native(
    operations:Vec<g5_elimination_activity::Operation>,variables:Vec<i64>,
) -> PyResult<(Vec<(i64,i64)>,Vec<((i64,i64),usize)>,usize)> {
    let report=g5_elimination_activity::pairwise_cross_merge_activity(&operations,&variables)
        .map_err(PyValueError::new_err)?;
    Ok((report.ranked_pairs,report.scores,report.cross_merge_events))
}


#[cfg(feature = "python")]
#[pyfunction]
fn g5_boundary_path_signal_native(
    initial:Vec<Vec<i64>>,
    operations:Vec<g5_boundary_path_signal::Operation>,
) -> PyResult<(usize,Vec<((i64,i64),usize,usize,usize,usize)>)> {
    let report=g5_boundary_path_signal::boundary_path_candidates_from_g5(
        &initial,&operations,
    ).map_err(PyValueError::new_err)?;
    let candidates=report.candidates.into_iter().map(|row| (
        row.separator,row.path_interior,row.path_edges,row.balance_proxy,
        row.operation_index,
    )).collect();
    Ok((report.xor_operations,candidates))
}


#[cfg(feature = "python")]
#[pyfunction]
fn sparse_column_signatures_native(
    rows:Vec<Vec<usize>>,clause_count:usize,
) -> PyResult<Vec<String>> {
    sparse_parity_checks::column_signatures(&rows,clause_count)
        .map(|rows|rows.iter().map(ToString::to_string).collect())
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn sparse_validate_rows_native(
    clause_count:usize,max_width:usize,rows:Vec<Vec<usize>>,
) -> PyResult<()> {
    sparse_parity_checks::validate_rows(clause_count,max_width,&rows)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn sparse_build_rows_native(
    py:Python<'_>,
    clause_count:usize,max_width:usize,max_attempts:usize,rng:Py<PyAny>,
) -> PyResult<Vec<Vec<usize>>> {
    sparse_parity_checks::build_sparse_odd_rows(
        clause_count,max_width,max_attempts,||{
            rng.call_method0(py,"random").map_err(|e|e.to_string())?
                .extract::<f64>(py).map_err(|e|e.to_string())
        },
    ).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn sparse_low_weight_collisions_native(
    rows:Vec<Vec<usize>>,clause_count:usize,max_weight:i64,
) -> PyResult<usize> {
    sparse_parity_checks::low_weight_collisions(&rows,clause_count,max_weight)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn sparse_row_scope_native(
    source:Vec<Vec<i32>>,row:Vec<usize>,
) -> PyResult<usize> {
    sparse_parity_checks::source_row_scope(&source,&row)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn sparse_audit_small_native(
    source:Vec<Vec<i32>>,nvars:usize,rows:Vec<Vec<usize>>,max_variables:i64,
) -> PyResult<(usize,usize,usize,usize,f64)> {
    sparse_parity_checks::audit_sparse_small(
        &source,nvars,&rows,max_variables,
    ).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn sparse_min_degree_width_native(
    scopes:Vec<Vec<i64>>,nvars:i64,
) -> PyResult<usize> {
    sparse_parity_checks::min_degree_elimination_width(&scopes,nvars)
        .map_err(PyValueError::new_err)
}


#[cfg(feature = "python")]
#[pyfunction]
fn expression_conjecture_evaluate_native(op:String,a:String,b:String,
    metrics:BTreeMap<String,i64>)->PyResult<i64>{
    expression_conjecture_search::evaluate(&op,&a,&b,&metrics)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn expression_conjecture_run_native(training:Vec<BTreeMap<String,i64>>,
    holdout:Vec<expression_conjecture_search::Holdout>,max_candidates:usize)
    ->PyResult<(usize,usize,Vec<String>,Vec<expression_conjecture_search::Rejected>)>{
    expression_conjecture_search::run(&training,&holdout,max_candidates)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn graph_conjecture_metrics_native(n:usize,edges:Vec<(usize,usize)>)
    ->PyResult<BTreeMap<String,i64>>{
    graph_conjecture_lab::metrics(n,&edges).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn graph_conjecture_run_native(training:Vec<graph_conjecture_lab::Metrics>,
    holdout:Vec<graph_conjecture_lab::Holdout>)
    ->PyResult<(usize,usize,Vec<String>,Vec<graph_conjecture_lab::Rejected>)>{
    graph_conjecture_lab::run(&training,&holdout).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn conjecture_triage_run_native(survivors:Vec<String>,
    adversarial:Vec<conjecture_triage::Adversarial>)
    ->PyResult<(Vec<String>,Vec<String>,Vec<conjecture_triage::Falsified>)>{
    conjecture_triage::triage(&survivors,&adversarial).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn conditional_graph_conjectures_run_native(
    training:Vec<conditional_graph_conjectures::Record>,
    holdout:Vec<conditional_graph_conjectures::Record>)
    ->PyResult<(usize,usize,Vec<String>,Vec<conditional_graph_conjectures::Falsified>)>{
    conditional_graph_conjectures::run(&training,&holdout).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn targeted_graph_challenge_native(cases:Vec<targeted_graph_families::Case>)
    ->PyResult<(Vec<targeted_graph_families::Failure>,Vec<targeted_graph_families::Failure>)>{
    targeted_graph_families::challenge(&cases).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn lean_numeric_emit_native(cases:Vec<lean_numeric_certificate_export::Case>)->String{
    lean_numeric_certificate_export::emit(&cases)
}

#[cfg(feature = "python")]
#[pyfunction]
fn lean_ascii_serialize_native(n:usize,edges:Vec<(usize,usize)>,
    colors:Vec<usize>,clique:Vec<usize>,k:usize)->PyResult<Vec<u8>>{
    if n==0 || k==0{return Err(PyValueError::new_err("positive graph/order required"));}
    Ok(lean_ascii_certificate_export::serialize(n,&edges,&colors,&clique,k))
}

#[cfg(feature = "python")]
#[pyfunction]
fn lean_ascii_bytes_native(data:Vec<u8>)->String{
    lean_ascii_certificate_export::lean_bytes(&data)
}

#[cfg(feature = "python")]
#[pyfunction]
fn lean_ascii_emit_native(cases:Vec<lean_ascii_certificate_export::Case>)->PyResult<String>{
    if cases.iter().any(|(_,n,_,_,_,k)|*n==0 || *k==0){
        return Err(PyValueError::new_err("positive graph/order required"));
    }
    Ok(lean_ascii_certificate_export::emit(&cases))
}

#[cfg(feature = "python")]
#[pyfunction]
fn lean_color_fin_values_native(name:String,var:String,n:usize,codomain:usize,
    values:Vec<usize>)->PyResult<String>{
    if n==0 || codomain==0 || values.len()!=n{
        return Err(PyValueError::new_err("invalid finite value domain"));
    }
    Ok(lean_color_certificate_export::fin_values(&name,&var,n,codomain,&values))
}

#[cfg(feature = "python")]
#[pyfunction]
fn lean_color_find_clique_native(n:usize,edges:Vec<(usize,usize)>,size:usize)
    ->Option<Vec<usize>>{
    lean_color_certificate_export::find_clique(n,&edges,size)
}

#[cfg(feature = "python")]
#[pyfunction]
fn lean_color_emit_native(cases:Vec<lean_color_certificate_export::Case>)->PyResult<String>{
    if cases.iter().any(|(_,n,_,colors,clique,k)|*n==0 || *k==0 || colors.len()!=*n || clique.len()!=*k){
        return Err(PyValueError::new_err("invalid coloring domain"));
    }
    Ok(lean_color_certificate_export::emit(&cases))
}

#[cfg(feature = "python")]
#[pyfunction]
fn crc_variable_eliminate_native(clauses:Vec<(String,String)>,variables:Vec<usize>,
    max_width:usize,max_operations:usize)
    ->PyResult<Option<crc_variable_elimination::Answer>>{
    crc_variable_elimination::count(&clauses,&variables,max_width,max_operations)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn dsatur_exact_k_coloring_native(n:usize,edges:Vec<(usize,usize)>,k:usize)
    ->PyResult<Option<Vec<usize>>>{
    dsatur_adversarial_lab::exact_k_coloring(n,&edges,k).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn color_bounded_recolor_native(n:usize,edges:Vec<(usize,usize)>,initial:Vec<usize>,
    max_changed:usize,max_nodes:usize)->PyResult<color_repair_lab::Answer>{
    color_repair_lab::recolor(n,&edges,&initial,max_changed,max_nodes)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn kempe_swaps_native(n:usize,edges:Vec<(usize,usize)>,initial:Vec<usize>)
    ->PyResult<Vec<kempe_repair_lab::Variant>>{
    kempe_repair_lab::swaps(n,&edges,&initial).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn double_kempe_repair_native(n:usize,edges:Vec<(usize,usize)>,original:Vec<usize>,
    first_limit:usize,second_limit:usize,total_limit:usize,recolor_nodes:usize)
    ->PyResult<double_kempe_lab::Answer>{
    double_kempe_lab::repair(n,&edges,&original,first_limit,second_limit,total_limit,recolor_nodes)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn greedy_clique_lower_bound_native(n:usize,edges:Vec<(usize,usize)>)->PyResult<usize>{
    structured_coloring_study::greedy_clique(n,&edges).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn color_selector_signals_native(n:usize,edges:Vec<(usize,usize)>,colors:Vec<isize>)
    ->PyResult<color_selector_lab::Signals>{
    color_selector_lab::signals(n,&edges,&colors).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn color_selector_triggers_native(rule:String,k:isize,gap:isize,
    last_size:usize,min_class:usize,singleton:usize)->PyResult<bool>{
    color_selector_lab::triggers(&rule,k,gap,last_size,min_class,singleton)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn color_selector_confusion_native(rule:String,
    rows:Vec<(bool,isize,isize,usize,usize,usize)>)
    ->PyResult<(usize,usize,usize,usize,usize,usize)>{
    color_selector_lab::confusion(&rule,&rows).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn dsatur_greedy_coloring_native(n:usize,edges:Vec<(usize,usize)>)
    ->PyResult<(usize,Vec<usize>)>{
    nonedge_matching_dsatur::greedy(n,&edges).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn nonedge_graph_bounds_native(n:usize,edges:Vec<(usize,usize)>)
    ->PyResult<nonedge_graph_bounds::Answer>{
    nonedge_graph_bounds::bounds(n,&edges).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn matching_color_bound_native(n:usize,edges:Vec<(usize,usize)>)
    ->PyResult<nonedge_matching_bound::Answer>{
    nonedge_matching_bound::matching_bound(n,&edges).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn anf_xor_native(left:Vec<Vec<usize>>,right:Vec<Vec<usize>>)
    ->Vec<Vec<usize>>{violation_image_anf::xor(&left,&right)}

#[cfg(feature = "python")]
#[pyfunction]
fn anf_multiply_native(left:Vec<Vec<usize>>,right:Vec<Vec<usize>>)
    ->Vec<Vec<usize>>{violation_image_anf::multiply(&left,&right)}

#[cfg(feature = "python")]
#[pyfunction]
fn anf_substitute_native(poly:Vec<Vec<usize>>,variable:usize,bit:bool)
    ->Vec<Vec<usize>>{violation_image_anf::substitute(&poly,variable,bit)}

#[cfg(feature = "python")]
#[pyfunction]
fn anf_canonical_equations_native(equations:Vec<Vec<Vec<usize>>>)
    ->Vec<Vec<Vec<usize>>>{violation_image_anf::canonical_equations(&equations)}

#[cfg(feature = "python")]
#[pyfunction]
fn anf_evaluate_native(poly:Vec<Vec<usize>>,assignment_bits:String)
    ->PyResult<bool>{
    violation_image_anf::evaluate(&poly,&assignment_bits)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn anf_clause_violation_native(clause:Vec<i64>)->PyResult<Vec<Vec<usize>>>{
    violation_image_anf::clause_violation(&clause)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn anf_source_violations_native(source:Vec<Vec<i64>>)
    ->PyResult<Vec<Vec<Vec<usize>>>>{
    violation_image_anf::source_violations(&source)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn anf_row_violations_native(clauses:Vec<Vec<Vec<usize>>>,rows:Vec<Vec<usize>>)
    ->PyResult<Vec<Vec<Vec<usize>>>>{
    violation_image_anf::row_violations(&clauses,&rows)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn anf_geometry_native(nvars:usize,clauses:Vec<Vec<Vec<usize>>>,
    rows:Vec<Vec<usize>>)->PyResult<violation_image_anf::GeometryAnswer>{
    violation_image_anf::geometry(nvars,&clauses,&rows)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn anf_count_conditioned_native(equations:Vec<Vec<Vec<usize>>>,
    nvars:usize,max_states:usize,max_separator_size:usize,
    max_candidate_checks:usize)
    ->PyResult<anf_separator_conditioning::ConditionAnswer>{
    anf_separator_conditioning::count_conditioned(
        &equations,nvars,max_states,max_separator_size,max_candidate_checks)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn anf_polynomial_scopes_native(equations:Vec<Vec<Vec<usize>>>)
    ->PyResult<Vec<String>>{
    anf_separator_conditioning::polynomial_scopes(&equations)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn xor_normalize_variables_native(variables:Vec<usize>) ->PyResult<Vec<usize>>{
    xor_equations::normalize_variables(&variables).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn xor_evaluate_native(variables:Vec<usize>,rhs:u8,
    assignment:Vec<(usize,bool)>)->Option<bool>{
    xor_equations::evaluate(&variables,rhs,&assignment)
}

#[cfg(feature = "python")]
#[pyfunction]
fn xor_substitute_native(variables:Vec<usize>,rhs:u8,
    assignment:Vec<(usize,bool)>)->(Vec<usize>,u8){
    xor_equations::substitute(&variables,rhs,&assignment)
}

#[cfg(feature = "python")]
#[pyfunction]
fn xor_system_substitute_native(equations:Vec<(Vec<usize>,u8)>,
    assignment:Vec<(usize,bool)>)->Vec<(Vec<usize>,u8)>{
    xor_equations::substitute_system(&equations,&assignment)
}

#[cfg(feature = "python")]
#[pyfunction]
fn xor_gaussian_native(equations:Vec<(Vec<usize>,u8)>)
    ->xor_equations::GaussianAnswer{
    xor_equations::gaussian(&equations)
}

#[cfg(feature = "python")]
#[pyfunction]
fn xor_verify_assignment_native(equations:Vec<(Vec<usize>,u8)>,
    assignment:Vec<(usize,bool)>)->bool{
    xor_equations::verify_assignment(&equations,&assignment)
}

#[cfg(feature = "python")]
#[pyfunction]
fn xor_canonical_cnf_native(variables:Vec<usize>,rhs:u8,max_width:usize)
    ->PyResult<Vec<Vec<i64>>>{
    xor_equations::canonical_xor_cnf(&variables,rhs,max_width)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn xor_extra_touching_clauses_native(clauses:Vec<Vec<i64>>,
    variables:Vec<usize>,source_clauses:Vec<Vec<i64>>)->Vec<Vec<i64>>{
    xor_equations::extra_touching_clauses(&clauses,&variables,&source_clauses)
}

#[cfg(feature = "python")]
#[pyfunction]
fn xor_detect_cnf_patterns_native(clauses:Vec<Vec<i64>>,
    include_3var:bool,max_k:usize)
    ->PyResult<(Vec<xor_equations::DetectedPattern>,
        Vec<xor_equations::DetectionDiagnostic>)>{
    xor_equations::detect_cnf_patterns(&clauses,include_3var,max_k)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn xor_parse_lines_native(content:String)
    ->PyResult<Vec<(Vec<i64>,u8)>>{
    xor_equations::parse_xor_lines(&content).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn xor_drat_resolve_fast_native(a:Vec<i64>,b:Vec<i64>,pivot:i64)
    ->Option<Vec<i64>>{
    xor_drat_resolution::resolve_fast(&a,&b,pivot)
}

#[cfg(feature = "python")]
#[pyfunction]
fn xor_sparse_schedule_native(equations:Vec<(Vec<usize>,u8)>)
    ->xor_sparse_schedule::ScheduleAnswer{
    xor_sparse_schedule::schedule(&equations)
}

#[cfg(feature = "python")]
#[pyfunction]
fn xor_proof_order_native(pivots:Vec<usize>,variables:Vec<usize>)->Vec<usize>{
    xor_proof_order::proof_order(&pivots,&variables)
}

#[cfg(feature = "python")]
#[pyfunction]
fn xor_gaussian_order_stats_native(pivots:Vec<usize>,variables:Vec<usize>,
    trace_widths:Vec<usize>,detected_widths:Vec<usize>,unsat:bool)
    ->(Vec<usize>,usize,usize,Option<usize>){
    xor_proof_order::gaussian_stats(&pivots,&variables,&trace_widths,&detected_widths,unsat)
}

#[cfg(feature = "python")]
#[pyfunction]
fn xor_drat_clause_line_native(clause:Vec<i64>)->String{
    xor_proof_emit::clause_line(&clause)
}

#[cfg(feature = "python")]
#[pyfunction]
fn xor_drat_line_size_native(clause:Vec<i64>)->usize{
    xor_proof_emit::line_size(&clause)
}

#[cfg(feature = "python")]
#[pyfunction]
fn xor_drat_emit_decision_native(clause:Vec<i64>,already_active:bool,
    emitted:usize,proof_bytes:usize,max_width:usize,max_proof_clauses:usize,
    max_proof_bytes:usize)->xor_proof_emit::EmitDecision{
    xor_proof_emit::emit(&clause,already_active,emitted,proof_bytes,max_width,
        max_proof_clauses,max_proof_bytes)
}

#[cfg(feature = "python")]
#[pyfunction]
fn xor_ve_refutation_native(original:Vec<Vec<i64>>,support:Vec<Vec<i64>>,
    order:Vec<usize>,max_clauses:usize,max_bytes:usize,timeout_seconds:Option<f64>)
    ->xor_ve_refutation::Answer{
    xor_ve_refutation::refute(&original,&support,&order,max_clauses,max_bytes,timeout_seconds)
}

#[cfg(feature = "python")]
#[pyfunction]
fn anf_count_common_zeros_native(equations:Vec<Vec<Vec<usize>>>,
    nvars:usize,max_states:usize)->PyResult<violation_image_anf::CountAnswer>{
    violation_image_anf::count_zeros(&equations,nvars,max_states)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn anf_residual_component_sizes_native(scopes:Vec<String>,removed_mask:String)
    ->PyResult<Vec<usize>>{
    anf_separator_conditioning::component_sizes(&scopes,&removed_mask)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn anf_find_bounded_separator_native(equations:Vec<Vec<Vec<usize>>>,
    nvars:usize,max_separator_size:usize,max_candidate_checks:usize)
    ->PyResult<(Option<Vec<usize>>,usize)>{
    anf_separator_conditioning::find_separator(
        &equations,nvars,max_separator_size,max_candidate_checks)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn anf_count_structured_native(equations:Vec<Vec<Vec<usize>>>,
    nvars:usize,max_states:usize)->PyResult<anf_structured_counter::Answer>{
    anf_structured_counter::count(&equations,nvars,max_states)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn crc_cutset_enumerate_native(normalized:Vec<(String,String)>,boundary:Vec<usize>,
    separator:Vec<usize>,max_component:usize,max_states:usize,max_branches:usize)
    ->PyResult<Option<(String,usize,usize,usize)>>{
    crc_cutset_count::count(&normalized,&boundary,&separator,
        max_component,max_states,max_branches).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn crc_separator_discover_native(normalized:Vec<(String,String)>,boundary:Vec<usize>,
    left:Vec<usize>,right:Vec<usize>,max_separator:usize,max_edges:usize)
    ->PyResult<Option<(Vec<usize>,usize,usize,usize)>>{
    crc_separator_discovery::discover(&normalized,&boundary,&left,&right,
        max_separator,max_edges).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn crc_orbit_walsh_native(normalized:Option<Vec<(String,String)>>,
    boundary:Vec<usize>,modes:Vec<String>,max_missing:usize)
    ->PyResult<Option<(Vec<(String,String,String)>,usize,usize,usize)>>{
    crc_orbit_oracle::query(normalized,&boundary,&modes,max_missing)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn crc_conflict_prepare_native(normalized:Vec<(String,String)>,boundary:Vec<usize>,
    modes:Vec<String>,max_clauses:usize,max_variables:usize,max_base_modes:usize)
    ->PyResult<Option<(Vec<(String,String)>,Vec<String>,Vec<i64>,Vec<String>,usize,usize)>>{
    let result=crc_conflict_oracle::prepare(&normalized,&boundary,&modes,
        max_clauses,max_variables,max_base_modes).map_err(PyValueError::new_err)?;
    Ok(result.map(|r|(r.base,r.local_masks,r.values,r.needed,r.exceptions,r.variables)))
}

#[cfg(feature = "python")]
#[pyfunction]
fn crc_conflict_convolve_native(modes:Vec<String>,local_masks:Vec<String>,
    values:Vec<i64>,coefficients:Vec<(String,String,String)>,q:usize)
    ->PyResult<Vec<(String,String,String)>>{
    crc_conflict_oracle::convolve(&modes,&local_masks,&values,&coefficients,q)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn crc_shannon_walsh_native(normalized:Option<Vec<(String,String)>>,
    boundary:Vec<usize>,modes:Vec<String>,max_states:usize)
    ->PyResult<Option<(Vec<(String,String,String)>,usize,usize)>>{
    crc_shannon_oracle::query(normalized,&boundary,&modes,max_states)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn crc_defect_walsh_native(normalized:Option<Vec<(String,String)>>,
    boundary:Vec<usize>,modes:Vec<String>,max_missing:usize,
    max_defect_variables:usize,max_subset_checks:usize)
    ->PyResult<Option<(Vec<(String,String,String)>,usize,usize,usize,usize)>>{
    crc_defect_oracle::query(normalized,&boundary,&modes,
        max_missing,max_defect_variables,max_subset_checks).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn crc_independence_modes_native(left:Vec<String>,right:Vec<String>)->PyResult<Vec<String>>{
    crc_independence_audit::mode_masks(&left,&right).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn crc_independence_audit_native(left:Vec<String>,right:Vec<String>,
    coefficients:Vec<(String,String,String)>)
    ->PyResult<Option<(String,String,String,String)>>{
    crc_independence_audit::audit(&left,&right,&coefficients).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn claim_boundary_scan_native(text:String)->Vec<(String,String,bool)>{
    claim_boundary::scan(&text).into_iter().map(|finding|
        (finding.phrase,finding.context,finding.allowed)).collect()
}

#[cfg(feature = "python")]
#[pyfunction]
fn geometry_aware_rows_native(source:Vec<Vec<i32>>,nvars:usize,width:usize)
    ->PyResult<Vec<Vec<usize>>>{
    geometry_aware_parity::build(&source,nvars,width).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn geometry_primal_pairs_native(source:Vec<Vec<i32>>)->Vec<(usize,usize)>{
    geometry_aware_parity::primal_pairs(&source)
}

#[cfg(feature = "python")]
#[pyfunction]
fn dense_geometry_rows_native(bitmaps:Vec<String>,clause_count:usize)->PyResult<Vec<Vec<usize>>>{
    constraint_geometry::rows_from_bitmaps(&bitmaps,clause_count).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn dense_geometry_validate_native(source:Vec<Vec<i32>>,nvars:usize,clause_count:usize,
    digest:String,security_bits:usize,rows:Vec<Vec<usize>>)->PyResult<()>{
    constraint_geometry::validate(&source,nvars,clause_count,&digest,security_bits,&rows)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn dense_geometry_audit_native(source:Vec<Vec<i32>>,nvars:usize,
    rows:Vec<Vec<usize>>,max_variables:usize)->PyResult<(usize,usize,usize,usize,Vec<usize>)>{
    constraint_geometry::audit(&source,nvars,&rows,max_variables).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn dense_geometry_singleton_bound_native(count:usize,width:usize)->PyResult<usize>{
    constraint_geometry::singleton_bound(count,width).map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn dense_geometry_row_stats_native(rows:Vec<Vec<usize>>)->(usize,f64,usize){
    constraint_geometry::row_stats(&rows)
}

#[cfg(feature = "python")]
#[pyfunction]
fn finite_parity_source_digest_native(
    source:Vec<Vec<i32>>,
) -> String {
    eth_clause_violation_parity::source_digest(&source)
}

#[cfg(feature = "python")]
#[pyfunction]
fn finite_parity_violation_mask_native(
    source:Vec<Vec<i32>>,assignment:String,
) -> PyResult<String> {
    eth_clause_violation_parity::decimal_violation(&source,&assignment)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn finite_parity_accepts_native(
    violations:String,rows:Vec<Vec<usize>>,
) -> PyResult<bool> {
    eth_clause_violation_parity::decimal_parity_accepts(&violations,&rows)
        .map_err(PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pyfunction]
fn finite_parity_build_native(
    source:Vec<Vec<i32>>,nvars:i64,
    candidates:Vec<Vec<usize>>,max_rows:Option<i64>,
) -> PyResult<(Vec<Vec<usize>>,Vec<usize>,usize)> {
    let result=eth_clause_violation_parity::build_finite_sketch(
        &source,nvars,&candidates,max_rows,
    ).map_err(PyValueError::new_err)?;
    Ok((result.rows,result.survivors,result.satisfying_count))
}

#[cfg(feature = "python")]
#[pyfunction]
fn finite_parity_verify_native(
    source:Vec<Vec<i32>>,nvars:i64,rows:Vec<Vec<usize>>,
) -> bool {
    eth_clause_violation_parity::verify_finite_sketch(&source,nvars,&rows)
}

#[cfg(feature = "python")]
#[pyfunction]
fn finite_parity_complete_primal_native(
    source:Vec<Vec<i32>>,nvars:i64,
) -> bool {
    eth_clause_violation_parity::is_complete_primal(&source,nvars)
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
    module.add_function(wrap_pyfunction!(canonical_cnf_hash_native, module)?)?;
    module.add_function(wrap_pyfunction!(first_subsumption_native, module)?)?;
    module.add_function(wrap_pyfunction!(symbolic_bound_path_native, module)?)?;
    module.add_function(wrap_pyfunction!(symbolic_normalize_native, module)?)?;
    module.add_function(wrap_pyfunction!(symbolic_derive_pair_native, module)?)?;
    module.add_function(wrap_pyfunction!(symbolic_known_axioms_native, module)?)?;
    module.add_function(wrap_pyfunction!(targeted_graph_family_native, module)?)?;
    module.add_function(wrap_pyfunction!(conjecture_normalize_native, module)?)?;
    module.add_function(wrap_pyfunction!(conjecture_identity_key_native, module)?)?;
    module.add_function(wrap_pyfunction!(conjecture_known_identities_native, module)?)?;
    module.add_function(wrap_pyfunction!(native_unsat_trace_metadata_supported_native, module)?)?;
    module.add_function(wrap_pyfunction!(bipartition_audit_native, module)?)?;
    module.add_function(wrap_pyfunction!(possible_two_xor_patterns_native, module)?)?;
    module.add_function(wrap_pyfunction!(full_cnf_anchors_separated_native, module)?)?;
    module.add_function(wrap_pyfunction!(independent_parity_cut_width_native, module)?)?;
    module.add_function(wrap_pyfunction!(make_hidden_separator_native, module)?)?;
    module.add_function(wrap_pyfunction!(make_hard_separator_case_native, module)?)?;
    module.add_function(wrap_pyfunction!(satlib_structural_metrics_native, module)?)?;
    module.add_function(wrap_pyfunction!(spoke_cnf_native, module)?)?;
    module.add_function(wrap_pyfunction!(collapse_spokes_native, module)?)?;
    module.add_function(wrap_pyfunction!(ood_pigeonhole_native, module)?)?;
    module.add_function(wrap_pyfunction!(ood_graph_coloring_native, module)?)?;
    module.add_function(wrap_pyfunction!(ood_tseitin_complete_native, module)?)?;
    module.add_function(wrap_pyfunction!(ood_n_queens_native, module)?)?;
    module.add_function(wrap_pyfunction!(ood_planted_samples_native, module)?)?;
    module.add_function(wrap_pyfunction!(benchmark_family_native, module)?)?;
    module.add_function(wrap_pyfunction!(benchmark_sampled_clauses_native, module)?)?;
    module.add_function(wrap_pyfunction!(parity_compress_native, module)?)?;
    module.add_function(wrap_pyfunction!(parity_reconstruct_native, module)?)?;
    module.add_function(wrap_pyfunction!(parity_rewrite_native, module)?)?;
    module.add_function(wrap_pyfunction!(crc_structural_independence_native, module)?)?;
    module.add_function(wrap_pyfunction!(crc_conditional_independence_native, module)?)?;
    module.add_function(wrap_pyfunction!(aux_local_scopes_native, module)?)?;
    module.add_function(wrap_pyfunction!(aux_direct_scopes_native, module)?)?;
    module.add_function(wrap_pyfunction!(aux_exact_models_native, module)?)?;
    module.add_function(wrap_pyfunction!(aux_weight_profile_native, module)?)?;
    module.add_function(wrap_pyfunction!(dense_geometry_rows_native, module)?)?;
    module.add_function(wrap_pyfunction!(dense_geometry_validate_native, module)?)?;
    module.add_function(wrap_pyfunction!(dense_geometry_audit_native, module)?)?;
    module.add_function(wrap_pyfunction!(dense_geometry_singleton_bound_native, module)?)?;
    module.add_function(wrap_pyfunction!(dense_geometry_row_stats_native, module)?)?;
    module.add_function(wrap_pyfunction!(geometry_aware_rows_native, module)?)?;
    module.add_function(wrap_pyfunction!(geometry_primal_pairs_native, module)?)?;
    module.add_function(wrap_pyfunction!(claim_boundary_scan_native, module)?)?;
    module.add_function(wrap_pyfunction!(crc_independence_modes_native, module)?)?;
    module.add_function(wrap_pyfunction!(crc_independence_audit_native, module)?)?;
    module.add_function(wrap_pyfunction!(crc_defect_walsh_native, module)?)?;
    module.add_function(wrap_pyfunction!(crc_shannon_walsh_native, module)?)?;
    module.add_function(wrap_pyfunction!(crc_conflict_prepare_native, module)?)?;
    module.add_function(wrap_pyfunction!(crc_conflict_convolve_native, module)?)?;
    module.add_function(wrap_pyfunction!(crc_orbit_walsh_native, module)?)?;
    module.add_function(wrap_pyfunction!(crc_separator_discover_native, module)?)?;
    module.add_function(wrap_pyfunction!(crc_cutset_enumerate_native, module)?)?;
    module.add_function(wrap_pyfunction!(expression_conjecture_evaluate_native, module)?)?;
    module.add_function(wrap_pyfunction!(expression_conjecture_run_native, module)?)?;
    module.add_function(wrap_pyfunction!(graph_conjecture_metrics_native, module)?)?;
    module.add_function(wrap_pyfunction!(graph_conjecture_run_native, module)?)?;
    module.add_function(wrap_pyfunction!(conjecture_triage_run_native, module)?)?;
    module.add_function(wrap_pyfunction!(conditional_graph_conjectures_run_native, module)?)?;
    module.add_function(wrap_pyfunction!(targeted_graph_challenge_native, module)?)?;
    module.add_function(wrap_pyfunction!(lean_numeric_emit_native, module)?)?;
    module.add_function(wrap_pyfunction!(lean_ascii_serialize_native, module)?)?;
    module.add_function(wrap_pyfunction!(lean_ascii_bytes_native, module)?)?;
    module.add_function(wrap_pyfunction!(lean_ascii_emit_native, module)?)?;
    module.add_function(wrap_pyfunction!(lean_color_fin_values_native, module)?)?;
    module.add_function(wrap_pyfunction!(lean_color_find_clique_native, module)?)?;
    module.add_function(wrap_pyfunction!(lean_color_emit_native, module)?)?;
    module.add_function(wrap_pyfunction!(crc_variable_eliminate_native, module)?)?;
    module.add_function(wrap_pyfunction!(dsatur_exact_k_coloring_native, module)?)?;
    module.add_function(wrap_pyfunction!(color_bounded_recolor_native, module)?)?;
    module.add_function(wrap_pyfunction!(kempe_swaps_native, module)?)?;
    module.add_function(wrap_pyfunction!(double_kempe_repair_native, module)?)?;
    module.add_function(wrap_pyfunction!(greedy_clique_lower_bound_native, module)?)?;
    module.add_function(wrap_pyfunction!(color_selector_signals_native, module)?)?;
    module.add_function(wrap_pyfunction!(color_selector_triggers_native, module)?)?;
    module.add_function(wrap_pyfunction!(color_selector_confusion_native, module)?)?;
    module.add_function(wrap_pyfunction!(dsatur_greedy_coloring_native, module)?)?;
    module.add_function(wrap_pyfunction!(nonedge_graph_bounds_native, module)?)?;
    module.add_function(wrap_pyfunction!(matching_color_bound_native, module)?)?;
    module.add_function(wrap_pyfunction!(anf_xor_native, module)?)?;
    module.add_function(wrap_pyfunction!(anf_multiply_native, module)?)?;
    module.add_function(wrap_pyfunction!(anf_substitute_native, module)?)?;
    module.add_function(wrap_pyfunction!(anf_canonical_equations_native, module)?)?;
    module.add_function(wrap_pyfunction!(anf_evaluate_native, module)?)?;
    module.add_function(wrap_pyfunction!(anf_clause_violation_native, module)?)?;
    module.add_function(wrap_pyfunction!(anf_source_violations_native, module)?)?;
    module.add_function(wrap_pyfunction!(anf_row_violations_native, module)?)?;
    module.add_function(wrap_pyfunction!(anf_geometry_native, module)?)?;
    module.add_function(wrap_pyfunction!(anf_count_conditioned_native, module)?)?;
    module.add_function(wrap_pyfunction!(anf_polynomial_scopes_native, module)?)?;
    module.add_function(wrap_pyfunction!(xor_normalize_variables_native, module)?)?;
    module.add_function(wrap_pyfunction!(xor_evaluate_native, module)?)?;
    module.add_function(wrap_pyfunction!(xor_substitute_native, module)?)?;
    module.add_function(wrap_pyfunction!(xor_system_substitute_native, module)?)?;
    module.add_function(wrap_pyfunction!(xor_gaussian_native, module)?)?;
    module.add_function(wrap_pyfunction!(xor_verify_assignment_native, module)?)?;
    module.add_function(wrap_pyfunction!(xor_canonical_cnf_native, module)?)?;
    module.add_function(wrap_pyfunction!(xor_extra_touching_clauses_native, module)?)?;
    module.add_function(wrap_pyfunction!(xor_detect_cnf_patterns_native, module)?)?;
    module.add_function(wrap_pyfunction!(xor_parse_lines_native, module)?)?;
    module.add_function(wrap_pyfunction!(xor_drat_resolve_fast_native, module)?)?;
    module.add_function(wrap_pyfunction!(xor_sparse_schedule_native, module)?)?;
    module.add_function(wrap_pyfunction!(xor_proof_order_native, module)?)?;
    module.add_function(wrap_pyfunction!(xor_gaussian_order_stats_native, module)?)?;
    module.add_function(wrap_pyfunction!(xor_drat_clause_line_native, module)?)?;
    module.add_function(wrap_pyfunction!(xor_drat_line_size_native, module)?)?;
    module.add_function(wrap_pyfunction!(xor_drat_emit_decision_native, module)?)?;
    module.add_function(wrap_pyfunction!(xor_ve_refutation_native, module)?)?;
    module.add_function(wrap_pyfunction!(anf_count_common_zeros_native, module)?)?;
    module.add_function(wrap_pyfunction!(anf_residual_component_sizes_native, module)?)?;
    module.add_function(wrap_pyfunction!(anf_find_bounded_separator_native, module)?)?;
    module.add_function(wrap_pyfunction!(anf_count_structured_native, module)?)?;
    module.add_function(wrap_pyfunction!(parse_dimacs_evidence_native, module)?)?;
    module.add_function(wrap_pyfunction!(indexed_rup_witness_native, module)?)?;
    module.add_function(wrap_pyfunction!(check_rup_subset_native, module)?)?;
    module.add_function(wrap_pyfunction!(primal_graph_native, module)?)?;
    module.add_function(wrap_pyfunction!(incidence_components_native, module)?)?;
    module.add_function(wrap_pyfunction!(treewidth_order_native, module)?)?;
    module.add_function(wrap_pyfunction!(verify_treewidth_order_native, module)?)?;
    module.add_function(wrap_pyfunction!(blocked_clause_witness_native, module)?)?;
    module.add_function(wrap_pyfunction!(blocked_clause_digest_native, module)?)?;
    module.add_function(wrap_pyfunction!(build_step_record_native, module)?)?;
    module.add_function(wrap_pyfunction!(stable_certificate_json_native, module)?)?;
    module.add_function(wrap_pyfunction!(certificate_file_digests_native, module)?)?;
    module.add_function(wrap_pyfunction!(compact_certificate_hash_native, module)?)?;
    module.add_function(wrap_pyfunction!(verify_certificate_file_digests_native, module)?)?;
    module.add_function(wrap_pyfunction!(reconstruct_assignment_native, module)?)?;
    module.add_function(wrap_pyfunction!(replay_local_certificate_native, module)?)?;
    module.add_function(wrap_pyfunction!(component_evidence_native, module)?)?;
    module.add_function(wrap_pyfunction!(verify_component_evidence_native, module)?)?;
    module.add_function(wrap_pyfunction!(verify_cd_children_native, module)?)?;
    module.add_function(wrap_pyfunction!(replay_root_component_certificate_native, module)?)?;
    module.add_function(wrap_pyfunction!(replay_prefixed_component_certificate_native, module)?)?;
    module.add_function(wrap_pyfunction!(first_blocked_clause_native, module)?)?;
    module.add_function(wrap_pyfunction!(unit_step_native, module)?)?;
    module.add_function(wrap_pyfunction!(pure_step_native, module)?)?;
    module.add_function(wrap_pyfunction!(eliminate_with_proof_native, module)?)?;
    module.add_function(wrap_pyfunction!(solve_two_sat_proof_native, module)?)?;
    module.add_function(wrap_pyfunction!(build_2sat_scc_resolution_native, module)?)?;
    module.add_function(wrap_pyfunction!(factor_elimination_order_native, module)?)?;
    module.add_function(wrap_pyfunction!(replay_factor_elimination_width_native, module)?)?;
    module.add_function(wrap_pyfunction!(unit_conflict_native, module)?)?;
    module.add_function(wrap_pyfunction!(probe_forced_relations_native, module)?)?;
    module.add_function(wrap_pyfunction!(make_separator_scaling_case_native, module)?)?;
    module.add_function(wrap_pyfunction!(discover_odd_xor_cycle_native, module)?)?;
    module.add_function(wrap_pyfunction!(elimination_options_native, module)?)?;
    module.add_function(wrap_pyfunction!(two_ply_pivot_native, module)?)?;
    module.add_function(wrap_pyfunction!(adaptive_pivot_native, module)?)?;
    module.add_function(wrap_pyfunction!(cheap_pivot_features_native, module)?)?;
    module.add_function(wrap_pyfunction!(selective_pivot_native, module)?)?;
    module.add_function(wrap_pyfunction!(parity_separator_fingerprint_native, module)?)?;
    module.add_function(wrap_pyfunction!(extract_binary_xor_equations_native, module)?)?;
    module.add_function(wrap_pyfunction!(extract_spoke_paths_native, module)?)?;
    module.add_function(wrap_pyfunction!(discover_parity_spoke_conflicts_native, module)?)?;
    module.add_function(wrap_pyfunction!(bounded_parity_separators_native, module)?)?;
    module.add_function(wrap_pyfunction!(graph_invariants_native, module)?)?;
    module.add_function(wrap_pyfunction!(eliminate_with_policy_native, module)?)?;
    module.add_function(wrap_pyfunction!(choose_threshold_native, module)?)?;
    module.add_function(wrap_pyfunction!(cost_sensitive_pivot_native, module)?)?;
    module.add_function(wrap_pyfunction!(articulation_vertices_native, module)?)?;
    module.add_function(wrap_pyfunction!(prioritized_singletons_native, module)?)?;
    module.add_function(wrap_pyfunction!(vertex_coupling_pairs_native, module)?)?;
    module.add_function(wrap_pyfunction!(prioritized_vertex_pairs_native, module)?)?;
    module.add_function(wrap_pyfunction!(two_edge_cut_boundary_pairs_native, module)?)?;
    module.add_function(wrap_pyfunction!(prioritized_global_pairs_native, module)?)?;
    module.add_function(wrap_pyfunction!(sparse_row_mask_native, module)?)?;
    module.add_function(wrap_pyfunction!(build_sparse_parity_basis_native, module)?)?;
    module.add_function(wrap_pyfunction!(verify_sparse_parity_basis_native, module)?)?;
    module.add_function(wrap_pyfunction!(sparse_accepts_masks_native, module)?)?;
    module.add_function(wrap_pyfunction!(g5_activity_native, module)?)?;
    module.add_function(wrap_pyfunction!(g5_ranked_pairs_native, module)?)?;
    module.add_function(wrap_pyfunction!(g5_cross_merge_native, module)?)?;
    module.add_function(wrap_pyfunction!(g5_boundary_path_signal_native, module)?)?;
    module.add_function(wrap_pyfunction!(sparse_column_signatures_native, module)?)?;
    module.add_function(wrap_pyfunction!(sparse_validate_rows_native, module)?)?;
    module.add_function(wrap_pyfunction!(sparse_build_rows_native, module)?)?;
    module.add_function(wrap_pyfunction!(sparse_low_weight_collisions_native, module)?)?;
    module.add_function(wrap_pyfunction!(sparse_row_scope_native, module)?)?;
    module.add_function(wrap_pyfunction!(sparse_audit_small_native, module)?)?;
    module.add_function(wrap_pyfunction!(sparse_min_degree_width_native, module)?)?;
    module.add_function(wrap_pyfunction!(finite_parity_source_digest_native, module)?)?;
    module.add_function(wrap_pyfunction!(finite_parity_violation_mask_native, module)?)?;
    module.add_function(wrap_pyfunction!(finite_parity_accepts_native, module)?)?;
    module.add_function(wrap_pyfunction!(finite_parity_build_native, module)?)?;
    module.add_function(wrap_pyfunction!(finite_parity_verify_native, module)?)?;
    module.add_function(wrap_pyfunction!(finite_parity_complete_primal_native, module)?)?;
    Ok(())
}
