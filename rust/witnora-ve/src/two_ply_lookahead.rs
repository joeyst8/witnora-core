//! R-042: bounded Davis-Putnam elimination with two-ply structural lookahead.
//! This is a heuristic scheduler, not a new proof rule or runtime guarantee.
//! Every proposed transition is exact existential variable elimination.

use crate::cnf::CanonicalCnf;
use std::cmp::Ordering;

fn structural_score(original: &CanonicalCnf, candidate: &CanonicalCnf) -> f64 {
    let variables = original.variables().len() as i64 - candidate.variables().len() as i64;
    let clauses = original.clauses.len() as i64 - candidate.clauses.len() as i64;
    let original_literals: usize = original.clauses.iter().map(Vec::len).sum();
    let candidate_literals: usize = candidate.clauses.iter().map(Vec::len).sum();
    let literals = original_literals as i64 - candidate_literals as i64;
    variables as f64 * 4.0 + clauses as f64 + literals as f64 * 0.1
}

/// Enumerate exact DP variable eliminations without asserting that they
/// improve SAT runtime. Negative budgets reproduce Python's empty/restricted
/// option semantics; the public two-ply heuristic validates its own budgets.
pub fn elimination_options(
    formula: &CanonicalCnf, max_pairs: i32, growth_budget: i32,
) -> Vec<(u32, CanonicalCnf)> {
    let mut options = Vec::new();
    for pivot in formula.variables() {
        let positive = pivot as i32;
        let negative = -positive;
        let pos: Vec<_> = formula.clauses.iter()
            .filter(|row| row.contains(&positive)).collect();
        let neg: Vec<_> = formula.clauses.iter()
            .filter(|row| row.contains(&negative)).collect();
        if (pos.len() as i64) * (neg.len() as i64) > max_pairs as i64 {
            continue;
        }
        let mut rows: Vec<Vec<i32>> = formula.clauses.iter()
            .filter(|row| !row.contains(&positive) && !row.contains(&negative))
            .cloned().collect();
        for p in &pos {
            for n in &neg {
                let resolved: Vec<i32> = p.iter().copied()
                    .filter(|&lit| lit != positive)
                    .chain(n.iter().copied().filter(|&lit| lit != negative))
                    .collect();
                rows.push(resolved);
            }
        }
        let reduced = CanonicalCnf::from_signed(&rows)
            .expect("resolution of canonical clauses stays valid");
        if reduced != *formula
            && reduced.clauses.len() as i64
                <= formula.clauses.len() as i64 + growth_budget as i64
        {
            options.push((pivot, reduced));
        }
    }
    options
}

/// Return the best candidate under the reference's fixed structural score,
/// including the unchanged input formula among the choices.
pub fn two_ply_pivot(
    formula: &CanonicalCnf, max_pairs: i32,
    growth_budget: i32, beam_width: i32,
) -> Result<CanonicalCnf, String> {
    if max_pairs < 0 || growth_budget < 0 || !(1..=32).contains(&beam_width) {
        return Err("invalid bounded lookahead budget".into());
    }
    let mut first = elimination_options(formula, max_pairs, growth_budget);
    first.sort_by(|(p1, f1), (p2, f2)| {
        structural_score(formula, f2)
            .partial_cmp(&structural_score(formula, f1))
            .unwrap_or(Ordering::Equal)
            .then_with(|| f1.clauses.len().cmp(&f2.clauses.len()))
            .then_with(|| p1.cmp(p2))
    });
    let mut choices: Vec<(Vec<u32>, CanonicalCnf)> =
        vec![(Vec::new(), formula.clone())];
    for (pivot, reduced) in first.into_iter().take(beam_width as usize) {
        choices.push((vec![pivot], reduced.clone()));
        for (next_pivot, twice) in
            elimination_options(&reduced, max_pairs, growth_budget)
        {
            choices.push((vec![pivot, next_pivot], twice));
        }
    }
    choices.sort_by(|(p1, f1), (p2, f2)| {
        structural_score(formula, f2)
            .partial_cmp(&structural_score(formula, f1))
            .unwrap_or(Ordering::Equal)
            .then_with(|| f1.clauses.len().cmp(&f2.clauses.len()))
            .then_with(|| p1.len().cmp(&p2.len()))
            .then_with(|| p1.cmp(p2))
    });
    Ok(choices.remove(0).1)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn cnf(rows: &[Vec<i32>]) -> CanonicalCnf {
        CanonicalCnf::from_signed(rows).unwrap()
    }

    #[test]
    fn exact_resolution_and_absent_polarity_elimination() {
        let input = cnf(&[vec![1, 2], vec![-1, 3]]);
        let options = elimination_options(&input, 12, 2);
        assert_eq!(options[0].0, 1);
        assert_eq!(options[0].1, cnf(&[vec![2, 3]]));
        assert_eq!(options[1].0, 2);
        assert_eq!(options[1].1, cnf(&[vec![-1, 3]]));
        assert_eq!(two_ply_pivot(&input, 12, 2, 8).unwrap(), cnf(&[]));
    }

    #[test]
    fn contradictory_units_and_budget_validation() {
        let input = cnf(&[vec![1], vec![-1]]);
        let output = two_ply_pivot(&input, 12, 2, 8).unwrap();
        assert_eq!(output, cnf(&[vec![]]));
        assert_eq!(elimination_options(&input, 0, 2).len(), 0);
        for (a, b, c) in [(-1, 0, 1), (0, -1, 1), (0, 0, 0), (0, 0, 33)] {
            assert!(two_ply_pivot(&input, a, b, c).is_err());
        }
    }
}
