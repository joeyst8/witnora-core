//! W-GEOMETRY-001: exact, source-faithful Hamming geometry of SAT solutions.
//! Source-primal components factor as Cartesian products; Walsh/XOR
//! autocorrelation gives the ordered pair-distance enumerator in O(k*2^k)
//! per component. Established techniques; no general efficient #SAT claim.

use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SolutionGeometry {
    pub models: u64,
    pub clusters: u64,
    pub largest_cluster: u64,
    /// distance_ordered[d] counts ordered satisfying pairs (x,y) with
    /// Hamming distance d; includes the diagonal pairs at distance zero.
    pub distance_ordered: Vec<u128>,
}

fn root(parent: &mut [usize], mut variable: usize) -> usize {
    while parent[variable] != variable {
        let next = parent[variable];
        parent[variable] = parent[next];
        variable = parent[variable];
    }
    variable
}

fn walsh(values: &mut [i64]) -> Result<(), String> {
    let mut step = 1usize;
    while step < values.len() {
        for start in (0..values.len()).step_by(2 * step) {
            for offset in 0..step {
                let left = values[start + offset];
                let right = values[start + offset + step];
                values[start + offset] = left.checked_add(right)
                    .ok_or("Walsh addition overflow")?;
                values[start + offset + step] = left.checked_sub(right)
                    .ok_or("Walsh subtraction overflow")?;
            }
        }
        step *= 2;
    }
    Ok(())
}

fn component_geometry(variables: &[usize], clauses: &[&Vec<i32>])
    -> Result<SolutionGeometry, String> {
    let width = variables.len();
    let states = 1usize << width;
    let satisfying = (0..states).map(|assignment| {
        clauses.iter().all(|clause| clause.iter().any(|&literal| {
            let variable = literal.unsigned_abs() as usize - 1;
            let bit = variables.binary_search(&variable)
                .expect("component must contain validated clause scope");
            let value = assignment & (1usize << bit) != 0;
            value == (literal > 0)
        }))
    }).collect::<Vec<_>>();
    let models = satisfying.iter().filter(|&&state| state).count() as u64;

    // Exact Hamming-one connectivity of the local solution-induced graph.
    let mut visited = vec![false; states];
    let mut clusters = 0u64;
    let mut largest_cluster = 0u64;
    for start in 0..states {
        if !satisfying[start] || visited[start] { continue; }
        clusters += 1;
        visited[start] = true;
        let mut pending = vec![start];
        let mut size = 0u64;
        while let Some(current) = pending.pop() {
            size += 1;
            for bit in 0..width {
                let next = current ^ (1usize << bit);
                if satisfying[next] && !visited[next] {
                    visited[next] = true;
                    pending.push(next);
                }
            }
        }
        largest_cluster = largest_cluster.max(size);
    }

    // XOR autocorrelation a(z) = sum_x 1_S(x) 1_S(x XOR z).
    // Walsh(a) = Walsh(1_S)^2; the inverse is the same transform / 2^width.
    // This avoids the O(|S|^2) pair enumeration for dense solution sets.
    let mut transformed = satisfying.iter().map(|&bit| if bit {1i64} else {0i64})
        .collect::<Vec<_>>();
    walsh(&mut transformed)?;
    for coefficient in &mut transformed {
        *coefficient = coefficient.checked_mul(*coefficient)
            .ok_or("autocorrelation square overflow")?;
    }
    walsh(&mut transformed)?;
    let mut distances = vec![0u128; width + 1];
    for (shift, &numerator) in transformed.iter().enumerate() {
        if numerator < 0 || numerator % states as i64 != 0 {
            return Err("nonintegral or negative XOR autocorrelation".into());
        }
        let count = (numerator / states as i64) as u128;
        let distance = shift.count_ones() as usize;
        distances[distance] = distances[distance].checked_add(count)
            .ok_or("distance histogram overflow")?;
    }
    if distances[0] != models as u128 {
        return Err("autocorrelation diagonal mismatch")?;
    }
    Ok(SolutionGeometry {
        models, clusters, largest_cluster, distance_ordered: distances,
    })
}

/// Exact source-CNF solution geometry for variable-disjoint primal components.
/// All variable IDs are one-based signed literals. The API fails closed if a
/// component exceeds the declared exhaustive cap: it does NOT solve arbitrary
/// large connected CNFs by a geometric shortcut.
pub fn exact_solution_geometry(
    source: &[Vec<i32>], nvars: usize, max_component_variables: usize,
) -> Result<SolutionGeometry, String> {
    if nvars > 32 || source.len() > 64 || max_component_variables == 0
        || max_component_variables > 14 {
        return Err("unsupported geometry/component cap".into());
    }
    let mut parent = (0..nvars).collect::<Vec<_>>();
    let mut clauses_by_anchor = Vec::new();
    let mut empty_clause = false;
    for clause in source {
        if clause.is_empty() {
            empty_clause = true;
            continue;
        }
        let mut support = BTreeSet::new();
        for &literal in clause {
            if literal == 0 || literal == i32::MIN
                || literal.unsigned_abs() as usize > nvars {
                return Err("literal outside source variable universe".into());
            }
            support.insert(literal.unsigned_abs() as usize - 1);
        }
        let anchor = *support.iter().next().ok_or("unexpected empty scope")?;
        for &variable in support.iter().skip(1) {
            let a = root(&mut parent, anchor);
            let b = root(&mut parent, variable);
            if a != b { parent[b] = a; }
        }
        clauses_by_anchor.push((clause, anchor));
    }

    // Empty CNF clause is unsatisfied on all assignments, regardless of
    // other components; every distance coefficient and cluster count is zero.
    if empty_clause {
        return Ok(SolutionGeometry {
            models: 0, clusters: 0, largest_cluster: 0,
            distance_ordered: vec![0u128; nvars + 1],
        });
    }

    let mut components: BTreeMap<usize, Vec<usize>> = BTreeMap::new();
    for variable in 0..nvars {
        components.entry(root(&mut parent, variable))
            .or_default().push(variable);
    }
    let mut grouped: BTreeMap<usize, Vec<&Vec<i32>>> = BTreeMap::new();
    for &(clause, anchor) in &clauses_by_anchor {
        grouped.entry(root(&mut parent, anchor)).or_default().push(clause);
    }

    let mut total = SolutionGeometry {
        models: 1, clusters: 1, largest_cluster: 1,
        distance_ordered: vec![1u128],
    };
    for (root_id, variables) in components {
        if variables.len() > max_component_variables {
            return Err("component exceeds exact geometry enumeration cap".into());
        }
        let component_clauses = grouped.remove(&root_id).unwrap_or_default();
        let local = component_geometry(&variables, &component_clauses)?;
        total.models = total.models.checked_mul(local.models)
            .ok_or("global model count overflow")?;
        total.clusters = total.clusters.checked_mul(local.clusters)
            .ok_or("global cluster count overflow")?;
        total.largest_cluster = total.largest_cluster.checked_mul(local.largest_cluster)
            .ok_or("global largest-cluster overflow")?;
        let mut product = vec![0u128;
            total.distance_ordered.len() + local.distance_ordered.len() - 1];
        for (i, &left) in total.distance_ordered.iter().enumerate() {
            for (j, &right) in local.distance_ordered.iter().enumerate() {
                let term = left.checked_mul(right)
                    .ok_or("distance convolution multiplication overflow")?;
                product[i + j] = product[i + j].checked_add(term)
                    .ok_or("distance convolution addition overflow")?;
            }
        }
        total.distance_ordered = product;
    }
    if total.distance_ordered[0] != total.models as u128 {
        return Err("global geometry diagonal mismatch".into());
    }
    let pair_sum = total.distance_ordered.iter().try_fold(0u128, |sum, &count|
        sum.checked_add(count).ok_or("distance polynomial sum overflow"))?;
    if pair_sum != (total.models as u128) * (total.models as u128) {
        return Err("global ordered-pair total mismatch".into());
    }
    Ok(total)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn two_independent_binary_clauses_have_product_distance_polynomial() {
        let source = vec![vec![1,2], vec![3,4]];
        let actual = exact_solution_geometry(&source, 4, 2).unwrap();
        assert_eq!(actual.models, 9);
        assert_eq!(actual.clusters, 1);
        assert_eq!(actual.largest_cluster, 9);
        assert_eq!(actual.distance_ordered, vec![9,24,28,16,4]);
    }

    #[test]
    fn six_variable_matched_energy_witnesses_have_distinct_solution_geometry() {
        let a = vec![vec![1,2],vec![-1,3],vec![-1,4],vec![-2,-3],
                     vec![-2,5],vec![-4,6],vec![-5,-6]];
        let b = vec![vec![1,2],vec![1,3],vec![-1,4],vec![-2,-3],
                     vec![-2,5],vec![-4,6],vec![-5,-6]];
        let ga = exact_solution_geometry(&a, 6, 6).unwrap();
        let gb = exact_solution_geometry(&b, 6, 6).unwrap();
        assert_eq!((ga.models, ga.clusters, ga.largest_cluster), (2,2,1));
        assert_eq!((gb.models, gb.clusters, gb.largest_cluster), (2,1,2));
        assert_eq!(ga.distance_ordered, vec![2,0,0,0,0,0,2]);
        assert_eq!(gb.distance_ordered, vec![2,2,0,0,0,0,0]);
    }

    #[test]
    fn thirty_two_free_variables_have_exact_implicit_pair_counts() {
        let geometry = exact_solution_geometry(&[], 32, 1).unwrap();
        assert_eq!(geometry.models, 1u64 << 32);
        assert_eq!(geometry.clusters, 1);
        assert_eq!(geometry.largest_cluster, 1u64 << 32);
        let mut choose = 1u128;
        for distance in 0..=32usize {
            assert_eq!(geometry.distance_ordered[distance], (1u128 << 32) * choose);
            if distance < 32 { choose = choose * (32 - distance) as u128
                / (distance + 1) as u128; }
        }
        assert_eq!(geometry.distance_ordered.iter().sum::<u128>(), 1u128 << 64);
    }

    #[test]
    fn source_empty_clause_and_bad_inputs_fail_closed() {
        assert_eq!(exact_solution_geometry(&[vec![]], 3, 1).unwrap(),
                   SolutionGeometry {models:0,clusters:0,largest_cluster:0,
                       distance_ordered:vec![0,0,0,0]});
        assert!(exact_solution_geometry(&[vec![0]], 2, 2).is_err());
        assert!(exact_solution_geometry(&[vec![3]], 2, 2).is_err());
        assert!(exact_solution_geometry(&[vec![1,2,3]], 3, 2).is_err());
    }
}
