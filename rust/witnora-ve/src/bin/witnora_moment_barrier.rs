//! W024: a constructed, exact first/second-moment information barrier.
//! 64 cases are paired isomorphic relabelings, NOT independent samples.
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

type Clause = Vec<i32>;
type Formula = Vec<Clause>;

const N: usize = 9;
const CASES: usize = 64;
const TRIPLES: [[usize; 3]; 5] = [
    [1, 2, 3],
    [1, 4, 5],
    [2, 4, 6],
    [3, 5, 6],
    [7, 8, 9],
];
const SAT_RHS: [bool; 5] = [false, false, false, false, true];
const UNSAT_RHS: [bool; 5] = [false, false, false, true, false];

#[derive(Clone, Debug, PartialEq, Eq)]
struct Statistics {
    positive: [usize; N],
    negative: [usize; N],
    negative_clause_histogram: [usize; 4],
    unsigned_supports: BTreeMap<[usize; 3], usize>,
    gram: [[i32; N]; N],
}

#[derive(Clone, Debug)]
struct Recovered {
    equations: Vec<([usize; 3], u16, bool)>,
    third_moments: BTreeMap<[usize; 3], i32>,
    contradiction: Option<Vec<[usize; 3]>>,
}

fn xorshift32(state: &mut u32) -> u32 {
    *state ^= *state << 13;
    *state ^= *state >> 17;
    *state ^= *state << 5;
    *state
}

fn fisher_yates<T>(v: &mut [T], state: &mut u32) {
    for i in (1..v.len()).rev() {
        let j = (xorshift32(state) as usize) % (i + 1);
        v.swap(i, j);
    }
}

fn encode_xors(triples: &[[usize; 3]; 5], rhs: &[bool; 5]) -> Formula {
    let mut clauses = Vec::with_capacity(20);
    for (vars, expected) in triples.iter().zip(rhs) {
        for pattern in 0..8 {
            let parity = pattern.count_ones() % 2 != 0;
            if parity != *expected {
                let clause = (0..3)
                    .map(|j| {
                        let var = vars[j] as i32;
                        if (pattern >> j) & 1 == 1 { -var } else { var }
                    })
                    .collect();
                clauses.push(clause);
            }
        }
    }
    assert_eq!(clauses.len(), 20);
    clauses
}

fn paired_formulas(index: usize) -> (u32, Formula, Formula) {
    let seed = 0xD24F_0240u32 ^ ((index as u32).wrapping_add(1).wrapping_mul(0x9E37_79B9));
    let mut state = seed;
    let mut names: Vec<usize> = (1..=N).collect();
    fisher_yates(&mut names, &mut state);
    let mapped = TRIPLES.map(|t| [names[t[0] - 1], names[t[1] - 1], names[t[2] - 1]]);
    let original_sat = encode_xors(&mapped, &SAT_RHS);
    let original_unsat = encode_xors(&mapped, &UNSAT_RHS);
    let mut clause_indices: Vec<usize> = (0..20).collect();
    fisher_yates(&mut clause_indices, &mut state);
    (
        seed,
        clause_indices.iter().map(|&i| original_sat[i].clone()).collect(),
        clause_indices.iter().map(|&i| original_unsat[i].clone()).collect(),
    )
}

fn source_statistics(clauses: &[Clause]) -> Statistics {
    let mut out = Statistics {
        positive: [0; N],
        negative: [0; N],
        negative_clause_histogram: [0; 4],
        unsigned_supports: BTreeMap::new(),
        gram: [[0; N]; N],
    };
    assert_eq!(clauses.len(), 20);
    for clause in clauses {
        assert_eq!(clause.len(), 3);
        let mut support = [0usize; 3];
        let mut neg_count = 0;
        for (i, &literal) in clause.iter().enumerate() {
            let v = literal.unsigned_abs() as usize;
            assert!((1..=N).contains(&v));
            support[i] = v;
            if literal > 0 {
                out.positive[v - 1] += 1;
            } else {
                out.negative[v - 1] += 1;
                neg_count += 1;
            }
            for &other in clause {
                let u = other.unsigned_abs() as usize - 1;
                out.gram[v - 1][u] += if (literal > 0) == (other > 0) { 1 } else { -1 };
            }
        }
        support.sort_unstable();
        assert!(support[0] < support[1] && support[1] < support[2]);
        *out.unsigned_supports.entry(support).or_default() += 1;
        out.negative_clause_histogram[neg_count] += 1;
    }
    out
}

fn check_diagonal_geometry(s: &Statistics) -> bool {
    for i in 0..N {
        if s.positive[i] == 0 || s.positive[i] != s.negative[i] {
            return false;
        }
        for j in 0..N {
            if s.gram[i][j] != if i == j { (s.positive[i] + s.negative[i]) as i32 } else { 0 } {
                return false;
            }
        }
    }
    true
}

fn models(clauses: &[Clause]) -> usize {
    (0u16..(1 << N))
        .filter(|&assignment| {
            clauses.iter().all(|c| {
                c.iter().any(|&lit| {
                    let value = (assignment >> (lit.unsigned_abs() as usize - 1)) & 1 != 0;
                    value == (lit > 0)
                })
            })
        })
        .count()
}

fn recover_xor_equations(clauses: &[Clause]) -> Recovered {
    let mut groups: BTreeMap<[usize; 3], Vec<[i8; 3]>> = BTreeMap::new();
    for clause in clauses {
        assert_eq!(clause.len(), 3);
        let mut terms: Vec<(usize, i8)> = clause
            .iter()
            .map(|&literal| (literal.unsigned_abs() as usize, if literal > 0 { 1 } else { -1 }))
            .collect();
        terms.sort_unstable_by_key(|x| x.0);
        let key = [terms[0].0, terms[1].0, terms[2].0];
        assert!(key[0] < key[1] && key[1] < key[2]);
        groups.entry(key).or_default().push([terms[0].1, terms[1].1, terms[2].1]);
    }
    assert_eq!(groups.len(), 5);
    let mut equations = Vec::new();
    let mut third_moments = BTreeMap::new();
    for (triple, signs) in groups {
        assert_eq!(signs.len(), 4);
        let unique: BTreeSet<[i8; 3]> = signs.iter().copied().collect();
        assert_eq!(unique.len(), 4);
        let products: Vec<i32> = signs.iter().map(|s| i32::from(s[0] * s[1] * s[2])).collect();
        assert!(products.iter().all(|p| *p == products[0]));
        let signed_triple_moment: i32 = products.iter().sum();
        assert_eq!(signed_triple_moment.abs(), 4);
        let rhs = products[0] > 0;
        let mask: u16 = triple.iter().fold(0u16, |m, &v| m ^ (1 << (v - 1)));
        third_moments.insert(triple, signed_triple_moment);
        equations.push((triple, mask, rhs));
    }
    let mut basis: [Option<(u16, bool, u8)>; N] = [None; N];
    let mut contradiction = None;
    for (idx, &(_, source_mask, source_rhs)) in equations.iter().enumerate() {
        let (mut mask, mut rhs, mut witness) = (source_mask, source_rhs, 1u8 << idx);
        for pivot in (0..N).rev() {
            if (mask >> pivot) & 1 == 0 {
                continue;
            }
            if let Some((existing_mask, existing_rhs, existing_witness)) = basis[pivot] {
                mask ^= existing_mask;
                rhs ^= existing_rhs;
                witness ^= existing_witness;
            } else {
                basis[pivot] = Some((mask, rhs, witness));
                break;
            }
        }
        if mask == 0 && rhs {
            let mut source_mask_xor = 0u16;
            let mut source_rhs_xor = false;
            let mut selected = Vec::new();
            for (j, &(support, m, b)) in equations.iter().enumerate() {
                if (witness >> j) & 1 == 1 {
                    selected.push(support);
                    source_mask_xor ^= m;
                    source_rhs_xor ^= b;
                }
            }
            assert_eq!(source_mask_xor, 0);
            assert!(source_rhs_xor);
            contradiction = Some(selected);
            break;
        }
    }
    Recovered { equations, third_moments, contradiction }
}

fn run_case(index: usize) -> Value {
    let (seed, sat, unsat) = paired_formulas(index);
    let sat_models = models(&sat);
    let unsat_models = models(&unsat);
    let lhs = source_statistics(&sat);
    let rhs = source_statistics(&unsat);
    let sat_recovered = recover_xor_equations(&sat);
    let unsat_recovered = recover_xor_equations(&unsat);
    let stats_equal = lhs == rhs;
    let diagonal_identity = check_diagonal_geometry(&lhs) && check_diagonal_geometry(&rhs);
    let mut sat_moments: Vec<i32> = sat_recovered.third_moments.values().copied().collect();
    let mut unsat_moments: Vec<i32> = unsat_recovered.third_moments.values().copied().collect();
    sat_moments.sort_unstable();
    unsat_moments.sort_unstable();
    let third_hist_match = sat_moments == unsat_moments;
    let third_indexed_different = sat_recovered.third_moments != unsat_recovered.third_moments;
    assert_eq!(sat_models, 32, "unexpected SAT model count at case {index}");
    assert_eq!(unsat_models, 0, "unexpected UNSAT model count at case {index}");
    assert!(stats_equal && diagonal_identity && third_hist_match && third_indexed_different);
    assert_eq!(sat_recovered.equations.len(), 5);
    assert_eq!(unsat_recovered.equations.len(), 5);
    assert!(sat_recovered.contradiction.is_none());
    assert_eq!(unsat_recovered.contradiction.as_ref().map(Vec::len), Some(4));
    let mut result = json!({
        "index": index,
        "seed": seed,
        "models_sat": sat_models,
        "models_unsat": unsat_models,
        "all_first_second_order_stats_match": stats_equal,
        "pairwise_normalized_gram_is_identity_over_three": diagonal_identity,
        "aggregate_third_order_histograms_match": third_hist_match,
        "triple_indexed_third_moments_differ": third_indexed_different,
        "xor_recovers_sat": sat_recovered.contradiction.is_none(),
        "xor_recovers_unsat": unsat_recovered.contradiction.is_some(),
        "unsat_xor_witness_triplets": unsat_recovered.contradiction,
        "matched_negative_clause_histogram": lhs.negative_clause_histogram,
    });
    if [0, 1, 31, 63].contains(&index) {
        result["independent_control"] = json!({"sat_clauses":sat,"unsat_clauses":unsat});
    }
    result
}

fn report() -> Value {
    let cases: Vec<Value> = (0..CASES).map(run_case).collect();
    json!({
        "study": "W-CROSSDOMAIN-024",
        "protocol": "docs/W_CROSSDOMAIN_024_MOMENT_INFORMATION_BARRIER_PROTOCOL.md",
        "scope": "64 paired isomorphic relabelings of one constructed SAT/UNSAT pair",
        "case_count": CASES,
        "controls_with_full_clauses": [0,1,31,63],
        "exact_source_truth": true,
        "second_order_barrier_confirmed": true,
        "all_source_reconstructed_xor_certificates_valid": true,
        "satisfiability_complexity_claim": "none; standard XOR/GF(2) phenomenon",
        "cases": cases,
    })
}

fn main() {
    let args: Vec<_> = std::env::args().skip(1).collect();
    if !args.is_empty() && !(args.len() == 1 && args[0] == "--json") {
        eprintln!("usage: witnora_moment_barrier [--json]");
        std::process::exit(2);
    }
    println!("{}", serde_json::to_string_pretty(&report()).expect("JSON serialization"));
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn all_pairs_pass_exact_checks() {
        let r = report();
        assert_eq!(r["cases"].as_array().unwrap().len(), 64);
    }

    #[test]
    fn unrelabelled_barrier_also_holds() {
        let sat = encode_xors(&TRIPLES, &SAT_RHS);
        let unsat = encode_xors(&TRIPLES, &UNSAT_RHS);
        assert_eq!(source_statistics(&sat), source_statistics(&unsat));
        assert_eq!(models(&sat), 32);
        assert_eq!(models(&unsat), 0);
        assert!(recover_xor_equations(&sat).contradiction.is_none());
        assert!(recover_xor_equations(&unsat).contradiction.is_some());
    }
}
