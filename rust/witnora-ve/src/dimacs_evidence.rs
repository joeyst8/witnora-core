//! R-012: source-preserving strict DIMACS text evidence in Rust.
//!
//! Retain the exact spellings of all numeric tokens before canonical CNF
//! simplification so later certificate audits can review the original input.
//! The parser checks signed i32 literals and bounded header counts; it
//! does not silently fall back to a different source string.

use crate::cnf::CanonicalCnf;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DimacsTextEvidence {
    pub canonical: CanonicalCnf,
    pub raw_clauses: Vec<Vec<i32>>,
    pub literal_stream: Vec<i32>,
    pub literal_spellings: Vec<String>,
}

pub fn parse_text_evidence(text: &str) -> Result<DimacsTextEvidence, String> {
    if text.trim().is_empty() {
        return Err("empty DIMACS document".into());
    }
    let mut header: Option<(u32, usize)> = None;
    let mut clauses = Vec::new();
    let mut current = Vec::new();
    let mut stream = Vec::new();
    let mut spellings = Vec::new();

    for (line_index, line) in text.lines().enumerate() {
        let line_no = line_index + 1;
        let line = line.trim();
        if line.is_empty() || line.starts_with('c') {
            continue;
        }
        let tokens: Vec<&str> = line.split_whitespace().collect();
        if tokens[0] == "p" {
            if header.is_some() {
                return Err(format!("duplicate DIMACS header at line {line_no}"));
            }
            if tokens.len() != 4 || tokens[1] != "cnf" {
                return Err(format!("invalid DIMACS header at line {line_no}"));
            }
            let n: i64 = tokens[2].parse().map_err(|_| "non-integer DIMACS header N")?;
            let m: i64 = tokens[3].parse().map_err(|_| "non-integer DIMACS header M")?;
            if n < 0 || m < 0 || n > i32::MAX as i64 || m > 100_000 {
                return Err("invalid or excessive DIMACS header counts".into());
            }
            header = Some((n as u32, m as usize));
            continue;
        }
        let (nvars, _) = header.ok_or(
            format!("missing DIMACS header before line {line_no}"))?;
        for token in tokens {
            let lit: i64 = token.parse().map_err(|_| {
                format!("non-integer DIMACS literal {token:?} at line {line_no}")
            })?;
            if lit < i32::MIN as i64 || lit > i32::MAX as i64 {
                return Err("DIMACS literal outside signed i32 range".into());
            }
            let lit = lit as i32;
            stream.push(lit);
            spellings.push(token.to_string());
            if lit == 0 {
                clauses.push(std::mem::take(&mut current));
                if clauses.len() > 100_000 {
                    return Err("DIMACS input clause cap exceeded".into());
                }
                continue;
            }
            if lit == i32::MIN || lit.unsigned_abs() > nvars {
                return Err("DIMACS literal outside declared universe".into());
            }
            current.push(lit);
            if current.len() > 1_000_000 {
                return Err("DIMACS clause length cap exceeded".into());
            }
        }
    }

    let (_, declared_clauses) = header.ok_or("invalid or missing DIMACS header")?;
    if !current.is_empty() {
        return Err("DIMACS last clause missing terminating zero".into());
    }
    if declared_clauses != clauses.len() {
        return Err("DIMACS header clause count mismatch".into());
    }
    let canonical = CanonicalCnf::from_signed(&clauses)?;
    Ok(DimacsTextEvidence {
        canonical, raw_clauses: clauses,
        literal_stream: stream, literal_spellings: spellings,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn retain_original_numeric_spellings_while_normalizing() {
        let raw = "c source document\np cnf +04 3\n+01 -002 0 0\nc comment\n-0\n";
        let got = parse_text_evidence(raw).unwrap();
        assert_eq!(got.raw_clauses, vec![vec![1, -2], vec![], vec![]]);
        assert_eq!(got.literal_stream, vec![1, -2, 0, 0, 0]);
        assert_eq!(got.literal_spellings,
                   vec!["+01", "-002", "0", "0", "-0"]);
        assert_eq!(got.canonical.canonical_dimacs(),
                   "p cnf 2 2\n0\n-2 1 0\n");
    }

    #[test]
    fn rejected_headers_out_of_bounds_and_unterminated_clauses() {
        for src in [
            "", "c just comment", "1 0", "p cnf 2 2\n1 0",
            "p cnf 2 1\n3 0", "p cnf 2 1\n1",
            "p cnf -1 0", "p cnf 2 0\np cnf 2 0",
            "p cnf 2 1\n-2147483648 0",
        ] {
            assert!(parse_text_evidence(src).is_err(), "{src:?}");
        }
    }
}
