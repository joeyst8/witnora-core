# R-131: native explicit XOR sidecar line parsing

`parse_xor_lines(text, backend="rust")` parses explicit sidecar equations,
comments, signs and parity right-hand sides in Rust, then constructs
`XorEquation` objects in Python with their original `EXPLICIT_SIDECAR`
trust mode. The Python parser remains default; the Rust path uses finite
64-bit signed variable tokens and rejects malformed lines rather than
silently reinterpreting them.

Focused native CI compares 320 seeded multiline sidecars plus invalid
grammar, variable and RHS controls. Parsing a sidecar is not equivalent
to proving that an independently supplied sidecar is entailed by source
CNF; this migration does not change the trust policy.
