//! Python-free renderer of CI release-verification log summaries.
//! Usage: witnora_ci_summary REPORT_JSON FAILURE_REASONS_JSON [--out SUMMARY_TXT]

#[path = "../ci_summary.rs"]
mod ci_summary;

use std::{env, fs, process};

fn run(args: &[String]) -> Result<(), String> {
    if args.len() == 1 && (args[0] == "--help" || args[0] == "-h") {
        println!("usage: witnora_ci_summary REPORT_JSON FAILURE_REASONS_JSON [--out SUMMARY_TXT]");
        return Ok(());
    }
    let (inputs, output) = if let Some(index) = args.iter().position(|arg| arg == "--out") {
        if index + 1 >= args.len() {
            return Err("missing output filename after --out".into());
        }
        let inputs: Vec<&String> = args.iter().enumerate()
            .filter_map(|(i, arg)| if i == index || i == index + 1 {
                None
            } else { Some(arg) }).collect();
        (inputs, Some(&args[index + 1]))
    } else {
        (args.iter().collect(), None)
    };
    if inputs.len() != 2 {
        return Err("expected a report and a failure-reasons JSON filename".into());
    }
    let report = fs::read_to_string(inputs[0])
        .map_err(|error| format!("cannot read verification report: {error}"))?;
    let reasons = fs::read_to_string(inputs[1])
        .map_err(|error| format!("cannot read failure reasons: {error}"))?;
    let text = ci_summary::render(&report, &reasons)?;
    if let Some(output) = output {
        fs::write(output, text)
            .map_err(|error| format!("cannot write CI summary: {error}"))?;
    } else {
        print!("{text}");
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
    fn incomplete_argv_is_rejected() {
        assert!(run(&[]).is_err());
        assert!(run(&["report.json".into()]).is_err());
    }
}
