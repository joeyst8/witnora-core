# R-087: exact cutset-conditioned enumeration in Rust

The `crc_cutset_count.py` source module now supports `backend="rust"` for
`component_backend="enumeration"`. Native Rust conditions on each discovered
separator assignment, computes residual primal components, exactly enumerates
local assignments, and returns source model count and resource statistics.
It uses arbitrary-precision bitmasks and counts, retaining the original caps.

The wrapper uses the independently verified R-086 Rust minimum separator,
which still requires the Python source-conditioned certificate. The existing
variable-elimination backends remain in Python, including their separate
Rust-backed component pathway. Therefore **the module is only partially
migrated** until all paths have verified native counterparts.

Focused differential coverage: 180 seeded signed-source cases, star, XOR and
disconnected examples, budget failures and exact field equality. No broad
SAT speedup or formal proof is claimed.

Verified: **focused Rust CI #41919476830 passed** library compilation,
native wheel and all cutset enumeration differential comparisons. Manifest
status is `partial_native_verified`, not `parallel_reference`.
