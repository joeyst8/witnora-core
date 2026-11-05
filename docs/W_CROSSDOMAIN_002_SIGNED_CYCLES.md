# W-CROSSDOMAIN-002 — Signed-graph balance × GF(2) XOR × CNF

**Status:** known mathematical identity, extended as a bounded Rust diagnostic
around existing source-CNF XOR recognition. No new theorem, general SAT
algorithm, or externally certified UNSAT result is claimed.

## Prior-art check

Signed-graph *balance* is classical: a signed graph is balanced precisely when
every cycle has positive sign product. See Harary's balance theory and
Zaslavsky's survey *Signed graphs* (1982),
https://www.sciencedirect.com/science/article/pii/0166218X82900336 .
For exact SAT representations of XOR equations, see *On SAT Representations
of XOR Constraints*, https://cronfa.swan.ac.uk/Record/cronfa18003 .

Witnora already implements exact complete small-XOR source-gadget extraction
in `source_xor.rs` and unverified odd-cycle candidate discovery in
`odd_xor_cycle.rs`. This experiment composes these known ideas rather than
recreating a separate inconsistent-cycle solver.

## Exact connection and elementary proof

For a pure binary XOR system, every edge `(u,v)` is labeled with
`b_uv` in GF(2), denoting `x_u XOR x_v = b_uv`. Summing the equations around
any cycle cancels each vertex twice. Thus satisfiability requires the XOR of
the cycle labels to be zero. Conversely, if every cycle is balanced, choose
one root value per connected component and propagate values along paths;
cycle balance makes this path-independent. Therefore:

- The system is **consistent iff every cycle has zero label XOR**.
- A consistent system on `n` declared variables with `c` graph components
  has exactly `2^c` satisfying assignments (isolated vertices count).
- For `m` equation edges (including parallel opposite-RHS edges), the
  independent graph cycle-space dimension is `m - n + c`.

This does **not** extend to general signed CNF, nonlinear clauses, or XOR
systems with arity greater than two without additional analysis.

## Important cross-domain falsification of W-CROSSDOMAIN-001

A triangle's *flag complex* fills the triangular cycle, so flag `beta_1=0`.
Yet its **graph** cycle space has dimension one. With edge labels `(0,0,1)`
the XOR constraints are inconsistent; with `(0,0,0)` they have two models.
Both sources have the *same unsigned graph topology*, so flag `beta_1` alone
cannot distinguish them. This is a concrete reason to explore **labeled
cycle obstructions** alongside topological graph summaries, not to claim
that topological holes by themselves determine SAT difficulty.

## Bounded Rust addition

`pure_binary_xor_topology` in `rust/witnora-ve/src/odd_xor_cycle.rs`:

1. Canonicalizes the exact source clauses; fails on invalid literals.
2. Recognizes all complete two-clause binary-XOR gadgets, and returns
   `None` unless their union accounts for **every** canonical source clause.
3. Counts graph components and multigraph cycle rank with union-find.
4. Reuses the existing odd-cycle witness finder and returns the predicted
   model count only for the accepted pure family, with a 32-variable cap.

The Rust unit test covers all labelings of triangle, square, bowtie and
parallel-edge families, and compares each reported model count directly to
an independent original-CNF exhaustive assignment evaluator. The result is
still **not** a Lean proof or independently checked UNSAT certificate.

## Next falsification / implementation gate

Test whether signed cycle obstructions plus graph decomposition can guide
XOR-augmented CNF preprocessing without falsely discarding nonlinear clauses.
Compare with existing GF(2) Gaussian elimination and `drat-trim`-checked
proof export on source-preserving cases; demand a measurable held-out runtime
or certificate-size benefit before deploying a new heuristic.
