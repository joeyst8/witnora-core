# W-CRC-007: false independence of disjoint sign-exception clusters

**Status:** falsification / negative mathematical result on draft PR #122.
The executable regression is in tests/test_crc_conflict_oracle.py.
The method and source semantics remain unchanged; this explicitly
prevents a tempting but incorrect shortcut.

## A six-variable exact counterexample

Let F0 consist of **every all-positive three-literal clause** on
variables 1,...,6 (20 source clauses). A satisfying assignment has
at most two false variables, so

    Z0 = 1 + 6 + C(6,2) = 22.

Introduce two exceptional clauses on disjoint variable sets:

    E1 = (not x1) OR x2 OR x3,   A1={1,2,3}
    E2 = (not x4) OR x5 OR x6,   A2={4,5,6}.

Each exception rules out exactly one F0 model: respectively the
assignments with false bits {2,3} and {5,6}. Those excluded models
are distinct, so exact source counts are

    Z(F0 AND E1) = 21,
    Z(F0 AND E2) = 21,
    Z(F0 AND E1 AND E2) = 20.

A naive independence assumption under the F0 model distribution
would predict

    Z_independent = Z(F0 AND E1) * Z(F0 AND E2) / Z(F0)
                  = (21*21)/22
                  = 441/22 != 20.

The integer interaction witness is

    Z0*Z12 - Z1*Z2 = 22*20 - 21*21 = -1 != 0.

Thus disjoint **exception scopes** do not imply independent
acceptance under a globally coupling coherent source CNF. The
complete three-clause source is already globally connected; it
correlates the two variable groups.

The source-CNF-backed exact W-CRC-006 oracle returns 20 here.
An independent exhaustive 64-assignment oracle checks all four
integers. The regression leaves the false multiplicative prediction
as an asserted *non*-equality. Full external W-CRC suite:
https://github.com/joeyst8/witnora-core/actions/runs/41712957364 .

## Correct algebraic boundary

For disjoint exception sets A1, A2, their standalone predicates
g1(x_A1),g2(x_A2) factor exactly. Their Walsh transforms also
factor. But the *base* indicator f(x) may correlate A1 and A2.

    Fourier(f*g1*g2,T)
       = SUM_{U1 subseteq A1, U2 subseteq A2}
           Fourier(g1,U1) Fourier(g2,U2)
           Fourier(f,T XOR U1 XOR U2).

The base response at combined mode U1 XOR U2 cannot generally be
reconstructed from separate marginal mode responses by simple
multiplication. The exact W-CRC-006 convolution already retains
those cross interactions, which is why it succeeds on this
counterexample.

**Negative conclusion:** grouping exceptional clauses by disconnected
exception-variable scopes is insufficient to justify multiplying
sub-counts or discarding cross-Walsh coefficient queries. Any
cluster-acceleration rule requires a *source-aware* independence
certificate, such as actual factorization of the full conditioned
base response, or must retain the cross modes.

## Next experiment

Define an explicit source-relative interaction diagnostic for two
exception predicates:

    I_f(g1,g2) = Z(f)*Z(f*g1*g2)
                 - Z(f*g1)*Z(f*g2).

A nonzero value is a rigorous witness that the proposed factorization
is invalid for that input. Zero in one pair is not sufficient to
certify all higher-order factorization across more clusters.

Next, search for tractable **certificates** of factorization over
exception clusters, e.g. exact source primal separation after a
small conditioned cut, or a provably factorized Walsh response.
Compare any resulting speed gain against the exact unclustered
W-CRC-006 oracle and Ganak, with total source-to-count runtime,
memory and fail-closed budgets. The default must remain the
exact cross-mode convolution until those obligations are met.

This is classical conditional dependence and Fourier analysis,
not a claim of a new complexity theorem or P-vs-NP result.
