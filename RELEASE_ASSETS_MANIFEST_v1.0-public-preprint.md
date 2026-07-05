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
| `witnora-paper-overleaf-v1.0-public-preprint-bundle.zip` | `10D41E18F8808752A869E7C9D3F8AA79BC0C4BB0DF2D5F43B3E24D6918517357` | Overleaf upload bundle |
| `paper/witnora_tseitin_certified_collapse.pdf` | `A98910C817974D3D15F6847690CD197008362A06984FA38BE81194BE7D26DB9A` | compiled paper PDF |
| `RELEASE_NOTES_v1.0-public-preprint.md` | `B41C6BCBB7A02DAC0E45C5E12847CA373D4A1B5538D941206F76D6140145777A` | release notes |
| `SUBMISSION_CHECKLIST.md` | `D4C09A0DB92083A66873B13D485EC48917613A497679A9422C9D0154CF9B2FA6` | submission checklist |
| `README_compile_overleaf.md` | `5C921F7C63FD29A57E3C871803638E7DD165F8AFDE37B07B90F04372301E1324` | Overleaf compile instructions |
| `paper/witnora_tseitin_certified_collapse.tex` | `8B83BE7890AA99B7A67E23FF756E4D188C76CD85C6A445BC6B651E228B9D3250` | LaTeX source |
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

Local PDF compilation was completed with Tectonic 0.16.9.

Compiler archive used:

`tectonic-0.16.9-x86_64-pc-windows-msvc.zip`

Compiler archive SHA256:

`131A24604785A9600989A3D91225F597DF52AC06F00AEFFE86FD529F99EE5CDD`

Compile command:

```powershell
tools\tectonic\tectonic-0.16.9\tectonic.exe paper\witnora_tseitin_certified_collapse.tex --keep-logs --keep-intermediates -o paper
```

The generated PDF was rendered for visual inspection. The final LaTeX log had
no overfull hbox warnings, undefined citations, or fatal errors. The Windows
run emitted a fontconfig notice, but the PDF was produced and rendered
successfully.

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
