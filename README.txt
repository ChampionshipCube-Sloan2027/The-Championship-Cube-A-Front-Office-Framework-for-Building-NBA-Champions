# The Championship Cube

A six-dimensional framework for evaluating NBA championship contention --
**Team Face, Player Face, Coach Face, Front Office Face, Controllable
External Face, Uncontrollable External Face** -- built from a dataset of 74
team-seasons (37 champions, 37 Finals runners-up) spanning three eras of
NBA history, 1990-2026. This repository accompanies the paper *"The
Championship Cube: A Front Office Framework for Building NBA Champions,"*
submitted to the MIT Sloan Sports Analytics Conference (SSAC) 2027.

It contains two things:

1. The **historical research dataset and analysis** used to test the
   framework retrospectively (statistically validated for Team Face and
   Player Face; null results for Coach Face, honestly reported).
2. **KIRIN**, a live self-assessed diagnostic prototype that applies the
   same six-face structure forward-looking, for a front office to score
   its own team.

## Repository structure

```
.
├── kirin_prototype.py                                  # KIRIN diagnostic tool + smoke tests
├── Championship-Cube-Era-Analysis.py                    # historical era/trend analysis
├── Data/
│   ├── Championship-Cube-Master-Dataset(Winner).csv     # 37 champion team-seasons
│   ├── Championship-Cube-Master-Dataset(Lossers).csv    # 37 Finals runner-up team-seasons
│   └── Championship-Cube-Coach-Face.csv                 # Coach Face scores, both groups
├── Championship-Cube-Qualitative-Coding-Audit-README.csv  # scaffold for the historical qualitative audit
├── requirements.txt
├── LICENSE
├── CITATION.cff
└── CHANGELOG.md
```

The historical qualitative coding workbook itself
(`Championship_Cube_Qualitative_Coding_Audit.xlsx`, 74 rows) is tracked
separately and is **not** included here in completed form -- see
[Qualitative audit status](#qualitative-audit-status) below.

## Data sources

- Team, player, and coach statistics: [Basketball Reference](https://www.basketball-reference.com/).
- SRS, ORtg, DRtg, Pace, Net Rating, and box-score fields are as published
  by Basketball Reference for each season.
- Player BPM figures are the top-three rostered players by BPM for that
  team-season ("Combined Top-3 BPM").
- Coach Face scores are a manually coded rubric input (see the audit
  workbook), not a Basketball Reference field.

## KIRIN vs. the historical rubric: two separate instruments

**This distinction matters and is easy to get wrong, so it's stated in the
code, the on-screen output, and here:**

- The **historical paper audit** scores each team-season with one holistic
  **0-2** score per qualitative face, based on documented case evidence.
- The **KIRIN prototype** asks three Yes / Partial / No / Insufficient
  evidence questions per face and converts them to a **0-10** diagnostic
  score, for a user assessing a team going forward.
- These are related applications of the same framework but are **not
  numerically interchangeable**. KIRIN's output should never be read as a
  reproduction of, or substitute for, the historical 0-2 coding.

## Quickstart

```bash
git clone <this-repo>
cd championship-cube
python -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
python kirin_prototype.py
```

Expected output (verified in a clean virtualenv against the CSVs in this
repo):

```
Validation smoke test passed: SRS and BPM regressions match published statistics; Coach Face remains a null result
KIRIN smoke test passed
```

If either line is missing, something in the data or environment has
changed -- see [Smoke tests](#smoke-tests) below for what each one checks.

## Using KIRIN

From Python:

```python
from kirin_prototype import run_from_answers

answers = {
    "Player Face": [
        {"answer": "Yes", "note": "Has a clear low-usage two-way wing."},
        {"answer": "Partial", "note": ""},
        {"answer": "Insufficient evidence", "note": "Draft-vs-trade split not yet researched."},
    ],
    "Front Office Face": [...],   # one entry per FACE_QUESTIONS[face]
    "Coach Face": [...],
    "Controllable External": [...],
    "Uncontrollable External": [...],
}

result = run_from_answers(
    "My Team", team_srs=6.5, ans_by_face=answers,
    team_ortg=114, team_drtg=108, team_pace=99, team_year=2026,
)
```

From a Jupyter notebook, `launch_guided_ui()` renders an interactive form
(team info, SRS, and Yes/Partial/No/Insufficient-evidence dropdowns with an
evidence-note field per question) and can export a PDF report.

Every self-assessed face reports:
- a 0-10 score,
- an **Input confidence** (based on answer consistency, reduced when
  evidence is marked insufficient),
- the three underlying answers and any evidence notes,
- a fixed disclosure that self-assessed inputs are not independently
  validated.

The composite **Scenario readiness index** and **Composite Cube score**
always carry the disclosure that they are an exploratory heuristic, not a
calibrated probability of winning.

## Smoke tests

Running `python kirin_prototype.py` executes two checks:

1. **`run_validation_smoke_test()`** -- loads the exact CSVs in `Data/`
   and confirms the headline regression outputs still match the paper's
   published statistics: Team Face (SRS) AUC ≈ 0.677, p ≈ 0.0035; Player
   Face (Combined Top-3 BPM) AUC ≈ 0.698, p ≈ 0.0034; Coach Face p ≥ 0.05
   (null result, as published). n = 74 for all three.
2. **`run_smoke_test()`** -- runs a full KIRIN audit end-to-end and checks:
   different SRS values move the Team Face score and composite; Team Face
   is *unaffected* by ORtg/DRtg/Pace changes; missing ORtg/DRtg/Pace values
   don't crash a run; results are deterministic given the same inputs; an
   "Insufficient evidence" answer lowers confidence without being scored as
   "No"; a face with zero substantiated answers raises an error rather than
   scoring silently; the calibration disclosure text is present; and a PDF
   report generates successfully.

## Weighting and methodology notes

All six faces receive **equal weight** in the Composite Cube score. Model
AUC, coefficients, p-values, and sample sizes reported for the data-tested
faces (Team, Player, Coach) are evidence of predictive validity for those
individual faces -- they are **not** used to derive composite weights, and
the composite itself is not trained or calibrated against a historical
six-face outcome. This is a deliberate choice: deriving weights from the
same statistics used to test significance would be closer to circular
reasoning than to a defensible weighting scheme.

## Qualitative audit status

`Championship-Cube-Qualitative-Coding-Audit-README.csv` in this repo is the
**scaffold's own documentation**, not the completed audit. Per its own
rules: the quantitative fields are populated from the research datasets,
but the qualitative 0-2 scores, evidence, coding rationale, and
second-coder checks are still required before any "Four-of-Six" alignment
result can be reported as a finding. Until that workbook is completed and
reviewed, this repository does not claim a validated Four-of-Six result --
only the two data-tested faces (Team Face, Player Face) currently carry
statistical evidence.

## License

MIT -- see [`LICENSE`](LICENSE).

## Citation

See [`CITATION.cff`](CITATION.cff).
