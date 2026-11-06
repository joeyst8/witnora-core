# W-CROSSDOMAIN-025: exact gauge holonomy and finite-temperature partition functions

## Result: verified known physics applied to Witnora

W025's prospective protocol was committed as 50cbb37a14fafbe95978e8a59e1ac2c08425eb46 before the experiment. After restoring the full repository tree, the [dedicated W025 workflow](https://github.com/joeyst8/witnora-core/actions/runs/42133492427) and [archival rerun](https://github.com/joeyst8/witnora-core/actions/runs/42133987931) completed **successfully** (Rust tests, independent Python audit, raw artifact).

This is a controlled mathematical connection, **not** a new SAT algorithm, complexity separation, or demonstrated solver speedup. The 64 variable relabelings and 16 gauge transformations per relabeling are **symmetry controls**, not independent samples.

## Physical encoding and observable

Map each Boolean bit to a spin, \(\sigma_i=(-1)^{x_i}\). Each XOR equation on three variables has coupling \(J_e=(-1)^{b_e}\). Define the spin Hamiltonian

\[
H(\sigma)=-\sum_{e=1}^{5} J_e \prod_{i\in e}\sigma_i.
\]

The four dependent XOR equations form an even-incidence hypergraph cycle. Its **gauge-invariant holonomy** is the product of the four couplings. It is \(h=+1\) for the SAT partner and \(h=-1\) for the UNSAT partner. Simultaneous spin and coupling sign changes cannot alter it because every variable occurs an even number of times in the cycle.

The exact high-temperature identity is

\[
Z_h(\beta)=2^9\cosh(\beta)^5\left(1+h\tanh(\beta)^4\right).
\]

The identity follows by expanding each interaction factor, then summing over spin assignments. Every nonempty term vanishes unless each variable has even total incidence. There is only one nonempty surviving source-edge subset, the dependent four-cycle.

## Measured and independently checked exact outcomes

| Observable | SAT partner | UNSAT partner |
| --- | ---: | ---: |
| Gauge-invariant loop holonomy | \(+1\) | \(-1\) |
| Ground-state energy, \(H_{\min}\) | \(-5\) | \(-3\) |
| Number of ground states | 32 | 128 |
| Exact finite-temperature partition function | \(2^9\cosh^5\beta(1+\tanh^4\beta)\) | \(2^9\cosh^5\beta(1-\tanh^4\beta)\) |

At \(\beta=1\), the SAT-to-UNSAT partition-function ratio is **2.01399895996**. Both sides have \(Z(0)=512\); the difference increases with inverse temperature because the UNSAT instance must violate at least one parity equation.

The Rust program exhaustively enumerated all \(2^9=512\) spin assignments per formula. It verified six inverse temperatures \(\beta\in\{0,0.25,0.5,1,2,4\}\), all 64 paired relabelings, and all 16 registered gauge masks per pair. Independent Python code recalculated spin energy histograms directly from the relabeled source triples and matched the Rust outputs.

### Reproduction and raw evidence

- [Rust source](../rust/witnora-ve/src/bin/witnora_spin_holonomy.rs).
- [Independent Python audit](../tests/test_spin_holonomy_rust.py).
- [GitHub Actions W025 PASS](https://github.com/joeyst8/witnora-core/actions/runs/42133492427).
- [W025 original raw JSON artifact](https://github.com/joeyst8/witnora-core/actions/runs/42133492427/artifacts/13463988340), with artifact ZIP SHA-256 b341aa03ba5ce89746406b1c9a7769aa6437d293578d24162687c497ed0f900e.
- Permanent original Rust JSON: [research/results/w025_spin_holonomy.json](../research/results/w025_spin_holonomy.json), recovered from the verified Rust workflow's evidence log and independently JSON-parsed (64 cases, 16 gauge masks each).

## Interpretation and next experiment

W024 showed ordinary signed pairwise geometry is exactly blind to this pair. W025 supplies an intuitive physics explanation: **local pairwise observations miss a global frustrated cycle**. The missing signal is not a magical frequency but a gauge-invariant product over a closed XOR dependency.

This is established XOR-SAT/spin-glass mathematics, for example [statistical physics of random XOR-SAT](https://arxiv.org/abs/cond-mat/0103200) and [dynamical cavity methods for k-XOR-SAT](https://arxiv.org/abs/2412.14794).

The next experiment, W026, should evaluate whether finding these higher-order loop signals has **net computational value** in mixed CNF, including the cost of recognizing parity structure. Benchmark against direct XOR/GF(2) solvers and standard SAT search on heldout problems, rather than treating a successful representation as an automatic runtime advantage.
