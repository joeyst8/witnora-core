# Verification Kernel Demo

This demo is intentionally small. It does not introduce a new benchmark claim.
It shows the product primitive:

```text
claim -> evidence -> verification report -> trust card
```

Files:

- `valid_claim.json`: scoped claim and supporting evidence names
- `verification_report.json`: example structured report
- `verification_report.md`: human-readable audit report
- `trust_card.json`: concise trust card
- `trust_card.md`: human-readable trust card

The demo claim is about release-evidence verification, not new SAT solving.
