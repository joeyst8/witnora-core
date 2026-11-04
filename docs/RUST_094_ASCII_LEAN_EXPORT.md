# R-094: ASCII Lean certificate exporter in Rust

The Rust backend reproduces source certificate ASCII serialization, explicit
Lean Nat byte lists and all generated Lean declarations, including deliberate
single-byte damaged controls. Python validation of candidate colorings and
Lean declaration names remains unchanged and runs before the native formatter.
The reference implementation stays the default; `backend="rust"` is opt-in.

The native differential gate checks byte-exact full source reports under
prefixes and permutations, 200 randomized raw byte vectors, source
serialization, and invalid input rejection. Lean is still responsible for
checking generated theorem proofs; emission alone proves nothing.

Status: awaiting compiled Rust CI.
