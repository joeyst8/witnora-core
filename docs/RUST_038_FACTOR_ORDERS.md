# R-038: native scope-aware graph elimination order experiments

**Verified green:** https://github.com/joeyst8/witnora-core/actions/runs/41770204244

## Migration

Previously untouched `witnora_core/factor_elimination_orders.py`
has an independent native counterpart in
`rust/witnora-ve/src/order_experiments.rs` that implements:

- Minimum-degree greedy elimination.
- Source-variable-first and auxiliary-variable-first staged orders.
- Limited-beam minimum-fill tie-breaking.
- Induced graph width and exact count of added undirected fill edges.
- Independent full permutation replay of elimination width.

PyO3 exports `factor_elimination_order_native` and
`replay_factor_elimination_width_native`; Python opt-in adapters
return the original `OrderResult` data shape.

## Tests and limits

`tests/test_factor_orders_rust.py` compares **1,600** seeded
graph/order/mode cases against the original Python heuristics,
independently replays their widths and checks invalid mode,
beam, domain and permutation rejection. The whole Rust/Python/Ganak
suite passed.

This is graph-fill experimentation, **not** a proof of SAT-solving
complexity, tensor contraction width or a novel algorithm. Rust's
opt-in implementation bounds its variable universe at 10,000 to
avoid unbounded allocation. Python remains the default reference;
Lean trust is unchanged.

## Inventory

**26** parallel-reference original Python modules, **534**
not-migrated originals, **0** original files retired.
