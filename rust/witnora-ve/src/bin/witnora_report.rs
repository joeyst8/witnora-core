//! Standalone native benchmark Markdown CLI (no Python runtime dependency).
//!
//! Usage: witnora_report benchmark.json --out report.md

use std::env;
use std::fs;
use std::process;

fn run(args: &[String]) -> Result<(), String> {
    if args.len() != 3 || args[1] != "--out" {
        return Err("usage: witnora_report BENCHMARK_JSON --out REPORT_MD".into());
    }
    let source = fs::read_to_string(&args[0])
        .map_err(|err| format!("cannot read benchmark JSON: {err}"))?;
    let report = witnora_ve::benchmark_report::generate_report(&source)
        .map_err(|err| format!("invalid benchmark JSON: {err}"))?;
    fs::write(&args[2], report)
        .map_err(|err| format!("cannot write Markdown report: {err}"))?;
    Ok(())
}

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    if let Err(message) = run(&args) {
        eprintln!("{message}");
        process::exit(2);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn invalid_argv_refuses_to_run() {
        assert!(run(&[]).is_err());
        assert!(run(&["a".into(), "--incorrect".into(), "b".into()]).is_err());
    }
}
