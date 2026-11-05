"""Materialize Python XOR-CNF source-byte verification fixtures."""
from pathlib import Path

from witnora_core.python_dimacs_xor_lean_export import emit_python_dimacs_lean


def main():
    output = Path("formal/Witnora/GeneratedPythonDimacsXor.lean")
    output.parent.mkdir(parents=True, exist_ok=True)
    source = emit_python_dimacs_lean()
    output.write_text(source, encoding="utf-8")
    print({"output": str(output), "source_bytes": len(source.encode("utf-8"))})


if __name__ == "__main__":
    main()
