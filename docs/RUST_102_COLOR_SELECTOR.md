# R-102: Rust frozen repair selector features

The Rust `color_selector_signals_native` and
`color_selector_triggers_native` functions compute the exact color-class
features and all ten predeclared selection rules. The Python-facing API
offers `backend="rust"` on `signals`, `triggers`, and experiment helpers.

Graph generation, training/holdout partitioning, model selection,
confusion-matrix aggregation, and timing remain in Python. Tests compare
features and every decision to the Python reference on seeded graphs.

Selection rules are heuristics. This migration makes no claim of
generalization, novel complexity theory, or Lean kernel proof.
