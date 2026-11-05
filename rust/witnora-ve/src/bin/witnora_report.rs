//! Standalone native benchmark Markdown CLI (no Python runtime dependency).
//!
//! Usage: witnora_report benchmark.json --out report.md

use std::env;
use std::fs;
use std::process;

fn run(args: &[String]) -> Result<(), String> {
    if args.len() == 1 && (args[0] == "--help" || args[0] == "-h") {
        println!("usage: witnora_report BENCHMARK_JSON --out REPORT_MD");
        return Ok(());
    }
    if args.len() != 3 {
        return Err("usage: witnora_report BENCHMARK_JSON --out REPORT_MD".into());
    }
    let (input, output) = if args[1] == "--out" {
        (&args[0], &args[2])
    } else if args[0] == "--out" {
        (&args[2], &args[1])
    } else {
        return Err("usage: witnora_report BENCHMARK_JSON --out REPORT_MD".into());
    };
    let source = fs::read_to_string(input)
        .map_err(|err| format!("cannot read benchmark JSON: {err}"))?;
    let report = witnora_ve::benchmark_report::generate_report(&source)
        .map_err(|err| format!("invalid benchmark JSON: {err}"))?;
    fs::write(output, report)
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
