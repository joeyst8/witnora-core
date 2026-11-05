//! R-145/R-146: bounded exact parent lookup and GF(2) row-value validation.
//! It validates candidate trace metadata; no derivation is accepted as a proof.
use std::collections::{BTreeMap, BTreeSet};

pub fn validate(
    rows: &[(String, Vec<usize>, u8)], left_id: &str, right_id: &str,
    result_variables: &[usize], result_rhs: u8,
) -> Option<String> {
    let values = rows.iter().map(|(name, variables, rhs)| {
        (name.as_str(), (variables.iter().copied().collect::<BTreeSet<_>>(), rhs & 1))
    }).collect::<BTreeMap<_, _>>();
    let (Some(left), Some(right)) = (values.get(left_id), values.get(right_id)) else {
        return Some("ROW_OPERATION_PARENT_MISSING".into());
    };
    let expected = left.0.symmetric_difference(&right.0).copied()
        .collect::<BTreeSet<_>>();
    let claimed = result_variables.iter().copied().collect::<BTreeSet<_>>();
    if expected != claimed || (left.1 ^ right.1) != (result_rhs & 1) {
        return Some("ROW_OPERATION_VALUE_MISMATCH".into());
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn parent_and_value_errors() {
        let rows = vec![("A".to_string(), vec![1, 2], 1),
                        ("B".to_string(), vec![2, 3], 1)];
        assert_eq!(validate(&rows, "A", "B", &[1, 3], 0), None);
        assert_eq!(validate(&rows, "A", "missing", &[1, 3], 0),
                   Some("ROW_OPERATION_PARENT_MISSING".into()));
        assert_eq!(validate(&rows, "A", "B", &[1, 2, 3], 0),
                   Some("ROW_OPERATION_VALUE_MISMATCH".into()));
        assert_eq!(validate(&rows, "A", "B", &[1, 3], 1),
                   Some("ROW_OPERATION_VALUE_MISMATCH".into()));
    }
}
