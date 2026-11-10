"""Read-only bridge from the public xnf-tests SQLite data to Witnora Rust.

Source: https://github.com/msoos/xnf-tests, revision pinned in WU-011 doc.
Only the two solver outcomes and pre-solve family/path identifiers are
exported; no runtime-derived features are passed to the selector.
"""

import argparse
import sqlite3
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sqlite_db", help="upstream data.sqlite")
    args = parser.parse_args()

    with sqlite3.connect(f"file:{args.sqlite_db}?mode=ro", uri=True) as db:
        query = """
            SELECT a.family, a.instance, a.dirname,
                   a.solved, a.solve_time, a.timeout_t, a.result,
                   b.solved, b.solve_time, b.timeout_t, b.result
            FROM data a JOIN data b
              ON a.family = b.family AND a.instance = b.instance
            WHERE a.solver = 'cms-improved' AND b.solver = 'xorcle'
            ORDER BY a.family, a.instance
        """
        rows = db.execute(query).fetchall()

    if len(rows) != 1695:
        raise ValueError(f"expected exactly 1695 paired rows, got {len(rows)}")
    keys = [(r[0], r[1]) for r in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate benchmark keys in source data")

    print("family\tinstance\tdirname\tcms_solved\tcms_time\tcms_timeout\t"
          "cms_result\txor_solved\txor_time\txor_timeout\txor_result")
    for row in rows:
        if any(isinstance(x, str) and ("\t" in x or "\n" in x) for x in row):
            raise ValueError("tab or newline inside a database field")
        print("\t".join("" if cell is None else str(cell) for cell in row))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, sqlite3.Error) as error:
        print(f"WU-011 export failed: {error}", file=sys.stderr)
        sys.exit(2)
