//! Python-free strict public benchmark artifact summary JSON CLI.
//! Usage: witnora_artifact_summary BENCHMARK_JSON [--out SUMMARY_JSON]

#[path = "../benchmark_artifact_summary.rs"]
mod benchmark_artifact_summary;

use std::{env, fs, process};

fn run(args: &[String]) -> Result<(), String> {
    if args.len() == 1 && (args[0] == "--help" || args[0] == "-h") {
        println!("usage: witnora_artifact_summary BENCHMARK_JSON [--out SUMMARY_JSON]");
        return Ok(());
    }
    let (input, output) = match args {
        [input] => (input, None),
        [input, flag, output] if flag == "--out" => (input, Some(output)),
        [flag, output, input] if flag == "--out" => (input, Some(output)),
        _ => return Err("usage: witnora_artifact_summary BENCHMARK_JSON [--out SUMMARY_JSON]".into()),
    };
    let source = fs::read_to_string(input)
        .map_err(|error| format!("cannot read benchmark JSON: {error}"))?;
    let output_text = benchmark_artifact_summary::summarize(&source)? + "\n";
    if let Some(output) = output {
        fs::write(output, output_text)
            .map_err(|error| format!("cannot write artifact summary JSON: {error}"))?;
    } else {
        print!("{output_text}");
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
    fn no_args_is_rejected() {
        assert!(run(&[]).is_err());
    }
}
