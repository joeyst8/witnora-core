# Planner Execution Certificate

The v2.20 `PlannerExecutionCertificate` links three separate artifacts:

1. the original CNF;
2. a verified G12 plan certificate;
3. an actual execution chain with checked operator certificates.

The certificate records planned steps, actual steps, formula-state hashes,
step-certificate hashes, planned-vs-actual comparison, and result obligations.

SAT is trusted only when the final witness satisfies the original CNF directly.
UNSAT is trusted only when every preservation or equisatisfiability obligation
in the actual chain verifies. Diagnostic-only steps cannot certify results.

A matching plan and execution is not a family theorem and does not prove all
plans succeed. It is finite checked execution evidence only.
