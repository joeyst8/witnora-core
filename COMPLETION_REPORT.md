# Witnora-Core v0 Completion Report

## 1. File Tree

Fresh command:

```powershell
tree /F /A
```

Output:

```text
Folder PATH listing for volume OS
Volume serial number is 000000C8 E401:EA77
C:.
|   .gitignore
|   COMPLETION_REPORT.md
|   README.md
|   
+---.agents
+---.git
+---examples
|       bce_demo.dimacs
|       treewidth_demo.dimacs
|       unsat_demo.dimacs
|       
+---tests
|   |   test_bce_demo.py
|   |   test_determinism.py
|   |   test_no_collapse.py
|   |   test_reconstruction.py
|   |   test_treewidth_demo.py
|   |   test_unsat.py
|   |   __init__.py
|   |   
|   \---__pycache__
|           test_bce_demo.cpython-311.pyc
|           test_determinism.cpython-311.pyc
|           test_no_collapse.cpython-311.pyc
|           test_reconstruction.cpython-311.pyc
|           test_treewidth_demo.cpython-311.pyc
|           test_unsat.cpython-311.pyc
|           __init__.cpython-311.pyc
|           
\---witnora_core
    |   bce.py
    |   certificate.py
    |   cnf.py
    |   components.py
    |   dimacs.py
    |   primal.py
    |   reconstruction.py
    |   runner.py
    |   simplify.py
    |   subsumption.py
    |   treewidth.py
    |   two_sat.py
    |   ve.py
    |   verifier.py
    |   __init__.py
    |   
    \---__pycache__
            bce.cpython-311.pyc
            certificate.cpython-311.pyc
            cnf.cpython-311.pyc
            components.cpython-311.pyc
            dimacs.cpython-311.pyc
            primal.cpython-311.pyc
            reconstruction.cpython-311.pyc
            runner.cpython-311.pyc
            simplify.cpython-311.pyc
            subsumption.cpython-311.pyc
            treewidth.cpython-311.pyc
            two_sat.cpython-311.pyc
            ve.cpython-311.pyc
            verifier.cpython-311.pyc
            __init__.cpython-311.pyc
```

`__pycache__` files are generated artifacts from running tests. `.gitignore` excludes them.

## 2. Commands Run

No install/setup commands were required. The implementation uses only Python standard-library modules.

Exploration commands:

```powershell
Get-ChildItem -Force
if (Get-Command rg -ErrorAction SilentlyContinue) { rg --files } else { Get-ChildItem -Recurse -File | ForEach-Object { $_.FullName } }
git status --short
```

Development verification commands:

```powershell
python -m py_compile witnora_core\*.py
python -m unittest discover
python -m compileall -q witnora_core tests
python -m unittest discover
python -m witnora_core.runner examples\bce_demo.dimacs --c 2
python -m witnora_core.runner examples\treewidth_demo.dimacs --c 2
python -m compileall -q witnora_core tests
python -m unittest discover
python -m witnora_core.runner examples\bce_demo.dimacs --c 2
python -m witnora_core.runner examples\treewidth_demo.dimacs --c 1
python -c "from witnora_core.cnf import CNFFormula; from witnora_core.runner import solve; f=CNFFormula.from_raw_clauses([[1,2],[1,-2],[-1,2],[-1,-2]]); r=solve(f, c=2); print(r.status, r.final_class, r.stats.get('verification_errors'))"
python -c "import itertools, random; from witnora_core.cnf import CNFFormula, formula_satisfied; from witnora_core.two_sat import solve_2sat; lits=[1,-1,2,-2,3,-3]; random.seed(1); ... print('2sat_random_ok')"
Get-ChildItem -Recurse -File | Select-Object -ExpandProperty FullName
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Select-Object -ExpandProperty FullName
```

Notes on failed/diagnostic commands:

- `git status --short` returned `fatal: not a git repository`.
- The first `python -m py_compile witnora_core\*.py` failed because Python does not expand the wildcard on Windows in that form.
- The first `python -m unittest discover` ran zero tests before `tests/__init__.py` was added.
- The random 2-SAT self-check used brute force only as an ad hoc external validation oracle for tiny 3-variable formulas. No brute-force SAT solving is present in Witnora-Core or in the acceptance tests.

Fresh report commands:

```powershell
tree /F /A
python -m compileall -q witnora_core tests
python -m unittest discover
python -m witnora_core.runner examples\unsat_demo.dimacs --c 2
python -m witnora_core.runner examples\bce_demo.dimacs --c 2
python -m witnora_core.runner examples\treewidth_demo.dimacs --c 2
python -m witnora_core.runner examples\treewidth_demo.dimacs --c 1
python -c "from witnora_core.cnf import CNFFormula; from witnora_core.runner import solve; import json; f=CNFFormula.from_raw_clauses([[1,2,3],[-1,-2],[-1,-3]]); a=solve(f,c=2).to_dict(); b=solve(f,c=2).to_dict(); print(json.dumps({...}, indent=2, sort_keys=True))"
```

## 3. Test Results

Fresh command:

```powershell
python -m unittest discover
```

Full output:

```text
BCE_RECONSTRUCTION_PASS
DETERMINISM_PASS
NO_COLLAPSE_PASS
RECONSTRUCTION_PASS
TREEWIDTH_COLLAPSE_PASS
UNSAT_PASS
......
----------------------------------------------------------------------
Ran 6 tests in 0.003s

OK
```

Required marker confirmation:

- `BCE_RECONSTRUCTION_PASS`: passed
- `TREEWIDTH_COLLAPSE_PASS`: passed
- `RECONSTRUCTION_PASS`: passed
- `UNSAT_PASS`: passed
- `NO_COLLAPSE_PASS`: passed
- `DETERMINISM_PASS`: passed

## 4. Example Outputs

### BCE Demo, c=2

Command:

```powershell
python -m witnora_core.runner examples\bce_demo.dimacs --c 2
```

Output:

```json
{
  "c_parameter": 2,
  "collapse_path": [
    {
      "added_clauses": [],
      "assigned_literals": [],
      "details": {
        "blocked_literal": 1,
        "checked_resolvents": [
          {
            "against_clause": [
              -3,
              -1
            ],
            "resolvent": [
              -3,
              2,
              3
            ],
            "tautological": true
          },
          {
            "against_clause": [
              -2,
              -1
            ],
            "resolvent": [
              -2,
              2,
              3
            ],
            "tautological": true
          }
        ],
        "opposite_clauses": [
          [
            -3,
            -1
          ],
          [
            -2,
            -1
          ]
        ],
        "proof_digest": "b4a048e11f4c94b3182bd7b5d1265ec7e591615174fa96e951ab5a7a2f76ad6f",
        "removed_clause": [
          1,
          2,
          3
        ]
      },
      "input_formula_hash": "896337a8730f733524ead5682cdddfd54dc85ae87b5b76d27f79c266083c2422",
      "output_formula_hash": "a94ac0e4015529e375ff67d33538a3926f8c9fc1d140bcea94c8d94529de48e3",
      "reconstruction_data": {
        "blocked_literal": 1,
        "opposite_clauses": [
          [
            -3,
            -1
          ],
          [
            -2,
            -1
          ]
        ],
        "removed_clause": [
          1,
          2,
          3
        ]
      },
      "removed_clauses": [
        [
          1,
          2,
          3
        ]
      ],
      "step_id": 1,
      "type": "BCE"
    },
    {
      "added_clauses": [],
      "assigned_literals": [
        -1
      ],
      "details": {
        "assigned_literal": -1,
        "removed_due_to_pure_literal": [
          [
            -3,
            -1
          ],
          [
            -2,
            -1
          ]
        ]
      },
      "input_formula_hash": "a94ac0e4015529e375ff67d33538a3926f8c9fc1d140bcea94c8d94529de48e3",
      "output_formula_hash": "e160232d0ce8816f12ecdcdc7bb0e939b55fb5ca43414ae6077dfa3989655732",
      "reconstruction_data": {
        "assigned_literal": -1
      },
      "removed_clauses": [
        [
          -3,
          -1
        ],
        [
          -2,
          -1
        ]
      ],
      "step_id": 2,
      "type": "PLE"
    }
  ],
  "final_assignment": {},
  "final_class": "EMPTY",
  "final_formula_hash": "e160232d0ce8816f12ecdcdc7bb0e939b55fb5ca43414ae6077dfa3989655732",
  "original_formula_hash": "896337a8730f733524ead5682cdddfd54dc85ae87b5b76d27f79c266083c2422",
  "original_verification": true,
  "reconstructed_original_assignment": {
    "1": true,
    "2": false,
    "3": false
  },
  "stats": {
    "collapse_path_length": 2,
    "num_clauses_added": 0,
    "num_clauses_removed": 3,
    "num_original_clauses": 3,
    "num_original_vars": 3,
    "num_vars_eliminated": 0,
    "time_ms": 0.218
  },
  "status": "SAT"
}
```

### Bounded-Treewidth Demo, c=2

Command:

```powershell
python -m witnora_core.runner examples\treewidth_demo.dimacs --c 2
```

Output:

```json
{
  "c_parameter": 2,
  "collapse_path": [
    {
      "added_clauses": [],
      "assigned_literals": [],
      "details": {
        "elimination_order": [
          1,
          3,
          2,
          4,
          5
        ],
        "primal_edges": [
          [
            1,
            3
          ],
          [
            1,
            4
          ],
          [
            2,
            3
          ],
          [
            2,
            4
          ],
          [
            2,
            5
          ],
          [
            3,
            4
          ],
          [
            4,
            5
          ]
        ],
        "primal_vertices": [
          1,
          2,
          3,
          4,
          5
        ],
        "width_cap": 2,
        "width_observed": 2
      },
      "input_formula_hash": "bc56aad72afe8064b15c1ee16433461aba4363199eb1d902d0e90b0f1c30b117",
      "output_formula_hash": "bc56aad72afe8064b15c1ee16433461aba4363199eb1d902d0e90b0f1c30b117",
      "reconstruction_data": {
        "elimination_order": [
          1,
          3,
          2,
          4,
          5
        ]
      },
      "removed_clauses": [],
      "step_id": 1,
      "type": "TREEWIDTH_SOLVE"
    },
    {
      "added_clauses": [
        [
          -3,
          4
        ]
      ],
      "assigned_literals": [],
      "details": {
        "added_resolvents": [
          [
            -3,
            4
          ]
        ],
        "eliminated_variable": 1,
        "generated_resolvents": [
          {
            "negative_clause": [
              -3,
              -1
            ],
            "positive_clause": [
              1,
              4
            ],
            "resolvent": [
              -3,
              4
            ]
          }
        ],
        "status": "OK",
        "tautological_resolvents_discarded": [],
        "width_cap": 2,
        "width_observed": 2
      },
      "input_formula_hash": "bc56aad72afe8064b15c1ee16433461aba4363199eb1d902d0e90b0f1c30b117",
      "output_formula_hash": "1a6a25d68262dfdb87c92393e8b43d49247fa519a25a45195590e8e6e829f0c7",
      "reconstruction_data": {
        "added_resolvents": [
          [
            -3,
            4
          ]
        ],
        "eliminated_variable": 1,
        "input_formula_hash": "bc56aad72afe8064b15c1ee16433461aba4363199eb1d902d0e90b0f1c30b117",
        "output_formula_hash": "1a6a25d68262dfdb87c92393e8b43d49247fa519a25a45195590e8e6e829f0c7",
        "removed_clauses": [
          [
            -3,
            -1
          ],
          [
            1,
            4
          ]
        ]
      },
      "removed_clauses": [
        [
          -3,
          -1
        ],
        [
          1,
          4
        ]
      ],
      "step_id": 2,
      "type": "VE"
    },
    {
      "added_clauses": [
        [
          -4,
          2
        ],
        [
          2,
          4
        ]
      ],
      "assigned_literals": [],
      "details": {
        "added_resolvents": [
          [
            -4,
            2
          ],
          [
            2,
            4
          ]
        ],
        "eliminated_variable": 3,
        "generated_resolvents": [
          {
            "negative_clause": [
              -4,
              -3,
              2
            ],
            "positive_clause": [
              2,
              3
            ],
            "resolvent": [
              -4,
              2
            ]
          },
          {
            "negative_clause": [
              -3,
              4
            ],
            "positive_clause": [
              2,
              3
            ],
            "resolvent": [
              2,
              4
            ]
          }
        ],
        "status": "OK",
        "tautological_resolvents_discarded": [],
        "width_cap": 2,
        "width_observed": 2
      },
      "input_formula_hash": "1a6a25d68262dfdb87c92393e8b43d49247fa519a25a45195590e8e6e829f0c7",
      "output_formula_hash": "8d2dd333a2aeabab80d873aa76160cefa77097a9085465b27862b8bc24597334",
      "reconstruction_data": {
        "added_resolvents": [
          [
            -4,
            2
          ],
          [
            2,
            4
          ]
        ],
        "eliminated_variable": 3,
        "input_formula_hash": "1a6a25d68262dfdb87c92393e8b43d49247fa519a25a45195590e8e6e829f0c7",
        "output_formula_hash": "8d2dd333a2aeabab80d873aa76160cefa77097a9085465b27862b8bc24597334",
        "removed_clauses": [
          [
            -4,
            -3,
            2
          ],
          [
            -3,
            4
          ],
          [
            2,
            3
          ]
        ]
      },
      "removed_clauses": [
        [
          -4,
          -3,
          2
        ],
        [
          -3,
          4
        ],
        [
          2,
          3
        ]
      ],
      "step_id": 3,
      "type": "VE"
    },
    {
      "added_clauses": [
        [
          -4,
          5
        ],
        [
          4,
          5
        ]
      ],
      "assigned_literals": [],
      "details": {
        "added_resolvents": [
          [
            -4,
            5
          ],
          [
            4,
            5
          ]
        ],
        "eliminated_variable": 2,
        "generated_resolvents": [
          {
            "negative_clause": [
              -2,
              5
            ],
            "positive_clause": [
              -4,
              2
            ],
            "resolvent": [
              -4,
              5
            ]
          },
          {
            "negative_clause": [
              -2,
              5
            ],
            "positive_clause": [
              2,
              4
            ],
            "resolvent": [
              4,
              5
            ]
          }
        ],
        "status": "OK",
        "tautological_resolvents_discarded": [],
        "width_cap": 2,
        "width_observed": 2
      },
      "input_formula_hash": "8d2dd333a2aeabab80d873aa76160cefa77097a9085465b27862b8bc24597334",
      "output_formula_hash": "1bd87c38b27688f4d965a8b6e9d86dfa06350a7d5f1b6b7412b82fb9541122be",
      "reconstruction_data": {
        "added_resolvents": [
          [
            -4,
            5
          ],
          [
            4,
            5
          ]
        ],
        "eliminated_variable": 2,
        "input_formula_hash": "8d2dd333a2aeabab80d873aa76160cefa77097a9085465b27862b8bc24597334",
        "output_formula_hash": "1bd87c38b27688f4d965a8b6e9d86dfa06350a7d5f1b6b7412b82fb9541122be",
        "removed_clauses": [
          [
            -4,
            2
          ],
          [
            -2,
            5
          ],
          [
            2,
            4
          ]
        ]
      },
      "removed_clauses": [
        [
          -4,
          2
        ],
        [
          -2,
          5
        ],
        [
          2,
          4
        ]
      ],
      "step_id": 4,
      "type": "VE"
    },
    {
      "added_clauses": [
        [
          5
        ]
      ],
      "assigned_literals": [],
      "details": {
        "added_resolvents": [
          [
            5
          ]
        ],
        "eliminated_variable": 4,
        "generated_resolvents": [
          {
            "negative_clause": [
              -4,
              5
            ],
            "positive_clause": [
              4,
              5
            ],
            "resolvent": [
              5
            ]
          }
        ],
        "status": "OK",
        "tautological_resolvents_discarded": [
          {
            "negative_clause": [
              -5,
              -4
            ],
            "positive_clause": [
              4,
              5
            ],
            "resolvent": [
              -5,
              5
            ]
          }
        ],
        "width_cap": 2,
        "width_observed": 1
      },
      "input_formula_hash": "1bd87c38b27688f4d965a8b6e9d86dfa06350a7d5f1b6b7412b82fb9541122be",
      "output_formula_hash": "23013db636ad5c76398ab9a64394a46d696aca34dbf5715419c9fb8c3446707a",
      "reconstruction_data": {
        "added_resolvents": [
          [
            5
          ]
        ],
        "eliminated_variable": 4,
        "input_formula_hash": "1bd87c38b27688f4d965a8b6e9d86dfa06350a7d5f1b6b7412b82fb9541122be",
        "output_formula_hash": "23013db636ad5c76398ab9a64394a46d696aca34dbf5715419c9fb8c3446707a",
        "removed_clauses": [
          [
            -5,
            -4
          ],
          [
            -4,
            5
          ],
          [
            4,
            5
          ]
        ]
      },
      "removed_clauses": [
        [
          -5,
          -4
        ],
        [
          -4,
          5
        ],
        [
          4,
          5
        ]
      ],
      "step_id": 5,
      "type": "VE"
    },
    {
      "added_clauses": [],
      "assigned_literals": [],
      "details": {
        "added_resolvents": [],
        "eliminated_variable": 5,
        "generated_resolvents": [],
        "status": "OK",
        "tautological_resolvents_discarded": [],
        "width_cap": 2,
        "width_observed": 0
      },
      "input_formula_hash": "23013db636ad5c76398ab9a64394a46d696aca34dbf5715419c9fb8c3446707a",
      "output_formula_hash": "e160232d0ce8816f12ecdcdc7bb0e939b55fb5ca43414ae6077dfa3989655732",
      "reconstruction_data": {
        "added_resolvents": [],
        "eliminated_variable": 5,
        "input_formula_hash": "23013db636ad5c76398ab9a64394a46d696aca34dbf5715419c9fb8c3446707a",
        "output_formula_hash": "e160232d0ce8816f12ecdcdc7bb0e939b55fb5ca43414ae6077dfa3989655732",
        "removed_clauses": [
          [
            5
          ]
        ]
      },
      "removed_clauses": [
        [
          5
        ]
      ],
      "step_id": 6,
      "type": "VE"
    }
  ],
  "final_assignment": {},
  "final_class": "TREEWIDTH_LEQ_C",
  "final_formula_hash": "e160232d0ce8816f12ecdcdc7bb0e939b55fb5ca43414ae6077dfa3989655732",
  "original_formula_hash": "bc56aad72afe8064b15c1ee16433461aba4363199eb1d902d0e90b0f1c30b117",
  "original_verification": true,
  "reconstructed_original_assignment": {
    "1": true,
    "2": true,
    "3": false,
    "4": false,
    "5": true
  },
  "stats": {
    "collapse_path_length": 6,
    "num_clauses_added": 6,
    "num_clauses_removed": 12,
    "num_original_clauses": 6,
    "num_original_vars": 5,
    "num_vars_eliminated": 5,
    "time_ms": 0.666
  },
  "status": "SAT"
}
```

### Bounded-Treewidth Demo, c=1

Command:

```powershell
python -m witnora_core.runner examples\treewidth_demo.dimacs --c 1
```

Output:

```json
{
  "c_parameter": 1,
  "collapse_path": [],
  "final_assignment": {},
  "final_class": "UNRESOLVED",
  "final_formula_hash": "bc56aad72afe8064b15c1ee16433461aba4363199eb1d902d0e90b0f1c30b117",
  "original_formula_hash": "bc56aad72afe8064b15c1ee16433461aba4363199eb1d902d0e90b0f1c30b117",
  "original_verification": false,
  "reconstructed_original_assignment": {},
  "stats": {
    "collapse_path_length": 0,
    "num_clauses_added": 0,
    "num_clauses_removed": 0,
    "num_original_clauses": 6,
    "num_original_vars": 5,
    "num_vars_eliminated": 0,
    "time_ms": 0.238
  },
  "status": "NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C"
}
```

### UNSAT Formula

Command:

```powershell
python -m witnora_core.runner examples\unsat_demo.dimacs --c 2
```

Output:

```json
{
  "c_parameter": 2,
  "collapse_path": [
    {
      "added_clauses": [
        []
      ],
      "assigned_literals": [
        -1
      ],
      "details": {
        "assigned_literal": -1,
        "conflict": true,
        "satisfied_clauses": [
          [
            -1
          ]
        ],
        "shortened_clauses": [
          {
            "from": [
              1
            ],
            "to": []
          }
        ],
        "unit_clause": [
          -1
        ]
      },
      "input_formula_hash": "51a56adba97a49c01f215c3f4cd21fea1cf12b369748daa3990d3f7bd83948d0",
      "output_formula_hash": "69ee12c3118a428a28f674ec24e362b721e0611c800f65afbcb8a48e778c1394",
      "reconstruction_data": {
        "assigned_literal": -1
      },
      "removed_clauses": [
        [
          -1
        ],
        [
          1
        ]
      ],
      "step_id": 1,
      "type": "UP"
    }
  ],
  "final_assignment": {},
  "final_class": "CONFLICT",
  "final_formula_hash": "69ee12c3118a428a28f674ec24e362b721e0611c800f65afbcb8a48e778c1394",
  "original_formula_hash": "51a56adba97a49c01f215c3f4cd21fea1cf12b369748daa3990d3f7bd83948d0",
  "original_verification": false,
  "reconstructed_original_assignment": {},
  "stats": {
    "collapse_path_length": 1,
    "num_clauses_added": 1,
    "num_clauses_removed": 2,
    "num_original_clauses": 2,
    "num_original_vars": 1,
    "num_vars_eliminated": 0,
    "time_ms": 0.1
  },
  "status": "UNSAT"
}
```

### Determinism Rerun Check

Command:

```powershell
python -c "from witnora_core.cnf import CNFFormula; from witnora_core.runner import solve; import json; f=CNFFormula.from_raw_clauses([[1,2,3],[-1,-2],[-1,-3]]); a=solve(f,c=2).to_dict(); b=solve(f,c=2).to_dict(); print(json.dumps({'same_original_formula_hash': a['original_formula_hash']==b['original_formula_hash'], 'same_collapse_path': a['collapse_path']==b['collapse_path'], 'same_status': a['status']==b['status'], 'same_reconstructed_assignment': a['reconstructed_original_assignment']==b['reconstructed_original_assignment'], 'first_status': a['status'], 'second_status': b['status'], 'first_reconstructed_assignment': a['reconstructed_original_assignment'], 'second_reconstructed_assignment': b['reconstructed_original_assignment']}, indent=2, sort_keys=True))"
```

Output:

```json
{
  "first_reconstructed_assignment": {
    "1": true,
    "2": false,
    "3": false
  },
  "first_status": "SAT",
  "same_collapse_path": true,
  "same_original_formula_hash": true,
  "same_reconstructed_assignment": true,
  "same_status": true,
  "second_reconstructed_assignment": {
    "1": true,
    "2": false,
    "3": false
  },
  "second_status": "SAT"
}
```

The determinism check intentionally excludes `stats.time_ms`, which is expected to vary.

## 5. Implementation Confirmation

- No external SAT solver used: confirmed. No solver dependency exists.
- No brute-force solving of arbitrary formulas in implementation: confirmed. The solver paths are simplification, 2-SAT SCC, and bounded-width VE. One ad hoc tiny brute-force command was used only as a development oracle for random 3-variable 2-SAT self-checks; it is not in the code or test suite.
- 2-SAT solver implemented internally: confirmed, in `witnora_core/two_sat.py`, using implication graph SCC.
- Exact bounded-width elimination-order search implemented for `c <= 4`: confirmed, in `witnora_core/treewidth.py`.
- Primal graph used for treewidth: confirmed, in `witnora_core/primal.py` and `runner.py`.
- VE reconstruction uses corrected sign rule: confirmed, in `witnora_core/reconstruction.py`.
- BCE reconstruction sets the blocked literal to true when the removed clause is falsified: confirmed, in `reconstruct_bce_step`.
- Every SAT result verifies against the original CNF: confirmed by `runner._finalize`, `reconstruct_assignment`, and `verify_collapse_path`.
- Every transformation is logged: confirmed for UP, PLE, SUB, BCE, CD marker, TREEWIDTH_SOLVE, VE, and 2SAT_SOLVE.
- Verifier can replay collapse path: confirmed, in `witnora_core/verifier.py`.
- Same input produces deterministic certificate fields: confirmed for hash, collapse path, status, and reconstructed assignment. `stats.time_ms` is runtime-dependent.

## 6. Deviations and Limitations

- Component decomposition is implemented as an incidence-graph split marker/log (`CD`) but the runner does not recursively solve each component independently. The current runner solves the simplified formula as one object through 2-SAT or a single primal-treewidth route.
- There is no explicit timeout mechanism, although `TIMEOUT` is included as an allowed status constant.
- The internal verifier is replay-based and implementation-level. It does not emit LRAT/FRAT.
- DIMACS declared variables that never appear in any retained clause are not preserved as explicit formula variables after normalization. Assignments are filled for variables present in the original normalized formula.
- Duplicate and tautological clauses are normalized away, but the parser does not currently return a warning list describing which were removed.
- The repository was not initialized as a new git repo and no zip file was created. The exact code files are in the workspace tree above.

## 7. Known Bugs or Weak Spots

- Exact bounded-width order search is exponential and intended only for v0 small-`c` use. Larger formulas may be slow.
- No timeout means a large non-collapsing instance can run until the exact search finishes.
- `stats.time_ms` prevents byte-for-byte equality of complete JSON outputs across runs; deterministic certificate fields are stable.
- The verifier relies on replaying the deterministic local implementation, not on an independent proof-checking format.
- Component-level independent solving needs review/implementation if strict decomposition semantics are required in the next milestone.

## 8. Key Code Summary

- CNF canonicalization and hashing: `Clause` removes duplicate literals, rejects tautological clauses by returning `None` during normalization, sorts literals, and `CNFFormula` removes duplicate clauses and sorts clauses. Hashing uses SHA-256 over canonical DIMACS-style serialization.
- Deterministic simplifier `S`: `simplify.py` loops UP, PLE, SUB, BCE, then CD marker in fixed order until no change or conflict.
- BCE detection: `bce.py` scans clauses by descending length then lexicographic order, scans literals by variable id with positive before negative, and checks every opposite-literal resolvent is tautological. The log includes checked resolvents and a proof digest.
- Exact bounded-width order search: `treewidth.py` recursively eliminates vertices with current degree `<= c`, adds fill edges, memoizes failed graph states, and independently verifies the returned order.
- Variable elimination: `ve.py` uses an explicit order, resolves positive and negative clauses for each variable, discards tautological resolvents, enforces `len(resolvent) <= c`, logs removed clauses and added resolvents.
- Reconstruction engine: `reconstruction.py` reverses logged steps. UP/PLE assign logged literals, BCE repairs falsified removed clauses by setting the blocked literal true, and VE chooses the eliminated variable value from falsified removed clauses using the sign-correct rule.
- Collapse path verifier: `verifier.py` replays each step from the original formula, checks hashes and exact transform behavior, validates treewidth order and VE resolvents, re-runs 2-SAT checks, and verifies the final original assignment for SAT or contradiction for UNSAT.
- Runner CLI: `runner.py` loads DIMACS, simplifies, chooses EMPTY/2-SAT/treewidth route/no-collapse, reconstructs SAT witnesses, verifies the certificate before returning certified SAT/UNSAT JSON, and exposes `python -m witnora_core.runner`.

## 9. Files

Final code files are in this workspace:

```text
witnora_core/__init__.py
witnora_core/bce.py
witnora_core/certificate.py
witnora_core/cnf.py
witnora_core/components.py
witnora_core/dimacs.py
witnora_core/primal.py
witnora_core/reconstruction.py
witnora_core/runner.py
witnora_core/simplify.py
witnora_core/subsumption.py
witnora_core/treewidth.py
witnora_core/two_sat.py
witnora_core/ve.py
witnora_core/verifier.py
tests/test_bce_demo.py
tests/test_determinism.py
tests/test_no_collapse.py
tests/test_reconstruction.py
tests/test_treewidth_demo.py
tests/test_unsat.py
examples/bce_demo.dimacs
examples/treewidth_demo.dimacs
examples/unsat_demo.dimacs
README.md
.gitignore
COMPLETION_REPORT.md
```

No zip or remote repo link was created.

---

# Patch Report: Component Recursion, CD Replay, Certificate Hash

## Changed Files

```text
README.md
COMPLETION_REPORT.md
examples/multi_component_demo.dimacs
tests/test_components.py
tests/test_determinism.py
witnora_core/certificate.py
witnora_core/components.py
witnora_core/runner.py
witnora_core/simplify.py
witnora_core/verifier.py
```

## Commands Run After Patch

```powershell
python -m compileall -q witnora_core tests
python -m unittest discover
python -m witnora_core.runner examples\multi_component_demo.dimacs --c 2
python -c "from witnora_core.cnf import CNFFormula; from witnora_core.runner import solve; import json; f=CNFFormula.from_raw_clauses([[1,2,3],[-1,-2],[-1,-3],[4,5],[-4,5]]); a=solve(f,c=2).to_dict(); b=solve(f,c=2).to_dict(); print(json.dumps({'first_certificate_hash': a['certificate_hash'], 'second_certificate_hash': b['certificate_hash'], 'same_certificate_hash': a['certificate_hash']==b['certificate_hash'], 'same_collapse_path': a['collapse_path']==b['collapse_path'], 'same_status': a['status']==b['status'], 'first_time_ms': a['stats']['time_ms'], 'second_time_ms': b['stats']['time_ms']}, indent=2, sort_keys=True))"
python -m witnora_core.runner examples\treewidth_demo.dimacs --c 2
python -m witnora_core.runner examples\treewidth_demo.dimacs --c 1
python -c "from tests.test_components import component_no_collapse_formula; from witnora_core.runner import solve; import json; print(json.dumps(solve(component_no_collapse_formula(), c=1).to_dict(), indent=2, sort_keys=True))"
```

## Full Test Output

```text
BCE_RECONSTRUCTION_PASS
COMPONENT_NO_COLLAPSE_PASS
COMPONENT_SOLVE_PASS
DETERMINISM_PASS
NO_COLLAPSE_PASS
RECONSTRUCTION_PASS
TREEWIDTH_COLLAPSE_PASS
UNSAT_PASS
........
----------------------------------------------------------------------
Ran 8 tests in 0.005s

OK
```

## Multi-Component Example JSON

Command:

```powershell
python -m witnora_core.runner examples\multi_component_demo.dimacs --c 2
```

Output:

```json
{
  "c_parameter": 2,
  "certificate_hash": "6b1f0225480376003fa93c0a04703a45d70025ade0d44b99a515e5ff90d3479a",
  "collapse_path": [
    {
      "added_clauses": [],
      "assigned_literals": [],
      "details": {
        "component_count": 2,
        "components": [
          {
            "clause_indices": [0, 4],
            "clauses": [[-4, 5], [4, 5]],
            "component_id": "0",
            "formula_hash": "b2afef252bd2bb64590720c8732b69fa3647f6ad86e78749392a285f0873da33",
            "variables": [4, 5]
          },
          {
            "clause_indices": [1, 2, 3],
            "clauses": [[-3, -1], [-2, -1], [1, 2, 3]],
            "component_id": "1",
            "formula_hash": "896337a8730f733524ead5682cdddfd54dc85ae87b5b76d27f79c266083c2422",
            "variables": [1, 2, 3]
          }
        ],
        "incidence_edges": [[4, 0], [5, 0], [1, 1], [3, 1], [1, 2], [2, 2], [1, 3], [2, 3], [3, 3], [4, 4], [5, 4]],
        "parent_component_id": null
      },
      "input_formula_hash": "d3c0788cbc927b3da4d37734fe333b9bc4ecc63d91528e6762f9fd771ea73a36",
      "output_formula_hash": "d3c0788cbc927b3da4d37734fe333b9bc4ecc63d91528e6762f9fd771ea73a36",
      "reconstruction_data": {
        "component_ids": ["0", "1"],
        "parent_component_id": null
      },
      "removed_clauses": [],
      "step_id": 1,
      "type": "CD"
    },
    {
      "added_clauses": [],
      "assigned_literals": [],
      "details": {
        "assignment": {"4": false, "5": true},
        "component_id": "0",
        "edges": [[-5, -4], [-5, 4], [-4, 5], [4, 5]],
        "num_implication_edges": 4,
        "num_implication_nodes": 4,
        "sccs": [[-5], [4], [-4], [5]],
        "status": "SAT"
      },
      "input_formula_hash": "b2afef252bd2bb64590720c8732b69fa3647f6ad86e78749392a285f0873da33",
      "output_formula_hash": "b2afef252bd2bb64590720c8732b69fa3647f6ad86e78749392a285f0873da33",
      "reconstruction_data": {"assignment": {"4": false, "5": true}, "component_id": "0"},
      "removed_clauses": [],
      "step_id": 2,
      "type": "2SAT_SOLVE"
    },
    {
      "added_clauses": [],
      "assigned_literals": [],
      "details": {
        "blocked_literal": 1,
        "checked_resolvents": [
          {"against_clause": [-3, -1], "resolvent": [-3, 2, 3], "tautological": true},
          {"against_clause": [-2, -1], "resolvent": [-2, 2, 3], "tautological": true}
        ],
        "component_id": "1",
        "opposite_clauses": [[-3, -1], [-2, -1]],
        "proof_digest": "b4a048e11f4c94b3182bd7b5d1265ec7e591615174fa96e951ab5a7a2f76ad6f",
        "removed_clause": [1, 2, 3]
      },
      "input_formula_hash": "896337a8730f733524ead5682cdddfd54dc85ae87b5b76d27f79c266083c2422",
      "output_formula_hash": "a94ac0e4015529e375ff67d33538a3926f8c9fc1d140bcea94c8d94529de48e3",
      "reconstruction_data": {
        "blocked_literal": 1,
        "component_id": "1",
        "opposite_clauses": [[-3, -1], [-2, -1]],
        "removed_clause": [1, 2, 3]
      },
      "removed_clauses": [[1, 2, 3]],
      "step_id": 3,
      "type": "BCE"
    },
    {
      "added_clauses": [],
      "assigned_literals": [-1],
      "details": {
        "assigned_literal": -1,
        "component_id": "1",
        "removed_due_to_pure_literal": [[-3, -1], [-2, -1]]
      },
      "input_formula_hash": "a94ac0e4015529e375ff67d33538a3926f8c9fc1d140bcea94c8d94529de48e3",
      "output_formula_hash": "e160232d0ce8816f12ecdcdc7bb0e939b55fb5ca43414ae6077dfa3989655732",
      "reconstruction_data": {"assigned_literal": -1, "component_id": "1"},
      "removed_clauses": [[-3, -1], [-2, -1]],
      "step_id": 4,
      "type": "PLE"
    }
  ],
  "final_assignment": {"4": false, "5": true},
  "final_class": "2SAT",
  "final_formula_hash": "b2afef252bd2bb64590720c8732b69fa3647f6ad86e78749392a285f0873da33",
  "original_formula_hash": "d3c0788cbc927b3da4d37734fe333b9bc4ecc63d91528e6762f9fd771ea73a36",
  "original_verification": true,
  "reconstructed_original_assignment": {"1": true, "2": false, "3": false, "4": false, "5": true},
  "stats": {
    "collapse_path_length": 4,
    "num_clauses_added": 0,
    "num_clauses_removed": 3,
    "num_original_clauses": 5,
    "num_original_vars": 5,
    "num_vars_eliminated": 0,
    "time_ms": 0.413
  },
  "status": "SAT"
}
```

## Certificate Hash Rerun Check

```json
{
  "first_certificate_hash": "6b1f0225480376003fa93c0a04703a45d70025ade0d44b99a515e5ff90d3479a",
  "first_time_ms": 0.375,
  "same_certificate_hash": true,
  "same_collapse_path": true,
  "same_status": true,
  "second_certificate_hash": "6b1f0225480376003fa93c0a04703a45d70025ade0d44b99a515e5ff90d3479a",
  "second_time_ms": 0.289
}
```

## Patch Confirmations

- Component solving is now recursive: a `CD` step creates component IDs, each component is solved independently, and nested splits are represented with child component IDs.
- CD replay verification works: verifier recomputes incidence edges and components, checks exact clause partition, disjoint variable ownership, no crossing clauses, component-local step hashes, and final assignment merge consistency.
- `certificate_hash` is deterministic across reruns and excludes `stats.time_ms`.
- The multi-component SAT test verifies component 1 collapses through BCE/PLE, component 2 solves via internal 2-SAT, merged assignment satisfies the original formula, and verifier accepts the split/merge.
- The multi-component no-collapse test verifies a solvable component can be processed first while the full formula still returns `NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C` when another component exceeds the c-budget. It does not return partial SAT.

---

# v0.0.1 Freeze Hardening Report

## Changed Files

```text
README.md
COMPLETION_REPORT.md
examples/multi_component_demo.dimacs
tests/test_adversarial_correctness.py
tests/test_components.py
tests/test_determinism.py
witnora_core/certificate.py
witnora_core/reconstruction.py
witnora_core/runner.py
witnora_core/verifier.py
```

## Package

Created:

```text
witnora-core-v0.0.1.zip
```

Archive contents:

```text
witnora_core/
witnora_core/bce.py
witnora_core/certificate.py
witnora_core/cnf.py
witnora_core/components.py
witnora_core/dimacs.py
witnora_core/primal.py
witnora_core/reconstruction.py
witnora_core/runner.py
witnora_core/simplify.py
witnora_core/subsumption.py
witnora_core/treewidth.py
witnora_core/two_sat.py
witnora_core/ve.py
witnora_core/verifier.py
witnora_core/__init__.py
tests/
tests/test_adversarial_correctness.py
tests/test_bce_demo.py
tests/test_components.py
tests/test_determinism.py
tests/test_no_collapse.py
tests/test_reconstruction.py
tests/test_treewidth_demo.py
tests/test_unsat.py
tests/__init__.py
examples/
examples/bce_demo.dimacs
examples/multi_component_demo.dimacs
examples/treewidth_demo.dimacs
examples/unsat_demo.dimacs
README.md
COMPLETION_REPORT.md
.gitignore
```

## Full Test Output

Command:

```powershell
python -m unittest discover
```

Output:

```text
ABSENT_DIMACS_VARIABLE_PASS
BCE_FORCED_REPAIR_PASS
C_ZERO_PASS
CROSS_COMPONENT_SPLIT_REJECT_PASS
EMPTY_FORMULA_SAT_PASS
NO_BRUTE_FORCE_NO_COLLAPSE_PASS
NON_BLOCKED_BCE_REJECT_PASS
TAUTOLOGY_NORMALIZATION_PASS
VE_CONFLICT_DETECTION_PASS
VE_SIGN_RECONSTRUCTION_PASS
VERIFIER_NEGATIVE_TESTS_PASS
BCE_RECONSTRUCTION_PASS
COMPONENT_NO_COLLAPSE_PASS
COMPONENT_SOLVE_PASS
DETERMINISM_PASS
NO_COLLAPSE_PASS
RECONSTRUCTION_PASS
TREEWIDTH_COLLAPSE_PASS
UNSAT_PASS
...................
----------------------------------------------------------------------
Ran 19 tests in 0.007s

OK
```

## Final Schema Notes

- Multi-component SAT output uses `"final_class": "COMPONENTS_SOLVED"`.
- Output includes deterministic `component_results`.
- `certificate_hash` includes `component_results` and excludes `stats.time_ms`.
- Determinism test compares `certificate_hash`.

## Certificate Hash Rerun Proof

```json
{
  "first_certificate_hash": "4edb998a2eb52d663e33be8e9f7121edd061682e121b3745d4c974cd4ea52a4a",
  "first_time_ms": 0.4,
  "same_certificate_hash": true,
  "same_collapse_path": true,
  "same_component_results": true,
  "same_status": true,
  "second_certificate_hash": "4edb998a2eb52d663e33be8e9f7121edd061682e121b3745d4c974cd4ea52a4a",
  "second_time_ms": 0.287
}
```

## Confirmations

- All old tests pass.
- All adversarial tests pass.
- No external SAT solver was added.
- No arbitrary brute-force solving was added.
- No GNN, MCTS, LRAT/FRAT, or P vs NP claim was added.
- No `HARD` or `UNKNOWN` output status is emitted.

## Remaining Limitations

- No timeout mechanism yet.
- No LRAT/FRAT proof output.
- Exact bounded-width search is exponential and intentionally scoped to `c <= 4`.
- The verifier is an internal replay verifier, not an independent external proof checker.
