"""Emit raw numeric Lean certificate data from existing Python graph colorings.

Lean owns range checking, finite-index decoding, and chromatic optimality.
"""
from __future__ import annotations

from .lean_color_certificate_export import generate_default_cases, _validate


def emit_numeric_lean(cases=None, *, backend="python") -> str:
    if cases is None:
        cases = generate_default_cases()
    names = [case[0] for case in cases]
    if len(names) != len(set(names)):
        raise ValueError("duplicate case name")
    if backend == "rust":
        from witnora_ve import lean_numeric_emit_native
        validated = []
        for name, n, edges, colors, clique in cases:
            if not name.isidentifier() or not name[0].isalpha():
                raise ValueError("invalid Lean declaration name")
            k = _validate(n, edges, colors, clique)
            validated.append((name, n, list(edges), list(colors), list(clique), k))
        return lean_numeric_emit_native(validated)
    if backend != "python":
        raise ValueError("unknown numeric Lean exporter backend")
    lines = [
        "import Witnora.NumericEdgeListBridge",
        "",
        "/- Python-generated raw Nat lists; Lean checks their meaning. -/",
        "namespace Witnora.GeneratedNumericCertificates",
        "",
        "open Witnora.NumericColorCertificate",
        "open Witnora.ConcreteColorCertificate",
        "open Witnora.ChromaticMinimum",
    ]
    for name, n, edges, colors, clique in cases:
        if not name.isidentifier() or not name[0].isalpha():
            raise ValueError("invalid Lean declaration name")
        k = _validate(n, edges, colors, clique)
        edge_list = ", ".join(f"({u}, {v})" for u, v in edges)
        color_list = ", ".join(str(c) for c in colors)
        clique_list = ", ".join(str(v) for v in clique)
        lines.extend(["", f"def {name}RawEdges : List (Nat × Nat) := [{edge_list}]"])
        lines.append(f"def {name}RawColors : List Nat := [{color_list}]")
        lines.append(f"def {name}RawClique : List Nat := [{clique_list}]")
        lines.extend(["", f"""theorem {name}NumericPasses :
    checkNumeric {n - 1} {k - 1}
      {name}RawEdges {name}RawColors {name}RawClique = true := by
  decide"""])
        lines.extend(["", f"""theorem {name}NumericOptimal :
    ∃ hNoLoops : ∀ u : Fin {n},
        ¬ edgeAdj (decodedEdges {n - 1} {name}RawEdges) u u,
      chromaticNumber (edgeAdj (decodedEdges {n - 1} {name}RawEdges))
        hNoLoops = {k} := by
  exact checked_numeric_sound
    {n - 1} {k - 1}
    {name}RawEdges {name}RawColors {name}RawClique
    {name}NumericPasses"""])
        lines.append(f"#print axioms {name}NumericOptimal")
    lines.extend(["", "end Witnora.GeneratedNumericCertificates", ""])
    return "\n".join(lines)
