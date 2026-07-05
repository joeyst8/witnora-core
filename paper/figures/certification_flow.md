# Certification Flow

| layer | checked by | meaning |
| --- | --- | --- |
| exact XOR source clauses | Witnora detector and independent checker | detected equation is implied by retained CNF clauses |
| GF(2) row-operation trace | independent checker | native XOR contradiction reaches `0 = 1` |
| `proof.drat` | real `drat-trim` | original-CNF UNSAT proof accepted against `original.dimacs` |
| public category | result metadata checks | externally verified rows use `UNSAT_DRAT_EXPORTED_VERIFIED` |
