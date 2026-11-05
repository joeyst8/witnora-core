//! Independent, deterministic mirror of the Python CI failure-selection policy.
//!
//! This is a diagnostic comparison candidate. It never verifies an UNSAT
//! certificate or upgrades a benchmark claim to a mathematical proof.

use std::collections::BTreeSet;

fn has_failed_status(statuses: &[String]) -> bool {
    statuses.iter().any(|status| {
        let normalized = status.to_uppercase();
        normalized == "FAIL" || normalized == "SKIP"
    })
}

pub fn failure_reasons(
    risk_flags: &[String],
    verdict: &str,
    drat_statuses: &[String],
    independent_statuses: &[String],
    fail_on: &[String],
    positive_verdicts: &[String],
) -> Vec<String> {
    let risk: BTreeSet<&str> = risk_flags.iter().map(String::as_str).collect();
    let enabled: BTreeSet<&str> = fail_on.iter().map(String::as_str).collect();
    let positive: BTreeSet<&str> = positive_verdicts.iter().map(String::as_str).collect();
    let mut result = Vec::new();

    if enabled.contains("hash_mismatch") && risk.contains("HASH_MISMATCH") {
        result.push("hash_mismatch".to_string());
    }
    if enabled.contains("missing_file") && risk.contains("MISSING_FILE") {
        result.push("missing_file".to_string());
    }
    if enabled.contains("overclaim")
        && (verdict == "OVERCLAIM" || risk.contains("UNVERIFIED_CLAIM"))
    {
        result.push("overclaim".to_string());
    }
    if enabled.contains("partial_or_not_verified")
        && (!positive.contains(verdict) || risk.contains("UNVERIFIED_CLAIM"))
    {
        result.push("partial_or_not_verified".to_string());
    }
    if enabled.contains("drat_replay_failed")
        && (risk.contains("DRAT_TRIM_REPLAY_FAILED_OR_SKIPPED")
            || has_failed_status(drat_statuses))
    {
        result.push("drat_replay_failed".to_string());
    }
    if enabled.contains("independent_checker_failed") && has_failed_status(independent_statuses) {
        result.push("independent_checker_failed".to_string());
    }
    result
}

pub fn marketplace_failure_reasons(
    risk_flags: &[String],
    verdict: &str,
    selected_flags: &[String],
    selected_verdicts: &[String],
) -> Vec<String> {
    let normalized_risk: BTreeSet<String> =
        risk_flags.iter().map(|flag| flag.to_uppercase()).collect();
    let enabled_flags: BTreeSet<&str> = selected_flags.iter().map(String::as_str).collect();
    let enabled_verdicts: BTreeSet<&str> = selected_verdicts.iter().map(String::as_str).collect();
    let mut reasons: Vec<String> = normalized_risk.iter()
        .filter(|flag| enabled_flags.contains(flag.as_str()))
        .map(|flag| format!("risk_flag:{flag}"))
        .collect();
    let normalized_verdict = verdict.to_uppercase();
    if enabled_verdicts.contains(normalized_verdict.as_str()) {
        reasons.push(format!("verdict:{normalized_verdict}"));
    }
    reasons
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn all_requested_failure_reasons_are_ordered_and_distinct() {
        let risk = vec!["HASH_MISMATCH".into(), "MISSING_FILE".into(),
            "UNVERIFIED_CLAIM".into(), "DRAT_TRIM_REPLAY_FAILED_OR_SKIPPED".into()];
        let enabled = vec!["independent_checker_failed".into(), "drat_replay_failed".into(),
            "partial_or_not_verified".into(), "overclaim".into(),
            "missing_file".into(), "hash_mismatch".into(), "hash_mismatch".into()];
        assert_eq!(failure_reasons(&risk, "OVERCLAIM", &["SKIP".into()],
            &["FAIL".into()], &enabled, &["VERIFIED".into()]), vec![
            "hash_mismatch", "missing_file", "overclaim", "partial_or_not_verified",
            "drat_replay_failed", "independent_checker_failed"]);
    }

    #[test]
    fn verified_control_with_no_failure_is_empty() {
        assert!(failure_reasons(&[], "VERIFIED", &[], &[],
            &["partial_or_not_verified".into()], &["VERIFIED".into()]).is_empty());
    }

    #[test]
    fn marketplace_flags_sort_and_deduplicate() {
        let reasons = marketplace_failure_reasons(
            &["b".into(), "A".into(), "a".into()], "partial",
            &["B".into(), "A".into()], &["PARTIAL".into()]);
        assert_eq!(reasons, vec!["risk_flag:A", "risk_flag:B", "verdict:PARTIAL"]);
    }

    #[test]
    fn missing_optional_failures_do_not_trigger() {
        assert!(failure_reasons(&["HASH_MISMATCH".into()], "OVERCLAIM", &[], &[],
            &[], &["VERIFIED".into()]).is_empty());
    }
}
