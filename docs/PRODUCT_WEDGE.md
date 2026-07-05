# Product Wedge: Witnora Verify

Disclaimer: This is a forward-looking vision document. It does not describe current production capabilities. Current Witnora-Core capabilities are limited to the scoped claims in the public release and verification reports.

Witnora Verify is a verification layer for AI-generated technical claims and
proof artifacts.

## Target Users

- researchers who need artifact and claim-boundary audits
- engineering teams shipping proof-carrying tools
- security and verification teams evaluating generated technical evidence
- enterprise buyers who need concise trust summaries before adopting an artifact

## Why They Care

Technical systems increasingly produce answers, proofs, logs, plans, and
release bundles faster than humans can inspect them manually. The painful
question is not only "what did the system say?" but "what evidence makes this
safe to believe?"

Witnora Verify turns that into a structured report:

- claim being audited
- evidence files
- independent checks
- external checkers
- artifact hashes
- allowed claims
- forbidden claims
- scoped verdict

## What It Checks

The first implementation checks Witnora SAT certificates, release packages,
SHA256 evidence, claim boundaries, and trust-card summaries. The v1.1.1 release
verification path is an artifact-integrity and metadata check; it does not rerun
the full scientific proof pipeline unless a future report explicitly says a
deeper replay was performed.

The same shape can later support other technical outputs:

- generated code with tests and static-analysis evidence
- AI-agent plans with constraints and execution logs
- scientific or scheduling claims with reproducibility files
- hardware or protocol artifacts with checker outputs

## What It Refuses To Claim

Witnora Verify does not claim unsupported capability, broad benchmark success,
general intelligence, or domain authority. It reports what the evidence supports
and records risk flags when the evidence is incomplete.

## Infrastructure Path

The wedge is a small but durable API:

```text
submit claim + evidence -> receive verification report + trust card
```

That is the bridge from a research prototype to a product primitive.
