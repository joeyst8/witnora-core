//! Presentation-only release verification and trust-card CLI, no Python runtime.
//! It never checks certificates, DRAT evidence, source CNF, or Lean theorems.

#[path = "../verification_view.rs"]
mod verification_view;

use serde_json::Value;
use std::{env, fs, process};

fn run(args: &[String]) -> Result<(), String> {
    if args.len() == 1 && (args[0] == "--help" || args[0] == "-h") {
        println!("usage: witnora_verification_view MODE INPUT_JSON [--project NAME] [--out OUTPUT]");
        println!("modes: trust-card, trust-markdown, report-markdown");
        return Ok(());
    }
    let mut positionals: Vec<&String> = Vec::new();
    let mut output = None;
    let mut project = "Witnora-Core";
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--out" | "--project" => {
                if i + 1 >= args.len() { return Err(format!("missing value for {}", args[i])); }
                if args[i] == "--out" { output = Some(args[i + 1].as_str()); }
                else { project = args[i + 1].as_str(); }
                i += 2;
            }
            _ => { positionals.push(&args[i]); i += 1; }
        }
    }
    if positionals.len() != 2 {
        return Err("expected a mode and one input JSON file".into());
    }
    let source = fs::read_to_string(positionals[1])
        .map_err(|error| format!("cannot read input JSON: {error}"))?;
    let data: Value = serde_json::from_str(&source)
        .map_err(|error| format!("invalid input JSON: {error}"))?;
    let rendered = match positionals[0].as_str() {
        "trust-card" => serde_json::to_string_pretty(
            &verification_view::trust_card(&data, project)?)
            .map_err(|error| error.to_string())? + "\n",
        "trust-markdown" => verification_view::render_trust_card(&data)?,
        "report-markdown" => verification_view::render_report(&data)?,
        _ => return Err("unsupported mode; choose trust-card, trust-markdown or report-markdown".into()),
    };
    if let Some(path) = output {
        fs::write(path, rendered)
            .map_err(|error| format!("cannot write output: {error}"))?;
    } else {
        print!("{rendered}");
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
    fn missing_arguments_fail_closed() {
        assert!(run(&[]).is_err());
        assert!(run(&["report-markdown".into()]).is_err());
    }
}
