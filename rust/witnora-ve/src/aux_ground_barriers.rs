//! W-GEOMETRY-002: exact *ground-state* connectivity under an energy budget.
//! Each satisfying assignment is a zero-energy state; two ground states are
//! equivalent at threshold t when connected by Hamming-one moves through
//! assignments violating at most t source clauses. This is NOT the total
//! Betti-0 count of the full sublevel set (which may contain components with
//! no satisfying states). For independent source components, equivalence on
//! ground states factors exactly as a Cartesian product.

use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct GroundBarrierProfile {
    pub models: u64,
    /// Ground-state equivalence classes for thresholds 0..=source.len().
    pub ground_clusters: Vec<u64>,
    /// Largest number of ground states in any such class at each threshold.
    pub largest_ground_cluster: Vec<u64>,
    /// Lowest energy budget connecting all ground states; None when UNSAT.
    pub connectivity_barrier: Option<usize>,
}

fn root(parent: &mut [usize], mut v: usize) -> usize {
    while parent[v] != v {
        let next = parent[v];
        parent[v] = parent[next];
        v = parent[v];
    }
    v
}

fn union(parent: &mut [usize], sizes: &mut [usize], a: usize, b: usize) {
    let mut ra = root(parent, a);
    let mut rb = root(parent, b);
    if ra == rb { return; }
    if sizes[ra] < sizes[rb] { std::mem::swap(&mut ra, &mut rb); }
    parent[rb] = ra;
    let absorbed = sizes[rb];
    sizes[ra] += absorbed;
}

fn local_profile(variables: &[usize], clauses: &[&Vec<i32>])
    -> Result<GroundBarrierProfile, String> {
    let width = variables.len();
    let states = 1usize << width;
    let mut energy_buckets = vec![Vec::<usize>::new(); clauses.len() + 1];
    for assignment in 0..states {
        let energy = clauses.iter().filter(|clause| !clause.iter().any(|&literal| {
            let variable = literal.unsigned_abs() as usize - 1;
            let bit = variables.binary_search(&variable)
                .expect("validated component contains entire clause scope");
            let value = assignment & (1usize << bit) != 0;
            value == (literal > 0)
        })).count();
        energy_buckets[energy].push(assignment);
    }
    let ground = &energy_buckets[0];
    let models = ground.len() as u64;

    let mut parent = (0..states).collect::<Vec<_>>();
    let mut sizes = vec![1usize; states];
    let mut active = vec![false; states];
    let mut ground_clusters = vec![0u64; clauses.len() + 1];
    let mut largest_ground_cluster = vec![0u64; clauses.len() + 1];
    for threshold in 0..=clauses.len() {
        for &assignment in &energy_buckets[threshold] {
            active[assignment] = true;
            for bit in 0..width {
                let neighbor = assignment ^ (1usize << bit);
                if active[neighbor] {
                    union(&mut parent, &mut sizes, assignment, neighbor);
                }
            }
        }
        let mut ground_sizes = BTreeMap::<usize, u64>::new();
        for &assignment in ground {
            let representative = root(&mut parent, assignment);
            *ground_sizes.entry(representative).or_default() += 1;
        }
        ground_clusters[threshold] = ground_sizes.len() as u64;
        largest_ground_cluster[threshold] = ground_sizes.values().copied().max().unwrap_or(0);
    }
    let connectivity_barrier = if models == 0 {None} else {
        ground_clusters.iter().position(|&clusters| clusters == 1)
    };
    Ok(GroundBarrierProfile {
        models, ground_clusters, largest_ground_cluster, connectivity_barrier,
    })
}

/// Compose source-exact ground-state connectivity profiles over independent
/// primal components. The local Hamming cube is enumerated only for each
/// bounded component, never for all global assignments.
pub fn exact_ground_barriers(
    source: &[Vec<i32>], nvars: usize, max_component_variables: usize,
) -> Result<GroundBarrierProfile, String> {
    if nvars > 32 || source.len() > 64 || max_component_variables == 0
        || max_component_variables > 14 {
        return Err("unsupported ground-geometry/source/component cap".into());
    }
    let mut parent = (0..nvars).collect::<Vec<_>>();
    let mut anchored = Vec::new();
    let mut has_empty_clause = false;
    for clause in source {
        if clause.is_empty() {
            has_empty_clause = true;
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
        let first = *support.iter().next().ok_or("unexpected empty support")?;
        for &variable in support.iter().skip(1) {
            let a = root(&mut parent, first);
            let b = root(&mut parent, variable);
            if a != b { parent[b] = a; }
        }
        anchored.push((clause, first));
    }
    if has_empty_clause {
        return Ok(GroundBarrierProfile {
            models: 0, ground_clusters: vec![0; source.len() + 1],
            largest_ground_cluster: vec![0; source.len() + 1],
            connectivity_barrier: None,
        });
    }

    let mut components: BTreeMap<usize, Vec<usize>> = BTreeMap::new();
    for variable in 0..nvars {
        components.entry(root(&mut parent, variable))
            .or_default().push(variable);
    }
    let mut grouped: BTreeMap<usize, Vec<&Vec<i32>>> = BTreeMap::new();
    for &(clause, first) in &anchored {
        grouped.entry(root(&mut parent, first)).or_default().push(clause);
    }

    let thresholds = source.len() + 1;
    let mut total = GroundBarrierProfile {
        models: 1, ground_clusters: vec![1; thresholds],
        largest_ground_cluster: vec![1; thresholds], connectivity_barrier: Some(0),
    };
    for (component, variables) in components {
        if variables.len() > max_component_variables {
            return Err("component exceeds ground-geometry enumeration cap".into());
        }
        let clauses = grouped.remove(&component).unwrap_or_default();
        let local = local_profile(&variables, &clauses)?;
        total.models = total.models.checked_mul(local.models)
            .ok_or("global ground-state count overflow")?;
        for threshold in 0..thresholds {
            let index = threshold.min(local.ground_clusters.len() - 1);
            total.ground_clusters[threshold] = total.ground_clusters[threshold]
                .checked_mul(local.ground_clusters[index])
                .ok_or("ground-cluster product overflow")?;
            total.largest_ground_cluster[threshold] = total.largest_ground_cluster[threshold]
                .checked_mul(local.largest_ground_cluster[index])
                .ok_or("largest-ground-cluster product overflow")?;
        }
    }
    total.connectivity_barrier = if total.models == 0 {None} else {
        total.ground_clusters.iter().position(|&count| count == 1)
    };
    if total.models > 0 && total.connectivity_barrier.is_none() {
        return Err("ground-state components never merged at complete energy budget".into());
    }
    if total.models > 0 && total.largest_ground_cluster[thresholds - 1] != total.models {
        return Err("complete-energy ground cluster size mismatch".into());
    }
    Ok(total)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn twelve_independent_equivalence_pairs_merge_at_one_violation() {
        let mut source = Vec::new();
        for j in 0..12 {
            let x = (2*j+1) as i32;
            let y = (2*j+2) as i32;
            source.push(vec![x, -y]);
            source.push(vec![-x, y]);
        }
        let got = exact_ground_barriers(&source, 24, 2).unwrap();
        assert_eq!(got.models, 1 << 12);
        assert_eq!(got.ground_clusters[0], 1 << 12);
        assert_eq!(got.largest_ground_cluster[0], 1);
        assert_eq!(got.ground_clusters[1], 1);
        assert_eq!(got.largest_ground_cluster[1], 1 << 12);
        assert_eq!(got.connectivity_barrier, Some(1));
    }

    #[test]
    fn matched_energy_histograms_have_different_ground_barrier_curves() {
        let a = vec![vec![1,2],vec![-1,3],vec![-1,4],vec![-2,-3],
                     vec![-2,5],vec![-4,6],vec![-5,-6]];
        let b = vec![vec![1,2],vec![1,3],vec![-1,4],vec![-2,-3],
                     vec![-2,5],vec![-4,6],vec![-5,-6]];
        let ga = exact_ground_barriers(&a, 6, 6).unwrap();
        let gb = exact_ground_barriers(&b, 6, 6).unwrap();
        assert_eq!(ga.models, 2);
        assert_eq!(gb.models, 2);
        assert_eq!((&ga.ground_clusters[0..2], ga.connectivity_barrier), (&[2,1][..],Some(1)));
        assert_eq!((&gb.ground_clusters[0..2], gb.connectivity_barrier), (&[1,1][..],Some(0)));
    }

    #[test]
    fn free_variables_and_unsatisfiable_source_have_exact_boundaries() {
        let free = exact_ground_barriers(&[], 32, 1).unwrap();
        assert_eq!(free.models, 1u64 << 32);
        assert_eq!(free.ground_clusters, vec![1]);
        assert_eq!(free.largest_ground_cluster, vec![1u64 << 32]);
        assert_eq!(free.connectivity_barrier, Some(0));
        let impossible = exact_ground_barriers(&[vec![1], vec![-1]], 1, 1).unwrap();
        assert_eq!(impossible.models, 0);
        assert_eq!(impossible.ground_clusters, vec![0,0,0]);
        assert_eq!(impossible.connectivity_barrier, None);
        assert_eq!(exact_ground_barriers(&[vec![]], 1, 1).unwrap().models, 0);
        assert!(exact_ground_barriers(&[vec![0]], 1, 1).is_err());
    }
}
