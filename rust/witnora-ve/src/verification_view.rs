//! Pure rendering and trust-card projection from an existing verification report.
//! No certificate, original-CNF, DRAT, or Lean verification is performed here.

use serde_json::{json, Value};

const ARTIFACT_SCOPE: &str = "The artifact hashes match the manifest, required files are present, and the claim-boundary scanner found no affirmative forbidden claims. This is a metadata and artifact-integrity check. It does not rerun the scientific proofs, rerun drat-trim on all proofs, or rerun the benchmark diagnostic.";
const PARTIAL_SCOPE: &str = "This report reflects partial replay of selected evidence already present in the artifact. It does not rerun the full solver, regenerate CNFgen instances, or rerun the full benchmark diagnostic.";
const CLAIM_LIMITATION: &str = "The claim-boundary scanner is a heuristic text safety net, not a proof of absence of overclaims. It can miss paraphrases, ambiguous wording, or context-sensitive claims. A human audit is still required before public release.";
const PROOF_SELECTION_LIMITED: &str = "Only selected proof evidence was replayed. This trust card does not represent full replay of every proof in the artifact.";

fn py_string(value: &Value) -> String {
    match value {
        Value::Null => "None".into(),
        Value::Bool(true) => "True".into(),
        Value::Bool(false) => "False".into(),
        Value::String(s) => s.clone(),
        _ => value.to_string(),
    }
}

fn get<'a>(value: &'a Value, key: &str, default: &'a Value) -> &'a Value {
    value.get(key).unwrap_or(default)
}

fn array<'a>(value: &'a Value, key: &str) -> Result<&'a [Value], String> {
    match value.get(key) {
        None => Ok(&[]),
        Some(Value::Array(items)) => Ok(items),
        _ => Err(format!("{key} must be an array")),
    }
}

fn truthy(value: &Value) -> bool {
    match value {
        Value::Null => false,
        Value::Bool(b) => *b,
        Value::Number(n) => n.as_f64().is_some_and(|n| n != 0.0),
        Value::String(s) => !s.is_empty(),
        Value::Array(a) => !a.is_empty(),
        Value::Object(o) => !o.is_empty(),
    }
}

fn s(value: &Value, key: &str, default: &Value) -> String {
    py_string(get(value, key, default))
}

fn valid_object(value: &Value) -> Result<(), String> {
    if !value.is_object() { Err("expected a JSON object".into()) } else { Ok(()) }
}

pub fn trust_card(report: &Value, project: &str) -> Result<Value, String> {
    valid_object(report)?;
    let empty = Value::String(String::new());
    let not_verified = Value::String("NOT_VERIFIED".into());
    let depth_default = Value::String("metadata_hash_checks_only".into());
    let name_default = Value::String("check".into());
    let checker_default = Value::String("checker".into());
    let null = Value::Null;
    let verdict = s(report, "verdict", &not_verified);
    let trust_verdict = match verdict.as_str() {
        "ARTIFACT_INTEGRITY_VERIFIED" => "VERIFIED_ARTIFACT_INTEGRITY_WITH_SCOPE_LIMITS",
        "PARTIAL_REPLAY_VERIFIED_WITH_SCOPE_LIMITS" => "PARTIAL_REPLAY_VERIFIED_WITH_SCOPE_LIMITS",
        "VERIFIED" => "VERIFIED_WITH_SCOPE_LIMITS",
        "PARTIALLY_VERIFIED" => "PARTIALLY_VERIFIED_WITH_RISK_FLAGS",
        "OVERCLAIM" => "OVERCLAIM_DETECTED",
        _ => "NOT_VERIFIED",
    };
    let mut verified_by = array(report, "external_checkers")?.to_vec();
    for check in array(report, "checks_performed")? {
        verified_by.push(get(check, "name", &name_default).clone());
    }
    for result in array(report, "checker_results")? {
        verified_by.push(get(result, "checker", &checker_default).clone());
    }
    Ok(json!({
        "project": project,
        "claim": get(report, "claim", &empty),
        "verified_by": verified_by,
        "certification_level": get(report, "certification_level", &empty),
        "verification_depth": get(report, "verification_depth", &depth_default),
        "replay_depth": get(report, "replay_depth", &null),
        "not_claimed": array(report, "forbidden_claims")?,
        "reproducibility": get(report, "reproducibility_status", &empty),
        "risk_flags": array(report, "risk_flags")?,
        "verdict": trust_verdict,
    }))
}

pub fn render_trust_card(card: &Value) -> Result<String, String> {
    valid_object(card)?;
    let empty = Value::String(String::new());
    let depth = s(card, "verification_depth", &empty);
    let scope = if depth == "partial_replay" {
        "This trust card reflects partial replay of selected evidence. It does not rerun the full solver or regenerate the benchmark diagnostic."
    } else {
        "This trust card verifies artifact integrity and scope boundaries only. It does not rerun the scientific proof pipeline."
    };
    let mut lines = vec![
        "# Witnora Trust Card".to_owned(), "".into(),
        format!("**Project:** {}", s(card, "project", &empty)), "".into(),
        scope.into(), "".into(), "## Claim".into(), "".into(),
        s(card, "claim", &empty), "".into(), "## Verified By".into(), "".into(),
    ];
    let risks = array(card, "risk_flags")?;
    if risks.iter().any(|flag| flag.as_str() == Some("PROOF_SELECTION_LIMITED")) {
        lines.insert(6, PROOF_SELECTION_LIMITED.to_string());
        lines.insert(7, String::new());
    }
    for item in array(card, "verified_by")? {
        lines.push(format!("- {}", py_string(item)));
    }
    lines.extend(["".into(), "## Certification Level".into(), "".into(),
        format!("`{}`", s(card, "certification_level", &empty)),
        "".into(), "## Verification Depth".into(), "".into(), format!("`{depth}`")]);
    if depth == "partial_replay" {
        lines.extend(["".into(), "## Replay Depth".into(), "".into(),
            format!("`{}`", s(card, "replay_depth", &empty))]);
    }
    lines.extend(["".into(), "## Not Claimed".into(), "".into()]);
    for item in array(card, "not_claimed")? {
        lines.push(format!("- {}", py_string(item)));
    }
    lines.extend(["".into(), "## Risk Flags".into(), "".into()]);
    for item in risks {
        lines.push(format!("- {}", py_string(item)));
    }
    lines.extend(["".into(), "## Reproducibility".into(), "".into(),
        s(card, "reproducibility", &empty), "".into(), "## Verdict".into(),
        "".into(), format!("`{}`", s(card, "verdict", &empty)), "".into()]);
    Ok(lines.join("\n"))
}

fn sections(lines: &mut Vec<String>, title: &str) {
    lines.extend(["".into(), title.into(), "".into()]);
}

fn replay_checks(lines: &mut Vec<String>, report: &Value, key: &str, title: &str,
                 empty: &Value) -> Result<(), String> {
    let checks = array(report, key)?;
    if !checks.is_empty() {
        sections(lines, title);
        for check in checks {
            lines.push(format!("- `{}`: {} - {}",
                s(check, "instance_id", empty), s(check, "status", empty),
                s(check, "message", empty)));
        }
    }
    Ok(())
}

pub fn render_report(report: &Value) -> Result<String, String> {
    valid_object(report)?;
    let empty = Value::String(String::new());
    let default_checker = Value::String("checker".into());
    let default_false = Value::Bool(false);
    let mut lines: Vec<String> = vec!["# Witnora Verification Report".into(), "".into(),
        "## Claim Being Audited".into(), "".into(), s(report, "claim", &empty),
        "".into(), "## Evidence Provided".into(), "".into()];
    let evidence_files = array(report, "evidence_files")?;
    if evidence_files.is_empty() {
        lines.push("- none".into());
    } else {
        for item in evidence_files { lines.push(format!("- `{}`", py_string(item))); }
    }
    let depth = s(report, "verification_depth", &empty);
    sections(&mut lines, "## Verification Depth");
    lines.push(format!("`{depth}`"));
    if depth == "metadata_hash_checks_only" {
        lines.extend(["".into(), ARTIFACT_SCOPE.into()]);
    }
    if depth == "partial_replay" {
        lines.extend(["".into(), PARTIAL_SCOPE.into()]);
        sections(&mut lines, "## Replay Depth");
        lines.push(format!("`{}`", s(report, "replay_depth", &empty)));
        sections(&mut lines, "## Selection Policy");
        lines.push(format!("`{}`", s(report, "selection_policy", &empty)));
        sections(&mut lines, "## Selected Evidence");
        let selected = array(report, "selected_evidence")?;
        if selected.is_empty() {
            lines.push("- none".into());
        } else {
            let none = Value::Null;
            for item in selected {
                lines.push(format!("- `{}` c={} ({}): `{}`",
                    s(item, "instance_id", &empty), s(item, "c", &empty),
                    s(item, "cap_profile", &none), s(item, "public_category", &empty)));
            }
        }
    }
    sections(&mut lines, "## Checks Performed");
    let checks = array(report, "checks_performed")?;
    if checks.is_empty() {
        lines.push("- none recorded".into());
    } else {
        for check in checks {
            lines.push(format!("- `{}`: {} (depth: `{}`)", s(check, "name", &empty),
                s(check, "status", &empty).to_lowercase(), s(check, "depth", &empty)));
        }
    }
    sections(&mut lines, "## Checker Results");
    for result in array(report, "checker_results")? {
        let name = get(result, "checker", get(result, "check", &default_checker));
        let passed = get(result, "passed", get(result, "verified", &default_false));
        lines.push(format!("- `{}`: {}", py_string(name), if truthy(passed) { "pass" } else { "fail" }));
    }
    sections(&mut lines, "## Evidence Checked");
    let checked = array(report, "evidence_checked")?;
    if checked.is_empty() {
        lines.push("- none recorded".into());
    } else {
        for item in checked {
            lines.push(format!("- `{}` ({}): {}; expected `{}`, actual `{}`",
                s(item, "path", &empty), s(item, "kind", &empty), s(item, "status", &empty),
                s(item, "sha256_expected", &empty), s(item, "sha256_actual", &empty)));
        }
    }
    sections(&mut lines, "## External Verification");
    let external = array(report, "external_checkers")?;
    if external.is_empty() { lines.push("- none recorded".into()); }
    else { for checker in external { lines.push(format!("- `{}`", py_string(checker))); } }
    for (key, title) in [
        ("proof_syntax_checks", "## Proof Syntax Checks"),
        ("drat_trim_log_checks", "## drat-trim Log Checks"),
        ("independent_checker_replay", "## Independent Checker Replay"),
        ("drat_trim_replay", "## drat-trim Replay"),
    ] {
        replay_checks(&mut lines, report, key, title, &empty)?;
    }
    sections(&mut lines, "## Claim Boundary Scanner Limitation");
    lines.push(CLAIM_LIMITATION.into());
    lines.extend(["".into(), format!("claim_scan_depth: `{}`", s(report, "claim_scan_depth", &empty))]);
    sections(&mut lines, "## Artifact Hashes");
    if let Some(hashes) = report.get("artifact_hashes") {
        let hashes = hashes.as_object().ok_or("artifact_hashes must be an object")?;
        for (name, digest) in hashes {
            lines.push(format!("- `{name}`: `{}`", py_string(digest)));
        }
    }
    sections(&mut lines, "## Certification Level");
    lines.push(format!("`{}`", s(report, "certification_level", &empty)));
    sections(&mut lines, "## Allowed Claims");
    for item in array(report, "allowed_claims")? { lines.push(format!("- {}", py_string(item))); }
    sections(&mut lines, "## Forbidden Claims");
    for item in array(report, "forbidden_claims")? { lines.push(format!("- {}", py_string(item))); }
    sections(&mut lines, "## Risk Flags");
    let risks = array(report, "risk_flags")?;
    if risks.is_empty() { lines.push("- none".into()); }
    else { for item in risks { lines.push(format!("- {}", py_string(item))); } }
    sections(&mut lines, "## Last Verification Timestamp");
    lines.push(s(report, "last_verification_timestamp", &empty));
    sections(&mut lines, "## Final Verdict");
    lines.extend([format!("`{}`", s(report, "verdict", &empty)), "".into()]);
    Ok(lines.join("\n"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn verified_vs_partial_trust_verdict_is_scoped() {
        let report = json!({"verdict":"VERIFIED", "external_checkers":["drat-trim"]});
        let card = trust_card(&report, "Witnora-Core").unwrap();
        assert_eq!(card["verdict"], "VERIFIED_WITH_SCOPE_LIMITS");
        assert_eq!(card["verified_by"], json!(["drat-trim"]));
    }

    #[test]
    fn partial_replay_proof_selection_disclaimer_is_explicit() {
        let report = json!({"verdict":"PARTIAL_REPLAY_VERIFIED_WITH_SCOPE_LIMITS",
            "verification_depth":"partial_replay", "risk_flags":["PROOF_SELECTION_LIMITED"]});
        let card = trust_card(&report, "Witnora-Core").unwrap();
        let rendered = render_trust_card(&card).unwrap();
        assert!(rendered.contains(PROOF_SELECTION_LIMITED));
        assert!(rendered.contains("## Replay Depth"));
    }

    #[test]
    fn empty_report_has_claim_limitation() {
        let rendered = render_report(&json!({})).unwrap();
        assert!(rendered.contains(CLAIM_LIMITATION));
        assert!(rendered.ends_with("## Final Verdict\n\n``\n"));
    }
}
