# W042 — Prospective cost-inclusive unit-propagation branching trial

## Scientific question (frozen before inspecting W042 outcomes)

W040 and W041 failed to predict DPLL work from static geometry, Walsh and
signed-cycle descriptors on two disjoint SATLIB `uf20-91` holdouts. W016 also
found that a static four-clause Walsh mutual-information branching rule lost
end-to-end time against degree branching. The next test asks a more actionable
question: **does a tightly budgeted two-sided unit-propagation probe at the
root improve *total* search work on a genuinely different publisher family?**

This is a replication/adaptation of **established SAT lookahead**, not a novel
propagation rule or a new SAT complexity theorem. Original prior art:

- Li and Anbulagan, *Heuristics Based on Unit Propagation for Satisfiability
  Problems*, IJCAI 1997, https://www.ijcai.org/Proceedings/97-1/Papers/054.pdf
  (two-sided UP lookahead and the MOMS comparison).
- Liang, Ganesh, Poupart and Czarnecki, *Learning Rate Based Branching
  Heuristic for SAT Solvers*, SAT 2016,
  https://cs.uwaterloo.ca/~ppoupart/publications/sat/learning-rate-branching-heuristic-SAT.pdf
  (dynamic feedback in modern CDCL; **not** implemented in this DPLL test).
- Selsam and Bjørner, *Guiding High-Performance SAT Solvers with Unsat-Core
  Predictions*, SAT 2019, https://arxiv.org/abs/1903.04671
  (actionable prediction changes real solver branching; **not** a result of W042).
- Xu et al., *SATzilla: Portfolio-based Algorithm Selection for SAT*, JAIR
  2008, https://www.jair.org/index.php/jair/article/view/10522
  (prediction matters only when the selection policy pays its own cost).

## Previously unused published sources and independent validity

Source: Hoos and Stützle's publisher SATLIB uniform random 3-SAT archives,
https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/RND3SAT/descr.html.

1. `uf50-218.tar.gz`, publisher SHA256
   `a40862e52dfdce78620b037254579a02dbda8182d2879433658a4c15cb00327c`
   (publisher SAT-only 50-variable, 218-clause cases).
2. `uuf50-218.tar.gz`, publisher SHA256
   `24cc9f492673e0f975fecc56b3a4d8ac21c385cc46205d83b7491a787f43e13d`
   (publisher UNSAT-only 50-variable, 218-clause cases).

For each independently SHA-verified archive, choose exact zero-based
lexicographic `.cnf` member ranks **0–31**; preserve the original clause and
literal order, original name, and per-file SHA. Do not replace or filter any
cases based on labels, observed difficulty or runtime. Reject incorrect
DIMACS headers, incomplete/malformed clauses and duplicate source variables
inside a three-literal clause. Do not use SAT/UNSAT label as a policy input.

## Frozen native Rust policies

All arms share **one** Rust DPLL implementation, root and recursive unit
propagation, true-before-false branch order, identical source order, and a
hard **2,000,000 inclusive clause-visit cap** per attempt. Every scan of a
source clause in unit propagation, variable ranking or trial propagation is
charged; unit propagation never removes clauses or changes source meaning.
No clause learning, magic physics variable, presolve, caching or GPU.

- **D** `degree`: fixed descending original unsigned occurrence degree,
  ties by variable index. Calculation charged once per attempt.
- **M** `moms`: dynamic highest unsigned occurrence in *shortest currently
  open clauses*, ties by variable index. This is a simple MOMS-inspired
  baseline, **not** a full original MOMS/VSIDS/CDCL implementation.
- **P** `probe`: M at all non-root nodes; at the root only, test both
  truth values of up to eight highest-ranked M candidates using ordinary
  unit propagation. Rank by the minimum of the two assignment counts,
  treating a conflict as score `n+1`, then original M score, then index.
  The probe cannot assert SAT/UNSAT or skip a branch. All probe work is charged.
- **G** `gated_probe` (primary): same as P only if the two highest M
  occurrence counts at the root differ by **at most one**; otherwise use M
  immediately. The gate observes no labels or future search work.

The initial formula and all resource limits are fixed; there is no parameter
optimization or model training after seeing W042 labels/results. Eight
candidates, the tie gate and root-only scope are engineering choices to bound
overhead, not previously established optimal settings.

## Measured end points and falsification gate

For each policy/source, run three same-process timed attempts, rotate the
policy execution order by repeat, retain all raw nanoseconds and report the
median. Shared JSON/DIMACS loading is excluded from **all** policy timings;
each policy includes its own source-feature selection and probe cost. Record
clause visits, decisions, propagation assignments, nodes, probe calls,
SAT/UNSAT/CENSORED, and SAT witness. Cross-check verdict against publisher
label; recheck SAT assignments directly against original source clauses.
Use independent PySAT Glucose3 on every original CNF as an additional truth
control; neither source labels nor Glucose3 guide Witnora's decisions.

Primary, predeclared comparison is G versus M over all 64 source cases:

1. Compare **number solved at cap**, separately for SAT and UNSAT.
2. Use a capped work score (`clause visits` if solved, `2 * cap` if censored),
   and same cap-based PAR2-style total as primary work effect. A true win
   requires G solve at least as many instances *in each label stratum*,
   reduce the 64-case mean capped work by **at least 10%**, and not increase
   total summed median within-solver wall time. Otherwise reject the
   cost-effective improvement hypothesis for this frozen experiment.
3. Secondary: paired per-case work and wall ratios, per-stratum results,
   number of gate activations, full P versus M, D versus M, worst regressions.
   All censored runs and unfavorable cases must remain visible.

This is a **DPLL branching study**, not a comparison with competitive CDCL.
A positive result still requires new family-held-out confirmation and an
unmodified Kissat/CaDiCaL comparison before any external speedup language.
Any infrastructure repair after precommit must be identified as such, with
unchanged inputs, selection and metrics. No P-versus-NP claim is admissible.
