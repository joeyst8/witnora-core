//! R-049: fixed preregistered cost-sensitive adaptive/greedy gate.
//! Score fitting is a finite training heuristic, not an exact complexity
//! predictor, new SAT inference rule, or Lean-certified proof.

use crate::cnf::CanonicalCnf;
use crate::adaptive_lookahead::adaptive_pivot;
use crate::selective_lookahead::{cheap_pivot_features,PivotFeatures};
use crate::two_ply_lookahead::bounded_elimination;

pub const THRESHOLDS:[i32;5]=[2,3,5,8,1_000_000];

#[derive(Clone,Debug)]
pub struct Observation {
    pub mixed_pivots:i32,
    pub variables:i32,
    pub clauses:i32,
    pub adaptive_score:f64,
    pub greedy_score:f64,
    pub adaptive_ms:f64,
    pub greedy_ms:f64,
}

#[derive(Clone,Debug,PartialEq)]
pub struct ThresholdResult {
    pub threshold:i32,
    pub train_utility:f64,
    pub selected_train_cases:usize,
    pub train_cases:usize,
    pub cost_weight:f64,
}

#[derive(Clone,Debug,PartialEq,Eq)]
pub struct GatedOutcome {
    pub formula:CanonicalCnf,
    pub features:PivotFeatures,
    pub mode:&'static str,
    pub expanded:usize,
    pub threshold:i32,
}

pub fn choose_threshold(
    observations:&[Observation],cost_weight:f64,
)->Result<ThresholdResult,String> {
    if observations.is_empty() || cost_weight<0.0 {
        return Err("missing observations or invalid penalty".into());
    }
    let mut best:Option<(f64,i32,usize)>=None;
    for threshold in THRESHOLDS {
        let mut utility=0.0f64;
        let mut selections=0usize;
        for row in observations {
            if row.mixed_pivots>=threshold &&
               row.variables<=25 && row.clauses<=140
            {
                selections+=1;
                utility+=(row.adaptive_score-row.greedy_score
                    -cost_weight*(row.adaptive_ms-row.greedy_ms));
            }
        }
        // Python's round(value, 8) uses ties-to-even on the
        // scaled decimal position. This reproduces the bounded
        // training-score presentation and tie ranking.
        let rounded=(utility*100_000_000.0).round_ties_even()
            /100_000_000.0;
        if best.as_ref().is_none_or(|(u,t,_)|
            rounded>*u || (rounded==*u && threshold>*t)
        ) {
            best=Some((rounded,threshold,selections));
        }
    }
    let (utility,threshold,selected)=best.expect("five thresholds");
    Ok(ThresholdResult {
        threshold,train_utility:utility,
        selected_train_cases:selected,train_cases:observations.len(),
        cost_weight,
    })
}

pub fn cost_sensitive_pivot(
    source:&[Vec<i32>],threshold:i32,max_pairs:i32,
)->Result<GatedOutcome,String> {
    if !THRESHOLDS.contains(&threshold)||max_pairs<0 {
        return Err("threshold must come from the preregistered set".into());
    }
    let formula=CanonicalCnf::from_signed(source)?;
    let features=cheap_pivot_features(&formula,max_pairs);
    let eligible=features.viable_mixed_pivots as i64 >=threshold as i64
        && features.variables<=25 && features.clauses<=140;
    let (candidate,expanded,mode)=if eligible {
        let out=adaptive_pivot(&formula,max_pairs,2,4,24,3,2.0)?;
        (out.formula,out.expanded,"adaptive")
    }else{
        let first=bounded_elimination(&formula,max_pairs);
        (bounded_elimination(&first,max_pairs),0,"greedy")
    };
    Ok(GatedOutcome {
        formula:candidate,features,mode,expanded,threshold,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn negative_utilities_favor_greedy_preregistered_threshold() {
        let observation=Observation {
            mixed_pivots:3,variables:5,clauses:8,
            adaptive_score:1.0,greedy_score:5.0,
            adaptive_ms:4.0,greedy_ms:1.0,
        };
        let result=choose_threshold(&[observation],2.0).unwrap();
        assert_eq!(result.threshold,1_000_000);
        assert_eq!(result.selected_train_cases,0);
        assert_eq!(result.train_utility,0.0);
        assert!(choose_threshold(&[],2.0).is_err());
        assert!(choose_threshold(&[], -1.0).is_err());
    }

    #[test]
    fn frozen_gate_and_errors() {
        let source=vec![vec![1,2],vec![-1,2],vec![1,-2]];
        let out=cost_sensitive_pivot(&source,1_000_000,12).unwrap();
        assert_eq!(out.mode,"greedy");
        assert_eq!(out.expanded,0);
        assert!(cost_sensitive_pivot(&source,1,12).is_err());
        assert!(cost_sensitive_pivot(&source,2,-1).is_err());
    }
}
