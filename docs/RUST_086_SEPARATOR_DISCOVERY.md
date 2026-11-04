# R-086: exact bounded source-primal separator search

The native Rust counterpart builds the source primal graph from normalized
clause scopes, performs ordered split-vertex augmenting-path max flow, and
extracts a minimum nonterminal A/B vertex cut under the original edge and
separator budgets. It preserves insertion order in residual adjacency lists
so the chosen cut and augmentation count reproduce Python for tied cuts.

Python retains the default reference, source-witness checks, independent
primal reachability check and a separately checked R-076 source-conditioned
independence certificate. A native cut is not accepted without that certificate.

Focused differential cases: 180 seeded source graphs, direct group edges,
disconnected cases, high-capacity terminal arcs, invalid witnesses and budgets.
This is standard graph max flow, not a general #SAT speedup or a Lean proof.

Status: focused native CI pending.
