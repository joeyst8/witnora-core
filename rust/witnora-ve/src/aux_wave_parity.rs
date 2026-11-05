//! W-CROSSDOMAIN-014: compute one exact Walsh character of the source-clause
//! violation vector by bounded inclusion-exclusion on selected clauses.
//! Cost is exponential in selected-row size, not in the total variable count;
//! no general polynomial-time SAT/#SAT algorithm follows.

use std::collections::BTreeSet;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct WaveBias {
    /// Sum over all Boolean assignments of (-1)^(selected violation parity).
    pub signed_assignment_sum: i128,
    pub normalized_selected_clauses: usize,
    pub subset_terms: usize,
    pub clause_visits: usize,
    pub literal_visits: usize,
}

pub fn exact_wave_bias(source: &[Vec<i32>], nvars: usize,
                       selected: &[usize]) -> Result<WaveBias, String> {
    if nvars > 20 || source.len() > 64 || selected.len() > 24 {
        return Err("source or wave-projection cap exceeded".into());
    }
    let mut normalized = BTreeSet::new();
    for &index in selected {
        if index >= source.len() { return Err("missing selected source clause".into()); }
        if !normalized.insert(index) { normalized.remove(&index); }
    }
    if normalized.len() > 12 { return Err("wave frequency support exceeds 12".into()); }
    // Validate every source clause, including those outside the selected row.
    for clause in source {
        for &lit in clause {
            if lit == 0 || lit == i32::MIN || lit.unsigned_abs() as usize > nvars {
                return Err("literal outside wave-projection variable universe".into());
            }
        }
    }
    let clauses = normalized.into_iter().collect::<Vec<_>>();
    let terms = 1usize << clauses.len();
    let mut signed_sum = 0i128;
    let mut clause_visits = 0usize;
    let mut literal_visits = 0usize;
    for subset in 0..terms {
        let mut required_true = 0u32;
        let mut required_false = 0u32;
        let mut consistent = true;
        for (position, &source_index) in clauses.iter().enumerate() {
            if subset & (1usize << position) == 0 { continue; }
            clause_visits += 1;
            for &lit in &source[source_index] {
                literal_visits += 1;
                let bit = 1u32 << (lit.unsigned_abs() - 1);
                // A positive literal is false iff its variable is false;
                // a negative literal is false iff its variable is true.
                if lit > 0 { required_false |= bit; }
                else { required_true |= bit; }
                if required_true & required_false != 0 {
                    consistent = false;
                    break;
                }
            }
            if !consistent { break; }
        }
        if consistent {
            let fixed = (required_true | required_false).count_ones() as usize;
            let assignments = 1i128 << (nvars - fixed);
            let sign = (-2i128).pow(subset.count_ones());
            signed_sum = signed_sum.checked_add(sign * assignments)
                .ok_or("wave projection sum overflow")?;
        }
    }
    Ok(WaveBias { signed_assignment_sum: signed_sum,
        normalized_selected_clauses: clauses.len(), subset_terms: terms,
        clause_visits, literal_visits })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn direct(source: &[Vec<i32>], nvars: usize, selected: &[usize]) -> i128 {
        let mut answer = 0i128;
        for assignment in 0..(1usize << nvars) {
            let parity = selected.iter().filter(|&&index| {
                !source[index].iter().any(|&lit| {
                    let bit = assignment & (1usize << (lit.unsigned_abs() as usize - 1)) != 0;
                    bit == (lit > 0)
                })
            }).count() % 2;
            answer += if parity == 0 { 1 } else { -1 };
        }
        answer
    }

    #[test]
    fn exact_wave_matches_literal_oracle_with_conflicts_empty_and_duplicates() {
        for (source, row, n) in [
            (vec![vec![1], vec![-1]], vec![0, 1], 1usize),
            (vec![vec![1, -1]], vec![0], 1),
            (vec![vec![]], vec![0], 2),
            (vec![vec![1, 2], vec![-1, -2], vec![2]], vec![0, 1, 2], 2),
            (vec![vec![1, 2, 3], vec![-1, 4], vec![4, -4]], vec![0, 1], 4),
            (vec![vec![1], vec![-1]], vec![0, 0, 1, 1], 1),
        ] {
            let coefficient = exact_wave_bias(&source, n, &row).unwrap();
            assert_eq!(coefficient.signed_assignment_sum, direct(&source, n, &row));
        }
        let both = exact_wave_bias(&[vec![1], vec![-1]], 1, &[0, 1]).unwrap();
        assert_eq!(both.signed_assignment_sum, -2);
        assert_eq!(exact_wave_bias(&[vec![1]], 1, &[0, 0]).unwrap()
                   .signed_assignment_sum, 2);
    }

    #[test]
    fn exact_wave_resource_bounds_are_explicit() {
        assert!(exact_wave_bias(&[vec![0]], 1, &[0]).is_err());
        assert!(exact_wave_bias(&[vec![i32::MIN]], 1, &[0]).is_err());
        assert!(exact_wave_bias(&[vec![2]], 1, &[0]).is_err());
        assert!(exact_wave_bias(&[vec![1]], 1, &[1]).is_err());
        assert!(exact_wave_bias(&[vec![1]], 21, &[0]).is_err());
    }
}
