//! WU-003: exact CNF-conservativity falsification of a semantic-necessity graph.
//! Inspired by Beame--Sun (SAT 2026) 1-UIP open question. Not a solver.

use std::collections::HashMap;

fn rank(mut rows: Vec<u64>, n: usize) -> usize {
    let mut next = 0;
    for bit in 0..n {
        if let Some(i) = (next..rows.len()).find(|&i| rows[i] & (1 << bit) != 0) {
            rows.swap(i, next);
            for j in (next + 1)..rows.len() {
                if rows[j] & (1 << bit) != 0 {
                    rows[j] ^= rows[next];
                }
            }
            next += 1;
        }
    }
    next
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Status {
    Satisfied,
    Conflict,
    Unit(u64),
    Inactive,
}

fn clause_status(prefix: &[u64], falsity: &[u64], n: usize) -> Status {
    let combined: Vec<_> = prefix.iter().chain(falsity).copied().collect();
    let coeff_rank = rank(combined.clone(), n);
    if rank(combined.clone(), n + 1) != coeff_rank {
        return Status::Satisfied;
    }
    match coeff_rank - rank(prefix.to_vec(), n) {
        0 => Status::Conflict,
        1 => {
            let target = falsity
                .iter()
                .copied()
                .find(|&row| rank([prefix, &[row]].concat(), n + 1) > rank(prefix.to_vec(), n + 1))
                .expect("rank-one reason must have new falsity equation");
            Status::Unit(target ^ (1 << n))
        }
        _ => Status::Inactive,
    }
}

// Complete fixed-point XNF unit closure. Only reasons selected earlier in
// the trace are included. The output affine span does not depend on which
// rank-one representative was chosen by a clause.
fn closure(n: usize, decision: bool, reasons: &[Vec<u64>], omitted: Option<usize>) -> Option<Vec<u64>> {
    let mut known = if decision { vec![1u64 | (1 << n)] } else { Vec::new() };
    loop {
        let mut changed = false;
        for (i, reason) in reasons.iter().enumerate() {
            if omitted == Some(i) {
                continue;
            }
            match clause_status(&known, reason, n) {
                Status::Conflict => return None,
                Status::Unit(row) => {
                    assert_eq!(rank([&known[..], &[row]].concat(), n + 1), known.len() + 1);
                    known.push(row);
                    changed = true;
                }
                _ => {}
            }
        }
        if !changed {
            return Some(known);
        }
    }
}

#[derive(Clone, Debug)]
struct Trace {
    // Node 0 is the a=1 decision. Node j>=1 is a propagated positive
    // Boolean variable x_j, with a chosen antecedent set (ordinary CNF).
    antecedents: Vec<Vec<usize>>,
    conflict_parents: Vec<usize>,
}

impl Trace {
    fn n(&self) -> usize {
        self.antecedents.len() + 1
    }

    fn reasons(&self) -> Vec<Vec<u64>> {
        let rhs = 1 << self.n();
        self.antecedents
            .iter()
            .enumerate()
            .map(|(i, parents)| {
                let mut falsity: Vec<u64> = parents.iter().map(|&p| (1 << p) | rhs).collect();
                falsity.push(1 << (i + 1)); // positive head is false
                falsity
            })
            .collect()
    }

    fn conflict(&self) -> Vec<u64> {
        self.conflict_parents
            .iter()
            .map(|&p| (1 << p) | (1 << self.n()))
            .collect()
    }

    fn original_graph(&self) -> Vec<(usize, usize)> {
        let mut edges = Vec::new();
        for (i, parents) in self.antecedents.iter().enumerate() {
            edges.extend(parents.iter().map(|&p| (p, i + 1)));
        }
        edges.extend(self.conflict_parents.iter().map(|&p| (p, self.n())));
        edges.sort_unstable();
        edges
    }

    /// Edge j->i iff deleting earlier event j makes event i cease to fire.
    /// This asks a *semantic* question via repeated exact propagation,
    /// independent of trail-equation coordinates. Hypothesis H3 says these
    /// edges suffice to reconstruct graph-theoretic classical first UIP.
    fn necessity_graph(&self) -> Vec<(usize, usize)> {
        let n = self.n();
        let reasons = self.reasons();
        let conflict = self.conflict();
        let mut edges = Vec::new();
        for target in 1..=n {
            let prior = &reasons[..(target - 1).min(reasons.len())];
            let target_clause = if target == n { &conflict } else { &reasons[target - 1] };
            let fires = |omit_event: Option<usize>| {
                let decision = omit_event != Some(0);
                let omitted_reason = omit_event.and_then(|j| if j == 0 { None } else { Some(j - 1) });
                let Some(prefix) = closure(n, decision, prior, omitted_reason) else {
                    return false;
                };
                match clause_status(&prefix, target_clause, n) {
                    Status::Conflict if target == n => true,
                    Status::Unit(_) if target < n => true,
                    _ => false,
                }
            };
            assert!(fires(None), "proposed trace must propagate and conflict");
            for candidate in 0..target {
                if !fires(Some(candidate)) {
                    edges.push((candidate, target));
                }
            }
        }
        edges
    }
}

fn first_uip(edges: &[(usize, usize)], conflict: usize) -> usize {
    let can_reach_without = |skip: usize| {
        if skip == 0 {
            return false;
        }
        let mut stack = vec![0];
        let mut seen = vec![false; conflict + 1];
        while let Some(node) = stack.pop() {
            if node == conflict {
                return true;
            }
            if node == skip || seen[node] {
                continue;
            }
            seen[node] = true;
            stack.extend(edges.iter().filter(|&&(p, q)| p == node && q != skip).map(|&(_, q)| q));
        }
        false
    };
    (0..conflict)
        .filter(|&node| !can_reach_without(node))
        .max()
        .expect("reachable conflict must be dominated by its decision")
}

fn chain_and_conjunction() -> (Trace, Trace) {
    // Both have selected trail a=1, b=1, c=1 and conflict !b OR !c.
    // Chain: R_c = !b OR c; conjunction: R_c = !a OR !b OR c.
    let chain = Trace { antecedents: vec![vec![0], vec![1]], conflict_parents: vec![1, 2] };
    let conjunction = Trace { antecedents: vec![vec![0], vec![0, 1]], conflict_parents: vec![1, 2] };
    (chain, conjunction)
}

fn enumerate_four_variable_traces() -> Vec<Trace> {
    // All valid 4-variable DAGs of this restricted CNF form; independent
    // reason sets for each newly propagated variable, all nonempty.
    // Conflict involves newest variable and at least one earlier variable.
    let mut traces = Vec::new();
    for parents_c in 1u64..4 {
        for parents_d in 1u64..8 {
            for conflict_earlier in 1u64..8 {
                let tr = Trace {
                    antecedents: vec![
                        vec![0],
                        (0..2).filter(|&p| (parents_c >> p) & 1 == 1).collect(),
                        (0..3).filter(|&p| (parents_d >> p) & 1 == 1).collect(),
                    ],
                    conflict_parents: (0..3)
                        .filter(|&p| (conflict_earlier >> p) & 1 == 1)
                        .chain(std::iter::once(3))
                        .collect(),
                };
                traces.push(tr);
            }
        }
    }
    traces
}

fn finite_collision_counts() -> (usize, usize, usize) {
    let traces = enumerate_four_variable_traces();
    let mut signatures: HashMap<Vec<(usize, usize)>, [usize; 4]> = HashMap::new();
    for tr in &traces {
        let signature = tr.necessity_graph();
        let uip = first_uip(&tr.original_graph(), 4);
        signatures.entry(signature).or_insert([0; 4])[uip] += 1;
    }
    let ambiguous_signatures = signatures
        .values()
        .filter(|counts| counts.iter().filter(|&&v| v > 0).count() > 1)
        .count();
    let disagreeing_trace_pairs = signatures.values().map(|counts| {
        (0..4).flat_map(|i| ((i + 1)..4).map(move |j| counts[i] * counts[j])).sum::<usize>()
    }).sum();
    (traces.len(), ambiguous_signatures, disagreeing_trace_pairs)
}

fn main() {
    let (chain, conjunction) = chain_and_conjunction();
    let same = chain.necessity_graph();
    assert_eq!(same, conjunction.necessity_graph());
    assert_eq!(first_uip(&chain.original_graph(), 3), 1); // b
    assert_eq!(first_uip(&conjunction.original_graph(), 3), 0); // a
    let (cases, ambiguous, pairs) = finite_collision_counts();
    println!("WU-003 H3 FALSIFIED on ordinary CNF, before parity generalization.");
    println!("Two different reason DAGs induce identical semantic leave-one-out necessity: {same:?}");
    println!("Their actual classical first UIPs are b (chain) and a (conjunction).");
    println!("Exact 4-variable scan: {cases} traces, {ambiguous} ambiguous signatures, {pairs} disagreeing trace pairs.");
    assert!(ambiguous > 0 && pairs > 0);
    println!("Conclusion: necessity of an ancestor does not reveal whether it was an IMMEDIATE antecedent.");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn necessity_collision_with_different_first_uips() {
        let (chain, conjunction) = chain_and_conjunction();
        assert_eq!(chain.necessity_graph(), conjunction.necessity_graph());
        assert_eq!(chain.necessity_graph(), vec![(0, 1), (0, 2), (1, 2), (0, 3), (1, 3), (2, 3)]);
        assert_eq!(first_uip(&chain.original_graph(), 3), 1);
        assert_eq!(first_uip(&conjunction.original_graph(), 3), 0);
    }

    #[test]
    fn exhaustive_four_variable_cnf_gate() {
        let (cases, ambiguous, pairs) = finite_collision_counts();
        assert_eq!(cases, 147);
        assert!(ambiguous > 0 && pairs > 0);
    }

    #[test]
    fn unit_closure_is_semantically_strong_enough_for_nontrivial_cnf() {
        let (chain, _) = chain_and_conjunction();
        let known = closure(3, true, &chain.reasons(), None).unwrap();
        assert_eq!(rank(known.clone(), 4), 3);
        assert_eq!(clause_status(&known, &chain.conflict(), 3), Status::Conflict);
        assert!(closure(3, false, &chain.reasons(), None).unwrap().is_empty());
    }

    #[test]
    fn reason_intersection_preserves_exact_cnf_antecedent_subspaces() {
        // For a chosen CNF implication reason (!p1 or ... or !pk or x_i),
        // neg(R_i) ∩ span(earlier true variables) is exactly span(p1,...,pk).
        // This is basis-intrinsic and distinguishes the two WU-003 traces;
        // it is an elementary restricted positive lemma, NOT parity 1-UIP.
        for trace in enumerate_four_variable_traces() {
            let n = trace.n();
            let rhs = 1 << n;
            let mut prefix = vec![1 | rhs];
            for (i, (falsity, parents)) in trace.reasons().iter().zip(&trace.antecedents).enumerate() {
                let concatenation = [prefix.as_slice(), falsity.as_slice()].concat();
                let intersection_dim = rank(prefix.clone(), n + 1)
                    + rank(falsity.clone(), n + 1)
                    - rank(concatenation, n + 1);
                assert_eq!(intersection_dim, parents.len());
                for &parent in parents {
                    let parent_row = (1 << parent) | rhs;
                    assert_eq!(
                        rank([prefix.as_slice(), &[parent_row]].concat(), n + 1),
                        rank(prefix.clone(), n + 1)
                    );
                    assert_eq!(
                        rank([falsity.as_slice(), &[parent_row]].concat(), n + 1),
                        rank(falsity.clone(), n + 1)
                    );
                }
                prefix.push((1 << (i + 1)) | rhs);
            }
        }
    }
}
