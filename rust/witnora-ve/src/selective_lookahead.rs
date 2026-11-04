//! R-044: cheap feature gate for adaptive versus greedy DP scheduling.
//! Experimental heuristic only: no trusted solver outcome or runtime claim.

use crate::cnf::CanonicalCnf;
use crate::adaptive_lookahead::adaptive_pivot;
use crate::two_ply_lookahead::bounded_elimination;
use std::collections::BTreeMap;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PivotFeatures {
    pub viable_mixed_pivots: usize,
    pub pure_pivots: usize,
    pub variables: usize,
    pub clauses: usize,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SelectiveOutcome {
    pub formula: CanonicalCnf,
    pub features: PivotFeatures,
    pub mode: &'static str,
    pub expanded: usize,
    pub trusted: bool,
    pub promoted: bool,
}

pub fn cheap_pivot_features(formula: &CanonicalCnf, max_pairs: i32) -> PivotFeatures {
    let mut occurrence = BTreeMap::<u32,(usize,usize)>::new();
    for clause in &formula.clauses {
        for &literal in clause {
            let counts = occurrence.entry(literal.unsigned_abs()).or_insert((0,0));
            if literal > 0 { counts.0 += 1; } else { counts.1 += 1; }
        }
    }
    PivotFeatures {
        viable_mixed_pivots: occurrence.values().filter(|&&(pos,neg)|
            pos > 0 && neg > 0
            && (pos as i64) * (neg as i64) <= max_pairs as i64
        ).count(),
        pure_pivots: occurrence.values().filter(|&&(pos,neg)|
            pos == 0 || neg == 0
        ).count(),
        variables: formula.variables().len(),
        clauses: formula.clauses.len(),
    }
}

pub fn selective_pivot(
    formula: &CanonicalCnf, max_pairs: i32,
    min_mixed_pivots: i32, max_vars: i32, max_clauses: i32,
    expansion_budget: i32,
) -> Result<SelectiveOutcome,String> {
    if max_pairs < 0 || min_mixed_pivots < 1
        || max_vars < 1 || max_clauses < 1 || expansion_budget < 1
    {
        return Err("invalid selective lookahead gate".into());
    }
    let features=cheap_pivot_features(formula,max_pairs);
    let eligible=features.viable_mixed_pivots as i64 >= min_mixed_pivots as i64
        && features.variables as i64 <= max_vars as i64
        && features.clauses as i64 <= max_clauses as i64;
    if eligible {
        // Python's adaptive_pivot applies its own upper expansion bound
        // only on this branch. Preserve that late validation.
        let result=adaptive_pivot(formula,max_pairs,2,4,expansion_budget,3,2.0)?;
        Ok(SelectiveOutcome {
            formula:result.formula,
            features,mode:"adaptive",expanded:result.expanded,
            trusted:false,promoted:false,
        })
    } else {
        let first=bounded_elimination(formula,max_pairs);
        let greedy=bounded_elimination(&first,max_pairs);
        Ok(SelectiveOutcome {
            formula:greedy,
            features,mode:"greedy",expanded:0,
            trusted:false,promoted:false,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn cheap_features_and_both_gates() {
        let formula=CanonicalCnf::from_signed(&[
            vec![1,2], vec![-1,3], vec![1,-3], vec![-1,-2],
        ]).unwrap();
        let features=cheap_pivot_features(&formula,12);
        assert_eq!(features.variables,3);
        assert_eq!(features.clauses,4);
        assert_eq!(features.viable_mixed_pivots,3);
        let eligible=selective_pivot(&formula,12,1,25,140,24).unwrap();
        assert_eq!(eligible.mode,"adaptive");
        let forced_greedy=selective_pivot(&formula,12,4,25,140,24).unwrap();
        assert_eq!(forced_greedy.mode,"greedy");
        assert!(!eligible.trusted && !eligible.promoted);
        assert!(selective_pivot(&formula,-1,1,25,140,24).is_err());
        // A >1000 expansion budget is rejected by adaptive search only
        // if the selective gate actually routes to that path.
        assert!(selective_pivot(&formula,12,1,25,140,1001).is_err());
        assert!(selective_pivot(&formula,12,4,25,140,1001).is_ok());
    }
}
