//! W-CROSSDOMAIN-012: preregistered, finite 3-CNF incidence hypergraph pilot.
//! Exact enumeration and matched search-cost diagnostics only; all formulas
//! here are SAT (six width-three clauses cannot cover all 64 assignments).

use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

const N: usize = 6;
const M: usize = 6;
const W: usize = 3;
const ALTERNATE: [usize; 3] = [0, 2, 4];
const FORWARD: [usize; N] = [0, 1, 2, 3, 4, 5];
const REVERSE: [usize; N] = [5, 4, 3, 2, 1, 0];
const T1: [[usize; W]; M] = [
    [0, 1, 2], [1, 2, 3], [2, 3, 4], [3, 4, 5], [4, 5, 0], [5, 0, 1],
];
const T2: [[usize; W]; M] = [
    [0, 1, 2], [0, 1, 3], [0, 2, 4], [0, 3, 5], [1, 2, 4], [3, 4, 5],
];
// W-CROSSDOMAIN-013 fresh Pasch-core families, preregistered separately before
// examining any signed solver costs. Indices are zero-based only in Rust.
const P1: [[usize; W]; M] = [
    [0, 1, 2], [0, 3, 4], [1, 3, 5], [2, 4, 5], [0, 1, 3], [2, 3, 4],
];
const P2: [[usize; W]; M] = [
    [0, 1, 2], [0, 3, 4], [1, 3, 5], [2, 4, 5], [0, 1, 3], [0, 1, 4],
];

#[derive(Clone, Debug, PartialEq, Eq)]
struct Cost {
    nodes: u32,
    models: u32,
    clause_scans: u32,
}

#[derive(Debug)]
struct Row {
    mask: u32,
    energy: [u32; M + 1],
    alternate_even: [u32; M + 1],
    forward: Cost,
    reverse: Cost,
}

fn source(mask: u32, scopes: &[[usize; W]; M]) -> Vec<Vec<i32>> {
    scopes.iter().enumerate().map(|(index, scope)| {
        scope.iter().enumerate().map(|(position, &variable)| {
            let literal = variable as i32 + 1;
            if mask & (1u32 << (index * W + position)) != 0 { -literal } else { literal }
        }).collect::<Vec<_>>()
    }).collect()
}

fn gauge_masks(scopes: &[[usize; W]; M]) -> Result<([u32; N], [usize; N]), String> {
    let mut variable_masks = [0u32; N];
    let mut first = [usize::MAX; N];
    for (index, scope) in scopes.iter().enumerate() {
        let mut distinct = BTreeSet::new();
        for (position, &variable) in scope.iter().enumerate() {
            if variable >= N || !distinct.insert(variable) {
                return Err("invalid or repeated source-hyperedge variable".into());
            }
            let bit = W * index + position;
            first[variable] = first[variable].min(bit);
            variable_masks[variable] |= 1u32 << bit;
        }
    }
    if first.contains(&usize::MAX) { return Err("isolated source-hyperedge variable".into()); }
    Ok((variable_masks, first))
}

fn canonical(mask: u32, variable_masks: &[u32; N], first: &[usize; N]) -> u32 {
    let mut answer = mask;
    for variable in 0..N {
        if answer & (1u32 << first[variable]) != 0 {
            answer ^= variable_masks[variable];
        }
    }
    answer
}

fn direct_spectra(clauses: &[Vec<i32>], parity_row: &[usize])
    -> ([u32; M + 1], [u32; M + 1], [u32; M + 1]) {
    let mut energy = [0u32; M + 1];
    let mut alternate_even = [0u32; M + 1];
    let mut all_even = [0u32; M + 1];
    for assignment in 0..(1usize << N) {
        let mut violations = 0usize;
        let mut alternating_violations = 0usize;
        for (index, clause) in clauses.iter().enumerate() {
            let satisfied = clause.iter().any(|&lit| {
                let value = assignment & (1usize << (lit.unsigned_abs() as usize - 1)) != 0;
                value == (lit > 0)
            });
            if !satisfied {
                violations += 1;
                if parity_row.contains(&index) { alternating_violations += 1; }
            }
        }
        energy[violations] += 1;
        if alternating_violations % 2 == 0 { alternate_even[violations] += 1; }
        if violations % 2 == 0 { all_even[violations] += 1; }
    }
    (energy, alternate_even, all_even)
}

// Count the full DPLL model tree under a frozen variable order. A clause scan
// is one attempted examination of a whole source clause during propagation or
// the terminal all-satisfied check, not a normalized CPU instruction or time.
fn dpll(clauses: &[Vec<i32>], order: &[usize; N]) -> Cost {
    fn recurse(clauses: &[Vec<i32>], order: &[usize; N],
               mut assignment: [i8; N], count: &mut Cost) -> u32 {
        count.nodes += 1;
        loop {
            let mut changed = false;
            for clause in clauses {
                count.clause_scans += 1;
                let mut satisfied = false;
                let mut free = 0usize;
                let mut last = 0i32;
                for &lit in clause {
                    let value = assignment[lit.unsigned_abs() as usize - 1];
                    if value < 0 { free += 1; last = lit; }
                    else if (value == 1) == (lit > 0) { satisfied = true; break; }
                }
                if satisfied { continue; }
                if free == 0 { return 0; }
                if free == 1 {
                    assignment[last.unsigned_abs() as usize - 1] = if last > 0 { 1 } else { 0 };
                    changed = true;
                }
            }
            if !changed { break; }
        }
        let mut all_satisfied = true;
        for clause in clauses {
            count.clause_scans += 1;
            if !clause.iter().any(|&lit| {
                let value = assignment[lit.unsigned_abs() as usize - 1];
                value >= 0 && (value == 1) == (lit > 0)
            }) {
                all_satisfied = false;
                break;
            }
        }
        if all_satisfied {
            let remaining = assignment.iter().filter(|&&value| value < 0).count();
            return 1u32 << remaining;
        }
        let branch = *order.iter().find(|&&variable| assignment[variable] < 0)
            .expect("unresolved clause must contain a free variable");
        assignment[branch] = 0;
        let left = recurse(clauses, order, assignment, count);
        assignment[branch] = 1;
        left + recurse(clauses, order, assignment, count)
    }
    let mut count = Cost { nodes: 0, models: 0, clause_scans: 0 };
    let models = recurse(clauses, order, [-1; N], &mut count);
    count.models = models;
    count
}

fn row(mask: u32, scopes: &[[usize; W]; M], parity_row: &[usize]) -> Result<Row, String> {
    let clauses = source(mask, scopes);
    let (energy, alternate_even, all_even) = direct_spectra(&clauses, parity_row);
    let forward = dpll(&clauses, &FORWARD);
    let reverse = dpll(&clauses, &REVERSE);
    if energy[0] < 16 || forward.models != energy[0] || reverse.models != energy[0] {
        return Err(format!("source-vs-DPLL model count mismatch at signing {mask}"));
    }
    // The parity of the *entire* source violation set is exactly determined
    // by its Hamming weight: it is a mandatory negative information control.
    for degree in 0..=M {
        let implied = if degree % 2 == 0 { energy[degree] } else { 0 };
        if all_even[degree] != implied {
            return Err("all-clause parity must be redundant with energy".into());
        }
    }
    let fourier = crate::aux_fourier_violation::fourier_parity_violation_profile(
        &clauses, N, &[parity_row.to_vec()], &[false], N)?;
    if fourier != alternate_even.iter().map(|&n| u64::from(n)).collect::<Vec<_>>() {
        return Err(format!("Fourier-vs-source syndrome mismatch at signing {mask}"));
    }
    Ok(Row { mask, energy, alternate_even, forward, reverse })
}

fn groups(rows: &[Row]) -> BTreeMap<[u32; M + 1], Vec<usize>> {
    let mut result: BTreeMap<_, Vec<usize>> = BTreeMap::new();
    for (index, row) in rows.iter().enumerate() {
        result.entry(row.energy).or_default().push(index);
    }
    result
}

fn score(rows: &[Row], groups: &BTreeMap<[u32; M + 1], Vec<usize>>,
         labels: &[[u32; M + 1]], forward: bool) -> (f64, f64, usize) {
    let count = |index: usize| -> f64 {
        if forward { rows[index].forward.nodes as f64 }
        else { rows[index].reverse.nodes as f64 }
    };
    let mut base_se = 0.0;
    let mut feature_se = 0.0;
    let mut used = 0usize;
    for indices in groups.values() {
        if indices.len() < 2 { continue; }
        let total: f64 = indices.iter().map(|&i| count(i)).sum();
        let mut finer: BTreeMap<[u32; M + 1], (usize, f64)> = BTreeMap::new();
        for &i in indices {
            let entry = finer.entry(labels[i]).or_insert((0, 0.0));
            entry.0 += 1;
            entry.1 += count(i);
        }
        for &i in indices {
            let observed = count(i);
            let base = (total - observed) / (indices.len() - 1) as f64;
            let &(sub_count, sub_sum) = finer.get(&labels[i]).unwrap();
            let enhanced = if sub_count > 1 {
                (sub_sum - observed) / (sub_count - 1) as f64
            } else { base };
            base_se += (observed - base).powi(2);
            feature_se += (observed - enhanced).powi(2);
            used += 1;
        }
    }
    if used == 0 { return (0.0, 0.0, 0); }
    (base_se / used as f64, feature_se / used as f64, used)
}

fn next_random(state: &mut u32) -> u32 {
    *state ^= *state << 13;
    *state ^= *state >> 17;
    *state ^= *state << 5;
    *state
}

fn example(row: &Row, scopes: &[[usize; W]; M]) -> Value {
    json!({"mask":row.mask,"source":source(row.mask, scopes),"energy":row.energy,
        "alternate_even":row.alternate_even,
        "forward":{"nodes":row.forward.nodes,"models":row.forward.models,
                   "clause_scans":row.forward.clause_scans},
        "reverse":{"nodes":row.reverse.nodes,"models":row.reverse.models,
                   "clause_scans":row.reverse.clause_scans}})
}

fn family(scopes: &[[usize; W]; M], name: &str,
          parity_row: &[usize]) -> Result<Value, String> {
    let (variable_masks, first) = gauge_masks(scopes)?;
    let masks = (0..(1u32 << (M * W)))
        .map(|mask| canonical(mask, &variable_masks, &first))
        .collect::<BTreeSet<_>>();
    if masks.len() != 4096 { return Err("unexpected hypergraph gauge orbit count".into()); }
    let mut rows = Vec::with_capacity(masks.len());
    for mask in masks { rows.push(row(mask, scopes, parity_row)?); }
    let groups = groups(&rows);
    let labels = rows.iter().map(|r| r.alternate_even).collect::<Vec<_>>();
    let spectra = rows.iter().map(|r| (r.energy, r.alternate_even))
        .collect::<BTreeSet<_>>().len();
    let min_models = rows.iter().map(|r| r.energy[0]).min().unwrap();
    let feature_scans = (M * (1 << N)) as u32;
    let scan_stats = |forward: bool| {
        let scans = rows.iter().map(|r| if forward { r.forward.clause_scans }
                                        else { r.reverse.clause_scans }).collect::<Vec<_>>();
        json!({"mean_dpll_clause_scans":scans.iter().map(|&x| x as f64).sum::<f64>()
                    / scans.len() as f64,
               "feature_scans_exceed_dpll_fraction":scans.iter()
                    .filter(|&&x| feature_scans > x).count() as f64 / scans.len() as f64})
    };
    let (b_forward, e_forward, samples_forward) = score(&rows, &groups, &labels, true);
    let (b_reverse, e_reverse, samples_reverse) = score(&rows, &groups, &labels, false);
    let mut seed = 0x1234_5678u32;
    let mut extreme_forward = 0usize;
    let mut extreme_reverse = 0usize;
    const TRIALS: usize = 1000;
    for _ in 0..TRIALS {
        let mut shuffled = labels.clone();
        for indices in groups.values() {
            for position in (1..indices.len()).rev() {
                let partner = next_random(&mut seed) as usize % (position + 1);
                shuffled.swap(indices[position], indices[partner]);
            }
        }
        let (bp, ep, _) = score(&rows, &groups, &shuffled, true);
        let (br, er, _) = score(&rows, &groups, &shuffled, false);
        if bp - ep >= b_forward - e_forward - 1e-12 { extreme_forward += 1; }
        if br - er >= b_reverse - e_reverse - 1e-12 { extreme_reverse += 1; }
    }
    let stats = |base: f64, enhanced: f64, samples: usize, extreme: usize| {
        json!({"samples":samples,"baseline_loo_mse":base,"syndrome_loo_mse":enhanced,
            "baseline_zero":base == 0.0,
            "improvement_fraction":if base > 0.0 {Some((base-enhanced)/base)} else {None},
            "permutation_extreme":extreme,"permutations":TRIALS,
            "exploratory_permutation_p":(extreme+1) as f64/(TRIALS+1) as f64})
    };
    let controls = [0u32, 1, 12345, (1u32 << (M*W)) - 1].iter()
        .map(|&mask| row(mask, scopes, parity_row).map(|r| example(&r, scopes)))
        .collect::<Result<Vec<_>, _>>()?;
    Ok(json!({"graph_name":name,"chosen_parity_indices":parity_row,
        "source_scopes_one_based":scopes.iter()
                .map(|s|s.iter().map(|&v|v+1).collect::<Vec<_>>()).collect::<Vec<_>>(),
        "signings":1u32<<(M*W),"gauge_representatives":rows.len(),
        "energy_profiles":groups.len(),"energy_plus_alternating_parity_profiles":spectra,
        "minimum_model_count":min_models,
        "feature_clause_scans_per_formula":feature_scans,
        "all_clauses_even_parity_is_energy_determined":true,
        "forward":stats(b_forward,e_forward,samples_forward,extreme_forward),
        "reverse":stats(b_reverse,e_reverse,samples_reverse,extreme_reverse),
        "forward_work":scan_stats(true),"reverse_work":scan_stats(false),
        "controls":controls}))
}

/// A negative result is a valid successful audit; only exact invariants may
/// cause an error. The locked statistical criterion is recorded, not enforced.
pub fn audit() -> Result<Value, String> {
    let t1 = family(&T1, "T1_cyclic_triple_overlap", &ALTERNATE)?;
    let t2 = family(&T2, "T2_skew_incidence", &ALTERNATE)?;
    let strict = [&t1, &t2].iter().all(|r| {
        ["forward", "reverse"].iter().all(|&policy| {
            r[policy]["improvement_fraction"].as_f64().is_some_and(|x| x > 0.0)
                && r[policy]["exploratory_permutation_p"].as_f64()
                    .is_some_and(|p| p <= 0.0125)
        })
    });
    Ok(json!({"research_id":"W-CROSSDOMAIN-012",
        "scope":"preregistered, exhaustive, six-variable six-clause 3-CNF; all SAT",
        "alternating_clause_indices":ALTERNATE,
        "strict_four_way_replication_met":strict,"families":[t1,t2]}))
}

/// Bounded exact GF(2) left-kernel search of an unsigned clause-variable
/// incidence matrix. This finds minimum support at m=6 by enumerating only
/// 63 nonzero subsets; no efficient general minimum-codeword claim is made.
fn smallest_even_incidence_row(scopes: &[[usize; W]; M]) -> Result<Vec<usize>, String> {
    gauge_masks(scopes)?; // validate all six active, triple scopes nonrepeating
    let mut clause_incidence = [0u8; M];
    for (index, scope) in scopes.iter().enumerate() {
        for &variable in scope { clause_incidence[index] ^= 1u8 << variable; }
    }
    let mut best: Option<(u32, usize)> = None;
    for mask in 1usize..(1usize << M) {
        let mut variable_parity = 0u8;
        for (index, &incidence) in clause_incidence.iter().enumerate() {
            if mask & (1usize << index) != 0 { variable_parity ^= incidence; }
        }
        if variable_parity != 0 { continue; }
        let weight = mask.count_ones();
        if best.map_or(true, |(prior_weight, prior_mask)|
            (weight, mask) < (prior_weight, prior_mask)) {
            best = Some((weight, mask));
        }
    }
    let (_, mask) = best.ok_or("no nonzero even-incidence hypercycle")?;
    Ok((0..M).filter(|&index| mask & (1usize << index) != 0).collect())
}

/// W-CROSSDOMAIN-013: prospective algebraic feature on new Pasch-core graphs.
pub fn audit_hypercycles() -> Result<Value, String> {
    let p1_row = smallest_even_incidence_row(&P1)?;
    let p2_row = smallest_even_incidence_row(&P2)?;
    let p1 = family(&P1, "P1_Pasch_offset", &p1_row)?;
    let p2 = family(&P2, "P2_Pasch_shared_vertices", &p2_row)?;
    let strict = [&p1, &p2].iter().all(|r| {
        ["forward", "reverse"].iter().all(|&policy| {
            r[policy]["improvement_fraction"].as_f64().is_some_and(|x| x > 0.0)
                && r[policy]["exploratory_permutation_p"].as_f64()
                    .is_some_and(|p| p <= 0.0125)
        })
    });
    Ok(json!({"research_id":"W-CROSSDOMAIN-013",
        "scope":"fresh preregistered 3-CNF Pasch-core families; bounded exact GF2 hypercycle selection",
        "selection":"minimum nonzero clause-subset weight then smallest numeric GF2 incidence-kernel mask",
        "strict_four_way_replication_met":strict,"families":[p1,p2]}))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn preregistered_hypergraphs_and_exact_orbits() {
        let report = audit().unwrap();
        assert_eq!(report["research_id"], "W-CROSSDOMAIN-012");
        let families = report["families"].as_array().unwrap();
        assert_eq!(families.len(), 2);
        for r in families {
            assert_eq!(r["signings"], 262144);
            assert_eq!(r["gauge_representatives"], 4096);
            assert!(r["minimum_model_count"].as_u64().unwrap() >= 16);
            assert_eq!(r["feature_clause_scans_per_formula"], 384);
            assert_eq!(r["all_clauses_even_parity_is_energy_determined"], true);
            assert_eq!(r["controls"].as_array().unwrap().len(), 4);
            // Do not assert a favorable predictive result: the predeclared
            // hypothesis must be able to fail without breaking correctness CI.
        }
    }

    #[test]
    fn gauge_flip_exactly_preserves_syndromes_and_dpll_work() {
        for scopes in [&T1, &T2] {
            let (bits, first) = gauge_masks(scopes).unwrap();
            for mask in [0u32, 1, 12345, (1u32 << (M*W)) - 1] {
                let original = row(mask, scopes, &ALTERNATE).unwrap();
                for variable in 0..N {
                    let flipped_mask = mask ^ bits[variable];
                    let flipped = row(flipped_mask, scopes, &ALTERNATE).unwrap();
                    assert_eq!(flipped.energy, original.energy);
                    assert_eq!(flipped.alternate_even, original.alternate_even);
                    assert_eq!(flipped.forward, original.forward);
                    assert_eq!(flipped.reverse, original.reverse);
                    assert_eq!(canonical(mask, &bits, &first),
                               canonical(flipped_mask, &bits, &first));
                }
            }
        }
    }

    #[test]
    fn known_unsat_three_clause_scope_control() {
        // Outside the prospective six-clause populations: all eight signed
        // 3-clauses on one triple forbid every assignment of that triple.
        let mut clauses = Vec::new();
        for sign in 0..8 {
            clauses.push((0..3).map(|position| {
                let lit = position as i32 + 1;
                if sign & (1 << position) != 0 { -lit } else { lit }
            }).collect::<Vec<_>>());
        }
        assert_eq!(dpll(&clauses, &FORWARD).models, 0);
        assert_eq!(dpll(&clauses, &REVERSE).models, 0);
    }

    #[test]
    fn preregistered_gf2_even_incidence_hypercycle_controls() {
        for scopes in [&P1, &P2] {
            let chosen = smallest_even_incidence_row(scopes).unwrap();
            assert_eq!(chosen, vec![0, 1, 2, 3]);
            let mut parity = [0u8; N];
            for &index in &chosen {
                for &variable in &scopes[index] { parity[variable] ^= 1; }
            }
            assert_eq!(parity, [0; N]);
            let (bits, first) = gauge_masks(scopes).unwrap();
            for mask in [0u32, 1, 12345, (1u32 << (M*W)) - 1] {
                let baseline = row(mask, scopes, &chosen).unwrap();
                for variable in 0..N {
                    let flip_mask = mask ^ bits[variable];
                    let flipped = row(flip_mask, scopes, &chosen).unwrap();
                    assert_eq!(flipped.energy, baseline.energy);
                    assert_eq!(flipped.alternate_even, baseline.alternate_even);
                    assert_eq!(flipped.forward, baseline.forward);
                    assert_eq!(flipped.reverse, baseline.reverse);
                    assert_eq!(canonical(mask, &bits, &first),
                               canonical(flip_mask, &bits, &first));
                }
            }
        }
        let report = audit_hypercycles().unwrap();
        assert_eq!(report["research_id"], "W-CROSSDOMAIN-013");
        let families = report["families"].as_array().unwrap();
        assert_eq!(families.len(), 2);
        for r in families {
            assert_eq!(r["chosen_parity_indices"], json!([0, 1, 2, 3]));
            assert_eq!(r["gauge_representatives"], 4096);
            assert!(r["minimum_model_count"].as_u64().unwrap() >= 16);
            // No favorable predictive outcome is required for CI success.
        }
    }
}
