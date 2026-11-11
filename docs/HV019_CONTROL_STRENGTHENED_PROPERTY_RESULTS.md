# HV-019 — One-hot controller lemma is insufficient for original chip safety

**Frozen protocol:** [HV019_CONTROL_STRENGTHENED_PROPERTY_PROTOCOL.md](HV019_CONTROL_STRENGTHENED_PROPERTY_PROTOCOL.md). **Generator:** [hv019_strengthened_property_query.py](../research/hv019_strengthened_property_query.py). **Result JSON:** [hv019_control_strengthened_property.json](../research/results/hv019_control_strengthened_property.json).

Using the unchanged SHA-pinned HKU HLS BTOR2 transition system, we asked one precise 1-induction question:

\[
P(s)\wedge L(s)\wedge T(s,i,s')\wedge\neg P(s'),
\]

where `P(s)=NOT node48` is the original chip safety property and `L(s)=node99` is the now SMT-checked one-hot controller lemma (HV-018). The query removed exactly seven initial constraints, retained all 26 transition equalities, and introduced no other strengthening. Query SHA256 `1a2cab04dc6eef7cd4f4f0316a0fdd9105e28faa605c6489c2b716d5c0c8e7a3`.

**Bitwuzla 0.6.1: `Bad property 794 satisfiable.`** Process exit 0, within 20s / 2 GiB. This is a counterexample to the *inductive step*, starting from an arbitrary legal controller/data state, **not a demonstrated reachable unsafe execution**. By the preregistered rule, no Cerbtora witness check was attempted.

The result identifies the remaining obstacle more precisely: controller reachability constraints **alone** do not capture the data-path dependencies that preserve the safety property. The source transition makes `state43' = NOT write_enable OR result_reg` and `state45' = NOT state43'`. Safety in the next frame therefore depends on the relation between the write-enable condition and the computed result bit. Discovering sufficient reachable-state relationships—then exporting an accepted certificate—is the next task.

This is a principled negative experiment, not a breakthrough claim.
