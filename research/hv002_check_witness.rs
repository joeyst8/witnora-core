//! HV-002 independent SAT-witness checker for the generated multiplier miters.
//! Validates every DIMACS clause, then checks primary-input arithmetic without
//! evaluating the generator's gates. This does *not* validate UNSAT; use DRAT.

use std::env;
use std::fs::read_to_string;

fn fail(message: &str) -> ! {
    eprintln!("HV-002 witness rejected: {message}");
    std::process::exit(1);
}

fn parse_list(line: &str) -> Vec<usize> {
    line.split_whitespace()
        .skip(2)
        .map(|v| v.parse::<usize>().unwrap_or_else(|_| fail("invalid input variable")))
        .collect()
}

fn input_value(bits: &[usize], model: &[Option<bool>]) -> u128 {
    bits.iter().enumerate().fold(0_u128, |acc, (i, &v)| {
        if model.get(v).and_then(|x| *x).unwrap_or_else(|| fail("input variable unassigned")) {
            acc | (1_u128 << i)
        } else {
            acc
        }
    })
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        fail("usage: hv002-check-witness FILE.cnf SOLVER.stdout");
    }
    let formula = read_to_string(&args[1]).unwrap_or_else(|_| fail("cannot read DIMACS"));
    let solver = read_to_string(&args[2]).unwrap_or_else(|_| fail("cannot read solver output"));

    let mut var_count = 0;
    let mut clause_count = 0;
    let mut a_vars = Vec::new();
    let mut b_vars = Vec::new();
    let mut width = 0_usize;
    let mut mode = String::new();
    let mut clauses = Vec::<Vec<i32>>::new();
    let mut open_clause = Vec::new();
    for line in formula.lines() {
        if let Some(rest) = line.strip_prefix("p cnf ") {
            let fields: Vec<_> = rest.split_whitespace().collect();
            if fields.len() != 2 {
                fail("invalid DIMACS header");
            }
            var_count = fields[0].parse::<usize>().unwrap_or_else(|_| fail("invalid variable count"));
            clause_count = fields[1].parse::<usize>().unwrap_or_else(|_| fail("invalid clause count"));
        } else if line.starts_with("c a_vars ") {
            a_vars = parse_list(line);
        } else if line.starts_with("c b_vars ") {
            b_vars = parse_list(line);
        } else if let Some(rest) = line.strip_prefix("c width ") {
            let fields: Vec<_> = rest.split_whitespace().collect();
            if fields.len() < 3 || fields[1] != "mode" {
                fail("invalid width/mode tag");
            }
            width = fields[0].parse::<usize>().unwrap_or_else(|_| fail("invalid width"));
            mode = fields[2].to_string();
        } else if !line.starts_with('c') && !line.trim().is_empty() {
            for word in line.split_whitespace() {
                let lit = word.parse::<i32>().unwrap_or_else(|_| fail("invalid DIMACS literal"));
                if lit == 0 {
                    clauses.push(std::mem::take(&mut open_clause));
                } else {
                    if lit.unsigned_abs() as usize > var_count || var_count == 0 {
                        fail("out-of-range literal");
                    }
                    open_clause.push(lit);
                }
            }
        }
    }
    if !open_clause.is_empty() || clauses.len() != clause_count || var_count == 0 || width != a_vars.len() || width != b_vars.len() || width > 32 {
        fail("incomplete or malformed DIMACS");
    }
    if mode != "stuck-zero" {
        fail("only stuck-zero SAT witnesses have an independent arithmetic oracle");
    }

    let mut model = vec![None; var_count + 1];
    let mut status_sat = false;
    for line in solver.lines() {
        if line == "s SATISFIABLE" {
            status_sat = true;
        } else if let Some(rest) = line.strip_prefix("v ") {
            for word in rest.split_whitespace() {
                let lit = word.parse::<i32>().unwrap_or_else(|_| fail("invalid model literal"));
                if lit == 0 {
                    continue;
                }
                let var = lit.unsigned_abs() as usize;
                if var == 0 || var > var_count {
                    fail("model variable out of range");
                }
                let val = lit > 0;
                if model[var].is_some_and(|previous| previous != val) {
                    fail("model has contradictory assignments");
                }
                model[var] = Some(val);
            }
        }
    }
    if !status_sat {
        fail("SAT solver did not report SATISFIABLE");
    }
    for (index, clause) in clauses.iter().enumerate() {
        if !clause.iter().any(|&lit| {
            let var = lit.unsigned_abs() as usize;
            model[var].is_some_and(|val| val == (lit > 0))
        }) {
            fail(&format!("clause {} is not satisfied by the witness", index + 1));
        }
    }
    let a = input_value(&a_vars, &model);
    let b = input_value(&b_vars, &model);
    let reference = a * b;
    let stuck_partial_product = (a & 1) * (b & 1);
    let candidate = reference - stuck_partial_product;
    if stuck_partial_product != 1 || candidate == reference {
        fail("primary inputs do not demonstrate the declared stuck-at-zero fault");
    }
    println!("VERIFIED: all {clause_count} CNF clauses satisfied; a={a}, b={b}, reference={reference}, candidate={candidate}");
}
