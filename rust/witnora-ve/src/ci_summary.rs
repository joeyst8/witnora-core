//! Standalone formatting of Witnora CI release verification summaries.
//! This is a display function only; it never evaluates certificates or proofs.

use serde_json::Value;

const SCOPE_LOG_TEXT: &str = "Witnora Verify did not rerun the solver, regenerate CNFgen instances, regenerate DRAT proofs, or rerun the full benchmark diagnostic.";

fn py_string(value: &Value) -> String {
    match value {
        Value::Null => "None".into(),
        Value::Bool(true) => "True".into(),
        Value::Bool(false) => "False".into(),
        Value::String(s) => s.clone(),
        _ => value.to_string(),
    }
}

fn property(value: &Value, key: &str, default: &Value) -> String {
    py_string(value.get(key).unwrap_or(default))
}

fn required_array<'a>(value: &'a Value, key: &str) -> Result<&'a [Value], String> {
    match value.get(key) {
        None => Ok(&[]),
        Some(Value::Array(items)) => Ok(items),
        Some(_) => Err(format!("{key} must be a JSON array")),
    }
}

pub fn render(report_source: &str, reasons_source: &str) -> Result<String, String> {
    let report: Value = serde_json::from_str(report_source)
        .map_err(|error| format!("report JSON: {error}"))?;
    let reasons: Value = serde_json::from_str(reasons_source)
        .map_err(|error| format!("failure reasons JSON: {error}"))?;
    if !report.is_object() {
        return Err("report must be a JSON object".into());
    }
    let reasons = reasons.as_array().ok_or("failure reasons must be a JSON array")?;
    let selected = required_array(&report, "selected_evidence")?;
    let checks = required_array(&report, "checks_performed")?;
    let risks = required_array(&report, "risk_flags")?;
    let missing = Value::Null;
    let check_default = Value::String("check".to_string());
    let mut lines = vec![
        "Witnora Verify CI Summary".into(),
        format!("Verdict: {}", property(&report, "verdict", &missing)),
        format!("Verification depth: {}", property(&report, "verification_depth", &missing)),
        format!("Replay depth: {}", property(&report, "replay_depth", &missing)),
        "Selected evidence:".into(),
    ];
    if selected.is_empty() {
        lines.push("- none".into());
    } else {
        for item in selected {
            lines.push(format!("- {} c={} ({})",
                property(item, "instance_id", &missing),
                property(item, "c", &missing),
                property(item, "public_category", &missing)));
        }
    }
    lines.push("Risk flags:".into());
    if risks.is_empty() {
        lines.push("- none".into());
    } else {
        for flag in risks {
            lines.push(format!("- {}", py_string(flag)));
        }
    }
    lines.push("Checks performed:".into());
    if checks.is_empty() {
        lines.push("- none".into());
    } else {
        for check in checks.iter().take(12) {
            lines.push(format!("- {}", property(check, "name", &check_default)));
        }
        if checks.len() > 12 {
            lines.push(format!("- ... {} more", checks.len() - 12));
        }
    }
    lines.extend(["What was not checked:".into(), format!("- {SCOPE_LOG_TEXT}"),
                  "Failure reasons:".into()]);
    if reasons.is_empty() {
        lines.push("- none".into());
    } else {
        for reason in reasons {
            lines.push(format!("- {}", py_string(reason)));
        }
    }
    Ok(lines.join("\n") + "\n")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_report_keeps_scope_disclaimer() {
        let text = render("{}", "[]").unwrap();
        assert!(text.contains("Verdict: None\n"));
        assert!(text.contains(SCOPE_LOG_TEXT));
        assert!(text.ends_with("Failure reasons:\n- none\n"));
    }

    #[test]
    fn large_check_list_is_truncated() {
        let checks = (0..15).map(|i| serde_json::json!({"name": format!("check{i}")}))
            .collect::<Vec<_>>();
        let report = serde_json::json!({"checks_performed": checks}).to_string();
        let text = render(&report, "[]").unwrap();
        assert!(text.contains("- check11\n- ... 3 more\n"));
        assert!(!text.contains("- check12\n"));
    }

    #[test]
    fn invalid_input_fails_closed() {
        assert!(render("{broken", "[]").is_err());
        assert!(render("{}", "{}").is_err());
    }
}
