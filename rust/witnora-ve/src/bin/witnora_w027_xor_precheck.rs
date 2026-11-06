//! W027: sound exact 3-XOR quartet recognition and GF(2) UNSAT certificate.
//! A NO_CERTIFICATE response never asserts SAT.
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};
use std::io::{BufRead, BufReader};
use std::time::Instant;

#[derive(Clone, Debug)]
struct XorRow {
    triple: [usize; 3],
    rhs: bool,
    clauses: [usize; 4],
}

#[derive(Default)]
struct Parsed {
    vars: usize,
    nclauses: usize,
    groups: BTreeMap<[usize; 3], Vec<([i8; 3], usize)>>,
}

fn index_clause(parsed: &mut Parsed, clause: &[i32]) -> Result<(), String> {
    if clause.len() != 3 {
        return Ok(());
    }
    let mut terms = clause
        .iter()
        .map(|&lit| (lit.unsigned_abs() as usize, if lit > 0 { 1i8 } else { -1i8 }))
        .collect::<Vec<_>>();
    terms.sort_unstable_by_key(|x| x.0);
    if terms[0].0 == terms[1].0 || terms[1].0 == terms[2].0 {
        return Ok(());
    }
    let key = [terms[0].0, terms[1].0, terms[2].0];
    parsed.groups.entry(key).or_default().push((
        [terms[0].1, terms[1].1, terms[2].1],
        parsed.nclauses,
    ));
    Ok(())
}

fn parse<R: BufRead>(input: R) -> Result<Parsed, String> {
    let mut out = Parsed::default();
    let mut header = None;
    let mut current = Vec::new();
    for (line_no, line) in input.lines().enumerate() {
        let line = line.map_err(|e| format!("DIMACS read error: {e}"))?;
        let stripped = line.trim();
        if stripped.is_empty() || stripped.starts_with('c') {
            continue;
        }
        if stripped.starts_with('p') {
            let parts = stripped.split_whitespace().collect::<Vec<_>>();
            if header.is_some() || parts.len() != 4 || parts[0] != "p" || parts[1] != "cnf" {
                return Err(format!("invalid/repeated DIMACS header at line {}", line_no + 1));
            }
            let n = parts[2].parse::<usize>().map_err(|_| "invalid var count")?;
            let m = parts[3].parse::<usize>().map_err(|_| "invalid clause count")?;
            if n > 1_000_000 || m > 4_000_000 {
                return Err("DIMACS exceeds safety bounds".to_owned());
            }
            out.vars = n;
            header = Some(m);
            continue;
        }
        if header.is_none() {
            return Err(format!("clause before header at line {}", line_no + 1));
        }
        for word in stripped.split_whitespace() {
            let literal = word.parse::<i32>().map_err(|_| format!("non-integer token at line {}", line_no + 1))?;
            if literal == 0 {
                index_clause(&mut out, &current)?;
                out.nclauses += 1;
                current.clear();
                if out.nclauses > header.unwrap() {
                    return Err("too many clauses".to_owned());
                }
            } else {
                if literal == i32::MIN || literal.unsigned_abs() as usize > out.vars {
                    return Err("literal out of variable range".to_owned());
                }
                current.push(literal);
                if current.len() > 1_000_000 {
                    return Err("oversize clause".to_owned());
                }
            }
        }
    }
    if !current.is_empty() || header != Some(out.nclauses) {
        return Err("DIMACS clause termination/count mismatch".to_owned());
    }
    Ok(out)
}

fn reconstruct(parsed: &Parsed) -> Vec<XorRow> {
    let mut rows = Vec::new();
    for (&triple, clauses) in &parsed.groups {
        // Signed clauses are corners of a Boolean 3-cube. Each of its two
        // complementary parity tetrahedra consists of exactly four corners.
        // A complete tetrahedron entails an XOR equation even if duplicate
        // clauses or corners of the opposite parity are also present.
        // Preserve source-clause provenance for the independent proof audit.
        let mut provenance = [None; 8];
        for &(signs, source) in clauses {
            let corner = usize::from(signs[0] < 0)
                | (usize::from(signs[1] < 0) << 1)
                | (usize::from(signs[2] < 0) << 2);
            provenance[corner].get_or_insert(source);
        }
        for rhs in [false, true] {
            let corners = (0usize..8)
                .filter(|&corner| (corner.count_ones() % 2 == 0) == rhs)
                .collect::<Vec<_>>();
            let found = corners
                .into_iter()
                .map(|corner| provenance[corner])
                .collect::<Option<Vec<_>>>();
            if let Some(sources) = found {
                rows.push(XorRow {
                    triple,
                    rhs,
                    clauses: [sources[0], sources[1], sources[2], sources[3]],
                });
            }
        }
    }
    rows
}

fn xor_in_place(target: &mut [u64], other: &[u64]) {
    for (a, b) in target.iter_mut().zip(other) {
        *a ^= b;
    }
}

fn contradiction(rows: &[XorRow], vars: usize) -> Option<Vec<usize>> {
    let width = vars.div_ceil(64);
    let proof_width = rows.len().div_ceil(64);
    let mut basis: Vec<Option<(Vec<u64>, bool, Vec<u64>)>> = vec![None; vars];
    for (source_idx, row) in rows.iter().enumerate() {
        let mut mask = vec![0u64; width];
        for &v in &row.triple {
            mask[(v - 1) / 64] ^= 1u64 << ((v - 1) % 64);
        }
        let mut proof = vec![0u64; proof_width];
        proof[source_idx / 64] ^= 1u64 << (source_idx % 64);
        let mut rhs = row.rhs;
        for pivot in (0..vars).rev() {
            if mask[pivot / 64] & (1u64 << (pivot % 64)) == 0 {
                continue;
            }
            if let Some((other_mask, other_rhs, other_proof)) = &basis[pivot] {
                xor_in_place(&mut mask, other_mask);
                rhs ^= *other_rhs;
                xor_in_place(&mut proof, other_proof);
            } else {
                basis[pivot] = Some((mask.clone(), rhs, proof.clone()));
                break;
            }
        }
        if rhs && mask.iter().all(|&m| m == 0) {
            let selected = (0..rows.len())
                .filter(|&i| proof[i / 64] & (1u64 << (i % 64)) != 0)
                .collect::<Vec<_>>();
            // Independent source-row validation of the contradiction witness.
            let mut parity = false;
            let mut all_vars = BTreeSet::new();
            for &i in &selected {
                parity ^= rows[i].rhs;
                for &v in &rows[i].triple {
                    if !all_vars.insert(v) {
                        all_vars.remove(&v);
                    }
                }
            }
            assert!(all_vars.is_empty() && parity);
            return Some(selected);
        }
    }
    None
}

fn report_from_reader<R: BufRead>(reader: R) -> Result<Value, String> {
    let start = Instant::now();
    let parsed = parse(reader)?;
    let parsed_elapsed = start.elapsed();
    let rows = reconstruct(&parsed);
    let witness = contradiction(&rows, parsed.vars);
    let witness_rows = witness.as_ref().map(|indices| {
        indices.iter().map(|&i| {
            json!({"variables": rows[i].triple, "rhs": rows[i].rhs,
                "source_clause_indices_zero_based": rows[i].clauses})
        }).collect::<Vec<_>>()
    });
    Ok(json!({
        "study": "W-CROSSDOMAIN-027",
        "status": if witness.is_some() {"UNSAT_CERTIFIED"} else {"NO_CERTIFICATE"},
        "variables": parsed.vars,
        "clauses": parsed.nclauses,
        "unsigned_triple_supports": parsed.groups.len(),
        "recovered_xor_equations": rows.len(),
        "parse_wall_ns": parsed_elapsed.as_nanos().to_string(),
        "total_wall_ns": start.elapsed().as_nanos().to_string(),
        "contradiction_certificate_rows": witness_rows,
    }))
}

fn main() {
    let path = match std::env::args().skip(1).collect::<Vec<_>>().as_slice() {
        [path] => path.clone(),
        _ => { eprintln!("usage: witnora_w027_xor_precheck <file.cnf>"); std::process::exit(2); }
    };
    let input = std::fs::File::open(&path).unwrap_or_else(|e| {
        eprintln!("open error: {e}"); std::process::exit(2);
    });
    match report_from_reader(BufReader::new(input)) {
        Ok(value) => println!("{}", serde_json::to_string(&value).unwrap()),
        Err(e) => { eprintln!("precheck error: {e}"); std::process::exit(2); }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn xor3(variables: [i32; 3], rhs: bool) -> Vec<Vec<i32>> {
        let mut result = Vec::new();
        for x in 0u8..8 {
            if (x.count_ones() % 2 != 0) != rhs {
                result.push((0..3).map(|i| if (x >> i) & 1 == 1 { -variables[i] } else { variables[i] }).collect());
            }
        }
        result
    }

    fn to_dimacs(rhs: [bool; 5]) -> String {
        let triples = [[1, 2, 3], [1, 4, 5], [2, 4, 6], [3, 5, 6], [7, 8, 9]];
        let clauses = triples.into_iter().zip(rhs).flat_map(|(t, r)| xor3(t, r)).collect::<Vec<_>>();
        let mut s = "c original source\np cnf 9 20\n".to_owned();
        for clause in clauses {
            s.push_str(&format!("{} {} {} 0\n", clause[0], clause[1], clause[2]));
        }
        s
    }

    #[test]
    fn exact_sat_and_unsat_parity() {
        let sat = to_dimacs([false, false, false, false, true]);
        let unsat = to_dimacs([false, false, false, true, false]);
        let a = report_from_reader(sat.as_bytes()).unwrap();
        let b = report_from_reader(unsat.as_bytes()).unwrap();
        assert_eq!(a["status"], "NO_CERTIFICATE");
        assert_eq!(b["status"], "UNSAT_CERTIFIED");
        assert_eq!(a["recovered_xor_equations"], 5);
        assert_eq!(b["contradiction_certificate_rows"].as_array().unwrap().len(), 4);
    }

    #[test]
    fn incomplete_quartet_not_accepted() {
        let s = "p cnf 3 3\n1 2 3 0\n-1 -2 3 0\n1 -2 -3 0\n";
        let r = report_from_reader(s.as_bytes()).unwrap();
        assert_eq!(r["status"], "NO_CERTIFICATE");
        assert_eq!(r["recovered_xor_equations"], 0);
    }

    #[test]
    fn exhaustive_cube_occupancy_and_duplicate_robustness() {
        // Each unique 3-clause removes exactly one of the eight assignments.
        // On one support, UNSAT occurs iff all eight corners are occupied.
        for occupancy in 0u16..256 {
            let mut clauses = Vec::new();
            for corner in 0u8..8 {
                if occupancy & (1u16 << corner) != 0 {
                    let terms = (0..3)
                        .map(|i| if corner & (1 << i) == 0 { (i + 1) as i32 } else { -((i + 1) as i32) })
                        .collect::<Vec<_>>();
                    clauses.push(terms);
                }
            }
            // Exercise duplicated sources too: they must neither erase valid
            // parity patterns nor manufacture a false contradiction.
            if let Some(first) = clauses.first().cloned() {
                clauses.push(first);
            }
            let mut text = format!("p cnf 3 {}\n", clauses.len());
            for clause in &clauses {
                text.push_str(&format!("{} {} {} 0\n", clause[0], clause[1], clause[2]));
            }
            let got = report_from_reader(text.as_bytes()).unwrap();
            let parity_mask_even = (0u8..8)
                .filter(|corner| corner.count_ones() % 2 == 0)
                .fold(0u16, |mask, corner| mask | (1 << corner));
            let parity_mask_odd = 0xff ^ parity_mask_even;
            let expected_rows = usize::from(occupancy & parity_mask_even == parity_mask_even)
                + usize::from(occupancy & parity_mask_odd == parity_mask_odd);
            assert_eq!(got["recovered_xor_equations"], expected_rows, "occupancy {occupancy:08b}");
            assert_eq!(got["status"], if occupancy == 255 { "UNSAT_CERTIFIED" } else { "NO_CERTIFICATE" });
        }
    }
}
