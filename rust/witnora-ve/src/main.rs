mod dimacs;

use std::io::{self, Read};
use witnora_ve::count_component;

fn run() -> Result<(), String> {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).map_err(|e| e.to_string())?;
    let mut lines = input.lines().filter(|line| {
        let s = line.trim();
        !s.is_empty() && !s.starts_with('#')
    });
    let header = lines.next().ok_or("missing protocol header")?;
    let p: Vec<_> = header.split_whitespace().collect();
    if p.len() != 6 || p[0] != "p" || p[1] != "witnora-ve" {
        return Err("expected p witnora-ve N CLAUSES WIDTH OPERATIONS".into());
    }
    let n: usize = p[2].parse().map_err(|_| "invalid variable count")?;
    let num_clauses: usize = p[3].parse().map_err(|_| "invalid clause count")?;
    let width: usize = p[4].parse().map_err(|_| "invalid width cap")?;
    let operations: u64 = p[5].parse().map_err(|_| "invalid operation cap")?;
    if n > 512 || num_clauses > 100000 {
        return Err("input size cap exceeded".into());
    }
    let variable_line = lines.next().ok_or("missing variable universe")?;
    let v: Vec<_> = variable_line.split_whitespace().collect();
    if v.first() != Some(&"v") || v.last() != Some(&"0") || v.len() != n + 2 {
        return Err("expected v followed by exactly N variable IDs and 0".into());
    }
    let variables: Vec<u32> = v[1..v.len() - 1].iter()
        .map(|t| t.parse::<u32>().map_err(|_| "invalid variable ID".to_string()))
        .collect::<Result<_, _>>()?;
    let mut clauses: Vec<Vec<i32>> = Vec::with_capacity(num_clauses);
    for _ in 0..num_clauses {
        let line = lines.next().ok_or("missing expected clause")?;
        let tokens: Vec<&str> = line.split_whitespace().collect();
        if tokens.last() != Some(&"0") {
            return Err("clause must end with exactly one 0".into());
        }
        let literals: Vec<i32> = tokens[..tokens.len() - 1].iter()
            .map(|t| t.parse::<i32>().map_err(|_| "invalid literal".to_string()))
            .collect::<Result<_, _>>()?;
        if literals.contains(&0) {
            return Err("embedded zero literal".into());
        }
        clauses.push(literals);
    }
    if lines.next().is_some() {
        return Err("extra unparsed input".into());
    }
    match count_component(&clauses, &variables, width, operations)? {
        Some(result) => println!(
            "EXACT {} {} {} {}",
            result.models, result.operations,
            result.max_factor_variables, result.eliminated_variables
        ),
        None => println!("INCOMPLETE"),
    }
    Ok(())
}

fn main() {
    if std::env::args().nth(1).as_deref() == Some("--two-sat-dimacs") {
        if let Err(e) = dimacs::run_two_sat() {
            eprintln!("ERROR: {e}");
            std::process::exit(2);
        }
        return;
    }
    if std::env::args().nth(1).as_deref() == Some("--fused-dimacs") {
        if let Err(e) = dimacs::run() {
            eprintln!("ERROR: {e}");
            std::process::exit(2);
        }
        return;
    }
    if let Err(e) = run() {
        eprintln!("ERROR: {e}");
        std::process::exit(2);
    }
}
