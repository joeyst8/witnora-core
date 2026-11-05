//! Deterministic benchmark Markdown rendering from the original JSON record.
//! This is reporting only; no SAT/UNSAT or proof semantics are asserted.

use serde_json::Value;
use std::collections::BTreeMap;

fn py_string(value: &Value) -> String {
    match value {
        Value::Null => "None".into(),
        Value::Bool(true) => "True".into(),
        Value::Bool(false) => "False".into(),
        Value::String(s) => s.clone(),
        _ => value.to_string(),
    }
}

fn prop(value: &Value, key: &str, fallback: &str) -> String {
    value.get(key).map(py_string).unwrap_or_else(|| fallback.to_string())
}

fn table(lines: &mut Vec<String>, headers: &[&str], rows: Vec<Vec<String>>) {
    lines.push(format!("| {} |", headers.join(" | ")));
    lines.push(format!("| {} |", vec!["---"; headers.len()].join(" | ")));
    for row in rows {
        lines.push(format!("| {} |", row.join(" | ")));
    }
}

fn pairs(rows: &[(&str, String)]) -> Vec<Vec<String>> {
    rows.iter().map(|(a, b)| vec![(*a).to_string(), b.clone()]).collect()
}

fn truthy(value: &Value) -> bool {
    match value {
        Value::Null => false,
        Value::Bool(v) => *v,
        Value::Number(n) => n.as_f64().unwrap_or(0.0) != 0.0,
        Value::String(s) => !s.is_empty(),
        Value::Array(a) => !a.is_empty(),
        Value::Object(o) => !o.is_empty(),
    }
}

fn summed(results: &[Value], field: &str) -> String {
    let numbers: Vec<&serde_json::Number> = results.iter()
        .filter_map(|r| r.get(field).and_then(Value::as_number)).collect();
    if numbers.iter().all(|n| n.as_i64().is_some()) {
        return numbers.iter().map(|n| n.as_i64().unwrap_or(0)).sum::<i64>().to_string();
    }
    let number = numbers.iter().map(|n| n.as_f64().unwrap_or(0.0)).sum::<f64>();
    if number.fract() == 0.0 { format!("{number:.1}") } else { number.to_string() }
}

fn maximum(results: &[Value], field: &str) -> String {
    let zero = Value::from(0);
    results.iter().map(|r| r.get(field).unwrap_or(&zero))
        .max_by(|left, right| {
            left.as_f64().unwrap_or(0.0)
                .partial_cmp(&right.as_f64().unwrap_or(0.0))
                .unwrap_or(std::cmp::Ordering::Equal)
        }).map(py_string).unwrap_or_else(|| "0".into())
}

pub fn generate_report(source: &str) -> Result<String, String> {
    let data: Value = serde_json::from_str(source).map_err(|e| e.to_string())?;
    let summary = data.get("summary").unwrap_or(&Value::Null);
    let results: Vec<Value> = data.get("per_case_results")
        .and_then(Value::as_array).cloned().unwrap_or_default();
    let mut route_counts: BTreeMap<String, usize> = BTreeMap::new();
    for result in &results {
        *route_counts.entry(prop(result, "solved_route", "")).or_default() += 1;
    }

    let mut lines = vec!["# Witnora Benchmark Report".to_string(), "".to_string(),
                         "## Benchmark Overview".to_string()];
    table(&mut lines, &["Field", "Value"], pairs(&[
        ("version", prop(&data, "version", "")),
        ("c_parameter", prop(&data, "c_parameter", "")),
        ("scale", prop(&data, "scale", "")),
        ("timestamp", prop(&data, "timestamp", "")),
        ("total_cases", summary.get("total_cases").map(py_string)
            .unwrap_or_else(|| results.len().to_string())),
    ]));
    lines.extend(["".into(), "## Summary Counts".into()]);
    table(&mut lines, &["Metric", "Value"], pairs(&[
        ("solved_count", prop(summary, "solved_count", "0")),
        ("sat_count", prop(summary, "sat_count", "0")),
        ("unsat_count", prop(summary, "unsat_count", "0")),
        ("no_collapse_count", prop(summary, "no_collapse_count", "0")),
    ]));
    lines.extend(["".into(), "## Route Breakdown".into()]);
    table(&mut lines, &["Route", "Count"], route_counts.iter()
        .map(|(route, count)| vec![route.clone(), count.to_string()]).collect());
    lines.extend(["".into(), "## Collapse Path Statistics".into()]);
    table(&mut lines, &["Metric", "Value"], pairs(&[
        ("average_collapse_path_length", prop(summary, "average_collapse_path_length", "0")),
        ("max_collapse_path_length", maximum(&results, "collapse_path_length")),
    ]));
    lines.extend(["".into(), "## Clause/Variable Reduction".into()]);
    table(&mut lines, &["Metric", "Value"], pairs(&[
        ("average_clause_reduction_pct", prop(summary, "average_clause_reduction_pct", "0")),
        ("average_variable_reduction_pct", prop(summary, "average_variable_reduction_pct", "0")),
    ]));
    lines.extend(["".into(), "## BCE / PLE / UP / SUB / VE Counts".into()]);
    table(&mut lines, &["Count Type", "Total"], pairs(&[
        ("BCE removed clauses", summed(&results, "num_bce_removed")),
        ("PLE assignments", summed(&results, "num_ple_assignments")),
        ("UP assignments", summed(&results, "num_up_assignments")),
        ("SUB removed clauses", summed(&results, "num_subsumed_clauses")),
        ("VE eliminations", summed(&results, "num_vars_eliminated")),
    ]));
    lines.extend(["".into(), "## Determinism Results".into()]);
    let checked: Vec<&Value> = results.iter()
        .filter(|r| r.get("determinism_pass").is_some_and(|v| !v.is_null())).collect();
    let failed = checked.iter().filter(|r| !r.get("determinism_pass")
        .is_some_and(truthy)).map(|r| prop(r, "case_name", "")).collect::<Vec<_>>().join(", ");
    table(&mut lines, &["Metric", "Value"], pairs(&[
        ("checked_cases", checked.len().to_string()),
        ("pass_rate", prop(summary, "certificate_hash_determinism_pass_rate", "")),
        ("failed_cases", failed),
    ]));
    lines.extend(["".into(), "## No-Collapse Cases".into()]);
    let no_collapse: Vec<&Value> = results.iter()
        .filter(|r| r.get("solved_route").and_then(Value::as_str) == Some("NO_COLLAPSE")).collect();
    if no_collapse.is_empty() {
        lines.push("No no-collapse cases were reported.".into());
    } else {
        table(&mut lines, &["Case", "Failure Reason", "Original Vars", "Original Clauses"],
            no_collapse.iter().map(|r| vec![prop(r, "case_name", ""),
                prop(r, "failure_reason", ""), prop(r, "original_num_vars", ""),
                prop(r, "original_num_clauses", "")]).collect());
    }
    lines.extend(["".into(), "## Width Measurement Skips".into()]);
    let skipped: Vec<&Value> = results.iter()
        .filter(|r| r.get("post_s_width_order_status").and_then(Value::as_str)
            == Some("SKIPPED_SIZE_CAP")).collect();
    if skipped.is_empty() {
        lines.push("No width-order measurements were skipped.".into());
    } else {
        table(&mut lines, &["Case", "Post-S Vars", "Reason"],
            skipped.iter().map(|r| vec![prop(r, "case_name", ""),
                prop(r, "post_s_num_vars", ""),
                prop(r, "post_s_width_order_skip_reason", "")]).collect());
    }
    lines.extend(["".into(), "## Limitations".into()]);
    for line in [
        "- Benchmark measurements are not proofs of industrial SAT competitiveness.",
        "- Clique lower bound is max clause width minus one, not exact treewidth.",
        "- Exact width-order search remains capped and can be skipped for large formulas.",
        "- NO_COLLAPSE means only no certified collapse was found under the current grammar and c.",
        "- No LRAT/FRAT, Horn, XOR, backdoor, GNN, MCTS, or external SAT solver route is included.",
    ] { lines.push(line.into()); }
    lines.extend(["".into(), "## Claims Allowed / Claims Forbidden".into(),
                  "Allowed:".into()]);
    for line in [
        "- Witnora measures certified collapse behavior for deterministic benchmark cases.",
        "- SAT results verify reconstructed assignments against the original CNF.",
        "- Certificate hashes are deterministic except for excluded runtime/timestamp data.",
    ] { lines.push(line.into()); }
    lines.extend(["".into(), "Forbidden:".into()]);
    for line in [
        "- Do not claim P = NP.",
        "- Do not claim no-collapse formulas are hard.",
        "- Do not claim competitiveness with modern industrial SAT solvers from this benchmark alone.",
    ] { lines.push(line.into()); }
    lines.push(String::new());
    Ok(lines.join("\n"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_report_matches_known_python_sections() {
        let report = generate_report("{}").unwrap();
        assert!(report.starts_with("# Witnora Benchmark Report\n\n## Benchmark Overview"));
        assert!(report.contains("| total_cases | 0 |"));
        assert!(report.contains("No no-collapse cases were reported."));
        assert!(report.ends_with("- Do not claim competitiveness with modern industrial SAT solvers from this benchmark alone.\n"));
    }

    #[test]
    fn rendered_cases_are_sorted_and_counts_are_added() {
        let sample = r#"{"per_case_results":[{"solved_route":"z","num_bce_removed":4},{"solved_route":"a","num_bce_removed":3}]}"#;
        let report = generate_report(sample).unwrap();
        assert!(report.find("| a | 1 |").unwrap() < report.find("| z | 1 |").unwrap());
        assert!(report.contains("| BCE removed clauses | 7 |"));
    }

    #[test]
    fn invalid_json_is_rejected() {
        assert!(generate_report("{broken").is_err());
    }
}
