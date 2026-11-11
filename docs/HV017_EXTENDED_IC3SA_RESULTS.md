# HV-017 — 120-second published IC3SA control

**Predeclared:** [HV017_EXTENDED_IC3SA_PROTOCOL.md](HV017_EXTENDED_IC3SA_PROTOCOL.md). **Result:** [hv017_extended_ic3sa.json](../research/results/hv017_extended_ic3sa.json).

Pono 2.0 (commit `c81aa36`) / Bitwuzla 0.8.2-dev, operating on the **unchanged** SoSy-Lab HKU HLS array model (SHA256 `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`), was run once with:

`--engine ic3sa --bound 1000000 --smt-solver bzla --show-invar`

The shell enforced a **120-second wall timeout** and **2 GiB virtual-memory address-space cap**. **Exit 124** from GNU `timeout`, with no stdout/stderr verdict and no invariant, means **UNKNOWN at the cutoff**. This extends the HV-016 20-second UNKNOWN but is *not* an impossibility result for any solver. It is not evidence that Witnora has a solver, proof, speedup, or novel algorithm. It establishes a useful incumbent reference for this exact resource-limited research task.

Next diagnostic: separate the elementary control-state one-hot invariant from the unsuccessful combined handwritten H1/H3 property witness. An independently checkable one-hot proof could be a building block, but would not certify the original chip property or count as novel mathematics.
