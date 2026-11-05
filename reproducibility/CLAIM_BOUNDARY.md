# Claim Boundary

## Allowed Claims

- Witnora-Core externally DRAT-verifies the recorded official CNFgen Tseitin
  rows, including `tseitin_20 c=2`, using exact CNF XOR extraction and
  deterministic sparse/min-fill XOR proof export against `original.dimacs`.
- The v0.8.4 baseline had no Tseitin collapse under the recorded diagnostic.
- The v0.9.8 artifact verifies 7 recorded Tseitin rows externally.
- Native XOR traces are independently replayed, while original-CNF UNSAT is
  counted as externally verified only when real `drat-trim` accepts
  `proof.drat`.
- The row-width cap transition for `tseitin_20 c=2` is explicit: default cap 8
  is native-only, medium cap 10 is externally verified.

## Forbidden Claims

- No parity support claim.
- No broad XOR extraction claim.
- No CryptoMiniSat-style claim.
- No competitive SAT solver claim.
- No industrial benchmark claim.
- No full DRAT/RAT/LRAT/FRAT claim.
- No P vs NP claim.
- No `HARD` or `UNKNOWN` statuses.

## Wording Guidance

Prefer:

- recorded diagnostic,
- official CNFgen-generated Tseitin rows,
- externally verified for the tested matrix,
- exact-pattern XOR extraction,
- bounded result,
- certified systems prototype,
- collapse-path framework.

Avoid:

- solves SAT,
- solves Tseitin generally,
- solves parity,
- state of the art,
- industrial relevance,
- unqualified proof-system support.
