//! Native reproduction of the strict public benchmark artifact summary.
//! UNSAT categorization is conservative: only externally verified DRAT counts.

use serde_json::{json, Value};

const ARTIFACT_VERSION: &str = "0.9.1";
const RULE: &str = "Only UNSAT_DRAT_EXPORTED_VERIFIED counts as externally certified UNSAT; UNSAT_NOT_EXTERNALLY_VERIFIED, UNSUPPORTED_DRAT, and UNSAT_XOR_NATIVE_ONLY are not aggregated with it.";

fn truthy(value: &Value) -> bool {
    match value {
        Value::Null => false,
        Value::Bool(v) => *v,
        Value::Number(n) => n.as_f64().is_some_and(|v| v != 0.0),
        Value::String(v) => !v.is_empty(),
        Value::Array(v) => !v.is_empty(),
        Value::Object(v) => !v.is_empty(),
    }
}

fn python_int(value: &Value) -> Result<i64, String> {
    match value {
        Value::Bool(v) => Ok(i64::from(*v)),
        Value::Number(n) => n.as_i64().or_else(|| n.as_f64().map(|v| v as i64))
            .ok_or("integer metric outside supported i64 range".into()),
        Value::String(s) => s.trim().parse::<i64>()
            .map_err(|_| format!("metric cannot be parsed as integer: {s:?}")),
        _ => Err("metric cannot be converted to integer".into()),
    }
}

fn metric(summary: &Value, key: &str) -> Result<i64, String> {
    let default = Value::from(0);
    python_int(summary.get(key).unwrap_or(&default))
}

pub fn summarize(source: &str) -> Result<String, String> {
    let data: Value = serde_json::from_str(source).map_err(|error| error.to_string())?;
    if !data.is_object() {
        return Err("benchmark input must be a JSON object".into());
    }
    let default_summary = json!({});
    let summary = data.get("summary").unwrap_or(&default_summary);
    if !summary.is_object() {
        return Err("benchmark summary must be a JSON object".into());
    }
    let default_array = json!([]);
    let results = data.get("per_case_results").unwrap_or(&default_array)
        .as_array().ok_or("per_case_results must be a JSON array")?;
    let failures = data.get("strict_unsat_external_failures").unwrap_or(&default_array)
        .as_array().ok_or("strict_unsat_external_failures must be a JSON array")?;
    let empty = Value::String(String::new());
    let mut uncertified = Vec::new();
    for result in results {
        let category = result.get("public_category").and_then(Value::as_str);
        if !matches!(category, Some("UNSAT_NOT_EXTERNALLY_VERIFIED" | "UNSUPPORTED_DRAT" | "UNSAT_XOR_NATIVE_ONLY")) {
            continue;
        }
        let field = |name: &str| result.get(name).unwrap_or(&empty).clone();
        uncertified.push(json!({
            "instance_name": field("instance_name"),
            "public_category": field("public_category"),
            "drat_export_status": field("drat_export_status"),
            "external_checker": field("external_checker"),
            "external_checker_verified": result.get("external_checker_verified").is_some_and(truthy),
            "error_message": field("error_message"),
        }));
    }
    let output = json!({
        "artifact_version": ARTIFACT_VERSION,
        "strict_unsat_external_pass": data.get("strict_unsat_external_pass").is_some_and(truthy),
        "strict_unsat_external_failures": failures,
        "unsat_total": metric(summary, "unsat_total")?,
        "drat_trim_verified_unsat_count": metric(summary, "externally_verified_unsat_count")?,
        "unverified_unsat_count": metric(summary, "unverified_unsat_count")?,
        "unsupported_drat_count": metric(summary, "unsupported_drat_count")?,
        "xor_native_unsat_count": metric(summary, "xor_native_unsat_count")?,
        "certified_unsat_rule": RULE,
        "uncertified_unsat_instances": uncertified,
    });
    serde_json::to_string_pretty(&output).map_err(|error| error.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_has_no_certified_unsat() {
        let output: Value = serde_json::from_str(&summarize("{}").unwrap()).unwrap();
        assert_eq!(output["drat_trim_verified_unsat_count"], 0);
        assert_eq!(output["uncertified_unsat_instances"], json!([]));
    }

    #[test]
    fn xor_native_is_never_external_proof() {
        let data = r#"{"per_case_results":[{"public_category":"UNSAT_XOR_NATIVE_ONLY","instance_name":"x"}]}"#;
        let output: Value = serde_json::from_str(&summarize(data).unwrap()).unwrap();
        assert_eq!(output["uncertified_unsat_instances"][0]["instance_name"], "x");
    }

    #[test]
    fn bad_json_is_rejected() {
        assert!(summarize("{bad").is_err());
    }
}
