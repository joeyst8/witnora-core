# W-STRUCT-001 — Rust-first source-constraint interaction diagnostic

## Falsifiable question

At equal source variable count, clause count, and primal-graph edge density,
can constraint structures exhibit different small-separator behavior? Yes:
the finite control below does. **This does not establish that separator
behavior predicts SAT/#SAT running time.** That stronger hypothesis requires
held-out solver benchmarks.

## Exact source definition

For a valid DIMACS source with declared variables `1..n`, the primal graph
has an edge `(u,v)` whenever some original clause contains both variables,
regardless of signs. Duplicate occurrences within a clause are ignored when
constructing edges. All declared variables—including unused variables—are
retained. We report:

- source variables and clauses, unique primal edges and possible edges;
- the number of connected components of the original primal graph;
- the smallest separator order in `{0,1,2}`, where order zero applies to an
  already disconnected graph, and for a connected graph removing the selected
  variables must leave **at least two nonempty** residual components;
- the lexicographically first minimum-order witness, residual component count,
  and largest component size. An absent result is `null`, which means only
  **no separator of size at most two**, not a global hardness result.

The diagnostic is implemented in Rust at
`rust/witnora-ve/src/bin/witnora_structure.rs`. Invoke:

```sh
cargo run --manifest-path rust/witnora-ve/Cargo.toml --bin witnora_structure -- SOURCE.cnf
```

The parser rejects malformed headers/literals/counts, unterminated clauses,
and instances exceeding the explicit diagnostic caps (128 variables, 20,000
clauses, width 32). This is deliberately **not** a SAT parser replacement,
SAT decision procedure, model counter or certificate checker.

## Matched-density finite negative control

Both sources have five variables, six positive binary clauses, six primal
edges (density 6/10) and are connected:

1. Bowtie: `(1,2),(2,3),(1,3),(1,4),(4,5),(1,5)`. Variable 1 is an
   articulation separator, so the minimum separator order is 1.
2. Chorded cycle: `(1,2),(2,3),(3,4),(4,5),(1,5),(1,3)`. There is no
   articulation separator; a two-variable separator exists, so the minimum
   order is 2.

An independent Python set/BFS oracle checks this result. The CI gate also
compares 300 seeded small signed-CNF sources to that oracle and exercises
malformed DIMACS negative controls. These are graph-structure tests, not
novel complexity results or speedup evidence.

## Next experiment / falsification gate

Generate matched `(n, m, primal-edge-density)` CNF families with and without
small separators, independently validate source SAT/#SAT counts, then compare
Rust W-CRC/TC-063 routes to a dedicated external exact #SAT counter (Ganak)
and a competitive SAT solver. Record preprocessing, solve time, maximum
resident memory, exactness, budgets and failures over multiple held-out
seeds. A predictive structural parameter is supported only if its advantage
persists after controlling for size/density and baseline solver behavior.

No theorem, general hardness predictor, P-versus-NP result, or external solver
superiority is claimed by W-STRUCT-001.
