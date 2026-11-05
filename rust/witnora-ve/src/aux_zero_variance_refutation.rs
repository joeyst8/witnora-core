//! W-CROSSDOMAIN-018: exact covariance-nullspace UNSAT witnesses.
//! Degree-three constant-coefficient polynomial refutations, not a SAT solver.

use num_bigint::BigInt;
use num_traits::{One, Zero};
use serde_json::{json, Value};
use std::collections::BTreeMap;

const N: usize = 12;
const STEP: u32 = 0x9E37_79B9;

#[derive(Clone, Copy, PartialEq, Eq)]
enum Family { Planted, Boundary, EightCore, ParityCycle }

impl Family {
    fn seed(self) -> u32 {
        match self {
            Self::Planted => 0xD18C_0DE1, Self::Boundary => 0xD18C_0DE2,
            Self::EightCore => 0xD18C_0DE3, Self::ParityCycle => 0xD18C_0DE4,
        }
    }
    fn name(self) -> &'static str {
        match self {
            Self::Planted => "fresh_planted_sat_48",
            Self::Boundary => "fresh_uniform_boundary_48",
            Self::EightCore => "eight_pattern_embedded_unsat_56",
            Self::ParityCycle => "four_xor_cycle_unsat_64",
        }
    }
}

fn next(state: &mut u32) -> u32 {
    *state ^= *state << 13;
    *state ^= *state >> 17;
    *state ^= *state << 5;
    *state
}

fn random_clause(state: &mut u32) -> Vec<i32> {
    let mut clause = Vec::with_capacity(3);
    let mut seen = [false; N];
    while clause.len() < 3 {
        let v = (next(state) as usize) % N;
        if seen[v] {continue;}
        seen[v] = true;
        let lit = (v + 1) as i32;
        clause.push(if next(state) & 1 != 0 {-lit} else {lit});
    }
    clause
}

fn source(family: Family, index: usize) -> Vec<Vec<i32>> {
    let mut state = family.seed() ^ ((index as u32) + 1).wrapping_mul(STEP);
    let target = match family {
        Family::EightCore => 56, Family::ParityCycle => 64, _ => 48,
    };
    let mut clauses = Vec::with_capacity(target);
    if family == Family::EightCore {
        for mask in 0..8 {
            clauses.push((0..3).map(|j| {
                let lit = j + 1;
                if mask & (1 << j) != 0 {-lit} else {lit}
            }).collect());
        }
    }
    if family == Family::ParityCycle {
        for (vars, desired) in [([1i32, 2, 3],0u32), ([1, 4, 5],0),
                                ([2, 4, 6],0), ([3, 5, 6],1)] {
            for bits in 0u32..8 {
                if bits.count_ones() & 1 == desired {continue;}
                clauses.push(vars.iter().enumerate().map(|(j,&v)| {
                    if (bits & (1u32 << j)) != 0 {-v} else {v}
                }).collect());
            }
        }
    }
    while clauses.len() < target {
        let clause = random_clause(&mut state);
        if family == Family::Planted && clause.iter().all(|&lit| lit > 0) {
            continue;
        }
        clauses.push(clause);
    }
    clauses
}

fn covariance(clauses: &[Vec<i32>]) -> Vec<Vec<i32>> {
    let m = clauses.len();
    let mut matrix = vec![vec![0; m];m];
    for i in 0..m {
        matrix[i][i] = 7;
        for j in (i+1)..m {
            let mut overlap = 0;
            let mut impossible = false;
            for &a in &clauses[i] {
                for &b in &clauses[j] {
                    if a.unsigned_abs() == b.unsigned_abs() {
                        overlap += 1;
                        if (a > 0) != (b > 0) {impossible = true;}
                    }
                }
            }
            let v = if impossible {-1} else {(1i32 << overlap)-1};
            matrix[i][j] = v;
            matrix[j][i] = v;
        }
    }
    matrix
}

fn gcd(mut a: BigInt, mut b: BigInt) -> BigInt {
    while !b.is_zero() {
        let remainder = &a % &b;
        a = b;
        b = remainder;
    }
    if a < BigInt::zero() {-a} else {a}
}

fn normalize(values: &mut [BigInt], weights: &mut [BigInt]) {
    let mut divisor = BigInt::zero();
    for x in values.iter().chain(weights.iter()) {
        if !x.is_zero() {
            divisor = gcd(divisor, x.clone());
            if divisor.is_one() {break;}
        }
    }
    if divisor > BigInt::one() {
        for x in values.iter_mut().chain(weights.iter_mut()) {
            *x /= &divisor;
        }
    }
}

// Integer fraction-free column elimination. Every stored vector equals K*w;
// when a column reduces to zero, its corresponding w is in ker(K).
fn kernel_certificate(matrix: &[Vec<i32>]) -> Option<Vec<BigInt>> {
    let m = matrix.len();
    let mut basis: BTreeMap<usize,(Vec<BigInt>,Vec<BigInt>)> = BTreeMap::new();
    for column in 0..m {
        let mut values = (0..m).map(|i|BigInt::from(matrix[i][column]))
            .collect::<Vec<_>>();
        let mut weights = (0..m).map(|i|if i==column {BigInt::one()}
            else {BigInt::zero()}).collect::<Vec<_>>();
        loop {
            let Some(pivot) = values.iter().position(|v|!v.is_zero()) else {
                if !weights.iter().sum::<BigInt>().is_zero() {
                    return Some(weights);
                }
                break;
            };
            if let Some((vbase,wbase)) = basis.get(&pivot) {
                let a = vbase[pivot].clone();
                let b = values[pivot].clone();
                for k in 0..m {
                    values[k] = &a*&values[k] - &b*&vbase[k];
                    weights[k] = &a*&weights[k] - &b*&wbase[k];
                }
                normalize(&mut values,&mut weights);
            } else {
                basis.insert(pivot,(values,weights));
                break;
            }
        }
    }
    None
}

fn violated(clause: &[i32], assignment: usize) -> bool {
    !clause.iter().any(|&lit| {
        let on = (assignment & (1usize << (lit.unsigned_abs() as usize - 1))) != 0;
        on == (lit > 0)
    })
}

fn model_count(clauses: &[Vec<i32>]) -> usize {
    (0..(1usize << N)).filter(|&a|clauses.iter().all(|c|!violated(c,a))).count()
}

fn verify(matrix:&[Vec<i32>], clauses:&[Vec<i32>], weights:&[BigInt]) -> Result<(),String> {
    let sum = weights.iter().sum::<BigInt>();
    if sum.is_zero() {return Err("W018 zero-sum witness".into());}
    for row in matrix {
        let check = row.iter().zip(weights).map(|(&k,w)|BigInt::from(k)*w)
            .sum::<BigInt>();
        if !check.is_zero() {return Err("W018 K*w != 0".into());}
    }
    let eight = BigInt::from(8);
    if &sum % &eight != BigInt::zero() {
        return Err("W018 witness constant not integral".into());
    }
    let constant = sum / eight;
    for assignment in 0..(1usize << N) {
        let energy = clauses.iter().zip(weights).filter(|(c,_)|violated(c,assignment))
            .map(|(_,w)|w.clone()).sum::<BigInt>();
        if energy != constant {return Err("W018 weighted energy not constant".into());}
    }
    Ok(())
}

fn family_report(family:Family) -> Result<Value,String> {
    let mut certificates = 0;
    let mut sat_count = 0;
    let mut controls = Vec::new();
    for index in 0..32 {
        let clauses = source(family,index);
        let matrix = covariance(&clauses);
        let count = model_count(&clauses);
        if count > 0 {sat_count += 1;}
        if family == Family::Planted && count == 0 {return Err("W018 planted UNSAT".into());}
        if matches!(family, Family::EightCore|Family::ParityCycle) && count != 0 {
            return Err("W018 contradiction core SAT".into());
        }
        let witness = kernel_certificate(&matrix);
        if let Some(ref weights) = witness {
            certificates += 1;
            if count != 0 {return Err("W018 false UNSAT certificate".into());}
            verify(&matrix,&clauses,weights)?;
        }
        if [0,1,31].contains(&index) {
            controls.push(json!({"index":index,"source":clauses,
                "models":count,"covariance_top_left_8":matrix.iter().take(8)
                    .map(|row|row.iter().take(8).copied().collect::<Vec<_>>())
                    .collect::<Vec<_>>(),
                "integer_nullspace_witness":witness.map(|w|w.iter()
                    .map(|x|x.to_string()).collect::<Vec<_>>())}));
        }
    }
    Ok(json!({"family":family.name(),"formulas":32,"satisfiable":sat_count,
        "unsatisfiable":32-sat_count,"certificates":certificates,
        "controls":controls}))
}

pub fn audit() -> Result<Value,String> {
    let mut families=Vec::new();
    for family in [Family::Planted,Family::Boundary,Family::EightCore,Family::ParityCycle] {
        families.push(family_report(family)?);
    }
    Ok(json!({"research_id":"W-CROSSDOMAIN-018",
        "claim":"sound sufficient UNSAT certificate; incomplete refutation system",
        "method":"exact integer K-nullvector with nonzero coefficient sum",
        "families":families}))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn eight_core_has_exact_integer_witness() {
        let clauses=source(Family::EightCore,0);
        let k=covariance(&clauses);
        let w=kernel_certificate(&k).expect("complete eight-core must be witnessed");
        verify(&k,&clauses,&w).unwrap();
        assert_eq!(model_count(&clauses),0);
    }
    #[test]
    fn the_parity_cycle_is_unsat_without_local_eight_core() {
        let clauses=source(Family::ParityCycle,0);
        assert_eq!(model_count(&clauses),0);
    }
}
