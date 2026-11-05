//! Native benchmark JSON comparison rendering, independent of Python.
//! The comparison is descriptive and makes no proof or SAT correctness claim.

use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};

fn py_string(value: &Value) -> String {
    match value {
        Value::Null => "None".into(),
        Value::Bool(true) => "True".into(),
        Value::Bool(false) => "False".into(),
        Value::String(text) => text.clone(),
        Value::Array(items) => format!("[{}]", items.iter().map(py_repr).collect::<Vec<_>>().join(", ")),
        Value::Object(fields) => format!("{{{}}}", fields.iter()
            .map(|(key, value)| format!("{}: {}", py_repr(&Value::String(key.clone())), py_repr(value)))
            .collect::<Vec<_>>().join(", ")),
        Value::Number(_) => value.to_string(),
    }
}

fn py_repr(value: &Value) -> String {
    match value {
        Value::String(s) => format!("{:?}", s).replace("\\\"", "\""),
        _ => py_string(value),
    }
}

fn value<'a>(record: &'a Value, key: &str, missing: &'a Value) -> &'a Value {
    record.get(key).unwrap_or(missing)
}

fn table(lines: &mut Vec<String>, headers: &[&str], rows: Vec<Vec<String>>) {
    lines.push(format!("| {} |", headers.join(" | ")));
    lines.push(format!("| {} |", vec!["---"; headers.len()].join(" | ")));
    for row in rows {
        lines.push(format!("| {} |", row.join(" | ")));
    }
}

fn rows_by_case<'a>(data: &'a Value) -> Result<BTreeMap<String, &'a Value>, String> {
    let mut cases = BTreeMap::new();
    if let Some(entries) = data.get("per_case_results") {
        let entries = entries.as_array().ok_or("per_case_results must be an array")?;
        let empty = Value::String(String::new());
        for entry in entries {
            if !entry.is_object() {
                return Err("per_case_results entries must be objects".into());
            }
            let name = py_string(value(entry, "case_name", &empty));
            cases.insert(name, entry);
        }
    }
    Ok(cases)
}

fn route_counts(data: &Value) -> Result<BTreeMap<String, usize>, String> {
    let mut counts = BTreeMap::new();
    if let Some(entries) = data.get("per_case_results") {
        let entries = entries.as_array().ok_or("per_case_results must be an array")?;
        let empty = Value::String(String::new());
        for entry in entries {
            if !entry.is_object() {
                return Err("per_case_results entries must be objects".into());
            }
            *counts.entry(py_string(value(entry, "solved_route", &empty))).or_insert(0) += 1;
        }
    }
    Ok(counts)
}

fn delta(left: &Value, right: &Value) -> String {
    let number = |item: &Value| match item {
        Value::Bool(v) => Some(if *v { 1.0 } else { 0.0 }),
        Value::Number(n) => n.as_f64(),
        _ => None,
    };
    let (Some(a), Some(b)) = (number(left), number(right)) else {
        return String::new();
    };
    let change = b - a;
    let rounded = (change * 1_000_000.0).round_ties_even() / 1_000_000.0;
    let integer_inputs = matches!(left, Value::Bool(_) | Value::Number(_))
        && matches!(right, Value::Bool(_) | Value::Number(_))
        && !matches!(left, Value::Number(n) if n.is_f64())
        && !matches!(right, Value::Number(n) if n.is_f64());
    if integer_inputs && rounded.fract() == 0.0 && rounded.abs() <= (i64::MAX as f64) {
        return format!("{rounded:.0}");
    }
    if rounded.fract() == 0.0 {
        format!("{rounded:.1}")
    } else {
        rounded.to_string()
    }
}

pub fn generate_comparison(left: &str, right: &str) -> Result<String, String> {
    let left: Value = serde_json::from_str(left).map_err(|err| err.to_string())?;
    let right: Value = serde_json::from_str(right).map_err(|err| err.to_string())?;
    if !left.is_object() || !right.is_object() {
        return Err("both benchmark documents must be JSON objects".into());
    }
    let empty = Value::String(String::new());
    let missing_zero = Value::from(0);
    let left_summary = left.get("summary").unwrap_or(&Value::Null);
    let right_summary = right.get("summary").unwrap_or(&Value::Null);
    if (!left_summary.is_null() && !left_summary.is_object())
        || (!right_summary.is_null() && !right_summary.is_object())
    {
        return Err("summary must be a JSON object".into());
    }
    let left_cases = rows_by_case(&left)?;
    let right_cases = rows_by_case(&right)?;
    let left_routes = route_counts(&left)?;
    let right_routes = route_counts(&right)?;
    let mut lines = vec!["# Witnora Benchmark Comparison".into(), "".into(), "## Overview".into()];
    table(&mut lines, &["Field", "Left", "Right"],
        ["version", "c_parameter", "scale", "timestamp"].iter()
        .map(|key| vec![(*key).into(), py_string(value(&left, key, &empty)),
                          py_string(value(&right, key, &empty))]).collect());
    lines.extend(["".into(), "## Summary Delta".into()]);
    let metrics = ["solved_count", "no_collapse_count", "average_collapse_path_length",
        "average_clause_reduction_pct", "certificate_hash_determinism_pass_rate"];
    table(&mut lines, &["Metric", "Left", "Right", "Delta"], metrics.iter().map(|key| {
        let a = value(left_summary, key, &missing_zero);
        let b = value(right_summary, key, &missing_zero);
        vec![(*key).into(), py_string(a), py_string(b), delta(a, b)]
    }).collect());
    lines.extend(["".into(), "## Route Breakdown".into()]);
    let route_names: BTreeSet<_> = left_routes.keys().chain(right_routes.keys()).collect();
    table(&mut lines, &["Route", "Left", "Right", "Delta"], route_names.iter().map(|route| {
        let a = left_routes.get(*route).copied().unwrap_or(0);
        let b = right_routes.get(*route).copied().unwrap_or(0);
        vec![(*route).clone(), a.to_string(), b.to_string(), (b as isize - a as isize).to_string()]
    }).collect());
    lines.extend(["".into(), "## Cases That Changed Status".into()]);
    let mut changed_status = Vec::new();
    let mut changed_routes = Vec::new();
    for (name, a) in &left_cases {
        let Some(b) = right_cases.get(name) else { continue; };
        for (key, rows) in [("status", &mut changed_status), ("solved_route", &mut changed_routes)] {
            let before = value(a, key, &empty);
            let after = value(b, key, &empty);
            if before != after {
                rows.push(vec![name.clone(), py_string(before), py_string(after)]);
            }
        }
    }
    if changed_status.is_empty() {
        lines.push("No common cases changed status.".into());
    } else {
        table(&mut lines, &["Case", "Left Status", "Right Status"], changed_status);
    }
    lines.extend(["".into(), "## Cases That Changed Route".into()]);
    if changed_routes.is_empty() {
        lines.push("No common cases changed route.".into());
    } else {
        table(&mut lines, &["Case", "Left Route", "Right Route"], changed_routes);
    }
    lines.extend(["".into(), "## Determinism Pass Rate".into()]);
    table(&mut lines, &["Side", "Pass Rate"], vec![
        vec!["left".into(), py_string(value(left_summary,
            "certificate_hash_determinism_pass_rate", &empty))],
        vec!["right".into(), py_string(value(right_summary,
            "certificate_hash_determinism_pass_rate", &empty))],
    ]);
    lines.push(String::new());
    Ok(lines.join("\n"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_is_deterministic() {
        let report = generate_comparison("{}", "{}").unwrap();
        assert!(report.contains("| solved_count | 0 | 0 | 0 |"));
        assert!(report.ends_with("| right |  |\n"));
    }

    #[test]
    fn changes_are_sorted() {
        let a = r#"{"per_case_results":[{"case_name":"z","status":"SAT","solved_route":"x"},{"case_name":"a","status":"SAT"}]}"#;
        let b = r#"{"per_case_results":[{"case_name":"z","status":"UNSAT","solved_route":"y"},{"case_name":"a","status":"UNSAT"}]}"#;
        let output = generate_comparison(a, b).unwrap();
        assert!(output.find("| a | SAT | UNSAT |").unwrap() < output.find("| z | SAT | UNSAT |").unwrap());
        assert!(output.contains("| z | x | y |"));
    }

    #[test]
    fn malformed_json_is_rejected() {
        assert!(generate_comparison("{", "{}").is_err());
        assert!(generate_comparison("{}", "[]").is_err());
    }
}
