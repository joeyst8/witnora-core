//! W-CROSSDOMAIN-016: prospective, bounded, statistical-wave DPLL experiment.
//! Correctness is checked against exhaustive 12-variable truth tables.
//! All favorable and unfavorable outcomes are reported, never used as CI gates.

use serde_json::{json, Value};
use std::hint::black_box;
use std::time::Instant;

const N: usize = 12;
const CASES: usize = 32;
const REPEATS: usize = 20;
const THRESHOLD_BITS: f64 = 0.02;

#[derive(Clone, Copy, PartialEq, Eq)]
enum Family { Planted, Boundary, Unsat }

impl Family {
    fn seed(self) -> u32 {
        match self { Self::Planted => 0xC0FF_EE11,
                     Self::Boundary => 0xC0FF_EE22,
                     Self::Unsat => 0xC0FF_EE33 }
    }
    fn name(self) -> &'static str {
        match self { Self::Planted => "new_planted_sat_48",
                     Self::Boundary => "new_uniform_boundary_48",
                     Self::Unsat => "new_embedded_unsat_56" }
    }
}

fn next_random(state: &mut u32) -> u32 {
    *state ^= *state << 13;
    *state ^= *state >> 17;
    *state ^= *state << 5;
    *state
}

fn random_three_clause(state: &mut u32) -> Vec<i32> {
    let mut result = Vec::with_capacity(3);
    let mut seen = [false; N];
    while result.len() < 3 {
        let variable = next_random(state) as usize % N;
        if seen[variable] { continue; }
        seen[variable] = true;
        let negative = next_random(state) & 1 != 0;
        let literal = variable as i32 + 1;
        result.push(if negative { -literal } else { literal });
    }
    result
}

fn source(family: Family, case_index: usize) -> Vec<Vec<i32>> {
    let mut seed = family.seed()
        ^ (case_index as u32 + 1).wrapping_mul(0x9E37_79B9);
    let mut clauses = Vec::with_capacity(if family == Family::Unsat { 56 } else { 48 });
    if family == Family::Unsat {
        for signs in 0..8 {
            clauses.push((0..3).map(|position| {
                let lit = position + 1;
                if signs & (1 << position) != 0 { -lit } else { lit }
            }).collect());
        }
    }
    while clauses.len() < if family == Family::Unsat { 56 } else { 48 } {
        let clause = random_three_clause(&mut seed);
        if family == Family::Planted && clause.iter().all(|&lit| lit > 0) {
            continue; // All-zero assignment must satisfy every accepted clause.
        }
        clauses.push(clause);
    }
    clauses
}

fn scope_overlap(a: &[i32], b: &[i32]) -> usize {
    a.iter().filter(|&&left| b.iter().any(|&right| left.abs() == right.abs()))
        .count()
}

fn select_four(clauses: &[Vec<i32>]) -> ([usize; 4], usize) {
    let mut selected = [0usize; 4];
    let mut comparisons = 0usize;
    for count in 1..4 {
        let mut best = None;
        for candidate in 0..clauses.len() {
            if selected[..count].contains(&candidate) { continue; }
            let mut score = 0usize;
            for &prior in &selected[..count] {
                comparisons += 1;
                score += scope_overlap(&clauses[candidate], &clauses[prior]);
            }
            if best.is_none_or(|(_, prior_score)| score > prior_score) {
                best = Some((candidate, score));
            }
        }
        selected[count] = best.expect("at least four source clauses").0;
    }
    (selected, comparisons)
}

#[derive(Debug, Clone)]
struct Moments {
    bias: i128,
    first: [i128; N],
    clause_visits: usize,
    literal_visits: usize,
    moment_updates: usize,
}

// Compute E[S_C] and E[S_C*(-1)^x_i] without enumerating 2^n assignments.
fn exact_moments(clauses: &[Vec<i32>], row: &[usize; 4]) -> Moments {
    let mut result = Moments { bias: 0, first: [0; N],
        clause_visits: 0, literal_visits: 0, moment_updates: 0 };
    for subset in 0u32..16 {
        let (mut forced_true, mut forced_false) = (0u32, 0u32);
        let mut consistent = true;
        for (position, &index) in row.iter().enumerate() {
            if subset & (1 << position) == 0 { continue; }
            result.clause_visits += 1;
            for &lit in &clauses[index] {
                result.literal_visits += 1;
                let bit = 1u32 << (lit.unsigned_abs() - 1);
                if lit > 0 { forced_false |= bit; }
                else { forced_true |= bit; }
                if forced_true & forced_false != 0 {
                    consistent = false;
                    break;
                }
            }
            if !consistent { break; }
        }
        if !consistent { continue; }
        let fixed = (forced_true | forced_false).count_ones() as usize;
        let contribution = (-2i128).pow(subset.count_ones()) * (1i128 << (N - fixed));
        result.bias += contribution;
        for variable in 0..N {
            let bit = 1u32 << variable;
            if forced_false & bit != 0 {
                result.first[variable] += contribution;
                result.moment_updates += 1;
            } else if forced_true & bit != 0 {
                result.first[variable] -= contribution;
                result.moment_updates += 1;
            }
        }
    }
    result
}

fn entropy(p: f64) -> f64 {
    if p <= 0.0 || p >= 1.0 { 0.0 }
    else { -p * p.log2() - (1.0 - p) * (1.0 - p).log2() }
}

fn mutual_information(moments: &Moments) -> [f64; N] {
    let mu = moments.bias as f64 / (1usize << N) as f64;
    let marginal = entropy((1.0 + mu) / 2.0);
    std::array::from_fn(|i| {
        let h = moments.first[i] as f64 / (1usize << N) as f64;
        let left = entropy(((1.0 + mu + h) / 2.0).clamp(0.0, 1.0));
        let right = entropy(((1.0 + mu - h) / 2.0).clamp(0.0, 1.0));
        (marginal - 0.5 * (left + right)).max(0.0)
    })
}

fn degrees(clauses: &[Vec<i32>]) -> [usize; N] {
    let mut counts = [0usize; N];
    for clause in clauses {
        for &lit in clause { counts[lit.unsigned_abs() as usize - 1] += 1; }
    }
    counts
}

fn degree_order(degree: &[usize; N]) -> [usize; N] {
    let mut order = std::array::from_fn(|i| i);
    order.sort_by(|&a, &b| degree[b].cmp(&degree[a]).then(a.cmp(&b)));
    order
}

fn wave_order(info: &[f64; N], degree: &[usize; N]) -> [usize; N] {
    let mut order = std::array::from_fn(|i| i);
    // Stable 12-decimal bins avoid platform-dependent ties in f64 log2.
    let quant = |score: f64| (score * 1e12).round() as i64;
    order.sort_by(|&a, &b| quant(info[b]).cmp(&quant(info[a]))
        .then(degree[b].cmp(&degree[a])).then(a.cmp(&b)));
    order
}

#[derive(Clone, Debug, Default, PartialEq, Eq)]
struct Cost { nodes: u32, clause_scans: u32, sat: bool }

fn dpll(clauses: &[Vec<i32>], order: &[usize; N]) -> Cost {
    fn visit(clauses: &[Vec<i32>], order: &[usize; N], mut assign: [i8; N],
             result: &mut Cost) -> bool {
        result.nodes += 1;
        loop {
            let mut changed = false;
            for clause in clauses {
                result.clause_scans += 1;
                let (mut free, mut last, mut satisfied) = (0usize, 0i32, false);
                for &lit in clause {
                    let value = assign[lit.unsigned_abs() as usize - 1];
                    if value < 0 { free += 1; last = lit; }
                    else if (value == 1) == (lit > 0) { satisfied = true; break; }
                }
                if satisfied { continue; }
                if free == 0 { return false; }
                if free == 1 {
                    assign[last.unsigned_abs() as usize - 1] = if last > 0 { 1 } else { 0 };
                    changed = true;
                }
            }
            if !changed { break; }
        }
        let mut all_satisfied = true;
        for clause in clauses {
            result.clause_scans += 1;
            if !clause.iter().any(|&lit| {
                let value = assign[lit.unsigned_abs() as usize - 1];
                value >= 0 && (value == 1) == (lit > 0)
            }) {
                all_satisfied = false;
                break;
            }
        }
        if all_satisfied { return true; }
        let branch = *order.iter().find(|&&v| assign[v] < 0)
            .expect("unsatisfied clause contains an unassigned variable");
        let mut left = assign;
        left[branch] = 0;
        if visit(clauses, order, left, result) { return true; }
        assign[branch] = 1;
        visit(clauses, order, assign, result)
    }
    let mut result = Cost::default();
    let sat = visit(clauses, order, [-1; N], &mut result);
    result.sat = sat;
    result
}

fn truth_sat(clauses: &[Vec<i32>]) -> bool {
    (0..(1usize << N)).any(|assignment| {
        clauses.iter().all(|clause| clause.iter().any(|&lit| {
            let bit = assignment & (1usize << (lit.unsigned_abs() as usize - 1)) != 0;
            bit == (lit > 0)
        }))
    })
}

struct Case {
    index: usize,
    clauses: Vec<Vec<i32>>,
    selected: [usize; 4],
    selector_comparisons: usize,
    moments: Moments,
    mutual_information: [f64; N],
    orders: [[usize; N]; 4],
    costs: [Cost; 4],
    gate_uses_wave: bool,
}

fn prepare(family: Family, index: usize) -> Result<Case, String> {
    let clauses = source(family, index);
    let (selected, selector_comparisons) = select_four(&clauses);
    let moments = exact_moments(&clauses, &selected);
    let info = mutual_information(&moments);
    let degree = degrees(&clauses);
    let asc = std::array::from_fn(|i| i);
    let base = degree_order(&degree);
    let wave = wave_order(&info, &degree);
    let gate_uses_wave = info.iter().copied().fold(0f64, f64::max) >= THRESHOLD_BITS;
    let gated = if gate_uses_wave { wave } else { base };
    let orders = [asc, base, wave, gated];
    let costs = std::array::from_fn(|i| dpll(&clauses, &orders[i]));
    let sat = truth_sat(&clauses);
    if costs.iter().any(|c| c.sat != sat) {
        return Err(format!("W016 source/DPLL verdict mismatch {}:{}", family.name(), index));
    }
    if (family == Family::Planted && !sat) || (family == Family::Unsat && sat) {
        return Err(format!("W016 seeded source class violated {}:{}", family.name(), index));
    }
    Ok(Case { index, clauses, selected, selector_comparisons,
        moments, mutual_information: info, orders, costs, gate_uses_wave })
}

fn timed(case: &Case, method: usize) -> u128 {
    let before = Instant::now();
    let degree = degrees(&case.clauses);
    let base = degree_order(&degree);
    let order = if method == 1 { base } else {
        let (selected, _) = select_four(&case.clauses);
        let moments = exact_moments(&case.clauses, &selected);
        let information = mutual_information(&moments);
        let wave = wave_order(&information, &degree);
        if method == 2 || information.iter().copied().fold(0f64, f64::max) >= THRESHOLD_BITS {
            wave
        } else { base }
    };
    let cost = dpll(&case.clauses, &order);
    black_box(cost);
    before.elapsed().as_nanos()
}

fn family_report(family: Family) -> Result<Value, String> {
    let cases = (0..CASES).map(|index| prepare(family, index))
        .collect::<Result<Vec<_>, _>>()?;
    let mut elapsed = [0u128; 4];
    for repetition in 0..REPEATS {
        for case in &cases {
            let methods = if repetition % 2 == 0 { [1, 2, 3] } else { [3, 2, 1] };
            for method in methods { elapsed[method] += timed(case, method); }
        }
    }
    let methods = ["ascending", "degree", "wave", "gated_wave"];
    let mut by_method = serde_json::Map::new();
    for (method, &name) in methods.iter().enumerate() {
        let nodes = cases.iter().map(|c| f64::from(c.costs[method].nodes)).sum::<f64>();
        let scans = cases.iter().map(|c| f64::from(c.costs[method].clause_scans)).sum::<f64>();
        let wins = cases.iter().filter(|c|c.costs[method].clause_scans < c.costs[1].clause_scans).count();
        let ties = cases.iter().filter(|c|c.costs[method].clause_scans == c.costs[1].clause_scans).count();
        let losses = CASES - wins - ties;
        by_method.insert(name.to_string(), json!({"mean_nodes":nodes/CASES as f64,
            "mean_clause_scans":scans/CASES as f64,"wins_vs_degree":wins,
            "ties_vs_degree":ties,"losses_vs_degree":losses,
            "timed_full_pipeline_total_nanoseconds":if method == 0 {None} else {Some(elapsed[method])},
            "timing_repetitions":if method == 0 {0} else {REPEATS}}));
    }
    let controls = cases.iter().filter(|c| [0, 1, 31].contains(&c.index)).map(|c| {
        json!({"index":c.index,"source":&c.clauses,"selected_parity_row":c.selected,
            "selector_comparisons":c.selector_comparisons,
            "signed_wave_bias":c.moments.bias,
            "signed_first_moments":c.moments.first,
            "mutual_information_bits":c.mutual_information,
            "gate_uses_wave":c.gate_uses_wave,
            "orders":c.orders,"costs":c.costs.iter().map(|cost|json!({"nodes":cost.nodes,
                "clause_scans":cost.clause_scans,"sat":cost.sat})).collect::<Vec<_>>()})
    }).collect::<Vec<_>>();
    Ok(json!({"name":family.name(),"cases":cases.len(),
        "sat_count":cases.iter().filter(|c|c.costs[1].sat).count(),
        "unsat_count":cases.iter().filter(|c|!c.costs[1].sat).count(),
        "gated_wave_uses":cases.iter().filter(|c|c.gate_uses_wave).count(),
        "mean_selector_overlap_comparisons":cases.iter()
            .map(|c|c.selector_comparisons as f64).sum::<f64>()/CASES as f64,
        "mean_wave_selected_clause_visits":cases.iter()
            .map(|c|c.moments.clause_visits as f64).sum::<f64>()/CASES as f64,
        "mean_wave_literal_visits":cases.iter()
            .map(|c|c.moments.literal_visits as f64).sum::<f64>()/CASES as f64,
        "mean_wave_first_moment_updates":cases.iter()
            .map(|c|c.moments.moment_updates as f64).sum::<f64>()/CASES as f64,
        "methods":by_method,"controls":controls}))
}

pub fn audit() -> Result<Value, String> {
    let planted = family_report(Family::Planted)?;
    let boundary = family_report(Family::Boundary)?;
    let unsat = family_report(Family::Unsat)?;
    Ok(json!({"research_id":"W-CROSSDOMAIN-016",
        "scope":"prospective 96 new 12-variable SAT/UNSAT 3-CNF; fixed 4-clause Walsh moments",
        "frozen_gate_min_mutual_information_bits":THRESHOLD_BITS,
        "timing":"20 alternated pipeline timings per case on CI host; noisy and descriptive",
        "signal":"Shannon information about selected violation parity, not satisfying-assignment distribution",
        "families":[planted,boundary,unsat]}))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn direct_moments(clauses: &[Vec<i32>], row: &[usize; 4]) -> (i128, [i128; N]) {
        let mut bias = 0i128;
        let mut moments = [0i128; N];
        for assignment in 0..(1usize << N) {
            let violations = row.iter().filter(|&&i| {
                !clauses[i].iter().any(|&lit| {
                    let bit = assignment & (1usize << (lit.unsigned_abs() as usize - 1)) != 0;
                    bit == (lit > 0)
                })
            }).count();
            let sign = if violations % 2 == 0 {1i128} else {-1};
            bias += sign;
            for (i, result) in moments.iter_mut().enumerate() {
                *result += if assignment & (1usize << i) == 0 {sign} else {-sign};
            }
        }
        (bias, moments)
    }

    #[test]
    fn fresh_source_classes_moments_and_dpll_match_direct_oracles() {
        for family in [Family::Planted, Family::Boundary, Family::Unsat] {
            for index in [0, 1, 31] {
                let case = prepare(family, index).unwrap();
                assert_eq!((case.moments.bias, case.moments.first),
                           direct_moments(&case.clauses, &case.selected));
                assert!(case.moments.clause_visits <= 32);
                assert!(case.moments.literal_visits <= 96);
                assert!(case.mutual_information.iter().all(|&x| (0.0..=1.0).contains(&x)));
                assert_eq!(case.costs.iter().map(|c|c.sat).collect::<Vec<_>>(),
                           vec![truth_sat(&case.clauses); 4]);
            }
        }
    }
}
