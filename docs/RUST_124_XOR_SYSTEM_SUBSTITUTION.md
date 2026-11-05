# R-124: batch XOR system substitution

`XorSystem.substitute(assignment, backend="rust")` performs the parity
substitution for every equation through one native Rust call, then rebuilds
the Python equations with their original proof/source metadata and system
diagnostics. Python still sorts equations and excludes tautologies.

The default Python path is unchanged. Focused native CI compares 300 seeded
whole systems, partial assignments, contradictions, metadata and ordering.
It does not establish a new solver bound or upgrade an untrusted detection
to a verified XOR sidecar.
