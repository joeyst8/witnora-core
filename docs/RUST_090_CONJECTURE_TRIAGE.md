# R-090: end-to-end conservative conjecture triage in Rust

Extends earlier R-061 native identity normalization/catalog with native
classification of conjecture survivors, bounded expression evaluation on
adversarial graph metrics, first falsifying witness, and deterministic sorting.
The Python entry point now accepts `backend="rust"`, using the R-088 native
expression search and new R-090 triage. Seeded graph sampling remains frozen
in Python to preserve the reference experiment. Python remains the default.

The native wheel gate compares three full studies, plus known-identity,
unclassified-survivor, and falsified-witness controls. No automatically
surviving identity is treated as a proof or a novel mathematical claim.

Status: awaiting compiled native CI.
