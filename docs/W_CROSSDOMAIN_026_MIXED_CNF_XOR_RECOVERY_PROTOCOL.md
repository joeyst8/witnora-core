# W-CROSSDOMAIN-026: frozen cost-aware 3-XOR recovery in mixed CNF

Status: prospective. Commit this protocol before implementation or measurements.

## Scientific question

W024 and W025 demonstrate exact information invisible to signed second-order moments but visible to indexed parity loops. Does recovering these parity blocks from **mixed 3-CNF** remain reliable when ordinary clauses greatly outnumber source-XOR clauses, and what exact *scan/index overhead* does the recovery require?

Existing CryptoMiniSat work has extensively studied CNF/XOR representation and Gaussian elimination, including Soos et al., *Tinted, Detached, and Lazy CNF-XOR Solving and Its Applications to Counting and Sampling* (CAV 2020), https://www.cs.toronto.edu/~meel/Papers/cav20-sgm.pdf. This experiment is an engineering falsification attempt, **not** a claim of novel XOR extraction, net SAT speedup, or a resolution of P versus NP.

## Frozen core and synthetic noise

Use the exact W024 five 3-XOR core hyperedges on variables 1 through 9. SAT RHS (0,0,0,0,1); UNSAT RHS (0,0,0,1,0). Encode each as four forbidden width-3 clauses, so the 20 core clauses form five groups of four.

Extend the variable domain to 64. The planted SAT assignment is all zero except x7=1. Add the **same** distractor clauses to SAT and UNSAT formulas. Draw one random triple of distinct variable indices in 1..64 at a time, sort its unsigned variable support, and reject if the support equals any core triple or a previously accepted distractor. Draw three independent sign bits and, only if the candidate is false under the planted assignment, reverse the sign of its first literal. This ensures the SAT partner remains SAT. Restrict each distractor support to one clause, so no distractor can directly impersonate a complete four-clause 3-XOR block.

Noise counts D = 0, 32, 256, 1024, 4096, 8192. For each D run 16 precommitted seeds with replicate index r=0..15:
seed = 0x02600260 XOR ((r+1)*0x9E3779B9 mod 2^32) XOR ((D+1)*0x85EBCA6B mod 2^32), xorshift32 updates and modulo-64 variable selection.

These noise cases are synthetic and reuse the same XOR core. They are not representative of all SAT industrial distributions.

## Exact source-based checks

1. Each SAT partner passes its explicitly planted full 64-variable assignment; each UNSAT partner contains an independently certified inconsistent four-equation XOR cycle.
2. A Rust **source-clause-only** extractor groups equal sorted triples, recognizes an XOR block only when exactly four clauses have distinct sign patterns with the same triple sign product, and recovers RHS from that product. It must recover exactly five true XOR equations and no distractor false positives in **all 96 cases**.
3. Source-derived GF(2) elimination over 64-bit row masks must identify UNSAT only for the UNSAT partner; both sides must share exactly D distractors.
4. Measure exact clause visits for full reconstruction, the number of support-index entries, and a model for repeated queries Q=1,2,8,32: scan-from-scratch visits = Q*(D+20), cached one-time indexed passes = D+20. The latter does **not** measure actual runtime, memory traffic, or end-to-end SAT speed; report them separately.
5. Independent Python reproduces generator seeds, verifies planted assignment, exact XOR block grouping and detected contradiction at D=0,256,8192 and replicate r=0,1,15 (nine configurations, paired SAT/UNSAT), without relying on Rust correctness flags.
6. GitHub CI must compile Rust, run 96 exact cases and independent Python audits, save raw JSON and the case-size overhead table. A failure to recognize 5 blocks, a spurious block, a wrong SAT result, or any generator mismatch invalidates the claim.

## Claim boundary

A green result establishes only that this deliberately controlled source-level hash/group extractor is reliable against the specified single-clause-per-support distractors and quantifies its scan requirements. It does **not** demonstrate that extracting parity beats DPLL/CDCL on heldout problems. A future study must include extraction wall time, actual solver runtimes, realistic hard CNFs, and existing CDCL/XOR baselines.
