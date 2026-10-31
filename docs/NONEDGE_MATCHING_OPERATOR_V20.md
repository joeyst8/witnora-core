# Nonedge-matching coloring operator — v20 experiment

**Status:** exploratory research branch; not promoted, not Lean-verified, not literature/novelty-verified.

## Construction

For a finite simple graph \(G=(V,E)\), choose a vertex cover \(S\). The outside \(V\setminus S\) is independent. Choose a maximum matching \(M\) in the **nonedges** of the induced graph \(G[S]\). Each pair of \(M\) can share one color; every remaining vertex of \(S\) receives its own color; all vertices outside \(S\) share one additional color when the outside is nonempty.

This yields the explicit, computationally testable upper bound

\[
\chi(G)\le B_M(G):=
\min_{S\text{ vertex cover}}
\bigl(|S|-\nu(\overline{G[S]})+\mathbf1_{V\setminus S\ne\varnothing}\bigr).
\]

The program returns a concrete proper coloring witness, checks every edge, and enumerates the covers and nonedge matchings exactly for \(n\le 11\). The short argument above is a **human mathematical construction**, not a Lean kernel proof.

## Adversarial baseline

The starting baseline is \(B_0=\max(\tau,\omega)\), whose chromatic upper-bound property has previously been proved in the separate Lean work. To challenge the matching mechanism, use the stronger classical combination

\[
B_{\mathrm{strong}}=\min\left(
 B_0,\
 \max_{C\in\operatorname{components}(G)}\max(\tau(C),\omega(C)),\
 \Delta(G)+1
\right).
\]

Here \(\Delta\) is **maximum degree**, stored as the legacy field `delta` in the graph metrics code. The hybrid is \(\min(B_M,B_{\mathrm{strong}})\).

## Predeclared finite run

The GitHub Actions run on 2026-10-31 passed unit tests and the full experiment, enumerating **33,867 labeled graphs with 1–6 vertices** and running **454 deterministic holdout/special graphs with up to 11 vertices**.

| Measure | Exhaustive | Holdout |
| --- | ---: | ---: |
| Graphs | 33,867 | 454 |
| Connected graphs | 27,476 | 325 |
| \(B_M<B_0\) | 2,740 | 208 |
| \(B_M<B_{\mathrm{strong}}\) | 2,730 | 195 |
| Connected with \(B_M<B_{\mathrm{strong}}\) | 2,730 | 181 |
| \(B_{\mathrm{strong}}=\chi\) | 29,177 | 234 |
| \(\min(B_M,B_{\mathrm{strong}})=\chi\) | 31,907 | 391 |
| Invalid upper-bound instances | 0 | 0 |

The first improvement over the *weak* baseline is two disconnected triangles. This is **not** evidence of a new structural insight, since componentwise coloring already handles it. The connected and stronger-baseline counts are the more informative falsification tests.

**Counterexample to exactness:** three disjoint edges (a matching on six vertices) have \(\chi=2\), whereas both \(B_M\) and \(B_0\) give 3. Thus the matching operator is not an exact chromatic-number formula.

## Interpretation and limits

The results show a repeatable improvement over these *specific* classical baselines. They do **not** imply improvement over the strongest known coloring bounds, novelty of the formula, or a breakthrough. The operator only merges color classes of size two inside one vertex cover plus at most one independent outside class; this restricted class of colorings is a plausible source of its failures.

Next: compare against established matching/complement-cover coloring bounds from the literature; independently audit the constructive proof; formalize the bound and its concrete witness validity in Lean if it survives that comparison. Keep this draft PR separate from the Lean-verified theorem branch until those gates are met.

## Reproduction

Run `PYTHONPATH=. python -m unittest tests.test_nonedge_matching_bound -v` and `PYTHONPATH=. python scripts/experiment_nonedge_matching_bound.py`. CI uploads `nonedge-matching-bound-ledger.json` as an experiment artifact. This report records the fixed, finite test design and its results; no statistical generalization beyond that design is claimed.
