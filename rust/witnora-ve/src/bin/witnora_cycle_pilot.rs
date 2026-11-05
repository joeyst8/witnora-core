//! W-CROSSDOMAIN-004: source-to-result pilot, not a SAT or proof certificate.
//! The baseline uses existing Rust complete-XOR extraction + GF(2) Gaussian;
//! the candidate uses existing Rust complete-gadget cycle analysis.

use num_bigint::BigUint;
use num_traits::{One, Zero};
use serde_json::{json, Value};
use std::{process, time::Instant};
use witnora_ve::{odd_xor_cycle, source_xor, xor_equations};

fn gadget(u: usize, v: usize, rhs: u8) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    for a in 0..=1u8 {
        for b in 0..=1u8 {
            if a ^ b == rhs { continue; }
            let mut clause = vec![if a == 1 { -(u as i32) } else { u as i32 },
                                  if b == 1 { -(v as i32) } else { v as i32 }];
            clause.sort_unstable();
            result.push(clause);
        }
    }
    result
}

fn source_case(n: usize, family: &str) -> Result<Vec<Vec<i32>>, String> {
    if !(2..=32).contains(&n) { return Err("pilot n must be 2..32".into()); }
    let mut edges = (1..n).map(|u| (u, u + 1)).collect::<Vec<_>>();
    match family {
        "tree" => {},
        "cycle_consistent" | "cycle_inconsistent" => edges.push((1, n)),
        "chorded_consistent" => {
            for u in 1..n - 1 { edges.push((u, u + 2)); }
        },
        _ => return Err("unknown source family".into()),
    }
    let mut clauses = Vec::new();
    for (index, (u, v)) in edges.iter().copied().enumerate() {
        let assignment_u = ((u * 7 + 3) % 3 == 0) as u8;
        let assignment_v = ((v * 7 + 3) % 3 == 0) as u8;
        let mut rhs = assignment_u ^ assignment_v;
        if family == "cycle_inconsistent" && index + 1 == edges.len() { rhs ^= 1; }
        clauses.extend(gadget(u, v, rhs));
    }
    Ok(clauses)
}

fn gaussian_source_count(source: &[Vec<i32>], n: usize) -> Result<u64, String> {
    let extracted = source_xor::extract_small_xors(source, n as u32)?;
    if !extracted.residual_clauses.is_empty() {
        return Err("Gaussian pilot source had non-XOR residual clauses".into());
    }
    let equations = extracted.rows.iter().map(|(mask, rhs)| {
        let vars = (0..n).filter(|&index| {
            ((mask >> index) & BigUint::one()) != BigUint::zero()
        }).map(|index| index + 1).collect::<Vec<_>>();
        (vars, *rhs as u8)
    }).collect::<Vec<_>>();
    let (inconsistent, _, pivots, _, _, _, _) = xor_equations::gaussian(&equations);
    if inconsistent { Ok(0) } else { Ok(1u64 << (n - pivots.len())) }
}

fn median(mut values: Vec<u128>) -> u128 {
    values.sort_unstable();
    values[values.len() / 2]
}

fn run_case(n: usize, family: &str, samples: usize) -> Result<Value, String> {
    if !(1..=25).contains(&samples) { return Err("samples must be 1..25".into()); }
    let source = source_case(n, family)?;
    let mut cycle_ns = Vec::new();
    let mut gaussian_ns = Vec::new();
    let mut cycle_count = None;
    for _ in 0..samples {
        let start = Instant::now();
        let profile = odd_xor_cycle::pure_binary_xor_topology(&source, n)?
            .ok_or("cycle route unexpectedly rejected pure source")?;
        cycle_ns.push(start.elapsed().as_nanos());
        let reported = profile.exact_model_count_if_pure.parse::<u64>()
            .map_err(|_| "cycle count was not an integer")?;
        let start = Instant::now();
        let baseline = gaussian_source_count(&source, n)?;
        gaussian_ns.push(start.elapsed().as_nanos());
        if reported != baseline {
            return Err(format!("source count disagreement: cycle={reported}, Gaussian={baseline}"));
        }
        cycle_count = Some(reported);
    }
    let count = cycle_count.ok_or("no pilot result")?;
    if n <= 8 {
        let exhaustive = (0..(1usize << n)).filter(|&assignment| {
            source.iter().all(|clause| clause.iter().any(|&lit| {
                let bit = assignment & (1usize << (lit.unsigned_abs() as usize - 1)) != 0;
                bit == (lit > 0)
            }))
        }).count() as u64;
        if count != exhaustive { return Err("source truth-table disagreement".into()); }
    }
    Ok(json!({
        "n": n, "family": family, "source_clauses": source.len(),
        "exact_model_count": count,
        "cycle_source_to_result_median_ns": median(cycle_ns).to_string(),
        "gaussian_source_to_result_median_ns": median(gaussian_ns).to_string(),
        "samples": samples,
        "scope": "pure binary XOR source only; exploratory within-process timing"
    }))
}

fn main() {
    let mut records = Vec::new();
    for n in [8, 16, 24, 32] {
        for family in ["tree", "cycle_consistent", "cycle_inconsistent", "chorded_consistent"] {
            match run_case(n, family, 7) {
                Ok(record) => records.push(record),
                Err(error) => { eprintln!("pilot failed closed at n={n} {family}: {error}"); process::exit(2); }
            }
        }
    }
    println!("{}", json!({"experiment": "W-CROSSDOMAIN-004", "rows": records}));
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn independent_small_source_controls() {
        for family in ["tree", "cycle_consistent", "cycle_inconsistent", "chorded_consistent"] {
            let record = run_case(8, family, 1).unwrap();
            assert_eq!(record["exact_model_count"],
                       if family == "cycle_inconsistent" { json!(0) } else { json!(2) });
        }
    }

    #[test]
    fn invalid_pilot_parameters_fail_closed() {
        assert!(source_case(33, "tree").is_err());
        assert!(source_case(8, "unknown").is_err());
        assert!(run_case(8, "tree", 0).is_err());
    }
}
