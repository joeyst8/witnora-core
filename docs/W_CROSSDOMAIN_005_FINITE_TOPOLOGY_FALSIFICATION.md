# W-CROSSDOMAIN-005 — Complete finite topology/counting controls

**Status:** exact Python research-oracle experiment passed locally; no Rust
runtime benchmark, novel #SAT theorem, or solver speedup is claimed.

## Experiment

Enumerate all `C(15,7)=6,435` labeled seven-edge simple graphs on six
vertices. For each connected graph, interpret every edge `(u,v)` as a
positive binary CNF clause `(u OR v)`, and independently compute:

- minimum primal-graph separator size up to two;
- first mod-2 Betti number of the primal graph's *flag complex*;
- exact #SAT by all 64 original-variable assignments.

All **5,700** connected graphs are accounted for. The reproducible reference
script is `scripts/benchmark_topology_finite_controls.py`; its regression is
`tests/test_topology_finite_controls.py`.

| Separator size | Flag beta1 | Labeled graphs | Exact model-count range |
| ---: | ---: | ---: | ---: |
| 1 | 0 | 2700 | 15–21 |
| 1 | 1 | 1980 | 17–18 |
| 1 | 2 | 300 | 18–20 |
| 2 | 1 | 360 | exactly 16 |
| 2 | 2 | 360 | exactly 17 |

The separator-two groups consist of **one** and **two** unlabeled graph
isomorphism classes, respectively. The 720 labeled examples are therefore
not 720 independent pieces of evidence. This exact finite coincidence is
not an asymptotic complexity theorem.

## Mandatory signed-polarity negative control

For a representative graph from each separator-two topology group, enumerate
every `4^7 = 16,384` choice of the two literal signs on its seven clauses,
holding the underlying graph, density, separator size and flag beta1 fixed.

- beta1=1 representative: possible #SAT counts **1 through 16**;
- beta1=2 representative: counts **1 through 15, and 17**.

The ranges overlap heavily. Consequently, **these graph features cannot
determine model count**, even on this fixed tiny graph family once the
constraint polarities change. This is consistent with W-CROSSDOMAIN-002's
stronger same-graph XOR SAT-versus-UNSAT control.

## Interpretation and next gate

This study found a narrow correlation in monotone binary clauses, and then
deliberately falsified a stronger interpretation under sign changes. The
correct research direction is to examine *labeled semantic interactions*,
not promote beta1 alone to a solver oracle. Next: sufficiently large,
held-out signed-CNF families, multiple solver implementations, matched
structural covariates and independent exact counts. Record all failures and
timeouts; do not extrapolate from six-variable enumeration.

Prior art: structural model-counting methods using graph decompositions are
well established (Samer/Szeider, 2010):
https://www.ac.tuwien.ac.at/files/pub/SamerSzeider10.pdf .

The script is Python research orchestration; Witnora's structural diagnostic
remains Rust-first. No source verifier or native-default production route is
altered by this experiment.
