"""Read-only, provenance-checked join for WU-013 retrospective deadline sweep.

Published source solver runs are NEVER re-executed here. Original XNF ZIPs
provide variable counts; the independent xnf-tests SQLite provides timings.
"""

import argparse
from collections import Counter
import hashlib
from pathlib import Path
import sqlite3
import sys
import zipfile

EXPECTED = {
    "database": "0b2ea5305e1cd72453ac757dcbee1555919201454f0105db6d588e24307d9e31",
    "rand": "65bf5f6312e9a3fda39c64a58cc3fd1898540fa9f15c4733fc629a8530fc628a",
    "rand_sat": "b3dbeaecd148645e55f24f4619c25796a531bfd0c341b2f9d3d14d14a829ae2e",
}


def require_source(path: str, label: str) -> None:
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if digest != EXPECTED[label]:
        raise ValueError(f"{label}: source SHA-256 mismatch: {digest}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sqlite_db")
    ap.add_argument("rand_zip")
    ap.add_argument("rand_sat_zip")
    args = ap.parse_args()
    require_source(args.sqlite_db, "database")
    require_source(args.rand_zip, "rand")
    require_source(args.rand_sat_zip, "rand_sat")

    names = {}
    for family, prefix, path in (
        ("2xnf-rand", "rand", args.rand_zip),
        ("2xnf-rand_sat", "rand_sat", args.rand_sat_zip),
    ):
        with zipfile.ZipFile(path) as z:
            entries = [p for p in z.namelist() if p.endswith(".xnf")]
            if len(entries) != 400:
                raise ValueError(f"{family}: expected 400 original XNF instances")
            for entry in entries:
                if not entry.startswith(prefix + "/") or entry.count("/") != 1:
                    raise ValueError(f"{family}: unexpected ZIP path: {entry}")
                sample = z.read(entry).decode("ascii")
                header = next((line for line in sample.splitlines()
                               if line.startswith("p xnf ")), None)
                if header is None or (family, entry[len(prefix)+1:-4]) in names:
                    raise ValueError(f"{family}: missing header or duplicate XNF: {entry}")
                names[(family, entry[len(prefix)+1:-4])] = header

    with sqlite3.connect(f"file:{args.sqlite_db}?mode=ro", uri=True) as db:
        rows = db.execute(
            """SELECT a.family, a.instance, a.solved, a.solve_time,
                      a.timeout_t, a.result, b.solved, b.solve_time,
                      b.timeout_t, b.result
                 FROM data a JOIN data b
                  ON a.family=b.family AND a.instance=b.instance
                WHERE a.solver='cms-improved' AND b.solver='xorcle'
                  AND a.family IN ('2xnf-rand','2xnf-rand_sat')
                ORDER BY a.family, a.instance"""
        ).fetchall()
    if len(rows) != 800 or len(names) != 800:
        raise ValueError("expected exactly 800 original-formula paired records")
    counted = Counter()
    print("family\tinstance\theader\tcms_solved\tcms_seconds\tcms_timeout\t"
          "xor_solved\txor_seconds\txor_timeout")
    for family, name, a_ok, a_time, a_limit, a_ans, b_ok, b_time, b_limit, b_ans in rows:
        counted[(family, name)] += 1
        if (a_ok and b_ok and a_ans != b_ans) or a_ok not in (0, 1) or b_ok not in (0, 1):
            raise ValueError(f"{family}/{name}: invalid or conflicting outcomes")
        if (family, name) not in names:
            raise ValueError(f"{family}/{name}: no original XNF file")
        cells = (family, name, names[(family, name)], a_ok, a_time,
                 a_limit, b_ok, b_time, b_limit)
        if any(isinstance(cell, str) and "\t" in cell for cell in cells):
            raise ValueError("source TSV injection")
        print("\t".join("" if cell is None else str(cell) for cell in cells))
    if set(counted) != set(names) or any(n != 1 for n in counted.values()):
        raise ValueError("source archives and paired outcomes do not match one-to-one")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, sqlite3.Error, zipfile.BadZipFile, UnicodeError) as exc:
        print(f"WU-013 rejected source: {exc}", file=sys.stderr)
        sys.exit(2)
