//! HV-002: self-contained unsigned multiplier equivalence miter generator.
//!
//! This is a benchmark generator, not a new solving method. It compares
//! sequential ripple accumulation against a 3:2 carry-save reduction tree.
//! Both circuits share primary inputs and partial-product gates. The resulting
//! DIMACS asks for a *difference*; UNSAT means combinational equivalence.
//!
//! Usage:
//! rustc --edition=2021 -O research/hv002_multiplier_miter.rs -o /tmp/hv002-gen
//! /tmp/hv002-gen --width 8 --mode equivalent --out /tmp/hv002-8.cnf
//! /tmp/hv002-gen --width 8 --mode stuck-zero --out /tmp/hv002-8-bug.cnf

use std::env;
use std::fs::File;
use std::io::{BufWriter, Write};

type Lit = i32;

#[derive(Default)]
struct Cnf {
    vars: i32,
    clauses: Vec<Vec<Lit>>,
    false_lit: Lit,
}

impl Cnf {
    fn new() -> Self {
        let mut cnf = Cnf::default();
        let false_lit = cnf.fresh();
        cnf.false_lit = false_lit;
        cnf.clauses.push(vec![-false_lit]);
        cnf
    }

    fn fresh(&mut self) -> Lit {
        self.vars += 1;
        self.vars
    }

    fn and(&mut self, a: Lit, b: Lit) -> Lit {
        let f = self.false_lit;
        if a == f || b == f || a == -b {
            return f;
        }
        if a == -f {
            return b;
        }
        if b == -f || a == b {
            return a;
        }
        let z = self.fresh();
        self.clauses.extend([vec![-a, -b, z], vec![a, -z], vec![b, -z]]);
        z
    }

    fn or(&mut self, a: Lit, b: Lit) -> Lit {
        let f = self.false_lit;
        if a == -f || b == -f || a == -b {
            return -f;
        }
        if a == f {
            return b;
        }
        if b == f || a == b {
            return a;
        }
        let z = self.fresh();
        self.clauses.extend([vec![a, b, -z], vec![-a, z], vec![-b, z]]);
        z
    }

    fn xor(&mut self, a: Lit, b: Lit) -> Lit {
        let f = self.false_lit;
        if a == f {
            return b;
        }
        if b == f {
            return a;
        }
        if a == -f {
            return -b;
        }
        if b == -f {
            return -a;
        }
        if a == b {
            return f;
        }
        if a == -b {
            return -f;
        }
        let z = self.fresh();
        // z = a XOR b; all four assignments to (a, b) are represented.
        self.clauses.extend([
            vec![-a, -b, -z],
            vec![a, b, -z],
            vec![a, -b, z],
            vec![-a, b, z],
        ]);
        z
    }

    fn full_adder(&mut self, a: Lit, b: Lit, cin: Lit) -> (Lit, Lit) {
        let parity = self.xor(a, b);
        let sum = self.xor(parity, cin);
        let carry_ab = self.and(a, b);
        let carry_pc = self.and(parity, cin);
        let carry = self.or(carry_ab, carry_pc);
        (sum, carry)
    }

    fn ripple_add(&mut self, a: &[Lit], b: &[Lit]) -> Vec<Lit> {
        assert_eq!(a.len(), b.len());
        let mut carry = self.false_lit;
        let mut out = Vec::with_capacity(a.len());
        for (&ai, &bi) in a.iter().zip(b) {
            let (sum, next) = self.full_adder(ai, bi, carry);
            out.push(sum);
            carry = next;
        }
        // Both n-bit unsigned input products fit into 2n bits.
        out
    }

    fn carry_save(&mut self, a: &[Lit], b: &[Lit], c: &[Lit]) -> (Vec<Lit>, Vec<Lit>) {
        assert_eq!(a.len(), b.len());
        assert_eq!(b.len(), c.len());
        let mut sum = Vec::with_capacity(a.len());
        let mut shifted_carry = vec![self.false_lit; a.len()];
        for i in 0..a.len() {
            let (s, carry) = self.full_adder(a[i], b[i], c[i]);
            sum.push(s);
            if i + 1 < a.len() {
                shifted_carry[i + 1] = carry;
            }
        }
        (sum, shifted_carry)
    }

    fn write(&self, path: &str, width: usize, mode: &str, a: &[Lit], b: &[Lit]) -> std::io::Result<()> {
        let mut writer = BufWriter::new(File::create(path)?);
        writeln!(writer, "c HV-002 unsigned multiplier miter, not an independently sourced industrial benchmark")?;
        writeln!(writer, "c width {} mode {} ref=ripple-accumulation candidate=carry-save-reduction", width, mode)?;
        writeln!(writer, "c a_vars {}", a.iter().map(|v| v.to_string()).collect::<Vec<_>>().join(" "))?;
        writeln!(writer, "c b_vars {}", b.iter().map(|v| v.to_string()).collect::<Vec<_>>().join(" "))?;
        if mode == "stuck-zero" {
            writeln!(writer, "c fault candidate's partial product a[0]&b[0] replaced by zero")?;
        }
        writeln!(writer, "p cnf {} {}", self.vars, self.clauses.len())?;
        for clause in &self.clauses {
            for &lit in clause {
                write!(writer, "{} ", lit)?;
            }
            writeln!(writer, "0")?;
        }
        writer.flush()
    }
}

fn generate(width: usize, mode: &str, path: &str) -> Result<(), String> {
    let mut cnf = Cnf::new();
    let a: Vec<Lit> = (0..width).map(|_| cnf.fresh()).collect();
    let b: Vec<Lit> = (0..width).map(|_| cnf.fresh()).collect();
    let bits = width * 2;
    let zero = cnf.false_lit;
    let mut rows = Vec::with_capacity(width);

    for j in 0..width {
        let mut row = vec![zero; bits];
        for i in 0..width {
            row[i + j] = cnf.and(a[i], b[j]);
        }
        rows.push(row);
    }

    // Reference: repeated ripple-carry additions of shifted partial products.
    let mut reference = vec![zero; bits];
    for row in &rows {
        reference = cnf.ripple_add(&reference, row);
    }

    // Candidate: independent topology, reducing three rows to two using
    // carry-save adders, followed by one final ripple-carry addition.
    let mut candidate_rows = rows;
    if mode == "stuck-zero" {
        candidate_rows[0][0] = zero;
    }
    while candidate_rows.len() > 2 {
        let c = candidate_rows.remove(2);
        let b = candidate_rows.remove(1);
        let a = candidate_rows.remove(0);
        let (sum, carry) = cnf.carry_save(&a, &b, &c);
        candidate_rows.push(sum);
        candidate_rows.push(carry);
    }
    let candidate = if candidate_rows.len() == 2 {
        cnf.ripple_add(&candidate_rows[0], &candidate_rows[1])
    } else {
        candidate_rows.remove(0)
    };

    let mut mismatch = zero;
    for i in 0..bits {
        let diff = cnf.xor(reference[i], candidate[i]);
        mismatch = cnf.or(mismatch, diff);
    }
    cnf.clauses.push(vec![mismatch]);
    cnf.write(path, width, mode, &a, &b).map_err(|e| e.to_string())?;
    eprintln!("width={width} mode={mode} vars={} clauses={} output={path}", cnf.vars, cnf.clauses.len());
    Ok(())
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut width = None;
    let mut mode = None;
    let mut path = None;
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--width" | "--mode" | "--out" if i + 1 < args.len() => {
                let key = args[i].as_str();
                i += 1;
                match key {
                    "--width" => width = args[i].parse::<usize>().ok(),
                    "--mode" => mode = Some(args[i].clone()),
                    "--out" => path = Some(args[i].clone()),
                    _ => unreachable!(),
                }
            }
            _ => {
                eprintln!("Usage: hv002-gen --width 2..32 --mode equivalent|stuck-zero --out PATH");
                std::process::exit(2);
            }
        }
        i += 1;
    }
    let width = width.unwrap_or(0);
    let mode = mode.unwrap_or_default();
    if !(2..=32).contains(&width) || !matches!(mode.as_str(), "equivalent" | "stuck-zero") || path.is_none() {
        eprintln!("Usage: hv002-gen --width 2..32 --mode equivalent|stuck-zero --out PATH");
        std::process::exit(2);
    }
    if let Err(error) = generate(width, &mode, &path.unwrap()) {
        eprintln!("HV-002 error: {error}");
        std::process::exit(1);
    }
}
