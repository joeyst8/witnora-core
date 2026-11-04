//! R-013: exact indexed unit-propagation conflict witness producer.
//!
//! This deliberately matches the existing Python queue order and cap
//! behavior. It is NOT a trusted proof checker: emitted units must
//! still be checked by the existing Lean GeneralRUP kernel.

use std::collections::{BTreeSet, HashMap, VecDeque};

fn unique_preserve_order(row: &[i32]) -> Vec<i32> {
    let mut used = BTreeSet::new();
    row.iter().copied().filter(|lit| used.insert(*lit)).collect()
}

/// Returns Some(ordered forced units) when the indexed propagation
/// reaches a contradictory source clause; None when no conflict or
/// budget refusal. An immediate contradiction yields Some(vec![]).
pub fn indexed_unit_conflict_witness(
    database: &[Vec<i32>],
    target_clause: &[i32],
    max_units: usize,
) -> Result<Option<Vec<i32>>, String> {
    for &lit in target_clause.iter().chain(database.iter().flatten()) {
        if lit == 0 || lit == i32::MIN {
            return Err("invalid indexed RUP literal".into());
        }
    }

    let mut assumptions: BTreeSet<i32> =
        target_clause.iter().map(|lit| -lit).collect();
    let mut satisfied = Vec::with_capacity(database.len());
    let mut remaining: Vec<i32> = Vec::with_capacity(database.len());
    let mut occurrence: HashMap<i32, Vec<usize>> = HashMap::new();
    let mut ready = VecDeque::new();

    for (i, row) in database.iter().enumerate() {
        let unique = unique_preserve_order(row);
        for &lit in &unique {
            occurrence.entry(lit).or_default().push(i);
        }
        let sat = unique.iter().any(|lit| assumptions.contains(lit));
        let count = unique.iter()
            .filter(|&&lit| !assumptions.contains(&-lit))
            .count() as i32;
        satisfied.push(sat);
        remaining.push(count);
        if !sat && count == 0 {
            return Ok(Some(vec![]));
        }
        if !sat && count == 1 {
            ready.push_back(i);
        }
    }

    let mut units = Vec::new();
    while let Some(i) = ready.pop_front() {
        if satisfied[i] || remaining[i] != 1 {
            continue;
        }
        let candidates = unique_preserve_order(&database[i])
            .into_iter()
            .filter(|lit| !assumptions.contains(&-lit))
            .collect::<Vec<_>>();
        if candidates.len() != 1 {
            return Ok(None);
        }
        let forced = candidates[0];
        if assumptions.contains(&forced) {
            continue;
        }
        if assumptions.contains(&-forced) || units.len() >= max_units {
            return Ok(None);
        }
        assumptions.insert(forced);
        units.push(forced);
        if let Some(hits) = occurrence.get(&forced) {
            for &j in hits {
                satisfied[j] = true;
            }
        }
        if let Some(hits) = occurrence.get(&-forced) {
            for &j in hits {
                if satisfied[j] {
                    continue;
                }
                remaining[j] -= 1;
                if remaining[j] == 0 {
                    return Ok(Some(units));
                }
                if remaining[j] == 1 {
                    ready.push_back(j);
                }
            }
        }
    }
    Ok(None)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn immediate_conflict_derived_conflict_and_caps() {
        assert_eq!(indexed_unit_conflict_witness(&[vec![]], &[], 10).unwrap(), Some(vec![]));
        assert_eq!(indexed_unit_conflict_witness(&[vec![1]], &[1], 10).unwrap(), Some(vec![]));
        assert_eq!(indexed_unit_conflict_witness(
            &[vec![1], vec![-1]], &[], 10).unwrap(), Some(vec![1]));
        assert_eq!(indexed_unit_conflict_witness(
            &[vec![1], vec![-1]], &[], 0).unwrap(), None);
        assert_eq!(indexed_unit_conflict_witness(&[vec![1]], &[], 10).unwrap(), None);
        assert!(indexed_unit_conflict_witness(&[vec![0]], &[], 10).is_err());
    }

    #[test]
    fn repeated_identical_literals_still_single_units() {
        assert_eq!(indexed_unit_conflict_witness(
            &[vec![1, 1], vec![-1, -1]], &[], 10).unwrap(),
            Some(vec![1]));
    }
}
