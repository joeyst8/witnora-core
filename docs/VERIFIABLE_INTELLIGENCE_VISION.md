# Verifiable Intelligence Vision

Witnora is moving from a single research artifact toward verifier-to-witness
infrastructure.

The core primitive is:

```text
claim -> evidence -> independent verification -> scoped trust
```

The first battlefield is SAT because SAT has unusually sharp notions of
witnesses, certificates, proof artifacts, independent checkers, and external
proof validation. That makes it a good place to build the habits needed for a
larger verification product: state the claim, collect the evidence, run the
checker, separate what is verified from what is not, and make the result legible
to a human.

## What Witnora Verifies Today

Witnora-Core currently verifies scoped SAT and UNSAT claims produced by its own
collapse-path framework. It can check certificate bundles, proof artifacts,
release hashes, claim boundaries, and reproducibility evidence.

The v1.1 verification kernel does not add solving power. It adds a reusable
audit layer that asks:

- What is being claimed?
- What files support the claim?
- Which checker evaluated the evidence?
- What is the certification level?
- What claims are explicitly not made?
- Is the artifact reproducible enough for an outside reviewer?

## Future Domains

Future domains may include software verification, AI-agent plan checking,
scheduling, hardware verification, and scientific constraints. These are future
directions, not current claims.

The product direction is not merely "solve more SAT instances." The broader
direction is to make technical claims checkable, bounded, and understandable.

## Claim Boundary

The verification kernel does not claim broad AI truth evaluation. It checks
structured evidence against explicit rules. It refuses to promote native-only or
unverified evidence into externally verified claims.

This discipline is the product: useful trust is scoped trust.
