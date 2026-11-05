# W-CROSSDOMAIN-003 — Source-exact signed-cycle routing validation

**Status:** opt-in diagnostic tests added; native Rust CI and external proof
replay pending. No new solver route has been enabled by default.

## Decision boundary

The signed-cycle method is a known exact technique for a *pure binary-XOR*
formula. The existing Rust `pure_binary_xor_topology` function first
canonicalizes original source-CNF clauses, recognizes complete signed XOR
gadgets, and returns `None` unless **every** clause is accounted for. Its
predicted model count or inconsistent-cycle indicator must never be applied
to arbitrary CNF with unrecognized/nonlinear residuals.

## Independent algorithm comparison

The new Rust regression compares three methods on 448 deterministic generated
source cases (seven declared sizes n=2..8, 64 trials each):

1. Source-bound complete binary-XOR gadget recognition followed by the
   graph cycle/connected-component formula;
2. A separate GF(2) Gaussian-elimination implementation in
   `rust/witnora-ve/src/xor_equations.rs`;
3. An independent direct truth table over every original signed CNF clause.

The test includes repeated edge supports, contradictory edge labels,
disconnected systems and free variables. It requires agreement on both
the contradiction verdict and exact integer model count. Additional controls
append units, a nonlinear/partial binary clause, or an empty clause to a
pure XOR formula: the pure-family diagnostic must return `None` rather than
assert a model count or UNSAT for the mixed source. Malformed variable IDs
are rejected.

## Independent certification retained

Witnora's existing `tests/test_xor_drat.py::test_detected_k2_xor_drat`
already constructs the binary-XOR triangle with labels (0,0,1), exports a
proof against **original CNF**, and requires real independent `drat-trim`
verification. This existing test is the source-bound proof gate. The new Rust
diagnostic does **not** replace it or claim certification on its own. The
broader existing `tests/test_xor_cycles_261_280.py` covers cycle witnesses,
graph cycle rank and additional parity structures.

Local Python regression: 29 tests run, eight skipped where required
external tools were absent. Native compilation and real external replay
must pass on the configured CI runner before claiming verified W-CROSSDOMAIN-003.

## Falsifiable next step

Once native and proof CI are green, profile the existing native Gaussian
and signed-cycle routes on held-out *pure* XOR and mixed-CNF cases. Measure
source recognition cost, operation counts, runtime, memory and proof size;
compare with original-CNF model-count checks. A routing heuristic is useful
only if it improves those metrics and remains fail-closed under all mixed
and incomplete gadgets. No new global SAT complexity result is claimed.
