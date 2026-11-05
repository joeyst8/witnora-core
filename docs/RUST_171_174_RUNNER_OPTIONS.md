# R-171–R-174: opt-in certificate and CLI proof controls

The existing `export_certificate_bundle` and `witnora_core.runner` paths now
expose the tested experimental XOR proof options without changing defaults.

- **R-171:** select `--xor-proof-backend python|rust`, default `python`.
- **R-172:** enable `--xor-dual-rup`, which requires internal Python/Rust RUP
  checker agreement before external `drat-trim`.
- **R-173:** enable `--xor-validate-source` and
  `--xor-dual-source-parser` for original-CNF semantic identity and parser
  agreement (the second requires the first).
- **R-174:** enable `--xor-native-proof-audit` for independent candidate text
  and byte-accounting checks.

Two CLI option-forwarding tests assert that defaults are unchanged and that
explicit flags reach certificate export. They do not constitute an external
DRAT proof test. Native checks are opt-in and any failed checker must still
block a verified claim; main/production behavior is unchanged.

**Status: implemented, CI pending.**
