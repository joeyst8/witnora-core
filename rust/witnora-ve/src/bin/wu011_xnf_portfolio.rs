//! WU-011: retrospective, censoring-aware solver portfolio audit on the
//! independently published xnf-tests paired runtime dataset (1695 rows).
//! This program does NOT run either solver or claim a Witnora speedup.
//! Input TSV is exported read-only by scripts/wu011_export_xnf_portfolio.py.

use std::collections::{BTreeMap, BTreeSet};
use std::io::{self, Read};

const HEADER: &str = "family\tinstance\tdirname\tcms_solved\tcms_time\tcms_timeout\tcms_result\txor_solved\txor_time\txor_timeout\txor_result";

#[derive(Clone, Debug)]
struct SolverRun {
    solved: bool,
    time: Option<f64>,
    timeout: f64,
    answer: Option<String>,
}

impl SolverRun {
    fn par2(&self) -> f64 {
        if self.solved { self.time.expect("a solved run must have time") }
        else { 2. * self.timeout }
    }
}

#[derive(Clone, Debug)]
struct Row {
    family: String,
    instance: String,
    rounds: Option<String>,
    cms: SolverRun,
    xor: SolverRun,
}

fn parse_rows(tsv: &str) -> Result<Vec<Row>, String> {
    let mut lines = tsv.lines();
    if lines.next() != Some(HEADER) { return Err("unexpected input header".into()); }
    let mut records = Vec::new();
    let mut seen = BTreeSet::new();
    for (line_id, line) in lines.enumerate() {
        let fields: Vec<&str> = line.split('\t').collect();
        if fields.len() != 11 { return Err(format!("line {}: expected eleven TSV columns", line_id + 2)); }
        let run = |base: usize| -> Result<SolverRun, String> {
            let solved = match fields[base] { "1" => true, "0" => false,
                _ => return Err("invalid solved value".into()) };
            let time = if fields[base + 1].is_empty() { None }
                else { Some(fields[base + 1].parse::<f64>().map_err(|e| e.to_string())?) };
            let timeout = fields[base + 2].parse::<f64>().map_err(|e| e.to_string())?;
            let answer = (!fields[base + 3].is_empty())
                .then(|| fields[base + 3].to_string());
            if !(timeout > 0. && timeout.is_finite()) ||
               time.is_some_and(|t| !t.is_finite() || t < 0.) ||
               (solved && (time.is_none() || !matches!(answer.as_deref(), Some("SAT" | "UNSAT"))))
            {
                return Err("invalid solve time, timeout or SAT result".into());
            }
            Ok(SolverRun { solved, time, timeout, answer })
        };
        let cms = run(3)?;
        let xor = run(7)?;
        if cms.solved && xor.solved && cms.answer != xor.answer {
            return Err(format!("{}: conflicting SAT/UNSAT answers", fields[1]));
        }
        let rounds = if fields[0] == "2xnf-ascon" {
            let end = fields[2].rsplit('/').next().unwrap_or("");
            if !matches!(end, "r2" | "r3" | "r4") {
                return Err(format!("{}: unknown Ascon round stratum", fields[1]));
            }
            Some(end.to_string())
        } else { None };
        let key = (fields[0].to_string(), fields[1].to_string());
        if !seen.insert(key.clone()) { return Err(format!("duplicate pair {key:?}")); }
        records.push(Row { family: key.0, instance: key.1, rounds, cms, xor });
    }
    Ok(records)
}

#[derive(Default, Clone, Copy, Debug)]
struct Score {
    count: usize,
    solved: usize,
    par2_total: f64,
    xor_routes: usize,
}

impl Score {
    fn include(&mut self, r: &SolverRun, chose_xor: bool) {
        self.count += 1;
        self.solved += usize::from(r.solved);
        self.par2_total += r.par2();
        self.xor_routes += usize::from(chose_xor);
    }

    fn mean_par2(&self) -> f64 { self.par2_total / self.count as f64 }
}

fn choose<'a>(r: &'a Row, xor: bool) -> &'a SolverRun {
    if xor { &r.xor } else { &r.cms }
}

fn direct(records: &[Row], policy: impl Fn(&Row) -> bool) -> Score {
    let mut score = Score::default();
    for r in records {
        let xor = policy(r);
        score.include(choose(r, xor), xor);
    }
    score
}

fn fnv1a(bytes: &[u8]) -> u64 {
    let mut hash = 0xcbf29ce484222325u64;
    for &byte in bytes { hash = (hash ^ byte as u64).wrapping_mul(0x100000001b3); }
    hash
}

fn fold(row: &Row) -> usize {
    (fnv1a(format!("{}/{}", row.family, row.instance).as_bytes()) % 5) as usize
}

fn stratum(row: &Row, round_aware: bool) -> String {
    if round_aware && row.family == "2xnf-ascon" {
        format!("{}:{}", row.family, row.rounds.as_deref().unwrap_or("?"))
    } else { row.family.clone() }
}

// Train using four disjoint folds, predict only on the unseen fifth fold.
// This is an exploratory within-dataset CV, NOT an external holdout.
fn five_fold(records: &[Row], round_aware: bool) -> (Score, Vec<(usize, usize, usize)>) {
    let mut total = Score::default();
    let mut fold_summary = Vec::new();
    for held_out in 0..5 {
        let mut costs = BTreeMap::<String, (f64, f64)>::new();
        for r in records.iter().filter(|r| fold(r) != held_out) {
            let entry = costs.entry(stratum(r, round_aware)).or_default();
            entry.0 += r.cms.par2();
            entry.1 += r.xor.par2();
        }
        let mut n = 0;
        let mut xor_choices = 0;
        for r in records.iter().filter(|r| fold(r) == held_out) {
            let xor = costs.get(&stratum(r, round_aware))
                .is_some_and(|(cms, other)| other < cms);
            total.include(choose(r, xor), xor);
            n += 1;
            xor_choices += usize::from(xor);
        }
        fold_summary.push((held_out, n, xor_choices));
    }
    (total, fold_summary)
}

#[derive(Default)]
struct Overlap { n: usize, cms_only: usize, xor_only: usize, both: usize, neither: usize }

fn overlaps(records: &[Row]) -> BTreeMap<String, Overlap> {
    let mut result = BTreeMap::<String, Overlap>::new();
    for r in records {
        let group = stratum(r, true);
        let out = result.entry(group).or_default();
        out.n += 1;
        match (r.cms.solved, r.xor.solved) {
            (true, false) => out.cms_only += 1,
            (false, true) => out.xor_only += 1,
            (true, true) => out.both += 1,
            (false, false) => out.neither += 1,
        }
    }
    result
}

fn report(records: &[Row]) -> Result<(), String> {
    if records.len() != 1695 { return Err(format!("expected 1695 cases, got {}", records.len())); }
    let cms = direct(records, |_| false);
    let xor = direct(records, |_| true);
    let ascon_route = direct(records, |r| r.family == "2xnf-ascon" && r.rounds.as_deref() == Some("r3"));
    let oracle = direct(records, |r| r.xor.par2() < r.cms.par2());
    let (family_cv, fam_folds) = five_fold(records, false);
    let (round_cv, round_folds) = five_fold(records, true);
    for (name, score) in [("cms-improved", cms), ("xorcle", xor),
        ("round-r3-exploratory", ascon_route), ("family-cv", family_cv),
        ("family-plus-round-cv", round_cv), ("per-instance-oracle-unattainable", oracle)]
    {
        println!("WU-011 portfolio={name} solved={}/{} PAR2_seconds={:.6} xor_routed={}",
            score.solved, score.count, score.mean_par2(), score.xor_routes);
    }
    println!("WU-011 family-folds={fam_folds:?} round-folds={round_folds:?}");
    println!("WU-011 stratum,count,cms_only,xor_only,both,neither,cms_PAR2,xor_PAR2");
    for (name, counts) in overlaps(records) {
        let selected: Vec<Row> = records.iter().filter(|r| stratum(r, true) == name).cloned().collect();
        let a = direct(&selected, |_| false);
        let b = direct(&selected, |_| true);
        println!("WU-011 {name},{},{},{},{},{},{:.3},{:.3}", counts.n,
            counts.cms_only, counts.xor_only, counts.both, counts.neither,
            a.mean_par2(), b.mean_par2());
    }
    let overall = overlaps(records);
    let union = overall.values().map(|o| o.n - o.neither).sum::<usize>();
    assert_eq!(union, oracle.solved);
    Ok(())
}

fn main() {
    let mut tsv = String::new();
    if let Err(err) = io::stdin().read_to_string(&mut tsv) {
        eprintln!("WU-011 cannot read data: {err}");
        std::process::exit(2);
    }
    match parse_rows(&tsv).and_then(|rows| report(&rows)) {
        Ok(()) => {},
        Err(err) => {
            eprintln!("WU-011 rejected external dataset: {err}");
            std::process::exit(2);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn small() -> String {
        [HEADER,
         "2xnf-ascon\ta\t./ascon/r3\t0\t\t180\t\t1\t3\t180\tSAT",
         "2xnf-ascon\tb\t./ascon/r4\t1\t2\t180\tSAT\t0\t\t180\t",
         "other\tc\t./other\t1\t4\t180\tUNSAT\t1\t5\t180\tUNSAT"].join("\n")
    }

    #[test]
    fn schema_and_source_outcomes_drive_round_gate() {
        let rows = parse_rows(&small()).unwrap();
        assert_eq!(rows.len(), 3);
        assert_eq!(direct(&rows, |_| false).solved, 2);
        assert_eq!(direct(&rows, |_| true).solved, 2);
        let rule = direct(&rows, |r| r.rounds.as_deref() == Some("r3"));
        assert_eq!(rule.solved, 3);
        assert!((rule.mean_par2() - 3.).abs() < 1e-9);
        assert_eq!(overlaps(&rows)["2xnf-ascon:r3"].xor_only, 1);
    }

    #[test]
    fn catches_wrong_answer_duplicates_missing_seconds_and_invalid_round() {
        let original = small();
        assert!(parse_rows(&original.replace("180\tUNSAT\t1\t5\t180\tUNSAT", "180\tUNSAT\t1\t5\t180\tSAT")).is_err());
        assert!(parse_rows(&format!("{original}\n{}", original.lines().nth(1).unwrap())).is_err());
        assert!(parse_rows(&original.replace("\t1\t3\t180\tSAT", "\t1\t\t180\tSAT")).is_err());
        assert!(parse_rows(&original.replace("./ascon/r3", "./ascon/r5")).is_err());
    }

    #[test]
    fn fold_and_training_are_deterministic() {
        let rows = parse_rows(&small()).unwrap();
        assert_eq!(fold(&rows[0]), fold(&rows[0]));
        let first = five_fold(&rows, true);
        let second = five_fold(&rows, true);
        assert_eq!(first.0.solved, second.0.solved);
        assert_eq!(first.1, second.1);
    }
}
