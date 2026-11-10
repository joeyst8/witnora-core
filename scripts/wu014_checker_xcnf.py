"""Normalize an upstream CNF-XOR file for the independent Cake XLRUP checker.

Xorcle's xnf_convert emits the number of *ordinary CNF* clauses in `p cnf`,
while Cake expects the header to count ordinary and XOR lines together.
CryptoMiniSat accepts the former convention. This creates a separate checker
input, retaining every original constraint and its original order/IDs.
"""

import argparse
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("output")
    args = parser.parse_args()
    raw = Path(args.source).read_text(encoding="ascii").splitlines()
    if not raw or len(raw[0].split()) != 4:
        raise ValueError("missing CNF-XOR header")
    kind, cnf, nv, nc = raw[0].split()
    if (kind, cnf) != ("p", "cnf"):
        raise ValueError("unexpected source header")
    entries = []
    ordinary = 0
    for line in raw[1:]:
        line = line.strip()
        if not line or line.startswith("c "):
            raise ValueError("unexpected blank/comment line in generated xcnf")
        if line.startswith("x"):
            # Preserve the same literal sequence, but normalize its prefix.
            line = "x " + line[1:].lstrip()
        else:
            ordinary += 1
        if line.split()[-1] != "0":
            raise ValueError("missing clause terminator")
        entries.append(line)
    if int(nc) != ordinary:
        raise ValueError("source's ordinary-CNF clause count does not match")
    if not entries or len(entries) <= ordinary:
        raise ValueError("expected both CNF and XOR lines")
    output = f"p cnf {int(nv)} {len(entries)}\n" + "\n".join(entries) + "\n"
    Path(args.output).write_text(output, encoding="ascii")
    print(f"WU-014 Cake checker input: {ordinary} CNF + {len(entries)-ordinary} XOR clauses")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as exc:
        print(f"WU-014 checker normalization rejected source: {exc}", file=sys.stderr)
        sys.exit(2)
