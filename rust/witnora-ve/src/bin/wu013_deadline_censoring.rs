//! WU-013: does the WU-012 n≈34 joint-timeout cliff move when changing the
//! **retrospective** wall-clock deadline? Original observed runs only.
//!
//! Replaying a shorter cutoff from a 180-second run is not a new solver run.
//! It is valid only for T <= original timeout, assuming the same execution.

use std::collections::{BTreeMap, BTreeSet};
use std::io::{self, Read};

const HEADER: &str = "family\tinstance\theader\tcms_solved\tcms_seconds\tcms_timeout\txor_solved\txor_seconds\txor_timeout";
const BUDGETS: &[f64] = &[1., 3., 10., 30., 60., 120., 180.];

#[derive(Debug, Clone)]
struct Run { solved: bool, seconds: Option<f64>, limit: f64 }

impl Run {
    fn by(&self, budget: f64) -> bool {
        // A published solver timeout stays censored at all shorter budgets.
        self.solved && budget <= self.limit && self.seconds.is_some_and(|s| s <= budget)
    }
}

#[derive(Debug)]
struct Row { family: String, instance: String, n: usize, cms: Run, xor: Run }

fn parse_rows(tsv: &str) -> Result<Vec<Row>, String> {
    let mut lines = tsv.lines();
    if lines.next() != Some(HEADER) { return Err("WU-013 schema mismatch".into()); }
    let mut seen = BTreeSet::new();
    let mut records = Vec::new();
    for (index, line) in lines.enumerate() {
        let cells: Vec<_> = line.split('\t').collect();
        if cells.len() != 9 { return Err(format!("row {}: nine TSV columns required", index+2)); }
        if !matches!(cells[0], "2xnf-rand" | "2xnf-rand_sat") || cells[1].is_empty() {
            return Err("invalid random-family/instance key".into());
        }
        if !seen.insert((cells[0].to_string(), cells[1].to_string())) {
            return Err("duplicate family/instance".into());
        }
        let head: Vec<_> = cells[2].split_whitespace().collect();
        if head.len() != 4 || head[0] != "p" || head[1] != "xnf" {
            return Err("invalid original XNF header".into());
        }
        let n = head[2].parse::<usize>().map_err(|_| "invalid variable count")?;
        let m = head[3].parse::<usize>().map_err(|_| "invalid clause count")?;
        if !(21..=40).contains(&n) || m != 3*n {
            return Err("original random benchmark requires n=21..40 and m=3n".into());
        }
        let parse_run = |col: usize| -> Result<Run, String> {
            let solved = match cells[col] {
                "0" => false, "1" => true,
                _ => return Err("invalid solved flag".into()),
            };
            let seconds = if cells[col+1].is_empty() { None } else {
                Some(cells[col+1].parse::<f64>().map_err(|_| "invalid solve seconds")?)
            };
            let limit = cells[col+2].parse::<f64>().map_err(|_| "invalid deadline")?;
            if !limit.is_finite() || (limit - 180.).abs() > 1e-6 ||
                seconds.is_some_and(|v| v < 0. || !v.is_finite() || v > limit) ||
                (solved && seconds.is_none()) {
                return Err("inconsistent published timing/deadline".into());
            }
            Ok(Run { solved, seconds, limit })
        };
        let cms = parse_run(3)?;
        let xor = parse_run(6)?;
        records.push(Row { family: cells[0].into(), instance: cells[1].into(), n, cms, xor });
    }
    Ok(records)
}

#[derive(Default, Debug, Clone, Copy)]
struct Counts { n: usize, cms_solved: usize, xor_solved: usize, union_solved: usize }

impl Counts {
    fn add(&mut self, row: &Row, t: f64) {
        let c = row.cms.by(t);
        let x = row.xor.by(t);
        self.n += 1;
        self.cms_solved += usize::from(c);
        self.xor_solved += usize::from(x);
        self.union_solved += usize::from(c || x);
    }
    fn joint_timeouts(&self) -> usize { self.n - self.union_solved }
}

fn grouped<'a>(rows: impl IntoIterator<Item=&'a Row>, t: f64) -> BTreeMap<(String, usize), Counts> {
    let mut result = BTreeMap::new();
    for row in rows {
        result.entry((row.family.clone(), row.n))
            .or_insert_with(Counts::default).add(row, t);
    }
    result
}

fn critical_n(family: &str, grouped: &BTreeMap<(String, usize), Counts>) -> Option<usize> {
    (21..=40).find(|&n| {
        let c = grouped.get(&(family.into(), n)).expect("complete original corpus");
        c.joint_timeouts()*2 >= c.n
    })
}

fn report(rows: &[Row]) -> Result<(), String> {
    if rows.len() != 800 || rows.iter().any(|r| r.instance.is_empty()) {
        return Err("expected all 800 original benchmark instances".into());
    }
    let at180 = grouped(rows, 180.);
    for family in ["2xnf-rand", "2xnf-rand_sat"] {
        for n in 21..=40 {
            if at180.get(&(family.to_string(), n)).is_none_or(|c| c.n != 20) {
                return Err(format!("{family} n={n}: expected 20 independent source cases"));
            }
        }
    }
    let hard = |family: &str| at180.iter().filter(|((f, _), _)| f == family)
        .map(|(_, c)| c.joint_timeouts()).sum::<usize>();
    if hard("2xnf-rand") != 136 || hard("2xnf-rand_sat") != 68 {
        return Err("published 180s outcomes disagree with independently audited WU-012".into());
    }
    println!("WU-013 original_cases=800 published_limit_seconds=180 replay_budget_seconds={BUDGETS:?}");
    println!("WU-013 budget,family,first_n_at_least_half_joint_timeouts,total_joint_timeouts,total_cms_solved,total_xor_solved,union_solved");
    for &t in BUDGETS {
        let groups = grouped(rows, t);
        for family in ["2xnf-rand", "2xnf-rand_sat"] {
            let overall = groups.iter().filter(|((f, _), _)| f == family)
                .fold(Counts::default(), |mut acc, (_, c)| {
                    acc.n += c.n;
                    acc.cms_solved += c.cms_solved;
                    acc.xor_solved += c.xor_solved;
                    acc.union_solved += c.union_solved;
                    acc
                });
            let first = critical_n(family, &groups).map_or_else(|| "none".into(), |n| n.to_string());
            println!("WU-013 {t:.0},{family},{first},{},{},{},{}",
                overall.joint_timeouts(), overall.cms_solved,
                overall.xor_solved, overall.union_solved);
        }
    }
    println!("WU-013 budget,family,n,cms_solved,xor_solved,joint_timeouts");
    for &t in BUDGETS {
        let groups = grouped(rows, t);
        for family in ["2xnf-rand", "2xnf-rand_sat"] {
            for n in 30..=40 {
                let c = groups[&(family.into(), n)];
                println!("WU-013 {t:.0},{family},{n},{},{},{}", c.cms_solved,
                    c.xor_solved, c.joint_timeouts());
            }
        }
    }
    // A single suite of historical runs can only infer shorter cutoffs,
    // never the behavior above 180 seconds, independent runs, or scaling.
    Ok(())
}

fn main() {
    let mut input = String::new();
    let result = io::stdin().read_to_string(&mut input)
        .map_err(|e| e.to_string()).and_then(|_| parse_rows(&input))
        .and_then(|rows| report(&rows));
    if let Err(e) = result {
        eprintln!("WU-013 source rejected: {e}");
        std::process::exit(2);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn single() -> String {
        [HEADER,
        "2xnf-rand\ta\tp xnf 21 63\t1\t10\t180\t0\t\t180",
        "2xnf-rand_sat\tb\tp xnf 40 120\t0\t\t180\t1\t150\t180",
        ].join("\n")
    }

    #[test]
    fn shorter_deadlines_replay_original_timing() {
        let rows = parse_rows(&single()).unwrap();
        assert_eq!(rows[0].cms.by(10.), true);
        assert_eq!(rows[0].cms.by(3.), false);
        assert_eq!(rows[1].xor.by(120.), false);
        assert_eq!(rows[1].xor.by(180.), true);
    }

    #[test]
    fn monotone_joint_censoring_and_reproducible_groups() {
        let rows = parse_rows(&single()).unwrap();
        let three = grouped(&rows, 3.);
        let one_eighty = grouped(&rows, 180.);
        assert_eq!(three[&("2xnf-rand".into(), 21)].joint_timeouts(), 1);
        assert_eq!(one_eighty[&("2xnf-rand".into(), 21)].joint_timeouts(), 0);
        assert_eq!(grouped(&rows, 180.).len(), 2);
    }

    #[test]
    fn reject_bad_schema_duplicate_and_impossible_timing() {
        assert!(parse_rows("garbage").is_err());
        let original = single();
        let duplicate = format!("{original}\n{}", original.lines().nth(1).unwrap());
        assert!(parse_rows(&duplicate).is_err());
        assert!(parse_rows(&original.replace("\t10\t180", "\t200\t180")).is_err());
        assert!(parse_rows(&original.replace("p xnf 21 63", "p xnf 21 60")).is_err());
    }
}
