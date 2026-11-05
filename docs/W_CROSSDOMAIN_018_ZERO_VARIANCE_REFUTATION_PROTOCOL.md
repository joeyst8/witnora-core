# W-CROSSDOMAIN-018: zero-variance algebraic UNSAT certificates

Status: prospective protocol, frozen *before* the Rust W-018 experiment.
Parent discovery: `W_CROSSDOMAIN_017_SIGNED_COVARIANCE_RESULTS.md`.

## Research question and claim boundary

Can Witnora use the signed violation covariance of a 3-CNF formula to
construct exact, independently checkable UNSAT certificates, rather than
weak predictions of DPLL search cost?

Let `v_i(x)` be the 0/1 violation indicator of clause `i`,
`K_ij=64 Cov_unif(v_i,v_j)` and `w` a *rational* column vector.
Because `K` is a covariance matrix, `K w=0` implies
`Var(sum_i w_i v_i)=0`. Then all assignments satisfy the exact identity

`sum_i w_i v_i(x) = (sum_i w_i)/8`.

If `sum_i w_i != 0`, no assignment can satisfy every clause. Thus
`K w=0` and `sum(w)!=0` constitute a sound UNSAT certificate.
Its verification requires only exact integer arithmetic after clearing
denominators. A missing certificate does **not** imply satisfiability.

This construction is a *constant-coefficient low-degree linear
combination of Boolean clause polynomials*, closely related to
polynomial calculus / Nullstellensatz proof systems. It is not a new
general-purpose polynomial SAT algorithm or proof of P=NP. In particular,
some unsatisfiable formulas have no such degree-3 constant-coefficient
refutation and need stronger algebraic methods.

## Frozen benchmark families

Each family has 32 formulas of 12 variables; xorshift32 generator and
distinct-variable/sign sampling match W-017 but **seeds differ**:

| Family | Base seed | Clauses | Truth status |
| --- | --- | ---: | --- |
| Fresh planted 3-CNF | `0xD18C0DE1` | 48 | SAT, all-zero assignment |
| Fresh uniform 3-CNF | `0xD18C0DE2` | 48 | unknown until exhaustive oracle |
| Complete eight-pattern contradiction + random tail | `0xD18C0DE3` | 56 | UNSAT |
| Four parity-equation inconsistent cycle + random tail | `0xD18C0DE4` | 64 | UNSAT |

For case `i` (zero-indexed), initialize RNG with
`seed ^ ((i+1) * 0x9E3779B9 mod 2^32)`.
Generate random 3-clauses as W-017. For planted formulas reject a
clause if all literals are positive; this makes the all-false assignment
solve every clause. For the full eight-pattern contradiction, prepend
the eight possible sign patterns of `(1,2,3)`, then add random clauses.

The parity-cycle source prepends four 3-XOR equations, each translated
to **exactly four** 3-CNF clauses (one for each forbidden parity
assignment), then 48 random 3-CNF clauses. The equations are:

`x1 xor x2 xor x3 = 0`

`x1 xor x4 xor x5 = 0`

`x2 xor x4 xor x6 = 0`

`x3 xor x5 xor x6 = 1`

XORing all four left-hand sides cancels every variable but the right
sides XOR to 1, so this family is UNSAT without a local eight-pattern
block. Its four independent cubic Fourier characters cannot cancel
using constant-coefficient group weights; the expected result is **no
zero-variance certificate**. This is a critical non-universality control.

## Fixed verification and falsification criteria

1. Implement integer nullspace extraction against `K` in Rust. Do not
   accept floating point, modular-field or approximate-zero witnesses.
   Emit integral weights and verify `K w=0` with an independent loop.
2. For every certificate, verify `sum(w)!=0`, and check exhaustively
   that weighted violated-clause energy is constant across all 4096
   assignments. No certificate may appear on a satisfiable instance.
3. For all 128 instances, independently enumerate SAT/UNSAT and report
   certificate detection by family; no solver-speed claims.
4. For controls indices `0,1,31` of all families, Python independently
   rebuilds source, `K`, truth status and verifies every Rust witness.
5. In particular: the complete eight-pattern UNSAT family should be
   detected; the parity-cycle UNSAT family should **not** be silently
   reported as SAT when this sufficient test fails.
6. Pass the Rust focused GitHub CI and native suite before treating the
   experiment as verified. Negative findings must be preserved.

Related established research to compare carefully: Nullstellensatz and
polynomial calculus proof complexity, Sherali–Adams and sum-of-squares.
