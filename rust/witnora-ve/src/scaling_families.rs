//! R-040: deterministic fixed-separator XOR scaling CNF family.
//! This is a finite experimental source generator, not a hardness proof.

use crate::cnf::CanonicalCnf;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ScalingCase {
    pub clauses: Vec<Vec<i32>>,
    pub width: i32,
    pub blocks_per_side: i32,
    pub parity_equations: i32,
    pub expected_boundary: Vec<i32>,
}

fn xor_clauses(vars: &[i32], rhs: u32) -> Vec<Vec<i32>> {
    let arity=vars.len();
    let mut result=Vec::new();
    for mask in 0u32..(1u32<<arity) {
        if mask.count_ones()%2==rhs { continue; }
        let mut clause=vars.iter().enumerate().map(|(i,&v)| {
            let bit=(mask>>(arity-1-i))&1;
            if bit==1 { -v } else { v }
        }).collect::<Vec<_>>();
        clause.sort_unstable();
        result.push(clause);
    }
    result
}

pub fn make_scaling_case(blocks_per_side:i32, width:i32)
    -> Result<ScalingCase,String> {
    if !(1..=128).contains(&blocks_per_side) || !matches!(width,2|3) {
        return Err("scaling case outside bounded experiment".into());
    }
    let boundary=(1..=width).collect::<Vec<i32>>();
    let mut source=Vec::new();
    for index in 0..(2*blocks_per_side) {
        let a=100+2*index;
        let b=a+1;
        let mut vars=boundary.clone();
        vars.extend([a,b]);
        source.extend(xor_clauses(&vars,(index%2) as u32));
    }
    let cnf=CanonicalCnf::from_signed(&source)?;
    Ok(ScalingCase{
        clauses:cnf.clauses,
        width,blocks_per_side,
        parity_equations:2*blocks_per_side,
        expected_boundary:boundary,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn deterministic_exact_parity_clause_counts() {
        for width in [2,3] {
            for blocks in [1,2,5,128] {
                let got=make_scaling_case(blocks,width).unwrap();
                assert_eq!(got.parity_equations,2*blocks);
                assert_eq!(got.expected_boundary,(1..=width).collect::<Vec<_>>());
                assert_eq!(got.clauses.len(),(2*blocks) as usize*
                    (1usize<<((width+1) as usize)));
            }
        }
    }
    #[test]
    fn reject_unbounded_cases() {
        assert_eq!(make_scaling_case(0,2).unwrap_err(),
                   "scaling case outside bounded experiment");
        assert_eq!(make_scaling_case(129,2).unwrap_err(),
                   "scaling case outside bounded experiment");
        assert_eq!(make_scaling_case(2,4).unwrap_err(),
                   "scaling case outside bounded experiment");
    }
}
