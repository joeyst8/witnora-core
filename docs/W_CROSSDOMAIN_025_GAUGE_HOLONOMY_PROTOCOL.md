# W-CROSSDOMAIN-025: preregistered spin-glass gauge holonomy experiment

Status: prospective, to be committed before the W025 implementation.

## Question and scientific boundary

W024 found a constructed pair of SAT and UNSAT 3-XOR CNFs with exactly
matched first- and second-order signed-incidence statistics. Can a
**gauge-invariant loop frustration** observable from statistical physics
recover their distinction and, more demanding, predict their **entire
finite-temperature partition function** without enumerating all spin
assignments?

XOR-SAT/Ising mappings, frustrated cycles, gauge symmetry, and the
high-temperature expansion are established mathematics and physics.
This experiment is a cross-domain consistency test and representation
design exercise, not an original spin-glass theorem, a new algorithmic
speedup, or a claim about P versus NP.

## Frozen source and 64 paired controls

Reuse W024's five source hyperedges over nine variables:
`(1,2,3), (1,4,5), (2,4,6), (3,5,6), (7,8,9)`.
Use RHS `b_S=(0,0,0,0,1)` and `b_U=(0,0,0,1,0)`, respectively.
Couplings `J_e=(-1)^(b_e)`, spin values `sigma_i in {-1,+1}` and
Hamiltonian `H(sigma)=-sum_e J_e product_{i in e} sigma_i`.
For every index `i in 0..64`, use the same xorshift32 and Fisher–Yates
variable relabeling of W024, seed
`0xD24F0240 ^ ((i+1)*0x9E3779B9) mod 2^32`. Clause shuffling is
irrelevant to the source hypergraph; report five source hyperedges.

## Frozen gauge interventions

For each paired relabeling, run 16 deterministic local spin-gauge flips
`j=0..15`, with 9-bit gauge mask
`(((i+1)*0x9E3779B9) ^ ((j+1)*0x85EBCA6B) ^ 0x02502425) & 0x1FF`.
Apply the same mask to both sides. Gauge variable redefinition sends
`J_e -> J_e * product_{i in e} g_i` where `g_i=-1` for flipped bits;
this must leave the energy distribution and partition function unchanged.

## Precommitted exact claims and tests

1. Find **all nonempty subsets** of the five source hyperedges with
   symmetric difference zero, directly from source variable masks.
   Require exactly one such nonempty subset, namely the four-edge
   dependent cycle; do not hardcode the cycle in its detector.
2. Its holonomy `h=product_{e in cycle} J_e` is `+1` for SAT and
   `-1` for UNSAT, even after any registered gauge transformation.
3. For beta in `{0, 0.25, 0.5, 1, 2, 4}`, compare the independently
   enumerated `Z(beta)=sum_{sigma in {-1,+1}^9} exp(-beta H(sigma))`
   to the high-temperature analytical expression

   `Z_h(beta)=2^9 * cosh(beta)^5 * (1 + h * tanh(beta)^4)`.

   Require relative difference under `1e-10` for both partners and
   all 64 relabelings / 16 gauge interventions.
4. Enumerate all 512 spin assignments per case and require minimum
   Hamiltonian `-5` (SAT), `-3` (UNSAT); require the ground-state
   degeneracies `32` and `128`, respectively. Check the complete
   energy histogram is gauge-invariant.
5. Independent Python audit reconstructs the source hypergraph,
   cycle, couplings, 64 relabelings and 16 gauge masks and verifies
   exact energy histograms, holonomy and selected `Z` values without
   relying on Rust correctness labels. Save complete Rust raw JSON.

The 64 relabelings and 16 gauge transformations are **symmetry
controls**, not 1,024 independent draws. They test implementation
correctness and invariance rather than generalization to hard SAT.

## Interpretation

The four-cycle sign product is a gauge-invariant, constraint-indexed
higher-order statistic. The formula for `Z` follows by expanding
`exp(beta J prod sigma)=cosh(beta)(1+J tanh(beta) prod sigma)`;
only subsets where each variable occurs an even number of times
survive the sum over spins. In this exact instance, the surviving
subsets are only the empty set and the four-cycle.

Literature context: statistical-physics treatments of XOR-SAT and
diluted spin glasses, e.g. https://arxiv.org/abs/cond-mat/0103200;
recent dynamical cavity work on k-XOR-SAT/p-spin systems,
https://arxiv.org/abs/2412.14794. Historical gauge frustration and
high-temperature loop expansions are well established.
