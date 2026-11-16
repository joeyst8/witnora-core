# HV-018 — One-hot controller lemma isolated successfully

**Predeclared protocol:** [HV018_FSM_ONEHOT_ISOLATION_PROTOCOL.md](HV018_FSM_ONEHOT_ISOLATION_PROTOCOL.md). **Generator:** [hv018_fsm_onehot_queries.py](../research/hv018_fsm_onehot_queries.py). **Raw digests/verdicts:** [hv018_fsm_onehot_isolation.json](../research/results/hv018_fsm_onehot_isolation.json).

On the unmodified SHA-pinned HKU HLS array transition system, original node 99 defines legal one-hot FSM states and node 100 its violation. We derived three combinational BTOR2 obligations from the previously audited mechanical HV-010 unroller. Only the **queries** were modified; source transition/init clauses were untouched.

| Query | Exact mathematical obligation | Bitwuzla 0.6.1 outcome | SHA256 |
| --- | --- | --- | --- |
| Base | `Init(s) ∧ illegal(s)` | **UNSAT** (bad 382) | `4af7a74075afd41ec1d396ab294aab57fc9ae45cae797c2b001f8907ab51aa99` |
| Inductive step | `legal(s) ∧ T(s,i,s') ∧ illegal(s')` | **UNSAT** (bad 792) | `0cb26138d4570c3ce65c314891664ee24e1574d5781b07b5f2bbab2d632b7760` |
| Positive control | `T(s,i,s') ∧ illegal(s)`, no initial or legality assumption | **SAT** (bad 790) | `871103af789b60fc536be8266f65dd88d3996b43662786a4cbf0a3e3d95bc4e5` |

Each ran under a 20-second cutoff and 2 GiB virtual-memory cap, with process exit 0. The base and step checks together establish an SMT-checked **1-inductive** controller-only lemma under the modeled transition semantics, subject to solver soundness. This is a genuine validation of an intermediate fact, but **not a newly discovered algorithm** and **not an independently Cerbtora-accepted proof of original bad 48**.

The failed combined HV-014 H3 witness therefore cannot be attributed to lack of inductiveness of the one-hot condition *alone*; its additional result-latch condition H1, or interactions in the conjunction, remain unresolved. Next strictly separate test: add only this proved controller lemma to the original bad-state induction step and see whether it suffices. If not, investigate reachable data-path relationships rather than inventing more informal invariants.
