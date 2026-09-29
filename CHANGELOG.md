# Changelog

## SSAC 2027 abstract submission (September 2026)

### Added
- `Championship-Cube-Paired-Analysis.py` and `Paired-Analysis-Results.md`: matched-pair conditional-logit analysis, franchise-clustered bootstrap, SRS-vs-BPM comparison, out-of-sample checks (leave-one-pair-out, temporal hold-out, expanding window), Front Office proxy tests.
- `Championship-Cube-Figure1.py` and `Figure1_paired_finals.png`.
- `pilot/`: completed coding sheet, answer key and analysis script for the 10-pair qualitative pilot (single coder; reliability not assessed).
- `Championship-Cube-Coach-Face.csv` handling documented (two stacked tables with repeated header rows).

### Changed
- `kirin_prototype.py`: running the file now prints both smoke tests and skips the notebook UI when ipywidgets/IPython are unavailable (previously it crashed after the first test outside a notebook).
- `requirements.txt` lists every imported package.
- README rewritten to match the submitted abstract: paired estimates are the primary results; pooled figures are identified as the earlier analysis; the qualitative faces are described as an unvalidated pilot.
