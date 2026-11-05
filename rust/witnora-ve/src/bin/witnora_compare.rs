//! Standalone Rust counterpart of `python -m witnora_core.compare`.
//! Usage: witnora_compare LEFT_JSON RIGHT_JSON --out COMPARISON_MD

#[path = "../benchmark_compare.rs"]
mod benchmark_compare;

use std::{env, fs, process};

fn run(args: &[String]) -> Result<(), String> {
    if args.len() == 1 && (args[0] == "--help" || args[0] == "-h") {
        println!("usage: witnora_compare LEFT_JSON RIGHT_JSON --out COMPARISON_MD");
        return Ok(());
    }
    if args.len() != 4 {
        return Err("usage: witnora_compare LEFT_JSON RIGHT_JSON --out COMPARISON_MD".into());
    }
    let out_index = args.iter().position(|arg| arg == "--out")
        .ok_or("missing required --out COMPARISON_MD")?;
    if out_index == args.len() - 1 {
        return Err("missing output path after --out".into());
    }
    let output = &args[out_index + 1];
    let inputs: Vec<&String> = args.iter().enumerate()
        .filter_map(|(index, arg)| {
            if index == out_index || index == out_index + 1 { None } else { Some(arg) }
        })
        .collect();
    if inputs.len() != 2 {
        return Err("expected two benchmark JSON files".into());
    }
    let left = fs::read_to_string(inputs[0])
        .map_err(|error| format!("cannot read left benchmark JSON: {error}"))?;
    let right = fs::read_to_string(inputs[1])
        .map_err(|error| format!("cannot read right benchmark JSON: {error}"))?;
    let markdown = benchmark_compare::generate_comparison(&left, &right)?;
    fs::write(output, markdown)
        .map_err(|error| format!("cannot write comparison Markdown: {error}"))?;
    Ok(())
}

fn main() {
    let args: Vec<_> = env::args().skip(1).collect();
    if let Err(message) = run(&args) {
        eprintln!("{message}");
        process::exit(2);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn missing_arguments_are_rejected() {
        assert!(run(&[]).is_err());
        assert!(run(&["one".into(), "two".into()]).is_err());
    }
}
