"""Generate a real Python two-component G14 UNSAT-cover Lean proof."""
from pathlib import Path

from witnora_core.python_g14_lean_artifact import emit_python_g14_lean


def main():
    path = Path("formal/Witnora/GeneratedPythonG14Multi.lean")
    path.parent.mkdir(parents=True, exist_ok=True)
    source = emit_python_g14_lean("saf_unsat_cover_2")
    path.write_text(source, encoding="utf-8")
    print({"instance": "saf_unsat_cover_2", "source_bytes": len(source.encode("utf-8"))})


if __name__ == "__main__":
    main()
