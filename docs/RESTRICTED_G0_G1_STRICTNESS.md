# Restricted G0-vs-G1 Strictness

v2.9 attempts the first restricted strictness proof kernel in Witnora.

The target is not full `G0_BASE`. The target is the bounded width/treewidth
subroute:

- `G0_WIDTH_C`: bounded treewidth terminal, VE width cap `c`, and exact width
  obstruction checking.
- `G1_XOR_FOR_STRICTNESS`: `G0_WIDTH_C` plus exact XOR extraction and native
  GF(2) elimination.

For selected finite witnesses, v2.9 records:

1. `G0_WIDTH_C` rejects the formula because exact bounded-width checking
   verifies no elimination ordering of width `<= c`.
2. `G1_XOR_FOR_STRICTNESS` accepts the formula because exact XOR equations are
   extracted and the native GF(2) certificate verifies.

This is a restricted theorem candidate/proof sketch unless explicitly marked
proven. It does not prove full `G0_BASE` strictness, hierarchy completeness,
P vs NP progress, or a lower bound against all G0 operators.

Scalable Tseitin/expander strictness remains a theorem candidate until a real
graph-theoretic proof is supplied.

