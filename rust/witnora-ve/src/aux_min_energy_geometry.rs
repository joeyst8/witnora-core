//! W-GEOMETRY-003: minimum-energy landscapes for both SAT and UNSAT CNFs.
//! The "ground states" of the statistical-physics energy E(x) are *all*
//! assignments minimizing violated source clauses; if E_min>0, the source
//! CNF is UNSAT. For independent source components, baseline energies add and
//! relative-energy ground-state connectivity factors as a Cartesian product.
//! This exact bounded construction is established energy/graph mathematics;
//! no general polynomial-time SAT or Max-SAT method is claimed.

use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MinimumEnergyGeometry {
    pub minimum_violations: usize,
    pub minimizers: u64,
    /// Components of the minimum-energy assignments under paths with E <=
    /// minimum_violations + extra_budget, for budgets 0..=source.len().
    pub minimum_clusters: Vec<u64>,
    pub largest_minimum_cluster: Vec<u64>,
    pub connectivity_barrier_extra: usize,
}

fn root(parent: &mut [usize], mut variable: usize) -> usize {
    while parent[variable] != variable {
        let next = parent[variable];
        parent[variable] = parent[next];
        variable = parent[variable];
    }
    variable
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

fn local_minimum(variables: &[usize], clauses: &[&Vec<i32>])
    -> Result<MinimumEnergyGeometry, String> {
    let width = variables.len();
    let states = 1usize << width;
    let mut energy = Vec::with_capacity(states);
    for assignment in 0..states {
        let violations = clauses.iter().filter(|clause| !clause.iter().any(|&literal| {
            let variable = literal.unsigned_abs() as usize - 1;
            let bit = variables.binary_search(&variable)
                .expect("validated source clause scope within component");
            let value = assignment & (1usize << bit) != 0;
            value == (literal > 0)
        })).count();
        energy.push(violations);
    }
    let minimum = *energy.iter().min().ok_or("empty local assignment universe")?;
    let mut buckets = vec![Vec::<usize>::new(); clauses.len() - minimum + 1];
    for (assignment, &value) in energy.iter().enumerate() {
        buckets[value - minimum].push(assignment);
    }
    let ground = &buckets[0];
    let minimizers = ground.len() as u64;

    let mut parent = (0..states).collect::<Vec<_>>();
    let mut sizes = vec![1usize; states];
    let mut active = vec![false; states];
    let mut clusters = vec![0u64; buckets.len()];
    let mut largest = vec![0u64; buckets.len()];
    for extra in 0..buckets.len() {
        for &assignment in &buckets[extra] {
            active[assignment] = true;
            for bit in 0..width {
                let neighbor = assignment ^ (1usize << bit);
                if active[neighbor] {union(&mut parent, &mut sizes, assignment, neighbor);}
            }
        }
        let mut ground_sizes = BTreeMap::<usize,u64>::new();
        for &assignment in ground {
            let representative = root(&mut parent, assignment);
            *ground_sizes.entry(representative).or_default() += 1;
        }
        clusters[extra] = ground_sizes.len() as u64;
        largest[extra] = ground_sizes.values().copied().max().unwrap_or(0);
    }
    let barrier = clusters.iter().position(|&count|count==1)
        .ok_or("minimum-energy states never connected at full local budget")?;
    Ok(MinimumEnergyGeometry {
        minimum_violations: minimum, minimizers,
        minimum_clusters: clusters, largest_minimum_cluster: largest,
        connectivity_barrier_extra: barrier,
    })
}

pub fn exact_minimum_energy_geometry(
    source: &[Vec<i32>], nvars: usize, max_component_variables: usize,
) -> Result<MinimumEnergyGeometry, String> {
    if nvars > 32 || source.len() > 64 || max_component_variables == 0
        || max_component_variables > 14 {
        return Err("unsupported minimum-energy source/component cap".into());
    }
    let mut parent = (0..nvars).collect::<Vec<_>>();
    let mut anchored = Vec::new();
    let mut empty_clauses = 0usize;
    for clause in source {
        if clause.is_empty() {empty_clauses += 1;continue;}
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
            if a != b {parent[b]=a;}
        }
        anchored.push((clause,first));
    }
    let mut components: BTreeMap<usize, Vec<usize>> = BTreeMap::new();
    for variable in 0..nvars {
        components.entry(root(&mut parent, variable))
            .or_default().push(variable);
    }
    let mut grouped: BTreeMap<usize, Vec<&Vec<i32>>> = BTreeMap::new();
    for &(clause,first) in &anchored {
        grouped.entry(root(&mut parent,first)).or_default().push(clause);
    }

    let thresholds = source.len() + 1;
    let mut result = MinimumEnergyGeometry {
        minimum_violations: empty_clauses, minimizers: 1,
        minimum_clusters: vec![1; thresholds],
        largest_minimum_cluster: vec![1; thresholds],
        connectivity_barrier_extra: 0,
    };
    for (component, variables) in components {
        if variables.len() > max_component_variables {
            return Err("component exceeds minimum-energy enumeration cap".into());
        }
        let local_clauses = grouped.remove(&component).unwrap_or_default();
        let local = local_minimum(&variables, &local_clauses)?;
        result.minimum_violations = result.minimum_violations
            .checked_add(local.minimum_violations)
            .ok_or("minimum energy overflow")?;
        result.minimizers = result.minimizers.checked_mul(local.minimizers)
            .ok_or("minimizer count overflow")?;
        for threshold in 0..thresholds {
            let index = threshold.min(local.minimum_clusters.len()-1);
            result.minimum_clusters[threshold] = result.minimum_clusters[threshold]
                .checked_mul(local.minimum_clusters[index])
                .ok_or("minimum-energy cluster count overflow")?;
            result.largest_minimum_cluster[threshold] = result.largest_minimum_cluster[threshold]
                .checked_mul(local.largest_minimum_cluster[index])
                .ok_or("largest minimum-energy class overflow")?;
        }
    }
    result.connectivity_barrier_extra = result.minimum_clusters.iter()
        .position(|&count|count==1)
        .ok_or("global minimum-energy states never connected")?;
    if result.largest_minimum_cluster[thresholds-1]!=result.minimizers {
        return Err("final minimum-state class does not include all minimizers".into());
    }
    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn contradictory_units_still_have_connected_nonzero_energy_ground_states() {
        let source = vec![vec![1],vec![-1]];
        let got = exact_minimum_energy_geometry(&source,1,1).unwrap();
        assert_eq!(got.minimum_violations,1);
        assert_eq!(got.minimizers,2);
        assert_eq!(got.minimum_clusters,vec![1,1,1]);
        assert_eq!(got.largest_minimum_cluster,vec![2,2,2]);
        assert_eq!(got.connectivity_barrier_extra,0);
    }

    #[test]
    fn unsat_25_variable_components_merge_after_one_extra_violation() {
        let mut source = Vec::new();
        for j in 0..12 {
            let x=(2*j+1) as i32;
            let y=(2*j+2) as i32;
            source.push(vec![x,-y]);
            source.push(vec![-x,y]);
        }
        source.push(vec![25]);
        source.push(vec![-25]);
        let got = exact_minimum_energy_geometry(&source,25,2).unwrap();
        assert_eq!(got.minimum_violations,1);
        assert_eq!(got.minimizers,1<<13);
        assert_eq!(got.minimum_clusters[0],1<<12);
        assert_eq!(got.largest_minimum_cluster[0],2);
        assert_eq!(got.minimum_clusters[1],1);
        assert_eq!(got.largest_minimum_cluster[1],1<<13);
        assert_eq!(got.connectivity_barrier_extra,1);
    }

    #[test]
    fn empty_clause_is_fixed_energy_offset_and_free_variables_are_exact() {
        let got = exact_minimum_energy_geometry(&[vec![]],3,1).unwrap();
        assert_eq!(got.minimum_violations,1);
        assert_eq!(got.minimizers,8);
        assert_eq!(got.minimum_clusters,vec![1,1]);
        assert_eq!(got.largest_minimum_cluster,vec![8,8]);
        assert_eq!(got.connectivity_barrier_extra,0);
        assert!(exact_minimum_energy_geometry(&[vec![0]],1,1).is_err());
        assert!(exact_minimum_energy_geometry(&[vec![1,2,3]],3,2).is_err());
    }
}
