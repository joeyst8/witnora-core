//! R-149/R-150: bounded parent-row resolution and expected encoding admission.
//! The output is a proof *candidate*; independent RUP/DRAT checking is required.
use std::collections::BTreeSet;
use std::time::Instant;

pub type Answer = (usize, usize, usize, Option<String>, Vec<String>, Vec<Vec<i64>>);

#[allow(clippy::too_many_arguments)]
pub fn derive(
    left_encoding: &[Vec<i64>], right_encoding: &[Vec<i64>],
    left_variables: &[usize], right_variables: &[usize],
    expected_encoding: &[Vec<i64>], active_clauses: &[Vec<i64>],
    emitted: usize, proof_bytes: usize, max_width: usize,
    max_proof_clauses: usize, max_proof_bytes: usize,
    timeout_seconds: Option<f64>, elapsed_before_seconds: f64,
) -> Answer {
    let started = Instant::now();
    let expired = || timeout_seconds.is_some_and(|cap| {
        elapsed_before_seconds + started.elapsed().as_secs_f64() > cap
    });
    let mut focus = left_encoding.iter().chain(right_encoding).cloned()
        .collect::<BTreeSet<_>>();
    let left = left_variables.iter().copied().collect::<BTreeSet<_>>();
    let right = right_variables.iter().copied().collect::<BTreeSet<_>>();
    let expected = expected_encoding.iter().cloned().collect::<BTreeSet<_>>();
    let mut active = active_clauses.iter().cloned().collect::<BTreeSet<_>>();
    let mut new_lines = Vec::<String>::new();
    let mut new_clauses = Vec::<Vec<i64>>::new();
    let mut count = emitted;
    let mut bytes = proof_bytes;
    let mut width = max_width;

    macro_rules! result {
        ($error:expr) => {
            (count, bytes, width, $error, new_lines, new_clauses)
        };
    }
    macro_rules! emit {
        ($clause:expr) => {{
            let clause = $clause;
            let (n, b, w, error, should_emit) = crate::xor_proof_emit::emit(
                clause, active.contains(clause), count, bytes, width,
                max_proof_clauses, max_proof_bytes);
            count = n; bytes = b; width = w;
            if let Some(error) = error {
                return result!(Some(error));
            }
            if should_emit {
                new_lines.push(crate::xor_proof_emit::clause_line(clause));
                active.insert(clause.clone());
                new_clauses.push(clause.clone());
            }
        }};
    }

    for &variable in left.intersection(&right) {
        if expired() { return result!(Some("SKIPPED_TIME_CAP".into())); }
        let Ok(pivot) = i64::try_from(variable) else {
            return result!(Some("ROW_OPERATION_ENCODING_DERIVATION_FAILED".into()));
        };
        let positives = focus.iter().filter(|c| c.contains(&pivot))
            .cloned().collect::<Vec<_>>();
        let negatives = focus.iter().filter(|c| c.contains(&-pivot))
            .cloned().collect::<Vec<_>>();
        let mut generated = BTreeSet::new();
        for a in &positives {
            for b in &negatives {
                let Some(resolvent) = crate::xor_drat_resolution::resolve_fast(a,b,pivot)
                    else { continue; };
                generated.insert(resolvent.clone());
                emit!(&resolvent);
                if expired() { return result!(Some("SKIPPED_TIME_CAP".into())); }
            }
        }
        focus.retain(|c| !c.contains(&pivot) && !c.contains(&-pivot));
        focus.extend(generated);
    }
    if !expected.is_subset(&focus) {
        return result!(Some("ROW_OPERATION_ENCODING_DERIVATION_FAILED".into()));
    }
    for clause in &expected { emit!(clause); }
    result!(None)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn contradictory_unit_row_derives_empty() {
        let out = derive(&[vec![1]], &[vec![-1]], &[1], &[1], &[vec![]],
            &[vec![1],vec![-1]], 0, 0, 0, 4, 20, None, 0.0);
        assert_eq!((out.0,out.1,out.2,out.3), (1,2,0,None));
        assert_eq!(out.4, vec!["0".to_string()]);
        assert_eq!(out.5, vec![vec![]]);
    }
}
