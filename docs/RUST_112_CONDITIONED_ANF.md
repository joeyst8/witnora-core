# R-112: composed native separator-conditioned ANF counting path

The existing Python bounded separator-conditioned search now forwards
`backend="rust"` into its selected separator search (R-110), symbolic
polynomial XOR (R-107), and component-aware structured counter (R-111).
The small branch-enumeration controller still runs in Python.

The focused CI compares full `SeparatorCountResult` values, including
branch counts and all internal counters, against the Python reference on
130 seeded bounded instances. Failure to finish within budget is reported
as exhaustion, not mathematical impossibility.
