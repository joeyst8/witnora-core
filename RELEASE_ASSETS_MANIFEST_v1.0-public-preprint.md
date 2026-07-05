# Witnora-Core v1.0 Public Preprint Release Assets Manifest

## Release

- Release title: `Witnora-Core v1.0 Public Preprint`
- Source tag: `v1.0-public-preprint`
- Source tag commit: `106904a91693ae672712c4818ef10790ff919e15`

## Assets

| asset | SHA256 | status |
| --- | --- | --- |
| `witnora-core-v1.0-public-preprint.zip` | `D79E4FCD48A18C395584EF04199D7156C63503B66F20385451E4B3F31176EFB2` | source archive |
| `witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip` | `4702299E28CDB4E3B16B0CD1CBFE9BA96018E625C0E8864A1C0476C2AEC3FA2C` | separate diagnostic artifact |
| `witnora-paper-overleaf-v1.0-public-preprint-bundle.zip` | `30B30254FB6A3559307B6FB5CAE958B5C53A9AE2CF329EC98810243C08F84B3C` | Overleaf upload bundle |
| `paper/witnora_tseitin_certified_collapse.pdf` | not available | PDF must be compiled in Overleaf or another LaTeX environment |
| `RELEASE_NOTES_v1.0-public-preprint.md` | `43A9FF5B12726812389B98FC36D1ABCB904A67420A8829B0CE97E48EAD4A4718` | release notes |
| `SUBMISSION_CHECKLIST.md` | `561E773F219BFF4F8A43A213DA5BBF755B1AA319E5339BACC611E667E29E8BF9` | submission checklist |
| `README_compile_overleaf.md` | `5C921F7C63FD29A57E3C871803638E7DD165F8AFDE37B07B90F04372301E1324` | Overleaf compile instructions |
| `paper/witnora_tseitin_certified_collapse.tex` | `C95FFB45FF38F78613FF5DA129A548661D21924788CC05F5960AA1DB73CEA791` | LaTeX source |
| `paper/references.bib` | `D5B04278642375099320F90168F941587A5C27E1DD88F370D5F143CBE7D1F547` | BibTeX bibliography |

## Overleaf Bundle Contents

The Overleaf bundle contains:

- `witnora_tseitin_certified_collapse.tex`
- `references.bib`
- `figures/certification_flow.md`
- `figures/pipeline_ascii.txt`
- `figures/version_progression_table.md`
- `README_compile_overleaf.md`

## PDF Status

Local PDF compilation was not completed because the available execution
environment did not provide `pdflatex`, `bibtex`, `latexmk`, `pandoc`,
`xelatex`, `lualatex`, or `tectonic`.

Use `witnora-paper-overleaf-v1.0-public-preprint-bundle.zip` in Overleaf and
download the compiled PDF as:

`witnora_tseitin_certified_collapse.pdf`

## Main Public Claim

Witnora-Core externally DRAT-verifies the recorded official CNFgen Tseitin rows,
including `tseitin_20 c=2`, using exact CNF XOR extraction and deterministic
sparse/min-fill XOR proof export against `original.dimacs`.

## Claim Boundary

This release does not claim:

- parity support
- broad XOR extraction
- CryptoMiniSat-style extraction
- competitive SAT solving
- industrial benchmark performance
- full DRAT/RAT/LRAT/FRAT support
- general SAT solving
- P vs NP progress

## Validation Command

```powershell
$env:WITNORA_DRAT_TRIM='C:\Users\maham\AppData\Local\Temp\witnora-drat-trim-real\drat-trim\drat-trim.exe'
python -m unittest discover -s tests -v
```

Expected result:

- 188 tests passing
- real drat-trim tests run and pass
- min-fill tests pass
- public category tests pass
- v0.9.8 diagnostic tests pass
