# R-111: native component-aware structured ANF zero counting

`anf_count_structured_native` ports the bounded Python structured ANF
counter. It retains canonical equation systems, free-variable multipliers,
unit-forcing, scope-component splits, cached cofactors, Shannon pivots and
all eight result/statistic fields. Counts are arbitrary-width integers.

`count_common_zeros_structured(..., backend="rust")` is optional; Python
remains the reference. The focused CI includes 200 seeded finite systems,
search-budget exhaustion, exact counter statistics, and 180 free variables.

This remains exponential in general. It does not prove TC-063 or make a
complexity-theory breakthrough, and no Lean theorem is changed.
