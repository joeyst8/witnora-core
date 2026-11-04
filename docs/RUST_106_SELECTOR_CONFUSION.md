# R-106: native frozen selector confusion accounting

The Rust selector now aggregates the chosen rule's graph, failure,
selection, true-positive, missed-positive, and false-positive counts.
The Python-facing `confusion(..., backend="rust")` opt-in computes derived
precision/recall using the same zero-denominator conventions as Python.

Focused CI compares full confusion reports for all ten frozen rules across
90 seeded synthetic datasets. Experimental train/holdout sampling remains
Python, and no predictive or theoretical claim is promoted.
