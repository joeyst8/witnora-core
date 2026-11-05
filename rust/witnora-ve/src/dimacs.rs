//! Standalone source-DIMACS parser and fully native Rust exact counting CLI.
//! No Python and no PyO3 wheel are required for this entrypoint.
use std::io::{self, Read};
use witnora_ve::fused_source::count_fused_source;

#[derive(Debug, PartialEq, Eq)]
struct Dimacs {
    nvars: u32,
    clauses: Vec<Vec<i32>>,
}

fn parse_dimacs(input: &str) -> Result<Dimacs, String> {
    let mut header: Option<(u32, usize)> = None;
    let mut clauses = Vec::new();
    let mut current = Vec::new();
    for line in input.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('c') {
            continue;
        }
        if line.starts_with('p') {
            if header.is_some() || !clauses.is_empty() || !current.is_empty() {
                return Err("duplicate or misplaced DIMACS header".into());
            }
            let parts: Vec<_> = line.split_whitespace().collect();
            if parts.len() != 4 || parts[0] != "p" || parts[1] != "cnf" {
                return Err("expected p cnf N M DIMACS header".into());
            }
            let nvars: u32 = parts[2].parse().map_err(|_| "invalid DIMACS N")?;
            let expected: usize = parts[3].parse().map_err(|_| "invalid DIMACS M")?;
            if nvars > 256 || expected > 100_000 {
                return Err("DIMACS source size cap exceeded".into());
            }
            header = Some((nvars, expected));
            continue;
        }
        let (nvars, expected) = header.ok_or("missing DIMACS header before clause")?;
        for token in line.split_whitespace() {
            let lit: i32 = token.parse().map_err(|_| "noninteger DIMACS literal")?;
            if lit == 0 {
                if clauses.len() >= expected {
                    return Err("too many DIMACS clauses".into());
                }
                clauses.push(std::mem::take(&mut current));
            } else {
                if lit.unsigned_abs() > nvars {
                    return Err("DIMACS literal outside declared universe".into());
                }
                if clauses.len() >= expected {
                    return Err("extra tokens after declared DIMACS clauses".into());
                }
                current.push(lit);
                if current.len() > 256 {
                    return Err("DIMACS source clause length cap exceeded".into());
                }
            }
        }
    }
    let (nvars, expected) = header.ok_or("missing p cnf header")?;
    if !current.is_empty() {
        return Err("unterminated DIMACS clause".into());
    }
    if clauses.len() != expected {
        return Err("DIMACS clause count mismatch".into());
    }
    Ok(Dimacs { nvars, clauses })
}

fn run_dimacs() -> Result<(), String> {
    let mut preprocess = String::from("rust_adaptive");
    let mut passes: usize = 64;
    let mut clause_visits: usize = 1_000_000;
    let mut spectrum: usize = 4096;
    let mut subsets: usize = 4096;
    let mut operations: u64 = 2_000_000;
    let mut args = std::env::args().skip(2);
    while let Some(option) = args.next() {
        let val = args.next().ok_or("missing value for native CLI option")?;
        match option.as_str() {
            "--preprocess" => preprocess = val,
            "--max-preprocess-passes" => passes = val.parse()
                .map_err(|_| "invalid max-preprocess-passes")?,
            "--max-preprocess-clause-visits" => clause_visits = val.parse()
                .map_err(|_| "invalid max-preprocess-clause-visits")?,
            "--max-spectrum-terms" => spectrum = val.parse()
                .map_err(|_| "invalid max-spectrum-terms")?,
            "--max-inclusion-subsets" => subsets = val.parse()
                .map_err(|_| "invalid max-inclusion-subsets")?,
            "--max-coefficient-operations" => operations = val.parse()
                .map_err(|_| "invalid max-coefficient-operations")?,
            _ => return Err(format!("unrecognized native CLI option: {option}")),
        }
    }
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).map_err(|e| e.to_string())?;
    let source = parse_dimacs(&input)?;
    match count_fused_source(
        &source.clauses, source.nvars, &preprocess, passes,
        clause_visits, spectrum, subsets, operations,
    )? {
        Some(out) => {
            println!("s mc {}", out.models);
            eprintln!(
                "c R-009 Rust-native models={} affine_rows={} boundary={} left_terms={} subsets={}",
                out.models, out.extracted_affine_rows, out.boundary_variables,
                out.left_fourier_terms, out.right_subset_operations
            );
        }
        None => println!("s INCOMPLETE"),
    }
    Ok(())
}

pub fn run() -> Result<(), String> {
    run_dimacs()
}

/// Native 2-SAT CLI using the same strict DIMACS reader.
/// Witnesses are fully checked by the Rust SCC solver. No proof log is claimed.
pub fn run_two_sat() -> Result<(), String> {
    let mut args = std::env::args().skip(2);
    if let Some(option) = args.next() {
        return Err(format!("unrecognized two-SAT CLI argument: {option}"));
    }
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).map_err(|e| e.to_string())?;
    let source = parse_dimacs(&input)?;
    match witnora_ve::two_sat::solve_2sat(&source.clauses, source.nvars)? {
        None => println!("s UNSATISFIABLE"),
        Some(assignment) => {
            println!("s SATISFIABLE");
            let witness = assignment.iter().enumerate()
                .map(|(i, value)| {
                    let var = (i + 1) as i32;
                    if *value { var } else { -var }
                })
                .map(|lit| lit.to_string())
                .collect::<Vec<_>>().join(" ");
            if !witness.is_empty() {
                println!("v {witness} 0");
            } else {
                println!("v 0");
            }
        }
    }
    Ok(())
}

/// Python-free RUP-only DRAT-style proof check. Returns true only
/// after the original-CNF database derives the empty clause by RUP.
/// This does not implement general RAT and is not a Lean kernel.
pub fn run_rup_check_files() -> Result<bool, String> {
    let args: Vec<_> = std::env::args().skip(2).collect();
    if args.len() < 2 || args.len() > 3 {
        return Err("usage: --check-rup SOURCE.cnf PROOF.drat [--strict-deletions]".into());
    }
    let strict = if args.len() == 3 {
        if args[2] != "--strict-deletions" {
            return Err("unknown native RUP CLI option".into());
        }
        true
    } else { false };
    let original = std::fs::read_to_string(&args[0])
        .map_err(|e| format!("cannot read source CNF: {e}"))?;
    let proof = std::fs::read_to_string(&args[1])
        .map_err(|e| format!("cannot read RUP proof: {e}"))?;
    let normalized = witnora_ve::dimacs_evidence::parse_text_evidence(&original)?;
    let result = witnora_ve::rup_checker::check_rup_text(
        &normalized.canonical.clauses, &proof, strict,
    )?;
    if result.verified {
        println!("s VERIFIED_RUP_SUBSET");
        Ok(true)
    } else {
        println!("s INVALID_RUP_SUBSET");
        if let Some(error) = result.error {
            eprintln!("c RUP-only checker rejected proof: {error}");
        }
        Ok(false)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_spanning_lines_and_empty_clauses() {
        let src = parse_dimacs(
            "c header\np cnf 4 3\n 1 -2\nc inline comment\n3 0\n0\n-4 0\n",
        ).unwrap();
        assert_eq!(src.nvars, 4);
        assert_eq!(src.clauses, vec![vec![1, -2, 3], vec![], vec![-4]]);
    }

    #[test]
    fn parse_rejects_ill_formed_and_undeclared_literals() {
        for bad in [
            "", "1 0", "p cnf 2 1\n3 0", "p cnf 2 2\n1 0",
            "p cnf 2 1\n1", "p cnf 2 0\n1 0",
            "p cnf 2 1\n1 0\np cnf 2 0",
            "p cnf 2 1\n-2147483648 0",
        ] {
            assert!(parse_dimacs(bad).is_err(), "{bad:?}");
        }
    }

    #[test]
    fn native_dimacs_matches_exact_source_count() {
        for (raw, expected) in [
            ("p cnf 3 0\n", 8u32),
            ("p cnf 2 2\n1 0\n-2 0\n", 1u32),
            ("p cnf 3 1\n0\n", 0u32),
        ] {
            let source = parse_dimacs(raw).unwrap();
            let out = count_fused_source(
                &source.clauses, source.nvars, "rust_adaptive",
                64, 1000000, 4096, 4096, 2000000,
            ).unwrap().unwrap();
            assert_eq!(out.models, expected.into());
        }
    }
}
