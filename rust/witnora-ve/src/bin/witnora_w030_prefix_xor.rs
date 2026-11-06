//! W030: source-auditable incremental XOR UNSAT proof from a DIMACS prefix.
//!
//! The first certified contradictory subset of source clauses suffices for UNSAT.
//! Without a certificate, no satisfiability claim is made. The original CNF is
//! never transformed; a benchmark driver must pass it unchanged to its solver.
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};
use std::io::{BufRead, BufReader};
use std::time::Instant;

#[derive(Clone, Debug)]
struct XorRow {
    variables: [usize; 3],
    rhs: bool,
    source: [usize; 4],
}

#[derive(Default)]
struct CornerGroup {
    corners: [Option<usize>; 8],
    emitted: [bool; 2],
}

struct Equation {
    variables: BTreeSet<usize>,
    rhs: bool,
    proof: BTreeSet<usize>,
}

fn xor_toggle<T: Ord + Copy>(left: &mut BTreeSet<T>, right: &BTreeSet<T>) {
    for item in right {
        if !left.insert(*item) {
            left.remove(item);
        }
    }
}

struct StreamingCertificate {
    variables: usize,
    declared_clauses: usize,
    read_clauses: usize,
    groups: BTreeMap<[usize; 3], CornerGroup>,
    rows: Vec<XorRow>,
    basis: Vec<Option<Equation>>,
}

impl StreamingCertificate {
    fn new(variables: usize, declared_clauses: usize) -> Self {
        let basis = (0..variables).map(|_| None).collect();
        Self { variables, declared_clauses, read_clauses: 0, groups: BTreeMap::new(), rows: Vec::new(), basis }
    }

    fn add_equation(&mut self, row: XorRow) -> Option<Vec<XorRow>> {
        let index = self.rows.len();
        let mut eq = Equation {
            variables: row.variables.into_iter().collect(),
            rhs: row.rhs,
            proof: [index].into_iter().collect(),
        };
        self.rows.push(row);

        while let Some(&pivot) = eq.variables.last() {
            if let Some(b) = &self.basis[pivot - 1] {
                xor_toggle(&mut eq.variables, &b.variables);
                xor_toggle(&mut eq.proof, &b.proof);
                eq.rhs ^= b.rhs;
            } else {
                self.basis[pivot - 1] = Some(eq);
                return None;
            }
        }
        if !eq.rhs {
            return None;
        }

        // Audit the GF(2) contradiction independently of the mutable basis.
        let selected: Vec<XorRow> = eq.proof.iter().map(|&i| self.rows[i].clone()).collect();
        let mut parity = false;
        let mut support = BTreeSet::new();
        for member in &selected {
            parity ^= member.rhs;
            for var in member.variables {
                if !support.insert(var) {
                    support.remove(&var);
                }
            }
        }
        assert!(parity && support.is_empty());
        Some(selected)
    }

    fn add_clause(&mut self, clause: &[i32]) -> Option<Vec<XorRow>> {
        let clause_index = self.read_clauses;
        self.read_clauses += 1;
        if clause.len() != 3 {
            return None;
        }
        let mut terms = clause.iter().map(|&x| (x.unsigned_abs() as usize, x < 0)).collect::<Vec<_>>();
        terms.sort_unstable_by_key(|x| x.0);
        if terms[0].0 == terms[1].0 || terms[1].0 == terms[2].0 {
            return None;
        }
        let key = [terms[0].0, terms[1].0, terms[2].0];
        let corner = usize::from(terms[0].1) | (usize::from(terms[1].1) << 1) | (usize::from(terms[2].1) << 2);

        // Keep the borrow of the corner group separate from the basis update.
        let mut emitted = Vec::new();
        {
            let group = self.groups.entry(key).or_default();
            group.corners[corner].get_or_insert(clause_index);
            for rhs_bit in 0..=1usize {
                if group.emitted[rhs_bit] {
                    continue;
                }
                let sources = (0..8usize)
                    .filter(|&c| c.count_ones() as usize % 2 == rhs_bit)
                    .map(|c| group.corners[c])
                    .collect::<Option<Vec<_>>>();
                if let Some(indices) = sources {
                    group.emitted[rhs_bit] = true;
                    emitted.push(XorRow {
                        variables: key,
                        // A clause's signed product is positive exactly for
                        // even-negative corners; this is the source-audited
                        // RHS convention used by the frozen W027 verifier.
                        rhs: rhs_bit == 0,
                        source: [indices[0], indices[1], indices[2], indices[3]],
                    });
                }
            }
        }
        for row in emitted {
            if let Some(proof) = self.add_equation(row) {
                return Some(proof);
            }
        }
        None
    }

    fn report(&self, elapsed_ns: u128, proof: Option<Vec<XorRow>>) -> Value {
        let certified = proof.is_some();
        let rows = proof.map(|p| p.into_iter().map(|r| {
            json!({"variables":r.variables,"rhs":r.rhs,"source_clause_indices_zero_based":r.source})
        }).collect::<Vec<_>>());
        json!({
            "study":"W-CROSSDOMAIN-030",
            "status":if certified {"UNSAT_CERTIFIED"} else {"NO_CERTIFICATE"},
            "variables":self.variables,
            "clauses":self.declared_clauses,
            "read_clauses":self.read_clauses,
            "terminated_early":certified && self.read_clauses < self.declared_clauses,
            "unsigned_triple_supports":self.groups.len(),
            "recovered_xor_equations":self.rows.len(),
            "total_wall_ns":elapsed_ns.to_string(),
            "contradiction_certificate_rows":rows,
        })
    }
}

fn report_from_reader<R: BufRead>(input: R) -> Result<Value, String> {
    let start = Instant::now();
    let mut state: Option<StreamingCertificate> = None;
    let mut current = Vec::new();
    for (line_no, line) in input.lines().enumerate() {
        let line = line.map_err(|e| format!("DIMACS read error: {e}"))?;
        let stripped = line.trim();
        if stripped.is_empty() || stripped.starts_with('c') {
            continue;
        }
        if stripped.starts_with('p') {
            let words = stripped.split_whitespace().collect::<Vec<_>>();
            if state.is_some() || words.len() != 4 || words[0] != "p" || words[1] != "cnf" {
                return Err(format!("invalid or duplicate DIMACS header at line {}", line_no + 1));
            }
            let variables = words[2].parse::<usize>().map_err(|_| "invalid variable count")?;
            let clauses = words[3].parse::<usize>().map_err(|_| "invalid clause count")?;
            if variables > 1_000_000 || clauses > 4_000_000 {
                return Err("DIMACS exceeds safety bounds".to_owned());
            }
            state = Some(StreamingCertificate::new(variables, clauses));
            continue;
        }
        let state = state.as_mut().ok_or_else(|| format!("clause before header at line {}", line_no + 1))?;
        for word in stripped.split_whitespace() {
            let x = word.parse::<i32>().map_err(|_| format!("invalid literal at line {}", line_no + 1))?;
            if x == 0 {
                if state.read_clauses >= state.declared_clauses {
                    return Err("too many clauses".to_owned());
                }
                let proof = state.add_clause(&current);
                current.clear();
                if proof.is_some() {
                    // A verified contradictory *subset* is sufficient for UNSAT;
                    // trailing clauses never need to be inspected for soundness.
                    return Ok(state.report(start.elapsed().as_nanos(), proof));
                }
            } else {
                if x == i32::MIN || x.unsigned_abs() as usize > state.variables {
                    return Err("literal out of range".to_owned());
                }
                current.push(x);
                if current.len() > 1_000_000 {
                    return Err("oversize clause".to_owned());
                }
            }
        }
    }
    let state = state.ok_or("missing DIMACS header")?;
    if !current.is_empty() || state.read_clauses != state.declared_clauses {
        return Err("DIMACS termination/count mismatch".to_owned());
    }
    Ok(state.report(start.elapsed().as_nanos(), None))
}

fn main() {
    let path = match std::env::args().skip(1).collect::<Vec<_>>().as_slice() {
        [path] => path.clone(),
        _ => { eprintln!("usage: witnora_w030_prefix_xor <file.cnf>"); std::process::exit(2); }
    };
    let f = std::fs::File::open(path).unwrap_or_else(|e| { eprintln!("open error: {e}"); std::process::exit(2) });
    match report_from_reader(BufReader::new(f)) {
        Ok(value) => println!("{}", serde_json::to_string(&value).unwrap()),
        Err(error) => { eprintln!("W030 parser error: {error}"); std::process::exit(2) }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn quartet(triple: [i32; 3], rhs: bool) -> Vec<Vec<i32>> {
        (0u8..8).filter(|&corner| (corner.count_ones() % 2 != 0) != rhs)
            .map(|corner| (0..3).map(|i| if corner & (1 << i) != 0 { -triple[i] } else { triple[i] }).collect())
            .collect()
    }

    fn make_core(unsat: bool, padding: usize, push_core_to_end: bool) -> String {
        let triples = [[1, 2, 3], [1, 4, 5], [2, 4, 6], [3, 5, 6], [7, 8, 9]];
        let parity = if unsat { [false, false, false, true, false] } else { [false, false, false, false, true] };
        let core = triples.into_iter().zip(parity).flat_map(|(triple, rhs)| quartet(triple, rhs))
            .collect::<Vec<_>>();
        let filler = (0..padding).map(|_| vec![10, 11, 12]).collect::<Vec<_>>();
        let clauses = if push_core_to_end { filler.into_iter().chain(core).collect::<Vec<_>>() }
            else { core.into_iter().chain(filler).collect::<Vec<_>>() };
        let mut out = format!("p cnf 12 {}\n", clauses.len());
        for clause in clauses {
            out.push_str(&format!("{} {} {} 0\n", clause[0], clause[1], clause[2]));
        }
        out
    }

    #[test]
    fn unsat_certificate_is_early_when_conflicting_core_is_first() {
        let result = report_from_reader(make_core(true, 500, false).as_bytes()).unwrap();
        assert_eq!(result["status"], "UNSAT_CERTIFIED");
        assert!(result["read_clauses"].as_u64().unwrap() <= 20);
        assert_eq!(result["terminated_early"], true);
        assert!(result["contradiction_certificate_rows"].as_array().unwrap().len() >= 2);
    }

    #[test]
    fn sat_control_never_certified_and_reads_full_file() {
        let result = report_from_reader(make_core(false, 500, false).as_bytes()).unwrap();
        assert_eq!(result["status"], "NO_CERTIFICATE");
        assert_eq!(result["read_clauses"], 520);
        assert_eq!(result["terminated_early"], false);
    }

    #[test]
    fn late_core_cannot_bypass_required_reading() {
        let result = report_from_reader(make_core(true, 500, true).as_bytes()).unwrap();
        assert_eq!(result["status"], "UNSAT_CERTIFIED");
        assert!(result["read_clauses"].as_u64().unwrap() > 500);
    }

    #[test]
    fn malformed_uncertified_dimacs_is_rejected() {
        let result = report_from_reader("p cnf 3 4\n1 2 3 0\n".as_bytes());
        assert!(result.is_err());
    }

    #[test]
    fn all_256_cube_corner_subsets_are_sound() {
        for mask in 0u16..256 {
            let mut clauses = Vec::new();
            for c in 0..8usize {
                if mask & (1 << c) != 0 {
                    clauses.push((0..3).map(|i| if c & (1 << i) != 0 { -((i + 1) as i32) } else { (i + 1) as i32 })
                        .collect::<Vec<_>>());
                }
            }
            if let Some(a) = clauses.first().cloned() { clauses.push(a); }
            let mut source = format!("p cnf 3 {}\n", clauses.len());
            for clause in clauses { source.push_str(&format!("{} {} {} 0\n", clause[0], clause[1], clause[2])); }
            let output = report_from_reader(source.as_bytes()).unwrap();
            assert_eq!(output["status"], if mask == 255 { "UNSAT_CERTIFIED" } else { "NO_CERTIFICATE" }, "mask={mask}");
        }
    }
}
