# W-CROSSDOMAIN-027: frozen cost-inclusive solver-level parity intervention

Status: prospective; commit before implementation and before first measurement. W024–W026 validated representation and source extraction; **no solver-level speedup has been demonstrated**.

## Question

Does W026's source-reconstructed exact 3-XOR contradiction certificate **actually reduce end-to-end SAT solving time**, after paying for extraction, compared with modern SAT solvers that already support clause learning and native XOR reasoning? Can it avoid degrading unrelated instances?

This is not a P versus NP proof experiment. Existing CDCL/XOR work, especially CryptoMiniSat, is a formidable baseline and may already beat the proposed mechanism. A negative result is valuable.

## Three precommitted solver arms

- **A: plain Kissat**, unchanged original CNF input.
- **B: Witnora Rust source extraction + Kissat**. Parse original CNF, detect only exact clause quartets per unsigned triple support, and use source-derived GF(2) contradiction detection. If a contradictory XOR witness is found and independently verified, return UNSAT immediately; otherwise invoke Kissat on the **unchanged** original CNF. Count **all preprocessing and downstream solver time**. Never return SAT based only on XOR consistency.
- **C: CryptoMiniSat**, original CNF input with its own built-in CNF/XOR handling and documented recommended settings, not Witnora-derived metadata.

Run external solvers from pinned, recorded source tags/commits and record compiler versions and hardware context. If CryptoMiniSat cannot be installed reproducibly, report that arm as unavailable; never substitute invented results.

## Frozen instance strata

1. **W026 synthetic source-XOR controls:** 96 SAT/UNSAT pairs at noise levels 0, 32, 256, 1,024, 4,096, 8,192 and the same 16 seeds; unchanged clause streams and SAT witnesses. These are intentionally favorable to exact XOR recognition.
2. **Eight W022 external VLSAT2 files:** reuse the independently hashed source files and original source metadata in the W022 archive, with no replacement or filtering based on outcome. This tests whether the parity gate adds harmful overhead when explicit XOR structure may be absent.
3. **Controlled near-XOR adversarial decoys:** add clause patterns with repeated unsigned triple supports but only three of the four required parity signs, or quartets with mixed products. Require **zero false extraction**. Freeze the generator seeds, sizes and hashes before timed measurement.
4. **Heldout XOR-rich formulas:** only if independently sourced and pinned by SHA-256 before any timed measurement. Otherwise report this stratum unavailable, never invent one.

## Timing and soundness policy

- Run each arm three times on the same single-host runner, interleaving arm order across instances; record every raw invocation, wall-time, exit status, timeout and source hash.
- Hard cap 30 seconds per invocation and the same memory limit for each arm, including wrapper preprocessing. Treat censored timeouts explicitly; do not replace them by success or drop them from aggregates.
- Recompute every reported SAT model against the *original* CNF. For UNSAT short circuits, preserve the chosen XOR rows and verify the contradiction via a separate source-derived checker.
- Report median complete-pipeline wall time, solved count, error count, paired speedup ratio where both solve within cap, and timeout-qualified aggregate by stratum. Provide total overhead and per-stage preprocessing cost. Reject broad speed claims based only on synthetic source-XOR successes.
- Do not tune thresholds, source decoys or benchmark selection on these same results. If any implementation change is necessary, create a new preregistered revision or explicitly label the run exploratory.

## Decision rule

Advance Witnora's parity intervention only if it is sound and reproducibly competitive after preprocessing, and the behavior on non-XOR heldouts is quantified. A source-recognition trick that merely rediscovers established XOR algebra without runtime benefit should stay a **research diagnostic**, not a default solver component.

Prior literature: Soos et al. (CAV 2020), *Tinted, Detached, and Lazy CNF-XOR Solving and Its Applications to Counting and Sampling*, https://www.cs.toronto.edu/~meel/Papers/cav20-sgm.pdf, and Laitinen et al., *Extending Clause Learning SAT Solvers with Complete Parity Reasoning*, https://arxiv.org/abs/1207.0988.
