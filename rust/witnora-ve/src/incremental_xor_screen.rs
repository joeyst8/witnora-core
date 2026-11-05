//! R-064: necessary count-only XOR-pattern prefilter, never a certificate.
use std::collections::{BTreeMap, BTreeSet};

pub fn possible_two_xor_patterns(clauses: &[Vec<i32>]) -> Result<bool, String> {
    let mut groups: BTreeMap<Vec<u32>, usize> = BTreeMap::new();
    for clause in clauses {
        if clause.contains(&0) { return Err("zero literal".into()); }
        let support: BTreeSet<u32> = clause.iter().map(|lit|lit.unsigned_abs()).collect();
        if (2..=6).contains(&support.len()) && support.len() == clause.len() {
            *groups.entry(support.into_iter().collect()).or_default() += 1;
        }
    }
    Ok(groups.iter().filter(|(support, count)|
        **count == (1usize << (support.len() - 1))).take(2).count() >= 2)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn necessary_not_sufficient() {
        assert_eq!(possible_two_xor_patterns(&[vec![1,2],vec![-1,2],
          vec![3,4],vec![-3,4]]),Ok(true));
        assert_eq!(possible_two_xor_patterns(&[vec![1,2],vec![-1,2]]),Ok(false));
        assert!(possible_two_xor_patterns(&[vec![0,2]]).is_err());
    }
}
