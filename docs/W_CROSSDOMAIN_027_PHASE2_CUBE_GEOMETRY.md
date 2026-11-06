# W027 Phase 2: parity-cube occupancy and adversarial soundness

## Mathematics and geometric connection

For a fixed triple of Boolean variables, the eight possible sign patterns
of a 3-CNF clause are the vertices of a three-dimensional Boolean cube.
The four corners with an even number of negative signs and the four with
an odd number are its two interleaved tetrahedra. Each *complete*
tetrahedron of four clauses logically entails one 3-XOR equation.

Incomplete tetrahedra do not justify a 3-XOR inference. A full eight-corner
cube entails both opposite parity equations and is therefore UNSAT.
Duplicate clauses do not alter the equation. The detector can safely
select one original source clause from each required corner even when
extra duplicates or opposite-parity corners are present.

This is established parity reasoning in a geometric representation, **not**
a newly discovered general SAT algorithm or a P versus NP result. Its
relevance is a more robust, source-certifying feature extractor for
the W027 solver pipeline.

## Correctness hypothesis and falsification

Enumerate **all 256 subsets** of the eight cube corners, with a duplicate
source clause added to every nonempty subset and source clauses reversed.
The independent Python harness and Rust unit test must establish:

1. Number of extracted XOR equations is exactly the number of complete
   parity tetrahedra (0, 1, or 2).
2. An UNSAT certificate is emitted only when the independent eight-state
   brute-force SAT oracle finds no satisfying assignment.
3. All returned contradiction source indices point to four actual input
   clauses per parity equation and pass the source-row XOR proof audit.
4. Deleting any one corner from the complete cube removes the UNSAT
   conclusion. Duplicate and partial patterns do not create false proofs.

This audit is a **logical correctness test**, not a throughput benchmark;
it does not amend the previously recorded W027 Phase-1 timings. Further
benchmarking must be prospective, pinned, and cost-inclusive.

## Prior work

- Rebola-Pardo et al., *DRAT Proofs for XOR Reasoning* (2016):
  https://repositum.tuwien.at/handle/20.500.12708/355
- *Certifying Parity Reasoning Efficiently Using Pseudo-Boolean Proofs*
  (AAAI 2021): https://ojs.aaai.org/index.php/AAAI/article/view/16494
- *SAT Solving Using XOR-OR-AND Normal Forms* (2024):
  https://link.springer.com/article/10.1007/s11786-024-00594-x

These references establish that XOR recovery and proof certification
already have a research history; our test evaluates this particular
small, explicit, source-indexed implementation.
