# Exact small-separator conditioning on connected ANF constraints

**Witnora · 2026-11-03 · draft PR #121**

Continuation of [violation-image ANF geometry](VIOLATION_IMAGE_ANF_GEOMETRY.md)
and the [exact structured ANF counter](../witnora_core/anf_structured_counter.py).
The previous experiment showed a ~73x exact model-counting gain on
**disconnected** 18-variable blocks. Here we test whether a bounded
separator search can recover some benefit in **connected** formulas.

## Exact construction

Let S be a small set of shared Boolean variables. If conditioning on
all bits of S leaves the residual equation system partitioned into
components E_1,...,E_t on pairwise disjoint variable sets, then

    #Z(E) = SUM_(s in {0,1}^S) #Z(E | S=s)

and for each branch

    #Z(E | S=s)
        = 2^(unconstrained residual variables)
          * PRODUCT_i #Z(E_i | S=s).

The first identity is Shannon decomposition. The second is the
disjoint-component multiplication identity underlying the
kernel-checked Lean theorem `ANFComponentFactor.splitCount_mul`.
No polynomial-time complexity guarantee follows: in general the outer
sum costs 2^|S| branches, and each residual solve may itself be hard.

New implementation
`witnora_core/anf_separator_conditioning.py`:

1. Compute exact equation scopes from the Boolean-ring ANF.
2. Deterministically test single- and then double-variable deletions;
   use a bounded candidate search (default 1,000 checks).
3. If deletion leaves at least two nonempty scope components, branch
   on every assignment to those separator variables.
4. Add explicit `x_v=0` or `x_v=1` *polynomial equality equations*
   for each branch. This prevents counting the fixed separator bits
   again as free variables.
5. Invoke the existing exact structured counter and sum branch counts.
   The state budget is shared across branches and fails closed.
6. If search finds nothing, fall back to the exact structured solver.

For more than 32 active variables, multi-variable candidate search
is intentionally limited to a high-degree pool. Hence `None` means
**no separator was found by this bounded heuristic**, never
a proof that no separator exists.

## Independent semantic controls

Five tests in
`tests/test_anf_separator_conditioning.py` passed:

- One shared bridge variable among three originally separate
  6-variable 3-CNF blocks; exact count matched a *separate local
  six-variable exhaustive oracle* and the previous structured solver.
- Two independent shared bridge variables, requiring two-bit
  conditioning; a one-bit search correctly found none on this test.
- A connected wide clause that cannot be split by the allowed small
  deletions, exercising exact fallback.
- The original four-clause adversarial parity collision still yields
  **one actual CNF model versus two sketch survivors**.
- Invalid literals, total-state budget exhaustion, scope-component
  calculations.

The connected planted examples consist of 3-CNF internal blocks
joined with **2-literal bridge clauses**; they are not claimed to be
uniform 3-CNF instances. Each independent per-block reference count
enumerates at most 64 assignments (six local variables), not the
19- or 26-variable global assignment space.

## Full measured performance, same GitHub runner

Frozen branch `formal/g14-python-seen-enqueue-v121`,
[full green CI #41684233632](https://github.com/joeyst8/witnora-core/actions/runs/41684233632).

Wall times are median of three `tracemalloc`-instrumented Python
runs on **identical source ANF equations**. The "conditioned" time
includes search overhead, branch generation, and all residual counts.
Both methods have a 5,000-state bounded-search limit.

| Connected planted source | Independent true #models | Structured states / ms | Conditioned states / ms | Selected bridge | Cost assessment |
|---|---:|---|---|---|---|
| 3 blocks, 1 bridge, 19 variables | 20,683 | 160 / 22.116 | 103 / 11.228 | (1), 2 branches | 1.97x faster |
| 4 blocks, 1 bridge, 25 variables | 541,441 | 342 / 62.427 | 136 / 16.322 | (1), 2 branches | 3.82x faster |
| 3 blocks, 2 bridges, 20 variables | 21,710 | 164 / 22.385 | 162 / 35.541 | (1,2), 4 branches | 1.59x slower |
| 4 blocks, 2 bridges, 26 variables | 551,522 | 347 / 63.301 | 212 / 70.051 | (1,2), 4 branches | 1.11x slower |

Even when two-bridge conditioning reduced the number of unique
states (347→212), the four branches and search overhead outweighed
those savings. The one-bridge gain is real for these constructions,
but is an instance-structural improvement, not an asymptotic
worst-case result.

### Negative controls: dense 8- and 10-variable source and sketch systems

Neither the source nor parity-sketch equations in these four
frozen dense SAT/UNSAT families yielded a separator of size <=2
under the completed small-case search. The method fell back
to the exact structured solver after checking 36 candidates at
8 variables or 55 candidates at 10 variables.

| Frozen source case | Structured source ms | Conditioned source ms | Structured sketch ms | Conditioned sketch ms |
|---|---:|---:|---:|---:|
| 8v/54c UNSAT | 3.870 | 7.029 | 5.636 | 9.950 |
| 8v/54c planted | 3.473 | 6.574 | 6.259 | 10.564 |
| 10v/66c UNSAT | 6.580 | 14.321 | 10.044 | 22.192 |
| 10v/66c planted | 6.617 | 14.755 | 15.085 | 28.413 |

Each source count matched an independent exhaustive small-instance
#SAT oracle; each sketch count matched its own independent
sketch-survivor oracle. The parity sketch is not generally equivalent
to the source CNF. All these dense cases show a **regression**
from unnecessary separator searching; they are not industrial
SAT comparisons.

## Trust boundary and next move

The exact disjoint-product identity is kernel-checked in Lean
(`formal/Witnora/ANFComponentFactor.lean`), and Python tests check
the conditioning mechanics on these frozen and adversarial cases.
However, a *universal Python-to-Lean refinement* of the
separator detector, pin serialization, Boolean-ring cofactors
and total budgeted solver has not been proved.

Next experiment: a conservative **adaptive admission rule** for
separator conditioning. It should assess a cheap upper bound on
search cost and predicted component payback, skip dense instances
when the heuristic is unlikely to help, and benchmark end-to-end
time/memory against the unchanged structured baseline. In
particular, a `k=2` separator is not automatically useful.

No general-purpose SAT solver, polynomial-time SAT or P vs NP
breakthrough is claimed.


## 2026-11-03 adaptive admission falsification (opt-in)

The follow-on experiment added an opt-in conservative admission policy
to count_common_zeros_conditioned, preserving the existing default.
Two independent checks govern admission:

1. If every active variable pair already appears together in an
   equation scope, the scope primal graph is complete. Deleting
   variables leaves the residual nonempty graph complete, so **no**
   small separator can produce two nonempty residual components.
   This is an exact structural no-cut shortcut, not a density guess.
2. Otherwise the existing bounded search runs. A discovered k-cut is
   admitted only when it exposes **more than 2^k residual components**.
   This is a conservative cost *heuristic*, not a runtime theorem.

The full existing general-CNF/Lean gate and eight ANF-separator tests
passed on draft PR #121, CI:
https://github.com/joeyst8/witnora-core/actions/runs/41709516550 .
Every compared source/sketch model count remained exactly unchanged.

**One-runner three-repeat median timings with tracemalloc (ms):**

| Construction | Direct structured | Original conditioned | New conservative | Interpretation |
| --- | ---: | ---: | ---: | --- |
| 1 bridge, 3 blocks | 30.949 | 15.799 | 15.755 | Useful 2-way conditioning retained |
| 1 bridge, 4 blocks | 83.472 | 22.542 | 23.628 | Useful 2-way conditioning retained |
| 2 bridges, 3 blocks | 30.713 | 50.814 | **61.847** | Rejecting after search is worse |
| 2 bridges, 4 blocks | 87.226 | 99.694 | **160.422** | Rejecting after search is much worse |
| Dense 10v/66c UNSAT source | 8.901 | 19.992 | 9.595 | Complete-primal shortcut avoids 55 scans |
| Dense 10v/66c UNSAT sketch | 13.993 | 31.642 | 15.605 | Complete-primal shortcut avoids 55 scans |

All eight dense source/sketch cases triggered the exact complete-primal
shortcut with **zero** cut candidates checked, compared with 36 or 55
candidates in the unmodified separator-search path. The other six
dense rows showed the same direction, with some residual cost from
building the clique certificate. These are exploratory small Python
timings, not statistical or general SAT results.

**Important negative finding:** a branch-count versus component-count
rule applied *after exhaustive pair search* can make performance worse,
even when it correctly predicts that four-way branching may not pay.
The 20- and 26-variable two-bridge cases still spent time on 210 and
351 candidate checks and then repeated the original structured
computation. The next admission rule must decide **before** pair search
whether that search deserves its cost, or share work with the solver.

This preserves the original checker and default algorithm, and does
not modify the proved restricted-family TC-063 Lean theorem.
