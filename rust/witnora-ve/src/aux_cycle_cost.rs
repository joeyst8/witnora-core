//! W-CROSSDOMAIN-010: gauge-quotiented, exhaustive, six-variable pilot of
//! clause-cycle syndrome spectra against fixed-policy DPLL model-count trees.
//! Every reported statistic is finite-family, exploratory evidence; the CNFs
//! are 2-SAT and the test is not a lower bound or a general hardness result.

use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

const N: usize = 6;
const M: usize = 7;
const EDGES: [(usize, usize); M] = [
    (0, 1), (0, 2), (0, 3), (1, 2), (1, 4), (3, 5), (4, 5),
];
const TRIANGLE: [usize; 3] = [0, 1, 3];
const FORWARD: [usize; N] = [0, 1, 2, 3, 4, 5];
const REVERSE: [usize; N] = [5, 4, 3, 2, 1, 0];

#[derive(Clone, Debug)]
struct Row {
    mask: u16,
    energy: [u16; M + 1],
    even: [u16; M + 1],
    forward_nodes: u32,
    reverse_nodes: u32,
}

fn source(mask: u16) -> Vec<Vec<i32>> {
    EDGES.iter().enumerate().map(|(index, &(a, b))| {
        [a, b].iter().enumerate().map(|(position, &variable)| {
            let value = (variable + 1) as i32;
            if mask & (1 << (2 * index + position)) != 0 { -value } else { value }
        }).collect()
    }).collect()
}

fn flip_variable(mut mask: u16, variable: usize) -> u16 {
    for (index, &(a, b)) in EDGES.iter().enumerate() {
        if a == variable { mask ^= 1 << (2 * index); }
        if b == variable { mask ^= 1 << (2 * index + 1); }
    }
    mask
}

fn gauge_representative(mut mask: u16) -> u16 {
    // Variable flips act on disjoint literal-incidence bits. Canonicalize the
    // first incidence of each variable to positive polarity (bit zero).
    for variable in 0..N {
        let first = EDGES.iter().enumerate().find_map(|(index, &(a, b))| {
            if a == variable { Some(2 * index) }
            else if b == variable { Some(2 * index + 1) }
            else { None }
        }).expect("every graph vertex has an incident edge");
        if mask & (1 << first) != 0 { mask = flip_variable(mask, variable); }
    }
    mask
}

fn direct_spectra(clauses: &[Vec<i32>]) -> ([u16; M + 1], [u16; M + 1]) {
    let mut energy = [0u16; M + 1];
    let mut even = [0u16; M + 1];
    for assignment in 0usize..(1 << N) {
        let mut weight = 0usize;
        let mut triangle_violations = 0usize;
        for (index, clause) in clauses.iter().enumerate() {
            let satisfied = clause.iter().any(|&lit| {
                let bit = (assignment >> (lit.unsigned_abs() as usize - 1)) & 1 != 0;
                bit == (lit > 0)
            });
            if !satisfied {
                weight += 1;
                if TRIANGLE.contains(&index) { triangle_violations += 1; }
            }
        }
        energy[weight] += 1;
        if triangle_violations % 2 == 0 { even[weight] += 1; }
    }
    (energy, even)
}

// Exhaustive model counting with fixed variable order and deterministic unit
// propagation. Cost is the number of recursive search calls, including leaves;
// this is *not* wall-clock time or the behavior of a CDCL solver.
fn dpll_count(clauses: &[Vec<i32>], order: &[usize; N]) -> (u32, u32) {
    fn recurse(clauses: &[Vec<i32>], order: &[usize; N],
               mut assignment: [i8; N], calls: &mut u32) -> u32 {
        *calls += 1;
        loop {
            let mut changed = false;
            for clause in clauses {
                let mut satisfied = false;
                let mut unassigned = 0;
                let mut last = 0i32;
                for &lit in clause {
                    let value = assignment[lit.unsigned_abs() as usize - 1];
                    if value < 0 { unassigned += 1; last = lit; }
                    else if (value == 1) == (lit > 0) { satisfied = true; break; }
                }
                if satisfied { continue; }
                if unassigned == 0 { return 0; }
                if unassigned == 1 {
                    assignment[last.unsigned_abs() as usize - 1] = if last > 0 { 1 } else { 0 };
                    changed = true;
                }
            }
            if !changed { break; }
        }
        let all_satisfied = clauses.iter().all(|clause| clause.iter().any(|&lit| {
            let value = assignment[lit.unsigned_abs() as usize - 1];
            value >= 0 && (value == 1) == (lit > 0)
        }));
        if all_satisfied {
            let free = assignment.iter().filter(|&&value| value < 0).count();
            return 1u32 << free;
        }
        let variable = *order.iter().find(|&&v| assignment[v] < 0)
            .expect("unresolved clause has an unassigned variable");
        assignment[variable] = 0;
        let left = recurse(clauses, order, assignment, calls);
        assignment[variable] = 1;
        left + recurse(clauses, order, assignment, calls)
    }
    let mut calls = 0u32;
    let models = recurse(clauses, order, [-1; N], &mut calls);
    (calls, models)
}

fn row(mask: u16) -> Result<Row, String> {
    let clauses = source(mask);
    let (energy, even) = direct_spectra(&clauses);
    let (forward_nodes, models_a) = dpll_count(&clauses, &FORWARD);
    let (reverse_nodes, models_b) = dpll_count(&clauses, &REVERSE);
    if models_a != u32::from(energy[0]) || models_b != u32::from(energy[0]) {
        return Err(format!("DPLL / truth table model-count disagreement for mask {mask}"));
    }
    // Cross-check the triangle projection using the existing exact Fourier
    // implementation rather than the direct parity-loop implementation.
    let via_fourier = crate::aux_fourier_violation::fourier_parity_violation_profile(
        &clauses, N, &[TRIANGLE.to_vec()], &[false], N)?;
    let direct_even = even.iter().map(|&count| u64::from(count)).collect::<Vec<_>>();
    if via_fourier != direct_even {
        return Err(format!("Fourier / truth table parity disagreement for mask {mask}"));
    }
    Ok(Row { mask, energy, even, forward_nodes, reverse_nodes })
}

fn energy_groups(rows: &[Row]) -> BTreeMap<[u16; M + 1], Vec<usize>> {
    let mut groups: BTreeMap<_, Vec<usize>> = BTreeMap::new();
    for (index, row) in rows.iter().enumerate() {
        groups.entry(row.energy).or_default().push(index);
    }
    groups
}

fn score(rows: &[Row], groups: &BTreeMap<[u16; M + 1], Vec<usize>>,
         labels: &[[u16; M + 1]], forward: bool) -> (f64, f64, usize) {
    let cost = |index: usize| -> f64 {
        let row = &rows[index];
        if forward { row.forward_nodes as f64 } else { row.reverse_nodes as f64 }
    };
    let mut baseline_sse = 0.0;
    let mut syndrome_sse = 0.0;
    let mut used = 0usize;
    for indices in groups.values() {
        // Singleton energy groups have no valid energy-profile leave-one-out
        // predictor and are excluded from BOTH estimators.
        if indices.len() < 2 { continue; }
        let total: f64 = indices.iter().map(|&index| cost(index)).sum();
        let mut subgroup: BTreeMap<[u16; M + 1], (usize, f64)> = BTreeMap::new();
        for &index in indices {
            let entry = subgroup.entry(labels[index]).or_insert((0, 0.0));
            entry.0 += 1;
            entry.1 += cost(index);
        }
        for &index in indices {
            let observed = cost(index);
            let baseline = (total - observed) / (indices.len() - 1) as f64;
            let &(sub_count, sub_sum) = subgroup.get(&labels[index]).unwrap();
            // A singleton syndrome subgroup falls back to the energy-group
            // leave-one-out predictor; it never predicts from its own target.
            let predicted = if sub_count > 1 {
                (sub_sum - observed) / (sub_count - 1) as f64
            } else { baseline };
            baseline_sse += (observed - baseline).powi(2);
            syndrome_sse += (observed - predicted).powi(2);
            used += 1;
        }
    }
    (baseline_sse / used as f64, syndrome_sse / used as f64, used)
}

fn next_random(state: &mut u32) -> u32 {
    *state ^= *state << 13;
    *state ^= *state >> 17;
    *state ^= *state << 5;
    *state
}

fn example(row: &Row) -> Value {
    json!({"mask": row.mask, "source": source(row.mask), "energy": row.energy,
        "triangle_even": row.even, "forward_nodes": row.forward_nodes,
        "reverse_nodes": row.reverse_nodes})
}

/// Exact finite-family audit; no random input formulas and no timing claims.
pub fn audit() -> Result<Value, String> {
    let representatives = (0..(1u16 << (2 * M)))
        .map(gauge_representative).collect::<BTreeSet<_>>();
    if representatives.len() != 256 { return Err("gauge orbit count changed".into()); }
    let mut rows = Vec::with_capacity(representatives.len());
    for mask in representatives { rows.push(row(mask)?); }
    let groups = energy_groups(&rows);
    let labels: Vec<_> = rows.iter().map(|r| r.even).collect();
    let energy_profiles = groups.len();
    let syndrome_profiles = rows.iter().map(|r| (r.energy, r.even))
        .collect::<BTreeSet<_>>().len();
    if energy_profiles != 80 || syndrome_profiles != 135 {
        return Err("W-CROSSDOMAIN-009 profile count regression".into());
    }
    let mut split_groups = 0usize;
    let mut forward_cost_split = 0usize;
    let mut reverse_cost_split = 0usize;
    for indices in groups.values() {
        if indices.iter().map(|&i| rows[i].even).collect::<BTreeSet<_>>().len() > 1 {
            split_groups += 1;
        }
        if indices.iter().map(|&i| rows[i].forward_nodes).collect::<BTreeSet<_>>().len() > 1 {
            forward_cost_split += 1;
        }
        if indices.iter().map(|&i| rows[i].reverse_nodes).collect::<BTreeSet<_>>().len() > 1 {
            reverse_cost_split += 1;
        }
    }
    let (forward_base, forward_spec, forward_samples) = score(&rows, &groups, &labels, true);
    let (reverse_base, reverse_spec, reverse_samples) = score(&rows, &groups, &labels, false);
    const PERMUTATIONS: usize = 1000;
    let mut seed = 0x1234_5678u32;
    let mut forward_extreme = 0usize;
    let mut reverse_extreme = 0usize;
    for _ in 0..PERMUTATIONS {
        let mut shuffled = labels.clone();
        for indices in groups.values() {
            for position in (1..indices.len()).rev() {
                let partner = next_random(&mut seed) as usize % (position + 1);
                shuffled.swap(indices[position], indices[partner]);
            }
        }
        let (b1, s1, _) = score(&rows, &groups, &shuffled, true);
        let (b2, s2, _) = score(&rows, &groups, &shuffled, false);
        if b1 - s1 >= forward_base - forward_spec - 1e-12 { forward_extreme += 1; }
        if b2 - s2 >= reverse_base - reverse_spec - 1e-12 { reverse_extreme += 1; }
    }
    let stats = |baseline: f64, syndrome: f64, samples: usize, extremes: usize| {
        json!({"samples":samples,"baseline_loo_mse":baseline,
            "spectrum_loo_mse":syndrome,
            "mse_improvement_fraction":(baseline-syndrome)/baseline,
            "permutation_extreme":extremes,
            "permutation_replicates":PERMUTATIONS,
            "exploratory_permutation_p":(extremes+1) as f64/(PERMUTATIONS+1) as f64})
    };
    let controls = [0u16, 2603, 2607, (1u16 << (2 * M)) - 1]
        .iter().map(|&mask| row(mask).map(|r| example(&r)))
        .collect::<Result<Vec<_>, _>>()?;
    Ok(json!({"research_id":"W-CROSSDOMAIN-010", "interpretation":"exploratory finite 2-SAT only",
        "graph_edges_one_based":EDGES.map(|(a,b)|[a+1,b+1]),
        "triangle_clause_indices":TRIANGLE,"signings":1u32<<(2*M),
        "gauge_representatives":rows.len(),"energy_profiles":energy_profiles,
        "energy_plus_triangle_profiles":syndrome_profiles,
        "energy_groups_split_by_triangle":split_groups,
        "energy_groups_with_distinct_forward_costs":forward_cost_split,
        "energy_groups_with_distinct_reverse_costs":reverse_cost_split,
        "forward":stats(forward_base,forward_spec,forward_samples,forward_extreme),
        "reverse":stats(reverse_base,reverse_spec,reverse_samples,reverse_extreme),
        "controls":controls}))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exact_finite_pilot_regression() {
        let value = audit().unwrap();
        assert_eq!(value["signings"], 16_384);
        assert_eq!(value["gauge_representatives"], 256);
        assert_eq!(value["energy_profiles"], 80);
        assert_eq!(value["energy_plus_triangle_profiles"], 135);
        assert_eq!(value["energy_groups_split_by_triangle"], 30);
        assert_eq!(value["forward"]["samples"], 243);
        assert_eq!(value["reverse"]["samples"], 243);
        assert!(value["forward"]["mse_improvement_fraction"].as_f64().unwrap() > 0.4);
        assert!(value["reverse"]["mse_improvement_fraction"].as_f64().unwrap() > 0.5);
    }

    #[test]
    fn all_six_gauge_flips_preserve_both_search_costs() {
        for mask in [0, 2603, 2607, (1u16 << (2 * M)) - 1] {
            let baseline = row(mask).unwrap();
            for variable in 0..N {
                let flipped = row(flip_variable(mask, variable)).unwrap();
                assert_eq!(flipped.energy, baseline.energy);
                assert_eq!(flipped.even, baseline.even);
                assert_eq!(flipped.forward_nodes, baseline.forward_nodes);
                assert_eq!(flipped.reverse_nodes, baseline.reverse_nodes);
                assert_eq!(gauge_representative(mask),
                           gauge_representative(flip_variable(mask, variable)));
            }
        }
    }

    #[test]
    fn known_identical_energy_witnesses_have_distinct_triangle_spectra() {
        let a = row(2603).unwrap();
        let b = row(2607).unwrap();
        assert_eq!(a.energy, b.energy);
        assert_ne!(a.even, b.even);
        assert_eq!(a.energy, [2, 22, 30, 10, 0, 0, 0, 0]);
    }
}
