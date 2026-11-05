"""Deterministic Python -> Lean graph optimal-coloring certificate emission.

This emits Lean source from concrete Python graph/color/clique data. A
subsequent Lean kernel build must validate the actual generated source.
The emitter itself is not yet a formally proved Python refinement.
"""
from __future__ import annotations

from itertools import combinations
import re

from .nonedge_matching_bound import _dsatur_greedy_coloring


def _validate(n: int, edges: tuple[tuple[int, int], ...],
              coloring: list[int], clique: tuple[int, ...]) -> int:
    if not 1 <= n <= 16:
        raise ValueError("supported certificate size is 1..16 vertices")
    if tuple(sorted(set(edges))) != edges:
        raise ValueError("edges must be normalized and unique")
    if any(not 0 <= u < v < n for u, v in edges):
        raise ValueError("invalid edge")
    if len(coloring) != n or any(not isinstance(c, int) or c < 0 for c in coloring):
        raise ValueError("invalid color assignment")
    k = max(coloring) + 1
    if set(coloring) != set(range(k)):
        raise ValueError("color IDs must be canonical and contiguous")
    if any(coloring[u] == coloring[v] for u, v in edges):
        raise ValueError("improper coloring")
    if len(clique) != k or len(set(clique)) != k or any(
            not isinstance(v, int) or not 0 <= v < n for v in clique):
        raise ValueError("invalid clique indices")
    edge_set = set(edges)
    if any((min(u, v), max(u, v)) not in edge_set
           for u, v in combinations(clique, 2)):
        raise ValueError("clique contains nonadjacent vertices")
    return k


def _fin_values(value_name: str, var: str, n: int, codomain: int,
                values: list[int], *, backend="python") -> str:
    if backend == "rust":
        from witnora_ve import lean_color_fin_values_native
        return lean_color_fin_values_native(value_name, var, n, codomain, values)
    if backend != "python":
        raise ValueError("unknown finite-value backend")
    lines = [f"def {value_name} ({var} : Fin {n}) : Fin {codomain} :="]
    if n == 1:
        lines.append(f"  {values[0]}")
    else:
        for index, value in enumerate(values[:-1]):
            prefix = "if" if index == 0 else "else if"
            lines.append(f"  {prefix} {var}.val = {index} then {value}")
        lines.append(f"  else {values[-1]}")
    return "\n".join(lines)


def _lean_case(name: str, n: int, edges: tuple[tuple[int, int], ...],
               colors: list[int], clique: tuple[int, ...]) -> str:
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name):
        raise ValueError("invalid Lean identifier")
    k = _validate(n, edges, colors, clique)
    edge_items = ", ".join(f"({u}, {v})" for u, v in edges)
    edges_decl = (
        f"def {name}Edges : List (Fin {n} × Fin {n}) :=\n"
        f"  [{edge_items}]")
    paint_decl = _fin_values(f"{name}Paint", "v", n, k, colors)
    clique_values = list(clique[1:])
    clique_lines = [
        f"def {name}Clique : Option (Fin {k - 1}) → Fin {n}",
        f"  | none => {clique[0]}",
    ]
    if not clique_values:
        clique_lines.append(f"  | some _ => {clique[0]}")
    else:
        clique_lines.append("  | some _ =>" if len(clique_values) == 1 else "  | some i =>")
        if len(clique_values) == 1:
            clique_lines.append(f"      {clique_values[0]}")
        else:
            for index, value in enumerate(clique_values[:-1]):
                prefix = "if" if index == 0 else "else if"
                clique_lines.append(f"      {prefix} i.val = {index} then {value}")
            clique_lines.append(f"      else {clique_values[-1]}")
    return "\n\n".join([
        edges_decl, paint_decl, "\n".join(clique_lines),
        f"""theorem {name}Passes :
    checkCertificate {name}Edges {name}Paint {name}Clique = true := by
  decide""",
        f"""theorem {name}Optimal :
    ∃ hNoLoops : ∀ u : Fin {n}, ¬ edgeAdj {name}Edges u u,
      chromaticNumber (edgeAdj {name}Edges) hNoLoops = {k} := by
  exact checked_certificate_sound
    {name}Edges {name}Paint {name}Clique {name}Passes""",
        f"#print axioms {name}Optimal",
    ])


def find_matching_clique(n: int, edges: tuple[tuple[int, int], ...],
                         size: int, *, backend="python") -> tuple[int, ...] | None:
    if backend == "rust":
        from witnora_ve import lean_color_find_clique_native
        answer = lean_color_find_clique_native(n, list(edges), size)
        return tuple(answer) if answer is not None else None
    if backend != "python":
        raise ValueError("unknown clique search backend")
    edge_set = set(edges)
    return next((vs for vs in combinations(range(n), size)
                 if all((u, v) in edge_set for u, v in combinations(vs, 2))), None)


def generate_default_cases() -> tuple[tuple[str, int, tuple[tuple[int, int], ...],
                                      list[int], tuple[int, ...]], ...]:
    graphs = (
        ("triangle", 3, ((0, 1), (0, 2), (1, 2))),
        ("pathFour", 4, ((0, 1), (1, 2), (2, 3))),
        ("cliqueFour", 4, tuple(combinations(range(4), 2))),
        ("twoTriangles", 6,
         ((0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5))),
    )
    cases = []
    for name, n, edges in graphs:
        colors = _dsatur_greedy_coloring(n, edges)["coloring"]
        size = max(colors) + 1
        clique = find_matching_clique(n, edges, size)
        if clique is None:
            raise AssertionError(f"no clique certificate for {name}")
        _validate(n, edges, colors, clique)
        cases.append((name, n, edges, colors, clique))
    return tuple(cases)


def emit_lean(cases=None, *, backend="python") -> str:
    if cases is None:
        cases = generate_default_cases()
    names = [case[0] for case in cases]
    if len(set(names)) != len(names):
        raise ValueError("duplicate certificate name")
    if backend == "rust":
        from witnora_ve import lean_color_emit_native
        validated = []
        for name, n, edges, colors, clique in cases:
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name):
                raise ValueError("invalid Lean identifier")
            k = _validate(n, edges, colors, clique)
            validated.append((name, n, list(edges), list(colors), list(clique), k))
        return lean_color_emit_native(validated)
    if backend != "python":
        raise ValueError("unknown color certificate backend")
    blocks = [
        "import Witnora.ConcreteColorCertificate",
        "",
        "/- Generated deterministically by Python; Lean checks all data. -/",
        "namespace Witnora.GeneratedColorCertificates",
        "",
        "open Witnora.ConcreteColorCertificate",
        "open Witnora.ChromaticMinimum",
    ]
    for case in cases:
        blocks.extend(["", _lean_case(*case)])
    blocks.extend(["", "end Witnora.GeneratedColorCertificates", ""])
    return "\n".join(blocks)
