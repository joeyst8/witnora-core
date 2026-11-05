//! Native artifact-integrity helpers only (SHA-256, hash-table lookup, file status).
//! Matching artifact hashes alone cannot certify SAT, UNSAT, or a proof.

use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs::File;
use std::io::{BufReader, Read};
use std::path::Path;

pub fn sha256_file(path: &Path) -> Result<String, String> {
    let reader = File::open(path).map_err(|e| format!("cannot open {}: {e}", path.display()))?;
    let mut reader = BufReader::new(reader);
    let mut sha = Sha256::new();
    let mut buffer = [0u8; 65_536];
    loop {
        let len = reader.read(&mut buffer)
            .map_err(|e| format!("cannot read {}: {e}", path.display()))?;
        if len == 0 { break; }
        sha.update(&buffer[..len]);
    }
    Ok(sha.finalize().iter().map(|b| format!("{b:02X}")).collect::<String>())
}

pub fn parse_manifest_hash_table(text: &str) -> BTreeMap<String, String> {
    let mut hashes = BTreeMap::new();
    for line in text.lines() {
        let Some(rest) = line.strip_prefix('|') else { continue; };
        let rest = rest.trim_start();
        let Some(rest) = rest.strip_prefix('`') else { continue; };
        let Some(end_name) = rest.find('`') else { continue; };
        if end_name == 0 { continue; }
        let name = &rest[..end_name];
        let Some(rest) = rest[end_name + 1..].trim_start().strip_prefix('|') else { continue; };
        let rest = rest.trim_start();
        let rest = rest.strip_prefix('`').unwrap_or(rest);
        if rest.len() < 64 { continue; }
        let (digits, tail) = rest.split_at(64);
        if !digits.bytes().all(|b| b.is_ascii_hexdigit()) { continue; }
        let tail = tail.strip_prefix('`').unwrap_or(tail);
        if !tail.trim_start().starts_with('|') { continue; }
        hashes.insert(name.to_string(), digits.to_ascii_uppercase());
    }
    hashes
}

pub fn manifest_lookup(path: &Path, hashes: &BTreeMap<String, String>) -> Option<String> {
    let raw = path.to_string_lossy().to_string();
    let candidates = [raw.clone(),
        path.file_name().map(|name| name.to_string_lossy().to_string()).unwrap_or_default(),
        raw.replace('\\', "/")];
    candidates.iter().find_map(|candidate| hashes.get(candidate).cloned())
}

pub fn evidence_status(path: &Path, kind: &str, expected: Option<&str>) -> Result<Value, String> {
    let exists = path.is_file();
    let actual = if exists { Some(sha256_file(path)?) } else { None };
    let expected = expected.map(str::to_owned).or_else(|| actual.clone());
    let status = if !exists { "MISSING" }
        else if expected.as_ref() == actual.as_ref() { "MATCH" }
        else { "MISMATCH" };
    Ok(json!({
        "path": path.to_string_lossy(),
        "kind": kind,
        "sha256_expected": expected,
        "sha256_actual": actual,
        "status": status,
    }))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn manifest_parser_accepts_exact_hashes_only() {
        let digits = "ab".repeat(32);
        let source = format!("| `proof.drat` | `{digits}` | state |\n| `bad` | 12 |\n");
        let hashes = parse_manifest_hash_table(&source);
        assert_eq!(hashes.get("proof.drat"), Some(&digits.to_uppercase()));
        assert_eq!(hashes.get("bad"), None);
    }

    #[test]
    fn missing_file_never_matches() {
        let result = evidence_status(Path::new("this-file-does-not-exist-verify-integrity"),
            "drat", None).unwrap();
        assert_eq!(result["status"], "MISSING");
    }
}
