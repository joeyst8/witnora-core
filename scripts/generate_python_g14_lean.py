"""Write Python-produced G14 residual and G5 proof instance as Lean."""
from pathlib import Path

from witnora_core.python_g14_lean_artifact import emit_python_g14_lean


def main():
    path = Path("formal/Witnora/GeneratedPythonG14.lean")
    path.parent.mkdir(parents=True, exist_ok=True)
    source = emit_python_g14_lean()
    path.write_text(source, encoding="utf-8")
    print({"output": str(path), "source_bytes": len(source.encode("utf-8"))})


if __name__ == "__main__":
    main()
