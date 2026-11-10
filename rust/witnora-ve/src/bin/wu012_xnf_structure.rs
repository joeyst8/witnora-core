//! WU-012: does cheap parity-cancellation geometry predict *joint* solver
//! timeouts on published random 2-XNF formulas beyond variable count/family?
//! This is a retrospective, single-corpus holdout experiment, NOT a solver.
//! Formulas and labels are paired read-only by wu012_export_random_xnf.py.

use std::collections::{BTreeMap, BTreeSet};
use std::io::{self, Read};

const HEADER: &str = "family\tinstance\tcms_solved\txor_solved\tformula";

#[derive(Clone, Debug)]
struct Row {
    family: String,
    instance: String,
    n: usize,
    jointly_unsolved: bool,
    // Prespecified, input-only parity support cancellation features.
    parity: [f64; 3], // minimum d/n, mean d/n, proportion d <= floor(n/3)
}

fn parse_literal(input: &str, n: usize) -> Result<u64, String> {
    let mut mask = 0u64;
    let mut vars = 0usize;
    for part in input.split('+') {
        if part.is_empty() || (part.starts_with('-') && vars != 0) {
            return Err("invalid affine lineral sign or empty variable".into());
        }
        let value = part.parse::<i32>().map_err(|_| "invalid lineral variable")?;
        let v = usize::try_from(value.unsigned_abs()).map_err(|_| "oversized variable")?;
        if v == 0 || v > n { return Err("XNF variable outside header range".into()); }
        let bit = 1u64 << (v - 1);
        if mask & bit != 0 { return Err("duplicate variable inside lineral".into()); }
        mask |= bit;
        vars += 1;
    }
    if vars == 0 { return Err("empty lineral".into()); }
    Ok(mask)
}

fn parse_formula(encoded: &str) -> Result<(usize, [f64; 3]), String> {
    let mut lines = encoded.split('|');
    let head = lines.next().ok_or("missing XNF header")?;
    let h: Vec<&str> = head.split_whitespace().collect();
    if h.len() != 4 || h[0] != "p" || h[1] != "xnf" {
        return Err("invalid XNF header".into());
    }
    let n = h[2].parse::<usize>().map_err(|_| "invalid variable count")?;
    let m = h[3].parse::<usize>().map_err(|_| "invalid clause count")?;
    if !(1..=64).contains(&n) || m != 3 * n {
        return Err("random-family source expected n<=64 and m=3n".into());
    }
    let mut count = 0usize;
    let mut sum_d = 0usize;
    let mut min_d = n;
    let mut short = 0usize;
    for line in lines {
        let terms: Vec<&str> = line.split_whitespace().collect();
        if terms.len() != 3 || terms[2] != "0" {
            return Err("random-family XNF clause must contain two linerals".into());
        }
        let left = parse_literal(terms[0], n)?;
        let right = parse_literal(terms[1], n)?;
        let d = (left ^ right).count_ones() as usize;
        min_d = min_d.min(d);
        sum_d += d;
        short += usize::from(d <= n / 3);
        count += 1;
    }
    if count != m { return Err("XNF header/clauses count mismatch".into()); }
    Ok((n, [min_d as f64 / n as f64,
            sum_d as f64 / (m * n) as f64,
            short as f64 / m as f64]))
}

fn parse_rows(input: &str) -> Result<Vec<Row>, String> {
    let mut lines = input.lines();
    if lines.next() != Some(HEADER) { return Err("invalid WU-012 schema".into()); }
    let mut rows = Vec::new();
    let mut seen = BTreeSet::new();
    for (idx, line) in lines.enumerate() {
        let f: Vec<&str> = line.split('\t').collect();
        if f.len() != 5 { return Err(format!("line {}: five columns required", idx+2)); }
        if !matches!(f[0], "2xnf-rand" | "2xnf-rand_sat") || f[1].is_empty() {
            return Err("unexpected family or empty instance".into());
        }
        if !seen.insert((f[0].to_owned(), f[1].to_owned())) {
            return Err("duplicate family/instance key".into());
        }
        let solved = |flag| match flag {
            "0" => Ok(false), "1" => Ok(true), _ => Err("invalid solved flag".to_owned())
        };
        let cms = solved(f[2])?;
        let xor = solved(f[3])?;
        let (n, parity) = parse_formula(f[4])?;
        rows.push(Row { family: f[0].into(), instance: f[1].into(), n,
            jointly_unsolved: !cms && !xor, parity });
    }
    Ok(rows)
}

fn fnv1a(s: &str) -> u64 {
    s.bytes().fold(0xcbf29ce484222325, |hash, byte| {
        (hash ^ u64::from(byte)).wrapping_mul(0x100000001b3)
    })
}

fn test_fold(row: &Row) -> bool {
    fnv1a(&format!("{}/{}", row.family, row.instance)) % 5 == 0
}

const FEATURES: usize = 6;
fn raw_features(row: &Row) -> [f64; FEATURES] {
    [1., row.n as f64, f64::from(row.family == "2xnf-rand_sat"),
        row.parity[0], row.parity[1], row.parity[2]]
}

#[derive(Clone)]
struct Classifier {
    mean: [f64; FEATURES],
    scale: [f64; FEATURES],
    weights: [f64; FEATURES],
}

impl Classifier {
    // Training statistics are computed only from train instances.
    fn fit(rows: &[&Row], enhanced: bool) -> Self {
        let mut mean = [0.; FEATURES];
        let mut scale = [1.; FEATURES];
        let n = rows.len() as f64;
        for k in [1, 3, 4, 5] {
            mean[k] = rows.iter().map(|r| raw_features(r)[k]).sum::<f64>() / n;
            let var = rows.iter().map(|r| {
                (raw_features(r)[k] - mean[k]).powi(2)
            }).sum::<f64>() / n;
            scale[k] = var.sqrt().max(1e-9);
        }
        let mut weights = [0.; FEATURES];
        // Fixed, identical optimization schedule and L2 penalty for both arms.
        // No feature or penalty is selected using the test fold.
        for _ in 0..2200 {
            let mut gradient = [0.; FEATURES];
            for row in rows {
                let x = Self::scaled(raw_features(row), &mean, &scale);
                let logit = (0..FEATURES).map(|k| weights[k] * x[k]).sum::<f64>();
                let p = sigmoid(logit);
                let residual = p - f64::from(row.jointly_unsolved);
                for k in 0..FEATURES {
                    if enhanced || k < 3 { gradient[k] += residual * x[k] / n; }
                }
            }
            for k in 0..FEATURES {
                if enhanced || k < 3 {
                    let ridge = if k == 0 { 0. } else { 0.02 * weights[k] };
                    weights[k] -= 0.40 * (gradient[k] + ridge);
                }
            }
        }
        Self { mean, scale, weights }
    }

    fn scaled(mut f: [f64; FEATURES], mean: &[f64; FEATURES],
              scale: &[f64; FEATURES]) -> [f64; FEATURES] {
        for k in [1, 3, 4, 5] { f[k] = (f[k] - mean[k]) / scale[k]; }
        f
    }

    fn predict(&self, f: [f64; FEATURES]) -> f64 {
        let x = Self::scaled(f, &self.mean, &self.scale);
        sigmoid((0..FEATURES).map(|k| x[k] * self.weights[k]).sum())
    }
}

fn sigmoid(z: f64) -> f64 { 1. / (1. + (-z.clamp(-40., 40.)).exp()) }

#[derive(Default)]
struct Metrics { count: usize, positives: usize, brier: f64, logloss: f64 }

impl Metrics {
    fn add(&mut self, y: bool, p: f64) {
        let truth = f64::from(y);
        let q = p.clamp(1e-12, 1. - 1e-12);
        self.count += 1;
        self.positives += usize::from(y);
        self.brier += (q - truth).powi(2);
        self.logloss -= truth * q.ln() + (1. - truth) * (1. - q).ln();
    }
    fn brier_mean(&self) -> f64 { self.brier / self.count as f64 }
    fn logloss_mean(&self) -> f64 { self.logloss / self.count as f64 }
}

fn score(rows: &[&Row], model: &Classifier, features: Option<&[[f64; 3]]>) -> Metrics {
    let mut m = Metrics::default();
    for (idx, row) in rows.iter().enumerate() {
        let mut f = raw_features(row);
        if let Some(replacement) = features {
            f[3..].copy_from_slice(&replacement[idx]);
        }
        m.add(row.jointly_unsolved, model.predict(f));
    }
    m
}

#[derive(Clone)]
struct Rng(u64);
impl Rng {
    fn next(&mut self) -> u64 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        self.0
    }
}

// Permute held-out geometries only *within* (family, variable count), keeping
// that stratum's input distribution fixed as a strong n/family negative control.
fn shuffled_test_features(test: &[&Row], seed: u64) -> Vec<[f64; 3]> {
    let mut features: Vec<_> = test.iter().map(|r| r.parity).collect();
    let mut strata = BTreeMap::<(String, usize), Vec<usize>>::new();
    for (idx, row) in test.iter().enumerate() {
        strata.entry((row.family.clone(), row.n)).or_default().push(idx);
    }
    let mut rng = Rng(seed);
    for indices in strata.values() {
        for i in (1..indices.len()).rev() {
            let j = (rng.next() % (i as u64 + 1)) as usize;
            features.swap(indices[i], indices[j]);
        }
    }
    features
}

fn report(rows: &[Row]) -> Result<(), String> {
    if rows.len() != 800 ||
        rows.iter().filter(|r| r.family == "2xnf-rand").count() != 400 ||
        rows.iter().filter(|r| r.family == "2xnf-rand_sat").count() != 400 {
        return Err("expected exactly 400 original XNF formulas in each family".into());
    }
    let train: Vec<_> = rows.iter().filter(|r| !test_fold(r)).collect();
    let test: Vec<_> = rows.iter().filter(|r| test_fold(r)).collect();
    let base = Classifier::fit(&train, false);
    let augmented = Classifier::fit(&train, true);
    let train_base = score(&train, &base, None);
    let train_aug = score(&train, &augmented, None);
    let test_base = score(&test, &base, None);
    let test_aug = score(&test, &augmented, None);
    let delta = test_base.brier_mean() - test_aug.brier_mean();

    // Prespecified one-sided conditional permutation against fixed trained
    // enhanced model. Counts are descriptive, not a cross-corpus p-value.
    let mut at_least = 0usize;
    let n_perm = 999usize;
    for perm in 1..=n_perm {
        let shuffled = shuffled_test_features(&test,
            0x682e44a9a792d7c1u64.wrapping_add(perm as u64));
        let null_score = score(&test, &augmented, Some(&shuffled));
        let null_delta = test_base.brier_mean() - null_score.brier_mean();
        if null_delta >= delta - 1e-12 { at_least += 1; }
    }

    println!("WU-012 sample total={} train={} holdout={} jointly_unsolved={} train_hard={} holdout_hard={}",
        rows.len(), train.len(), test.len(),
        rows.iter().filter(|r| r.jointly_unsolved).count(),
        train_aug.positives, test_aug.positives);
    for (group, model, metrics) in [
        ("train", "n-plus-family", &train_base),
        ("train", "n-family-plus-parity", &train_aug),
        ("holdout", "n-plus-family", &test_base),
        ("holdout", "n-family-plus-parity", &test_aug),
    ] {
        println!("WU-012 split={group} model={model} n={} failures={} Brier={:.6} logloss={:.6}",
            metrics.count, metrics.positives, metrics.brier_mean(), metrics.logloss_mean());
    }
    println!("WU-012 heldout_Brier_gain={delta:.6} within_n_family_permutation_one_sided_p={:.4} ({at_least}/{n_perm} >= observed)",
        (at_least+1) as f64 / (n_perm+1) as f64);
    println!("WU-012 enhanced_weights(intercept,n,family,min_diff,mean_diff,short_fraction)={:?}",
        augmented.weights);
    let mut by_n = BTreeMap::<(String, usize), (usize, usize)>::new();
    for row in rows {
        let stats = by_n.entry((row.family.clone(), row.n)).or_default();
        stats.0 += 1;
        stats.1 += usize::from(row.jointly_unsolved);
    }
    for ((family, n), (count, hard)) in by_n {
        println!("WU-012 source_stratum family={family} variables={n} instances={count} jointly_unsolved={hard}");
    }
    for family in ["2xnf-rand", "2xnf-rand_sat"] {
        let subset: Vec<_> = test.iter().copied().filter(|r| r.family == family).collect();
        let b = score(&subset, &base, None);
        let a = score(&subset, &augmented, None);
        println!("WU-012 heldout_family={family} n={} failures={} baseline_Brier={:.6} parity_Brier={:.6}",
            subset.len(), b.positives, b.brier_mean(), a.brier_mean());
    }
    Ok(())
}

fn main() {
    let mut input = String::new();
    let result = io::stdin().read_to_string(&mut input)
        .map_err(|e| e.to_string()).and_then(|_| parse_rows(&input))
        .and_then(|rows| report(&rows));
    if let Err(err) = result {
        eprintln!("WU-012 rejected experiment data: {err}");
        std::process::exit(2);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parity_support_cancellation_is_measured_without_assignments() {
        let (n, feat) = parse_formula("p xnf 6 18|1+2 -1+2 0|1+3 3+4 0|1+2 1+3 0|1+2 1+3 0|1+2 1+3 0|1+2 1+3 0|1+2 1+3 0|1+2 1+3 0|1+2 1+3 0|1+2 1+3 0|1+2 1+3 0|1+2 1+3 0|1+2 1+3 0|1+2 1+3 0|1+2 1+3 0|1+2 1+3 0|1+2 1+3 0|1+2 1+3 0").unwrap();
        assert_eq!(n, 6);
        assert_eq!(feat[0], 0.);
        assert!(feat[1] > 0. && feat[1] < 1.);
        assert!(feat[2] > 0. && feat[2] <= 1.);
    }

    #[test]
    fn invalid_xnf_is_rejected() {
        assert!(parse_formula("p xnf 5 15|1+1 2 0").is_err());
        assert!(parse_formula("p xnf 5 15|1 6 0").is_err());
        assert!(parse_formula("p xnf 5 15|1 2 3 0").is_err());
        assert!(parse_literal("1+-2", 5).is_err());
        assert!(parse_rows("other\theader\n").is_err());
    }

    #[test]
    fn deterministic_predefined_split_and_within_stratum_shuffle() {
        let make = |name: &str| Row { family: "2xnf-rand".into(), instance: name.into(),
            n: 24, jointly_unsolved: false, parity: [0.1, 0.2, 0.3] };
        let a = make("a");
        let b = make("b");
        assert_eq!(test_fold(&a), test_fold(&a));
        let rows = vec![&a, &b];
        assert_eq!(shuffled_test_features(&rows, 143),
            shuffled_test_features(&rows, 143));
    }
}
