KIRIN: The Championship Cube

A Front-Office Framework for Building NBA Champions

Research project submitted to the MIT Sloan Sports Analytics Conference 2027.

**Author:** Mohammad Rahman

KIRIN is an interpretable championship-readiness diagnostic built on the Championship Cube: a six-dimensional framework for examining how NBA teams are constructed, perform, and respond to pressure.

The project examines whether NBA championships can be better understood through the alignment of statistical, organisational, and contextual factors rather than talent alone.

Research question

What statistical, organisational, and contextual characteristics distinguish NBA champions from Finals runners-up across different eras of the NBA?

## Why this project exists

Championships are often explained as if one superstar, one statistic, or one front-office move determines success. The Championship Cube takes a broader view.

It examines six connected faces of championship construction:

1. Team.
2. Players.
3. Coaching.
4. Front-office decision-making.
5. Controllable external conditions.
6. Uncontrollable external conditions.

The purpose is not to claim that every championship can be reduced to one formula. The purpose is to create an interpretable framework that helps explain why some teams are structurally better prepared for a title run than others.

Data and sample

The quantitative analysis contains 74 Finals team-seasons:

- 37 NBA champions.
- 37 Finals runners-up.
- Seasons from 1990 through 2026.
- Three eras: Physical, Transition, and Analytics.

Basketball-Reference is the primary public data source.

The analysis includes:

- SRS.
- Net Rating.
- Defensive Rating.
- Player Face measures.
- Coach Face measures.
- Era comparisons.
- Champion-versus-runner-up matched-pair comparisons.
- Logistic regression.

The Finals-only design is intentional: comparing champions with the teams they defeated provides a direct test of what separated the winner from the runner-up at the final stage of competition.

The six faces

| Face | What it examines |
|---|---|
| Team Face | Roster quality, balance, performance, and era-adjusted team strength. |
| Player Face | Player impact, role hierarchy, acquisition, and complementarity. |
| Coach Face | Coaching overperformance, system fit, culture, and roster alignment. |
| Front Office Face | Drafting, trades, free agency, payroll discipline, and long-term decision-making. |
| Controllable External Face | Workload management, scheduling, depth, recovery, and sports science. |
| Uncontrollable External Face | Injuries, variance, resilience, and the ability to absorb bad breaks. |

Main findings

The current quantitative results include:

- Player Face is the strongest standalone signal in the tested models, achieving 75.7% matched-pair accuracy across 37 Finals comparisons (28 of 37; p=0.003).
- SRS also distinguishes champions from Finals runners-up (β=0.33, p=0.0035, n=74), achieving 67.6% matched-pair accuracy (25 of 37).
- Player Face and SRS are moderately correlated (r=0.61), indicating that they capture related but non-identical information.
- Coach Face does not significantly distinguish champions from Finals runners-up in the Finals-only comparison (p≈0.62).
- The SRS gap between champions and Finals runners-up increased from 0.67 in the Physical Era to 2.65 in the Analytics Era.

Statistical significance was assessed using pooled logistic regression. Predictive performance was evaluated using matched-pair accuracy. These are different quantities and are reported separately.

KIRIN prototype

KIRIN operationalises the Championship Cube for current-team analysis.

KIRIN:

- Scores each face using an interpretable rubric.
- Identifies a team’s weakest face.
- Produces scenario-based results.
- Provides targeted recommendations.
- Separates controllable weaknesses from external uncertainty.

KIRIN is a scenario diagnostic, not a calibrated prediction model.

Its scores should not be interpreted as guaranteed probabilities. A higher-scoring team is not guaranteed to win a championship, and a lower-scoring team is not mathematically eliminated. The tool is designed to identify structural strengths, weaknesses, and possible pressure points.

## Historical audit and live diagnostic

The retrospective historical audit and the live KIRIN prototype use related but distinct instruments.

The historical audit uses a documented face-level 0–2 coding rubric:

- 0 = absent or harmful.
- 1 = partial or mixed.
- 2 = clear alignment.

KIRIN uses three operational Yes/Partial/No questions per face:

- Yes = 2.
- Partial = 1.
- No = 0.

The historical audit is designed to document retrospective case-study judgements. KIRIN is designed to assess a current team through a repeatable decision-support interface.

These two systems should therefore not be treated as identical statistical instruments.

Repository structure

```text
.
├── data/
│   ├── championship-cube-master-dataset(Winner).csv
│   ├── championship-cube-master-dataset(Lossers).csv
│   └── championship-cube-coach-face.csv
├── scripts/
│   └── championship-cube-era-analysis.py
├── kirin/
│   └── prototype files
├── audit/
│   └── Championship_Cube_Qualitative_Coding_Audit.xlsx
├── abstract/
│   └── submitted abstract
├── paper/
│   └── research paper
├── notes/
├── requirements.txt
├── CITATION.cff
├── LICENSE
└── README.md
```

Folder names may change as the repository develops. This README will be updated if the structure changes.

Installation

Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
cd YOUR-REPOSITORY
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Requirements

The main analysis uses Python and the packages listed in `requirements.txt`.

The current dependency list includes:

```text
pandas
numpy
scikit-learn
scipy
matplotlib
seaborn
openpyxl
```

Running the analysis

Run the main analysis script from the repository root:

```bash
python scripts/championship-cube-era-analysis.py
```

The script loads the files in `data/`, performs the statistical analysis, and produces the reported era comparisons and champion-versus-runner-up results.

The analysis is designed to use repository-relative paths. It should not require Google Colab-specific paths or manually created `/content/` folders.

Reproducibility

The repository includes the primary inputs used for the quantitative analysis.

The intended workflow is:

1. Clone the repository.
2. Install the listed dependencies.
3. Run the analysis script.
4. Compare the generated results with the reported findings.
5. Inspect the source data, scripts, abstract, paper, and audit workbook.

The quantitative analysis has been checked against the source CSV files. The 37 matched-pair comparisons have also been independently reconciled against the raw data.

Qualitative audit

The repository includes the `Championship_Cube_Qualitative_Coding_Audit.xlsx` workbook.

The workbook contains:

- The 74 team-season identifiers.
- Champion and Finals-runner-up labels.
- Era labels.
- The face-level 0–2 rubric.
- The prototype’s Yes/Partial/No mapping.
- The Four-of-Six tally formulas.
- Fields for evidence and coding rationale.
- Fields for coder and second-coder documentation.

The workbook is an audit scaffold for qualitative historical coding. It should not be treated as evidence that every qualitative score has been completed unless the relevant cells contain documented research evidence.

Limitations

- The quantitative sample contains Finals teams rather than all playoff teams.
- The sample size is modest for predictive modelling.
- Coach Face is based on proxy measures.
- Some qualitative face scores involve structured judgement and require documented evidence.
- Historical qualitative coding and live KIRIN scoring are related but not identical instruments.
- The Four-of-Six qualitative finding depends on documented case-study coding.
- KIRIN is a scenario diagnostic, not a calibrated forecasting model.
- The framework is intended to improve structured reasoning, not eliminate uncertainty from championship outcomes.

Status

The quantitative analysis, abstract, KIRIN prototype, and qualitative audit workbook are complete.

The repository is being prepared for final public release and conference submission. The research paper remains subject to further review and revision.

## How to cite this project

If you use the framework, code, prototype, or reported results, please cite the project using the citation information in `CITATION.cff`.

Suggested paper citation:

> Rahman, M. (2026). The Championship Cube: A Front-Office Framework for Building NBA Champions. Research paper submitted to the MIT Sloan Sports Analytics Conference, 2027. GitHub repository: https://github.com/YOUR-USERNAME/YOUR-REPOSITORY

If a DOI or published version becomes available, the citation information will be updated.

## Licence

The original code in this repository is released under the MIT License.

The research paper, abstract, audit workbook, and supporting documentation are authored research materials. Please cite them when reused or discussed.

Third-party data and external libraries remain subject to their own licences and source-specific terms. Basketball-Reference is the primary public data source for the quantitative analysis.

See the `LICENSE` file for the code licence and the relevant source documentation for data-use conditions.

## Contact

For questions about the research, methodology, KIRIN prototype, or reproducibility, please open a GitHub issue or contact Mohammad Rahman through GitHub.
