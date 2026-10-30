# Witnora research operator promotion protocol

This file defines a **claim boundary**, not a novelty announcement.

## States

1. `NO_SUPPORTED_OPERATOR_DISCOVERED`: the proposed family was not found
   in the supplied formula.
2. `RESEARCH_CANDIDATE_ONLY`: a candidate was found but the exact original
   source document were not supplied.
3. `SOURCE_BOUND_LEAN_PROOF_REJECTED`: the independent source-bound Lean
   gate failed or its attestation was incomplete.
4. `PROOF_VERIFIED_PER_INSTANCE_BENCHMARK_PENDING`: actual Lean execution
   checked the original document, canonicalization and the discovered spoke
   contradiction directly (an optional G5 certificate is also checked when provided).
   This proves **only the checked instance**, not the proposed general
   transformation, novelty, or superiority.

No state above automatically promotes an operator into the trusted library.

## Evidence required before future promotion

- **Soundness**: a kernel-checked *universal* preservation/soundness theorem
  for the proposed operation **and** source-bound checks on actual outputs.
- **Scope**: explicit domain of supported input formulas, rejection behavior
  outside that domain, and tests challenging that boundary.
- **Generality**: a parameterized family or independent test families, with
  examples beyond discovery seeds.
- **Performance**: reproducible experiments against at least an appropriate
  general SAT solver and a specialized baseline; include hardware details,
  preprocessing, certificate construction/check time and failure rates.
- **Novelty**: independent literature/prior-art review. The parity-spoke
  candidate is standard GF(2) elimination and **does not satisfy this**.
- **Reproducibility**: frozen benchmark instances, scripts, version pins,
  raw measurements and a stable evidence digest.

A positive benchmark or a forged JSON field must never substitute for Lean
acceptance. Equally, Lean acceptance alone does not establish a performance
advantage. Research claims must preserve both distinctions.

## Current implementation

- `witnora_core/spoke_discovery.py`: implied two-variable XOR discovery.
- `witnora_core/operator_promotion.py`: recomputes discovery, verifies
  source/canonical correspondence, then invokes the actual source-bound
  `verify_discovered_spoke_with_lean` gate; an optionally supplied G5
  certificate must independently pass its own Lean gate.
- `tests/test_operator_promotion.py`: missing provenance, fake status and
  fail-closed regression tests.
- `scripts/benchmark_spoke_collapse.py`: first exploratory comparison,
  not proof of superiority.

## Known open work

The general spoke contradiction theorem and a source-bound theorem connecting
four checked patterns in an arbitrary CNF are built in Lean. The executable
`SpokeDiscoverySpec.discoverFrom` filter also has universal output-soundness
and exact filter-membership theorems. The finite reference enumerator
`SpokeDiscoverySpec.allProposals` ranges over endpoint IDs, intermediate IDs
and all Boolean labels, and its coverage proof establishes that any proposal
within the supplied ID domain is included. `tests/test_spoke_discovery_reference.py`
compares Python output with an independently written exhaustive enumerator
on bounded randomized inputs. The production spoke gate additionally checks
exact Python binary-equation extraction against the executable Lean
`BinaryXorDiscovery.extract` specification for inputs with at most 24
variables. Lean proves this binary specification's complete pair/RHS
coverage and source-CNF soundness. These are checked-output guarantees,
not universal CPython execution refinement. The production
gate checks concrete discovered instances with this theorem; **universal
correctness and completeness of the Python detector's proposal enumeration** remains unproved. Universal Python interpreter
refinement and independent novelty audit also remain open.
