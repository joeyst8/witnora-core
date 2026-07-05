# Cardinality / PB Collapse

v2.3 adds a native cardinality/counting certificate for standard pigeonhole
CNFs. It is not a complete pseudo-Boolean solver.

## Assignment Variables

Standard `php_n_m` formulas use assignment variables:

`x[i,j] = pigeon i is assigned to hole j`

Witnora does not model separate pigeon variables and hole variables.

## Original-CNF Checks

The detector accepts a standard PHP structure only when the original CNF
contains:

- for each pigeon `i`, the ALO clause
  `x[i,1] or x[i,2] or ... or x[i,m]`;
- for each hole `j` and each pigeon pair `i < k`, the AMO clause
  `not x[i,j] or not x[k,j]`.

If any required clause is missing, exact PHP recognition fails.

## Native Counting Certificate

When `n > m`, the certificate records:

- every pigeon requires at least one hole;
- every hole accepts at most one pigeon;
- required assignments: `n`;
- available holes: `m`;
- contradiction: `n > m`.

The public category is `UNSAT_PIGEONHOLE_NATIVE_CERTIFIED`.

## Boundary

This is native semantic certification. It is not DRAT, not RAT, not a PB solver,
and not a proof-complexity lower bound. A DRAT claim would require an externally
checked proof against the original CNF.
