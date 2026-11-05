//! R-143/R-144: retain source row IDs and exact source clause sets.
//! Only data preparation; this does not certify any derived proof line.
use std::collections::BTreeSet;

pub type SourceRow = (String, Vec<Vec<i64>>, Vec<usize>, u8);

pub fn source_rows(rows: &[(Vec<usize>, u8, Vec<Vec<i64>>)]) -> Vec<SourceRow> {
    rows.iter().enumerate().map(|(index, (variables, rhs, clauses))| {
        let canonical_clauses = clauses.iter().cloned().collect::<BTreeSet<_>>()
            .into_iter().collect();
        let canonical_variables = variables.iter().copied().collect::<BTreeSet<_>>()
            .into_iter().collect();
        (format!("input_{index:04}"), canonical_clauses, canonical_variables, rhs & 1)
    }).collect()
}

/// R-148: exact union of source-CNF witness supports.
pub fn source_union(rows: &[Vec<Vec<i64>>]) -> Vec<Vec<i64>> {
    rows.iter().flat_map(|clauses| clauses.iter().cloned())
        .collect::<BTreeSet<_>>().into_iter().collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn preserves_index_and_deduplicates() {
        let rows = source_rows(&[(vec![2, 1, 2], 3,
            vec![vec![-2, 1], vec![-2, 1], vec![2, -1]])]);
        assert_eq!(rows, vec![("input_0000".to_string(),
            vec![vec![-2, 1], vec![2, -1]], vec![1, 2], 1)]);
    }
    #[test]
    fn source_union_deduplicates_empty_clause() {
        assert_eq!(source_union(&[vec![vec![1],vec![]],
            vec![vec![1],vec![-2]]]), vec![vec![],vec![-2],vec![1]]);
    }
}
