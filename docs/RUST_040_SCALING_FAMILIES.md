# R-040: native fixed-separator XOR scaling families

**Green full CI:** https://github.com/joeyst8/witnora-core/actions/runs/41771639708

## Migration

Previously untouched `witnora_core/separator_scaling_families.py`
now has an independent native Rust implementation in
`rust/witnora-ve/src/scaling_families.rs`.

It reproduces the original deterministic finite family builder:
two sides of private variable pairs, a common 2- or 3-variable
boundary, alternating binary parity right-hand sides, full
exact forbidden-assignment XOR CNF encoding, canonical clause order
and the original metadata. The Python `make_scaling_case_rust`
adapter is opt-in; default callers and Lean proof boundaries are
untouched.

## Verification evidence

`tests/test_scaling_families_rust.py` compares **all 256 permitted**
`blocks_per_side`/boundary-width inputs against the exact Python
CNF and metadata, including the canonical source SHA-256.
It also tests **800 independent sampled assignments** against
their defining parity equations and invalid-grid rejection.
The full native compiler, Python differential and Ganak workflow
passed.

The generator creates finite benchmarks; it does not establish
SAT hardness or a novel complexity theorem.

## Inventory

**28** original Python modules have partial parallel Rust
counterparts, **532** original Python files remain not migrated,
and **0** originals have been removed or retired.
