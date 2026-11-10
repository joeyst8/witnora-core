//! WU-019: deterministic wide-XNF generator (not a solver).
//! Four explicitly different families avoid extrapolating a 21-variable core
//! to genuinely wide random parity interactions.
//!
//! Usage: wu019_generate_wide_xnf OUT_DIR BASE_SEED

use std::collections::BTreeSet;
use std::fs;
use std::path::PathBuf;

#[derive(Clone)]
struct Rng(u64);

impl Rng {
    fn new(seed: u64) -> Self { Self(if seed == 0 { 1 } else { seed }) }
    fn draw(&mut self) -> u64 {
        self.0 ^= self.0 >> 12;
        self.0 ^= self.0 << 25;
        self.0 ^= self.0 >> 27;
        self.0.wrapping_mul(0x2545f4914f6cdd1d)
    }
    fn bit(&mut self) -> bool { self.draw() & 1 != 0 }
    fn range(&mut self, n: usize) -> usize { (self.draw() as usize) % n }
    fn support(&mut self, allowed: &[usize], density: usize) -> Vec<usize> {
        loop {
            let picked = if density == 0 {
                allowed.iter().copied().filter(|_| self.bit()).collect::<Vec<_>>()
            } else {
                let mut s = BTreeSet::new();
                while s.len() < density.min(allowed.len()) {
                    s.insert(allowed[self.range(allowed.len())]);
                }
                s.into_iter().collect()
            };
            if !picked.is_empty() { return picked; }
        }
    }
}

fn parity(support: &[usize], witness: &[bool]) -> bool {
    support.iter().fold(false, |p, &idx| p ^ witness[idx])
}

fn literal(support: &[usize], rhs: bool) -> String {
    let mut sorted = support.to_vec();
    sorted.sort_unstable();
    let terms = sorted.into_iter().map(|v| (v + 1).to_string())
        .collect::<Vec<_>>().join("+");
    format!("{}{}", if rhs { "" } else { "-" }, terms)
}

fn pair_clause(rng: &mut Rng, allowed: &[usize], density: usize,
               witness: &[bool], planted: bool) -> String {
    let a = rng.support(allowed, density);
    let b = rng.support(allowed, density);
    let rhs_a = rng.bit();
    let mut rhs_b = rng.bit();
    if planted && parity(&a, witness) != rhs_a && parity(&b, witness) != rhs_b {
        rhs_b = !rhs_b;
    }
    format!("{} {} 0", literal(&a, rhs_a), literal(&b, rhs_b))
}

fn witness_hex(witness: &[bool]) -> String {
    let mut digits = String::new();
    for chunk in witness.chunks(4).rev() {
        let mut value = 0u8;
        for (i, bit) in chunk.iter().enumerate() {
            if *bit { value |= 1 << i; }
        }
        digits.push(char::from_digit(value as u32, 16).expect("hex digit"));
    }
    format!("0x{digits}")
}

fn generate(n: usize, family: &str, seed: u64) -> (String, Option<String>) {
    let mut rng = Rng::new(seed);
    let witness = (0..n).map(|_| rng.bit()).collect::<Vec<_>>();
    let mut lines = Vec::new();
    if family.starts_with("embedded_") {
        // Every variable occurs, and all variables above the 22 free core
        // dimensions are linked to two core variables by parity unit equations.
        let core = (0..22).map(|i| i * (n - 1) / 21).collect::<Vec<_>>();
        let planted = family == "embedded_planted";
        for _ in 0..(3 * core.len()) {
            lines.push(pair_clause(&mut rng, &core, 0, &witness, planted));
        }
        for v in 0..n {
            if core.contains(&v) { continue; }
            let a = core[rng.range(core.len())];
            let mut b = core[rng.range(core.len())];
            if a == b { b = core[(core.iter().position(|&c| c == a).unwrap() + 1) % core.len()]; }
            let support = [v, a, b];
            let rhs = if planted { parity(&support, &witness) } else { rng.bit() };
            lines.push(format!("{} 0", literal(&support, rhs)));
        }
    } else {
        let allowed = (0..n).collect::<Vec<_>>();
        let density = if family == "sparse_planted" { 4 } else { 0 };
        for _ in 0..3*n {
            lines.push(pair_clause(&mut rng, &allowed, density, &witness, true));
        }
    }
    let mut formula = format!("c Witnora WU-019 independent seed {seed}\n\
        c family {family}; embedded has low effective dimension by design\n\
        p xnf {n} {}\n", lines.len());
    formula.push_str(&lines.join("\n"));
    formula.push('\n');
    let planted = family.ends_with("_planted");
    (formula, planted.then(|| witness_hex(&witness)))
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = std::env::args().collect::<Vec<_>>();
    if args.len() != 3 {
        return Err("usage: wu019_generate_wide_xnf OUT_DIR BASE_SEED".into());
    }
    let destination = PathBuf::from(&args[1]);
    let base = args[2].parse::<u64>()?;
    fs::create_dir_all(&destination)?;
    let mut manifest = String::from("family\tvariables\tseed\tfile\tplanted_witness_bits\n");
    let families = ["embedded_unplanted", "embedded_planted", "dense_planted", "sparse_planted"];
    for n in [80, 129, 192] {
        for (f, family) in families.iter().enumerate() {
            let seed = base.wrapping_add(n as u64 * 4_294_967_291 + f as u64);
            let (formula, witness) = generate(n, family, seed);
            let file = format!("{family}_n{n}_seed{seed}.xnf");
            fs::write(destination.join(&file), formula)?;
            manifest.push_str(&format!("{family}\t{n}\t{seed}\t{file}\t{}\n",
                                       witness.unwrap_or_default()));
        }
    }
    fs::write(destination.join("manifest.tsv"), manifest)?;
    println!("WU019 generated 12 wide 2-XNF cases with base seed {base}");
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn witnesses_satisfy_generated_planted_clauses() {
        for n in [80, 129, 192] {
            for family in ["embedded_planted", "dense_planted", "sparse_planted"] {
                let (text, witness) = generate(n, family, 910019);
                assert!(witness.is_some());
                assert!(text.contains(&format!("p xnf {n} ")));
                let mut rng = Rng::new(910019);
                let assignment = (0..n).map(|_| rng.bit()).collect::<Vec<_>>();
                for line in text.lines().filter(|s| !s.starts_with('c') && !s.starts_with('p')) {
                    let mut any_true = false;
                    for term in line.split_whitespace().filter(|&s| s != "0") {
                        let rhs = !term.starts_with('-');
                        let indices = term.trim_start_matches('-').split('+')
                            .map(|s| s.parse::<usize>().unwrap() - 1).collect::<Vec<_>>();
                        any_true |= parity(&indices, &assignment) == rhs;
                    }
                    assert!(any_true, "planted witness failed {family}, width {n}: {line}");
                }
            }
        }
    }
}
