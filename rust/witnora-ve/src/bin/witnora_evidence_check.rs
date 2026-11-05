//! Python-free SHA-256 artifact integrity helper; not an UNSAT proof verifier.
//! Usage: witnora_evidence_check check FILE KIND [--expected SHA] [--manifest HASH_TABLE] [--out JSON]
//!        witnora_evidence_check manifest HASH_TABLE [--out JSON]

#[path = "../verification_integrity.rs"]
mod verification_integrity;

use std::{env, fs, path::Path, process};

fn run(args: &[String]) -> Result<(), String> {
    if args.len() == 1 && (args[0] == "--help" || args[0] == "-h") {
        println!("usage: witnora_evidence_check check FILE KIND [--expected SHA] [--manifest HASH_TABLE] [--out JSON]");
        println!("       witnora_evidence_check manifest HASH_TABLE [--out JSON]");
        return Ok(());
    }
    let mut positionals: Vec<&String> = Vec::new();
    let mut expected = None;
    let mut manifest = None;
    let mut output = None;
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--expected" | "--manifest" | "--out" => {
                if i + 1 >= args.len() { return Err(format!("missing value after {}", args[i])); }
                match args[i].as_str() {
                    "--expected" if expected.is_none() => expected = Some(args[i + 1].as_str()),
                    "--manifest" if manifest.is_none() => manifest = Some(args[i + 1].as_str()),
                    "--out" if output.is_none() => output = Some(args[i + 1].as_str()),
                    _ => return Err(format!("duplicate option {}", args[i])),
                }
                i += 2;
            }
            option if option.starts_with('-') => return Err(format!("unknown option {option}")),
            _ => { positionals.push(&args[i]); i += 1; }
        }
    }
    // Never overwrite a file that is being used as integrity evidence. This
    // includes a symlink alias to the same existing file.
    if let Some(destination) = output {
        if let Ok(destination_file) = fs::canonicalize(destination) {
            for input in positionals.iter().skip(1).map(|s| s.as_str()).chain(manifest) {
                if fs::canonicalize(input).ok().as_ref() == Some(&destination_file) {
                    return Err("output would overwrite an input evidence file".into());
                }
            }
        }
    }
    let payload = match positionals.as_slice() {
        [mode, table_path] if mode.as_str() == "manifest" => {
            if expected.is_some() || manifest.is_some() {
                return Err("manifest mode does not accept check options".into());
            }
            let source = fs::read_to_string(table_path)
                .map_err(|e| format!("cannot read hash table: {e}"))?;
            serde_json::to_value(verification_integrity::parse_manifest_hash_table(&source))
                .map_err(|e| e.to_string())?
        }
        [mode, path, kind] if mode.as_str() == "check" => {
            let path = Path::new(path.as_str());
            let from_manifest = if let Some(table_path) = manifest {
                let source = fs::read_to_string(table_path)
                    .map_err(|e| format!("cannot read hash table: {e}"))?;
                let hashes = verification_integrity::parse_manifest_hash_table(&source);
                verification_integrity::manifest_lookup(path, &hashes)
            } else { None };
            let chosen = expected.or(from_manifest.as_deref());
            verification_integrity::evidence_status(path, kind, chosen)?
        }
        _ => return Err("expected 'manifest HASH_TABLE' or 'check FILE KIND'".into()),
    };
    let serialized = serde_json::to_string_pretty(&payload)
        .map_err(|e| e.to_string())? + "\n";
    if let Some(output) = output {
        fs::write(output, serialized)
            .map_err(|e| format!("cannot write result JSON: {e}"))?;
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
    fn incomplete_arguments_fail_closed() {
        assert!(run(&[]).is_err());
        assert!(run(&["check".into(), "x".into()]).is_err());
        assert!(run(&["check".into(), "x".into(), "drat".into(), "--bogus".into()]).is_err());
        assert!(run(&["check".into(), "x".into(), "drat".into(), "--expected".into(), "a".into(), "--expected".into(), "b".into()]).is_err());
        assert!(run(&["manifest".into(), "x".into(), "--expected".into(), "a".into()]).is_err());
    }
}
