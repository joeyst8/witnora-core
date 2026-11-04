//! R-043: adaptive bounded Davis-Putnam elimination scheduling.
//! All transitions preserve SAT/UNSAT, and all scores are heuristic only.
//! This module is experimental; it is not a Lean proof checker.

use crate::cnf::CanonicalCnf;
use crate::two_ply_lookahead::{
    bounded_elimination, elimination_options, structural_score,
};
use std::collections::BTreeSet;
use std::cmp::Ordering;

#[derive(Clone, Debug, PartialEq)]
pub struct AdaptiveOutcome {
    pub formula: CanonicalCnf,
    pub mode: &'static str,
    pub expanded: usize,
    pub depth: usize,
    pub baseline_score: f64,
    pub candidate_score: f64,
}

pub fn adaptive_pivot(
    formula: &CanonicalCnf, max_pairs: i32, growth_budget: i32,
    beam_width: i32, expansion_budget: i32, max_depth: i32,
    ambiguity_margin: f64,
) -> Result<AdaptiveOutcome, String> {
    if max_pairs < 0 || growth_budget < 0
        || !(1..=32).contains(&beam_width)
        || !(1..=1000).contains(&expansion_budget)
        || (max_depth != 2 && max_depth != 3) || ambiguity_margin < 0.0
    {
        return Err("invalid adaptive lookahead budget".into());
    }
    let once = bounded_elimination(formula, max_pairs);
    let greedy = bounded_elimination(&once, max_pairs);
    let score = |candidate: &CanonicalCnf| structural_score(formula, candidate);
    let mut best = if score(&greedy) > 0.0 {
        greedy.clone()
    } else {
        formula.clone()
    };
    let mut options = elimination_options(formula, max_pairs, growth_budget);
    options.sort_by(|(p1, f1), (p2, f2)| {
        score(f2).partial_cmp(&score(f1)).unwrap_or(Ordering::Equal)
            .then_with(|| f1.clauses.len().cmp(&f2.clauses.len()))
            .then_with(|| p1.cmp(p2))
            .then_with(|| f1.formula_hash().cmp(&f2.formula_hash()))
    });
    let report = |result: CanonicalCnf, mode, expanded, depth| {
        let candidate_score = score(&result);
        AdaptiveOutcome {
            formula: result,
            mode, expanded, depth,
            baseline_score: score(&greedy), candidate_score,
        }
    };
    if options.is_empty() {
        return Ok(report(best, "no_pivots", 0, 0));
    }
    if score(&options[0].1) > 0.0
        && (options.len() == 1
            || score(&options[0].1) - score(&options[1].1) >= ambiguity_margin)
    {
        return Ok(report(best, "greedy_confident", 0, 0));
    }

    let mut frontier: Vec<(Vec<u32>, CanonicalCnf)> = options.into_iter()
        .take(beam_width as usize)
        .map(|(pivot, reduced)| (vec![pivot], reduced)).collect();
    let mut seen = BTreeSet::from([formula.formula_hash()]);
    let mut expanded = 0usize;
    let mut depth_reached = 0usize;
    for depth in 1..=max_depth as usize {
        if frontier.is_empty() || expanded >= expansion_budget as usize {
            break;
        }
        let mut next_frontier = Vec::<(Vec<u32>, CanonicalCnf)>::new();
        for (path, state) in frontier {
            if !seen.insert(state.formula_hash()) {
                continue;
            }
            expanded += 1;
            // The original tuple comparison has path length as its second
            // field. Since every explored path is nonempty, a score tie
            // cannot replace the prior best.
            if score(&state) > score(&best) {
                best = state.clone();
            }
            depth_reached = depth_reached.max(depth);
            if expanded >= expansion_budget as usize {
                break;
            }
            if depth < max_depth as usize {
                for (pivot, reduced) in
                    elimination_options(&state, max_pairs, growth_budget)
                {
                    let mut extended = path.clone();
                    extended.push(pivot);
                    next_frontier.push((extended, reduced));
                }
            }
        }
        if depth == 2 && score(&best) > score(&greedy) {
            break;
        }
        next_frontier.sort_by(|(p1, f1), (p2, f2)| {
            score(f2).partial_cmp(&score(f1)).unwrap_or(Ordering::Equal)
                .then_with(|| p1.len().cmp(&p2.len()))
                .then_with(|| p1.cmp(p2))
                .then_with(|| f1.formula_hash().cmp(&f2.formula_hash()))
        });
        frontier = next_frontier.into_iter().take(beam_width as usize).collect();
    }
    Ok(report(best, "adaptive_search", expanded, depth_reached))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_formula_and_invalid_budgets() {
        let cnf = CanonicalCnf::from_signed(&[]).unwrap();
        let result = adaptive_pivot(&cnf, 12, 2, 4, 48, 3, 2.0).unwrap();
        assert_eq!(result.formula, cnf);
        assert_eq!(result.mode, "no_pivots");
        assert_eq!(result.expanded, 0);
        for (pair, growth, beam, expansion, depth, margin) in [
            (-1, 2, 4, 48, 3, 2.0),
            (12, -1, 4, 48, 3, 2.0),
            (12, 2, 0, 48, 3, 2.0),
            (12, 2, 4, 0, 3, 2.0),
            (12, 2, 4, 48, 4, 2.0),
            (12, 2, 4, 48, 3, -1.0),
        ] {
            assert!(adaptive_pivot(
                &cnf, pair, growth, beam, expansion, depth, margin,
            ).is_err());
        }
    }

    #[test]
    fn exact_greedy_and_full_contradiction() {
        let original = CanonicalCnf::from_signed(&[
            vec![1, 2], vec![-1, 3],
        ]).unwrap();
        assert_eq!(
            bounded_elimination(&original, 12).clauses.len(), 1
        );
        let contradictory = CanonicalCnf::from_signed(&[
            vec![1], vec![-1],
        ]).unwrap();
        let result = adaptive_pivot(
            &contradictory, 12, 2, 4, 48, 3, 2.0,
        ).unwrap();
        assert_eq!(result.formula.clauses, vec![Vec::<i32>::new()]);
    }
}
