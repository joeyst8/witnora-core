# R-100: native two-step Kempe repair

The Rust routine `double_kempe_repair_native` reproduces the Python
first-swap/second-swap traversal, de-duplicated visited set, attempt and node
limits, palette compaction, and bounded-recolor fallback. The native path is
opt-in with `double_kempe_repair(..., backend="rust")`. Python seeded graph
generation stays the reference so the comparison does not depend on a changed
random-number generator.

The bounded search remains incomplete. A failed search is not a chromatic
number lower-bound proof; no research claim is promoted by this migration.
