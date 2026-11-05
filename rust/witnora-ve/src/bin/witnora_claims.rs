//! Standalone native counterpart of claim_boundary.scan_files_for_claim_boundary.
//! A conservative statement scanner, not proof of any mathematical theorem.

use serde_json::{json, Map, Value};
use std::{env, fs, process};
use witnora_ve::claim_boundary;

fn scan_paths(paths: &[String]) -> Result<Value, String> {
    if paths.is_empty() {
        return Err("at least one UTF-8 text file is required".into());
    }
    let mut file_results = Map::new();
    let mut all_flagged = Vec::new();
    for path in paths {
        let source = fs::read_to_string(path)
            .map_err(|error| format!("cannot read {path}: {error}"))?;
        let findings: Vec<Value> = claim_boundary::scan(&source).into_iter().map(|finding| {
            let severity = if finding.allowed {
                "allowed_negative_context"
            } else {
                "forbidden_affirmative"
            };
            json!({
                "phrase": finding.phrase,
                "context": finding.context,
                "severity": severity,
                "allowed_by_negative_context": finding.allowed,
            })
        }).collect();
        let mut flagged = Vec::new();
        for finding in &findings {
            if finding["allowed_by_negative_context"] == Value::Bool(false) {
                let mut with_path = finding.as_object()
                    .ok_or("invalid native finding object")?.clone();
                with_path.insert("path".into(), Value::String(path.clone()));
                let with_path = Value::Object(with_path);
                flagged.push(finding.clone());
                all_flagged.push(with_path);
            }
        }
        file_results.insert(path.clone(), json!({
            "passed": flagged.is_empty(),
            "findings": findings,
            "flagged_phrases": flagged,
        }));
    }
    Ok(json!({
        "passed": all_flagged.is_empty(),
        "files": file_results,
        "flagged_phrases": all_flagged,
    }))
}

fn run(args: &[String]) -> Result<(), String> {
    if args.len() == 1 && (args[0] == "--help" || args[0] == "-h") {
        println!("usage: witnora_claims FILE [FILE ...] [--out RESULTS_JSON]");
        return Ok(());
    }
    let (files, output) = if let Some(index) = args.iter().position(|a| a == "--out") {
        if index + 2 != args.len() {
            return Err("--out must be followed by the output JSON path".into());
        }
        (&args[..index], Some(&args[index + 1]))
    } else {
        (args, None)
    };
    let data = scan_paths(files)?;
    let serialized = serde_json::to_string_pretty(&data)
        .map_err(|error| error.to_string())? + "\n";
    if let Some(path) = output {
        fs::write(path, serialized)
            .map_err(|error| format!("cannot write {path}: {error}"))?;
    } else {
        print!("{serialized}");
    }
    Ok(())
}

fn main() {
    let args: Vec<_> = env::args().skip(1).collect();
    if let Err(error) = run(&args) {
        eprintln!("{error}");
        process::exit(2);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn no_file_is_rejected() {
        assert!(scan_paths(&[]).is_err());
    }

    #[test]
    fn nonexistent_input_is_rejected() {
        assert!(scan_paths(&["does-not-exist--native-claim-test.txt".into()]).is_err());
    }
}
