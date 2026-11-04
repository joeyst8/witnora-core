//! R-062: metadata-only UNSAT trace recognition (not proof verification).

pub fn is_supported(
    format: Option<&str>, replayed: bool, external: Option<&str>,
    lrat_frat: Option<&str>, reason: Option<&str>,
) -> bool {
    format == Some("WITNORA_NATIVE_UNSAT_TRACE_V1")
        && replayed
        && external == Some("NONE")
        && lrat_frat == Some("NOT_EXPORTED")
        && matches!(reason, Some("EXPLICIT_EMPTY_CLAUSE" | "INDEPENDENT_2SAT_SCC"))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn conservative_recognition() {
        assert!(is_supported(Some("WITNORA_NATIVE_UNSAT_TRACE_V1"),true,
            Some("NONE"),Some("NOT_EXPORTED"),Some("EXPLICIT_EMPTY_CLAUSE")));
        assert!(!is_supported(Some("WITNORA_NATIVE_UNSAT_TRACE_V1"),false,
            Some("NONE"),Some("NOT_EXPORTED"),Some("EXPLICIT_EMPTY_CLAUSE")));
        assert!(!is_supported(None,true,Some("NONE"),Some("NOT_EXPORTED"),
            Some("INDEPENDENT_2SAT_SCC")));
    }
}
