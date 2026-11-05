# W-CROSSDOMAIN-004 — Rust source-to-result parity-route pilot

**Status:** compiled execution/CI pending. The implementation has not yet
established any runtime advantage. No new complexity theorem or proof claim.

The experiment compares two existing Rust computational paths on exactly
the same deliberately pure binary-XOR CNF source:

1. `pure_binary_xor_topology` — canonical source accounting, complete
   binary-gadget matching, signed-cycle detection, component counting, then
   an integer model count.
2. `source_xor::extract_small_xors` followed by `xor_equations::gaussian` —
   separate source-to-GF(2) extraction and elimination, followed by the model
   count `2^(n-rank)` if consistent, zero on a contradiction.

The Rust executable `witnora_cycle_pilot` generates tree, consistent cycle,
inconsistent cycle, and chorded consistent families at n=8/16/24/32. It
measures seven within-process source-to-result timings per row and emits
median nanoseconds for each method. It **fails closed** if any count differs;
for n=8 it also checks the original clauses against all 256 assignments.
All samples use fixed source generation, no stochastic sampling or solver
timeouts. This is an intentionally narrow engineering pilot, not a claim of
general SAT/#SAT superiority or statistical significance. No results are
reported until the Rust binary actually compiles and executes in CI.

Run (with Rust toolchain):

```sh
cargo test --manifest-path rust/witnora-ve/Cargo.toml --bin witnora_cycle_pilot
cargo run --release --manifest-path rust/witnora-ve/Cargo.toml --bin witnora_cycle_pilot
```

Interpretation cautions:

- These are source-to-result paths, but their algorithms have different
  preprocessing strategies. Report both costs rather than timing only one
  method's inner kernel.
- The source family is tailored to exact XOR structure and cannot justify a
  claim about arbitrary overlapping CNF. The existing independent original
  CNF `drat-trim` regression remains required for UNSAT certification.
- If the cycle method is slower, keep it as a diagnostic/witness finder.
- If it is faster, first reproduce on held-out seeds/graph families and
  compare the actual full solver/proof pipeline before proposing a route.

Follow-up: add externally verified proof size and total solve time, and
separate structure preprocessing from backend execution so false speedups
caused by differing interfaces are not mistaken for algorithmic gains.
