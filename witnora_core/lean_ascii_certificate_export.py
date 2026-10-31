"""Export Python DSATUR certificates as explicit ASCII byte lists for Lean.

The byte transport is a concrete generated Lean literal, not a universal
proof that all Python executions faithfully implement a Lean specification.
"""
from __future__ import annotations

import re

from .lean_color_certificate_export import _validate, generate_default_cases


def serialize_ascii_certificate(n: int, edges: tuple[tuple[int, int], ...],
                                colors: list[int], clique: tuple[int, ...]) -> bytes:
    """Canonical N|K|edges|colors|clique, with zero-based max indices."""
    k = _validate(n, edges, colors, clique)
    fields = (
        str(n - 1),
        str(k - 1),
        ";".join(f"{u},{v}" for u, v in edges),
        ",".join(map(str, colors)),
        ",".join(map(str, clique)),
    )
    return "|".join(fields).encode("ascii")


def lean_bytes(data: bytes) -> str:
    return "[" + ", ".join(str(b) for b in data) + "]"


def emit_ascii_lean(cases=None) -> str:
    if cases is None:
        cases = generate_default_cases()
    names = [case[0] for case in cases]
    if len(names) != len(set(names)):
        raise ValueError("duplicate case name")
    lines = [
        "import Witnora.KernelAsciiNumericCertificate",
        "",
        "/- Python DSATUR source bytes as Lean Nat lists; checked by Lean. -/",
        "namespace Witnora.GeneratedAsciiCertificates",
        "open Witnora.KernelAsciiNumericCertificate",
        "open Witnora.NumericColorCertificate",
        "open Witnora.ConcreteColorCertificate",
        "open Witnora.ChromaticMinimum",
        "set_option maxRecDepth 8192",
        "set_option maxHeartbeats 4000000",
    ]
    for name, n, edges, colors, clique in cases:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name):
            raise ValueError("invalid Lean declaration name")
        k = _validate(n, edges, colors, clique)
        data = serialize_ascii_certificate(n, edges, colors, clique)
        damaged = bytes([120]) + data[1:]  # Replace first digit with ASCII 'x'.
        raw_edges = ", ".join(f"({u}, {v})" for u, v in edges)
        raw_colors = ", ".join(map(str, colors))
        raw_clique = ", ".join(map(str, clique))
        lines.extend([
            "",
            f"def {name}AsciiBytes : List Nat := {lean_bytes(data)}",
            f"def {name}DamagedBytes : List Nat := {lean_bytes(damaged)}",
            f"""theorem {name}AsciiParses :
    parseAsciiCertificate {name}AsciiBytes =
      some ({n - 1}, {k - 1}, [{raw_edges}], [{raw_colors}], [{raw_clique}]) := by
  decide""",
            f"""theorem {name}AsciiPasses :
    checkAsciiCertificate {name}AsciiBytes = true := by
  decide""",
            f"""theorem {name}AsciiDamagedRejects :
    checkAsciiCertificate {name}DamagedBytes = false := by
  decide""",
            f"""theorem {name}AsciiOptimal :
    ∃ hNoLoops : ∀ u : Fin {n},
        ¬ edgeAdj (decodedEdges {n - 1} [{raw_edges}]) u u,
      chromaticNumber (edgeAdj (decodedEdges {n - 1} [{raw_edges}]))
        hNoLoops = {k} := by
  exact checked_ascii_certificate_sound {name}AsciiBytes
    {n - 1} {k - 1} [{raw_edges}] [{raw_colors}] [{raw_clique}]
    {name}AsciiParses {name}AsciiPasses""",
            f"#print axioms {name}AsciiOptimal",
        ])
    lines.extend(["", "end Witnora.GeneratedAsciiCertificates", ""])
    return "\n".join(lines)
