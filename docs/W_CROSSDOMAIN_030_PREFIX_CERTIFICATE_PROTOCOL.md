# W030 — incremental prefix-XOR UNSAT certification

**Study status:** correctness prototype proposed after observing W027's significant always-on precheck cost. No solver speedup is claimed until a separately preregistered cost-inclusive head-to-head comparison completes.

## Hypothesis and physics/computation connection

Boolean 3-XOR constraints are discrete parity interactions. Their signed-clause patterns form parity tetrahedra in a three-dimensional Boolean cube. A set of source-certified parity equations can be reduced over GF(2); when the combined variable support cancels but the RHS is one, the subset is inconsistent. In physics language this is a frustrated parity loop; computationally it is a finite exact refutation. **Crucially, an UNSAT subset makes the entire CNF UNSAT even if trailing clauses remain unread.**

Unlike the W027 all-clauses-first reconstruction, the new Rust engine reconstructs source quadruples and incrementally updates a parity basis as clauses arrive. It returns `UNSAT_CERTIFIED` at the first contradiction with indices into original source clauses, or `NO_CERTIFICATE` only after complete input validation. It never claims SAT, and never rewrites the original CNF.

## Exact test and falsification gates before any timing claim

1. Rust unit tests: early UNSAT when the contradictory core precedes a large filler; exact SAT no-certificate control; core moved to the end must not enable an earlier proof; malformed uncertified DIMACS is rejected; exhaustive 256 possible three-variable signed-cube corner sets with duplicated clauses.
2. Independent Python proof checker: verify each returned quartet corresponds to four *actual source clauses* with correct signed parity; independently check GF(2) cancellation; independently brute-force the 256 tiny cube cases.
3. Check original W026 SAT/UNSAT core with 0, 256, 8192 noise clauses and an UNSAT core moved after 256 noise clauses. A missing certificate is only a fallback, never a satisfiability assertion.
4. Any mismatched verdict, proof-audit failure, or parser error blocks speed claims and requires a documented code correction followed by rerun.

## Future performance protocol (not yet run)

- Compare (A) unchanged-CNF Kissat, (B) frozen W027 full Rust precheck+Kissat, and (C) W030 prefix Rust precheck+Kissat; include CryptoMiniSat only as a secondary baseline.
- Reuse frozen W026 source hashes and external VLSAT2 hashes as far as possible, include four frozen near-XOR planted SAT decoys, and add **two clause-order strata** (core-first and deterministic seeded shuffled) to expose sensitivity to proof placement.
- Fix all seeds, clause-order transforms, manifests, wall/memory caps, and measurement aggregation **before** running timing. W030 can't claim a speedup from rearranging the frozen official external suite.
- Count process launch, gating, parsing, proof, external independent audit, fallback solver, and model verification consistently with W027's reported wall-time convention. Retain 30-second end-to-end cap and 2GiB limit per invocation.
- Primary effect: paired median full-pipeline wall time by SAT/UNSAT and clause-order stratum; secondary effect: ratio `read_clauses / declared_clauses` on certified UNSAT cases. Separate proven correctness from the cost profile.

## Limitations

The exact parity-subset proof may be absent even when a CNF is UNSAT; arbitrary SAT remains NP-complete. A short prefix proof is sensitive to clause order, and its detection cost may outweigh its saving on cases with no early contradiction. This work neither proves P = NP nor a general complexity separation.
