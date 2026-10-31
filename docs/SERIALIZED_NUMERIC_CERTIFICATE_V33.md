# Serialized numeric certificate experiment (v33)

Draft PR #34, based on numeric bridge PR #33.

## Text format

`N|K|u,v;u,v|c0,c1,...|q0,q1,...`

- `N` and `K` are the largest vertex and color IDs, so actual counts are `N+1` and `K+1`.
- Edge pairs are separated by `;`, endpoints by `,`. The empty edge field is permitted.
- Color and clique lists use `,` separators.
- Naturals must be canonically decimal: no leading zeroes, signs, or spaces.
- A parsed certificate is still rejected if the existing numeric range, length, coloring, or clique checker fails.

## Trust audit

The general theorem `checked_serialized_sound` proves that **if** Lean's parser returns given data and the serialized checker returns true, then that decoded graph has chromatic number `K+1`. The theorem's axiom report is only `propext`, `Classical.choice`, `Quot.sound`.

The concrete triangle and malformed-input regression tests are executable Lean examples using `native_decide`. The concrete optimality theorem therefore additionally depends on **`Lean.ofReduceBool`**, an axiom used by native evaluation. That is **not a kernel-only evaluation proof** for the actual string. This distinction is deliberate and must remain visible. No `sorry` or user-declared axioms were introduced.

## Limitations and next work

This is a Lean `String` parser, not yet a byte-level verified parser or a proof of Python's serializer/refinement. The next trust milestone is to replace native evaluation assumptions for concrete files with a fully reflected/kernel-checked parse trace or an explicitly trusted-bytes-to-data bridge, then run deterministic/adversarial fuzzing of serialized cases. Nothing here proves TC-063, G5, or G14.
