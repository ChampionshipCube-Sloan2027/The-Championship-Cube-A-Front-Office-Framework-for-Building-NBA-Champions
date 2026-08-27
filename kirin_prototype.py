# -*- coding: utf-8 -*-
"""KIRIN Prototype (Championship Cube live diagnostic tool).

Run `pip install -r requirements.txt` first, then either:
    python kirin_prototype.py          # runs both smoke tests
or import run_from_answers() / launch_guided_ui() from a notebook.

KIRIN is a self-assessed, forward-looking diagnostic. It is a separate
instrument from the historical paper's 0-2 case-study coding rubric
(see Championship_Cube_Qualitative_Coding_Audit.xlsx) and its outputs
are not numerically interchangeable with that rubric's scores.
"""

from __future__ import annotations
import warnings
import tempfile
import html
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tools.sm_exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

try:
    from IPython.display import HTML, FileLink, clear_output, display
except ImportError:
    HTML = FileLink = clear_output = display = None

try:
    import ipywidgets as widgets
except ImportError:
    widgets = None

try:
    from fpdf import FPDF, XPos, YPos
except ImportError:
    FPDF = XPos = YPos = None

BRAND_NAME='KIRIN'
FACE_COLS=['Player Face','Team Face','Front Office Face','Coach Face','Controllable External','Uncontrollable External']
OPTIONAL_TEAM_METRICS=['ORtg','DRtg','Pace']
INSUFFICIENT='Insufficient evidence'
ANSWER_POINTS={'Yes':2,'Partial':1,'No':0}
VALID_ANSWERS=list(ANSWER_POINTS)+[INSUFFICIENT]
ERA_LABELS={'P':'Physical Era','T':'Transition Era','A':'Analytics Era'}
EXPECTED_N_CHAMPS=37; EXPECTED_N_LOSERS=37; EXPECTED_N_COACH=74
READINESS_THRESHOLD=50.0; SIGNIFICANCE_ALPHA=0.05
READINESS_DISCLOSURE=("Exploratory scenario output -- not a probability of winning. Readiness reflects the "
    "entered Cube scores and simulated uncertainty. It has not been calibrated against future "
    "championship outcomes and should not be interpreted as a forecast.")
SELF_ASSESSED_DISCLOSURE=("Self-assessed inputs are not independently validated. Insufficient-evidence answers are "
    "excluded from the face-score calculation and lower input confidence; they are not treated as 'No.' "
    "Face scores therefore reflect only the substantiated answers provided.")
INSTRUMENT_NOTE=("This diagnostic score is a separate instrument from the historical paper's 0-2 "
    "case-study rubric and is not numerically interchangeable with it.")

@dataclass
class CubeFace:
    score: float
    confidence: float  # displayed as "Input confidence" -- based on answer consistency, reduced when a question is marked Insufficient evidence; not a statistical confidence level, and does not measure whether a note was written
    answers: list[str]=field(default_factory=list)
    notes: list[str]=field(default_factory=list)
    input_source: str='self-assessed'
@dataclass
class TeamProfile:
    srs: float
    ortg: float|None=None
    drtg: float|None=None
    pace: float|None=None
    year: int|None=None

FACE_QUESTIONS={'Player Face':["Does the roster have a clear Third Man who defends multiple positions and contributes winning plays without needing high usage?","Is there a clear, accepted usage hierarchy rather than several ball-dominant players competing for touches?","Was the current core built mainly through the draft or internal development rather than assembled entirely through transactions?"],'Front Office Face':["Has leadership generally drafted first and used trades to accelerate an existing core rather than relying mainly on free agency?","Does the roster avoid one oversized contract or commitment that crowds out depth?","Has leadership made an unpopular but well-reasoned long-term decision rather than always optimising for short-term approval?"],'Coach Face':["Does the coach's system fit this roster's strengths rather than being applied regardless of personnel?","Does the team have a clear identity it can execute reliably under pressure?","Does trust run both ways between the coaching staff and players?"],'Controllable External':["Is there a deliberate plan for managing player workload across the season?","Does the roster have enough depth to survive a congested schedule stretch?","Does the organisation invest in recovery and conditioning infrastructure?"],'Uncontrollable External':["Does the roster have enough depth to absorb a significant injury to a top contributor?","Has the team kept its execution and identity intact after tough losses?","Is the team's success not overwhelmingly dependent on a single player's availability?"]}
FACE_RECOMMENDATIONS={'Team Face':'Keep SRS as the Team Face score.','Player Face':'Check for a genuine Third Man.','Front Office Face':'Draft first, use trades to accelerate.','Coach Face':"Assess coach-roster fit.",'Controllable External':'Treat workload as a strategic problem.','Uncontrollable External':'Build depth and resilience.'}

def root():
    for c in [Path("/content"), Path.cwd()] + _data_subdirs([Path("/content"), Path.cwd()]):
        if c.exists():
            if any(p.name.lower().startswith("championship-cube-master") for p in c.iterdir()):
                return c
    return Path("/content") if Path("/content").exists() else Path.cwd()

def _data_subdirs(bases):
    """Case-insensitive lookup of a 'Data' or 'data' child directory (repo layout uses 'Data')."""
    found = []
    for b in bases:
        if not b.exists(): continue
        for child in b.iterdir():
            if child.is_dir() and child.name.lower() == "data": found.append(child)
    return found

def find_file(base, names):
    search_paths = [base, Path("/content"), Path.cwd()] + _data_subdirs([base, Path("/content"), Path.cwd()])
    wanted = {n.lower() for n in names}
    for path in search_paths:
        if not path.exists(): continue
        for child in path.iterdir():
            if child.is_file() and child.name.lower() in wanted:
                return child
    raise FileNotFoundError(f"Missing required file: {names} in {[str(p) for p in search_paths]}")

def era(year):
    if year is None: return None
    try: y = int(year)
    except (TypeError, ValueError) as e: raise ValueError(f"Invalid year: {year}") from e
    if 1990 <= y <= 1998: return "P"
    if 1999 <= y <= 2011: return "T"
    if 2012 <= y <= 2026: return "A"
    raise ValueError(f"Year out of range: {year}")

def opt_float(value, name):
    if value is None or (isinstance(value, str) and not value.strip()): return None
    try: number = float(value)
    except (TypeError, ValueError) as e: raise ValueError(f"{name} must be numeric or blank") from e
    return number if np.isfinite(number) else None

def read_csv(path):
    for enc in ("utf-8", "cp1252", "latin1"):
        try: return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError: continue
    raise ValueError(f"Unable to decode {path}")

def normalize_results(series):
    was_na = series.isna()
    values = series.astype(str).str.strip().str.lower().str.replace("\u2013", "-", regex=False)
    result = values.map({"champion": "Champion", "runner-up": "Loser", "runner up": "Loser", "loser": "Loser"})
    invalid = result.isna() & ~(was_na | values.isin(['result', 'nan', '']))
    if invalid.any(): raise ValueError(f"Unexpected Result labels: {sorted(values[invalid].unique())}")
    return result

def require_columns(df, req, label):
    missing = sorted(set(req) - set(df.columns))
    if missing: raise ValueError(f"{label} dataset missing columns: {missing}")

def fit_test(df, column):
    clean = df[[column, "won"]].dropna()
    if len(clean) < 10: raise ValueError(f"Not enough data for {column}")
    if clean["won"].nunique() != 2: raise ValueError(f"{column} lacks both outcome classes")
    X = clean[[column]]; y = clean["won"]
    pipeline = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler()), ("model", LogisticRegression(random_state=42))])
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(pipeline, X, y, cv=cv, scoring="roc_auc", error_score="raise")
    auc = float(np.mean(scores))
    if not np.isfinite(auc): raise RuntimeError(f"Non-finite AUC for {column}")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            model = sm.Logit(y.to_numpy(), sm.add_constant(X.to_numpy())).fit(disp=0)
        except Exception as e:
            raise RuntimeError(f"Logistic test failed for {column}: {e}") from e
    if not bool(model.mle_retvals.get("converged", False)):
        raise RuntimeError(f"Logistic test for {column} did not converge")
    if any(issubclass(w.category, ConvergenceWarning) for w in caught):
        raise RuntimeError(f"Logistic test for {column} emitted a convergence warning")
    beta, p_val = float(model.params[1]), float(model.pvalues[1])
    if not (np.isfinite(beta) and np.isfinite(p_val)):
        raise RuntimeError(f"Non-finite statistics generated for {column}")
    return auc, beta, p_val, len(clean)

def load_state():
    d = root(); weights = {f: 1/len(FACE_COLS) for f in FACE_COLS}; evidence = {}; status = {}
    win_p = find_file(d, ["Championship-Cube-Master-Dataset(Winner).csv"])
    los_p = find_file(d, ["Championship-Cube-Master-Dataset(Lossers).csv"])
    coa_p = find_file(d, ["Championship-Cube-Coach-Face.csv"])
    ch = read_csv(win_p); lo = read_csv(los_p); co = read_csv(coa_p)
    ch.columns = ch.columns.str.strip(); lo.columns = lo.columns.str.strip(); co.columns = co.columns.str.strip()
    if len(ch) != EXPECTED_N_CHAMPS: raise ValueError(f"Champions mismatch: expected {EXPECTED_N_CHAMPS}, found {len(ch)}")
    if len(lo) != EXPECTED_N_LOSERS: raise ValueError(f"Runners-up mismatch: expected {EXPECTED_N_LOSERS}, found {len(lo)}")
    ch.rename(columns={"BMP 1":"BPM 1","BMP 2":"BPM 2","BMP 3":"BPM 3"}, inplace=True)
    lo.rename(columns={"BMP 1":"BPM 1","BMP 2":"BPM 2","BMP 3":"BPM 3"}, inplace=True)
    team_req = ["SRS", "BPM 1", "BPM 2", "BPM 3"] + OPTIONAL_TEAM_METRICS
    require_columns(ch, team_req, "Champions"); require_columns(lo, team_req, "Runners-up"); require_columns(co, ["Result", "Coach Face Score"], "Coach Face")
    for f in (ch, lo):
        f["Combined_Top3_BPM" ] = pd.to_numeric(f[["BPM 1", "BPM 2", "BPM 3" ]].sum(axis=1, min_count=1), errors='coerce')
        f["SRS"] = pd.to_numeric(f["SRS"], errors='coerce')
    ch["won"] = 1; lo["won" ] = 0; combined = pd.concat([ch, lo], ignore_index=True)
    for face, col in [("Team Face", "SRS"), ("Player Face", "Combined_Top3_BPM")]:
        auc, beta, p, n = fit_test(combined, col)
        evidence[face] = {"auc": auc, "beta": beta, "p_value": p, "n": n, "status": "Significant" if p < SIGNIFICANCE_ALPHA else "Not significant"}
        status[face] = ("Significant in sample" if p < SIGNIFICANCE_ALPHA else "Not significant in sample", f"AUC={auc:.3f}; p={p:.4f}")
    co["Coach Face Score"] = pd.to_numeric(co["Coach Face Score"], errors="coerce")
    co["Result" ] = normalize_results(co["Result"])
    co = co.dropna(subset=["Coach Face Score", "Result"]).copy()

    if len(co) != EXPECTED_N_COACH: raise ValueError(f"Coach dataset has {len(co)} usable rows; expected {EXPECTED_N_COACH}")
    champ_c = (co["Result"] == "Champion").sum()
    lose_c = (co["Result"] == "Loser").sum()
    if champ_c != EXPECTED_N_CHAMPS: raise ValueError(f"Coach dataset has {champ_c} champions; expected {EXPECTED_N_CHAMPS}")
    if lose_c != EXPECTED_N_LOSERS: raise ValueError(f"Coach dataset has {lose_c} runners-up; expected {EXPECTED_N_LOSERS}")

    co["won"] = (co["Result" ] == "Champion").astype(int)
    auc, beta, p, n = fit_test(co, "Coach Face Score")
    evidence["Coach Face"] = {"auc": auc, "beta": beta, "p_value": p, "n": n, "status": "Significant" if p < SIGNIFICANCE_ALPHA else "Not significant"}
    status["Coach Face"] = ("Significant in sample" if p < SIGNIFICANCE_ALPHA else "Not significant in sample", f"AUC={auc:.3f}; p={p:.4f}")
    for f in FACE_COLS:
        if f not in status: status[f] = ("Self-assessed", "Rubric input")
    mdists = {m: pd.to_numeric(combined[m], errors='coerce').dropna().to_numpy() for m in OPTIONAL_TEAM_METRICS}
    return {"weights": weights, "evidence": evidence, "srs": combined["SRS"].dropna().to_numpy(), "bpm": combined["Combined_Top3_BPM"].dropna().to_numpy(), "coach": co["Coach Face Score"].dropna().to_numpy(), "statuses": status, "message": "State loaded successfully", "data_is_real": True, "metric_dists": mdists}

def initialize_state():
    S = load_state()
    if not np.isclose(sum(S["weights"].values()), 1.0): raise ValueError("Face weights must sum to 1.0")
    return S

# Main initialization
S = initialize_state()
WEIGHTS = S["weights"]; SRS_DIST = S["srs"]; BPM_DIST = S["bpm"]; COACH_DIST = S["coach"]; STATUS = S["statuses"]; DATA_MSG = S["message"]; DATA_IS_REAL = S["data_is_real"]; METRIC_DISTS = S["metric_dists"]; MODEL_EVIDENCE = S["evidence"]

def ordinal_percentile(v):
    i = int(v); suffix = "th"
    if not (10 < i % 100 < 14): suffix = {1:"st", 2:"nd", 3:"rd"}.get(i % 10, "th")
    return f"{v:.1f}{suffix}"

def percentile(val, dist):
    if val is None or len(dist) == 0: return None
    return float((dist < float(val)).mean() * 100)

def percentile_score(val, dist):
    p = percentile(val, dist)
    return round(float(np.clip(p/10, 0, 10)), 1) if p is not None else 5.0

def score_answers(entries):
    """entries: list of 3 dicts {'answer': Yes/Partial/No/Insufficient evidence, 'note': str}."""
    if len(entries) != 3: raise ValueError("Exactly three answers required")
    answers = [e["answer"] for e in entries]
    if any(a not in VALID_ANSWERS for a in answers): raise ValueError(f"Invalid answers: {answers}")
    scored = [a for a in answers if a in ANSWER_POINTS]
    n_insufficient = answers.count(INSUFFICIENT)
    if not scored:
        raise ValueError("At least one question needs a substantiated Yes/Partial/No answer; "
                          "a face cannot be scored from 'Insufficient evidence' alone")
    score = sum(ANSWER_POINTS[a] for a in scored) / (len(scored) * 2) * 10
    base_confidence = 90 if len(set(scored)) == 1 else 65
    confidence = max(base_confidence - 25 * n_insufficient, 20)
    return round(score, 1), confidence

def metric_sentence(label, val, hb, dist):
    if val is None: return f"{label} not provided."
    pct = percentile(val, dist)
    if pct is None: return f"{label} was {val:.1f}; no context."
    if hb is None: return f"{label} was {val:.1f}, at the {ordinal_percentile(pct)} percentile (contextual only)."
    quality = "a relative strength" if (pct >= 75 if hb else pct <= 25) else "a relative weakness" if (pct <= 25 if hb else pct >= 75) else "around the historical middle"
    return f"{label} was {val:.1f}, at the {ordinal_percentile(pct)} percentile ({quality}; {'higher' if hb else 'lower'} is preferred)."

def build_breakdown(profile, era_code):
    return " ".join(["Team Face uses SRS only.", f"Era: {ERA_LABELS.get(era_code, 'not supplied')}.", metric_sentence("ORtg", profile.ortg, True, METRIC_DISTS.get('ORtg', [])), metric_sentence("DRtg", profile.drtg, False, METRIC_DISTS.get('DRtg', [])), metric_sentence("Pace", profile.pace, None, METRIC_DISTS.get('Pace', []))])

class ChampionshipCubeAPEX:
    def __init__(self, team, faces, profile=None, breakdown=None):
        self.team = team; self.faces = faces; self.profile = profile; self.breakdown = breakdown or ""
    def weighted(self, sc): return sum(sc[f] * WEIGHTS[f] for f in FACE_COLS) * 10
    def readiness(self, s): return 1 / (1 + np.exp(np.clip(-(s - READINESS_THRESHOLD) / 10, -60, 60)))
    def run_audit(self, trials=5000, render=True):
        base = self.weighted({f: cf.score for f, cf in self.faces.items()})
        rng = np.random.default_rng(42)
        sims = np.array([self.weighted({f: np.clip(rng.normal(cf.score, (100-cf.confidence)/100*2.5), 0, 10) for f, cf in self.faces.items()}) for _ in range(trials)])
        readiness = self.readiness(sims) * 100
        res = {"team": self.team, "apex_score": float(base), "readiness": float(readiness.mean()), "p10": float(np.percentile(readiness, 10)), "p50": float(np.percentile(readiness, 50)), "p90": float(np.percentile(readiness, 90)), "weakest": min(self.faces, key=lambda f: self.faces[f].score), "breakdown": self.breakdown, "faces": self.faces}
        if render and display: self.render(res)
        return res
    def qa_html(self, f, cf):
        if cf.input_source != 'self-assessed': return ""
        rows = ''.join(f"<div style='font-size:10px;color:#aaa;margin-top:3px'>&bull; {html.escape(q)} &mdash; <b>{html.escape(a)}</b>{f': {html.escape(n)}' if n else ''}</div>" for q, a, n in zip(FACE_QUESTIONS[f], cf.answers, cf.notes))
        return rows + f"<div style='font-size:9px;color:#888;margin-top:2px'>{SELF_ASSESSED_DISCLOSURE}</div>"
    def render(self, res):
        cards = ''.join(f"<div style='background:#141414;padding:12px;margin:5px 0;border-radius:10px'><b>{f}</b><span style='float:right;color:#fa0'>{STATUS[f][0]}</span><div style='font-size:20px;color:cyan'>{res['faces'][f].score:.1f}/10<span style='font-size:11px;color:#999'>&nbsp; Input confidence: {res['faces'][f].confidence:.0f}/100</span></div>{self.qa_html(f, res['faces'][f])}</div>" for f in FACE_COLS)
        display(HTML(f"<div style='background:#0a0a0a;color:white;padding:20px;border-radius:15px;max-width:600px'><h2 style='color:gold;text-align:center'>{BRAND_NAME}: {self.team}</h2><div style='display:flex;justify-content:space-around'><div><b>Composite Cube score</b><br><span style='font-size:24px;color:cyan'>{res['apex_score']:.1f}</span></div><div><b>Scenario readiness index</b><br><span style='font-size:24px;color:#0f0'>{res['readiness']:.1f}%</span></div></div><p style='font-size:9px;color:#f66;text-align:center'>{READINESS_DISCLOSURE}</p>{cards}<p style='font-size:9px;color:#777'>{res['breakdown']}</p><p style='font-size:9px;color:#777'>{INSTRUMENT_NOTE}</p></div>"))

def run_from_answers(team_name, team_srs, ans_by_face, team_ortg=None, team_drtg=None, team_pace=None, team_year=None, render=True):
    """ans_by_face[face] is a list of 3 entries, each either a plain answer string
    (Yes/Partial/No/Insufficient evidence, note defaults to '') or a {'answer':..., 'note':...} dict."""
    y_val = int(team_year) if team_year is not None else None
    profile = TeamProfile(float(team_srs), opt_float(team_ortg, "ORtg"), opt_float(team_drtg, "DRtg"), opt_float(team_pace, "Pace"), y_val)
    faces = {}
    for f in FACE_COLS:
        if f == "Team Face":
            faces[f] = CubeFace(percentile_score(profile.srs, SRS_DIST), 90, [], [], "data-derived")
        elif f not in ans_by_face:
            raise ValueError(f"Missing answers for {f}")
        else:
            entries = [e if isinstance(e, dict) else {"answer": e, "note": ""} for e in ans_by_face[f]]
            score, cons = score_answers(entries)
            faces[f] = CubeFace(score, cons, [e["answer"] for e in entries], [e.get("note", "") for e in entries], "self-assessed")
    return ChampionshipCubeAPEX(team_name, faces, profile, build_breakdown(profile, era(y_val))).run_audit(render=render)

def safe_fn(t): return "".join(c if c.isalnum() or c in " _-" else "_" for c in str(t)).strip() or "Team"
def pdf_safe(t): return str(t).encode('latin-1', 'replace').decode('latin-1')

def generate_pdf_report(res, fn=None):
    if FPDF is None: raise ImportError("fpdf2 is required. Install with pip install fpdf2")
    path = Path(fn) if fn is not None else Path(f"KIRIN_{safe_fn(res['team'])}_Report.pdf")
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = FPDF(); pdf.add_page(); pdf.set_title(pdf_safe(f"KIRIN Report - {res['team']}")); pdf.set_author("KIRIN / Championship Cube")

    def para(text, h=5, style="", size=9):
        # fpdf2's multi_cell leaves the cursor at the right edge by default, which drifts
        # off-page on repeated calls -- force it back to the left margin every time.
        pdf.set_font("Helvetica", style, size)
        pdf.multi_cell(190, h, text=pdf_safe(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "B", 20); pdf.cell(190, 12, text=pdf_safe(f"{BRAND_NAME}: {res['team']}"), align="C"); pdf.ln(16)
    pdf.set_font("Helvetica", size=12); pdf.cell(95, 8, text=f"Composite Cube score: {res['apex_score']:.1f}"); pdf.cell(95, 8, text=f"Scenario readiness index: {res['readiness']:.1f}%"); pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8); pdf.multi_cell(190, 4, text=pdf_safe(READINESS_DISCLOSURE), new_x=XPos.LMARGIN, new_y=YPos.NEXT); pdf.ln(2)
    pdf.set_font("Helvetica", size=11); pdf.cell(190, 8, text=f"Scenario range (P10/P50/P90): {res['p10']:.1f}% / {res['p50']:.1f}% / {res['p90']:.1f}%"); pdf.ln(12)
    pdf.set_font("Helvetica", "B", 11); pdf.cell(190, 8, text="Face Breakdown:"); pdf.ln(8)
    for f in FACE_COLS:
        face = res["faces"][f]; hist = STATUS.get(f, ("Unknown", ""))[0]
        pdf.set_font("Helvetica", size=10)
        pdf.cell(190, 6, text=pdf_safe(f"{f}: {face.score:.1f}/10 | Hist: {hist} | Input: {face.input_source} | Input confidence: {face.confidence:.0f}/100")); pdf.ln(6)
        if face.input_source == "self-assessed":
            for q, a, n in zip(FACE_QUESTIONS[f], face.answers, face.notes):
                line = f"    - {q} -- {a}" + (f": {n}" if n else "")
                pdf.set_font("Helvetica", size=8); pdf.multi_cell(190, 4, text=pdf_safe(line), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "I", 8); pdf.multi_cell(190, 4, text=pdf_safe(f"    {SELF_ASSESSED_DISCLOSURE}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT); pdf.ln(1)
    pdf.ln(4); pdf.set_font("Helvetica", "B", 11); pdf.cell(190, 8, text=f"Weakest face: {res['weakest']}"); pdf.ln(8)
    para(FACE_RECOMMENDATIONS[res['weakest']], h=5); pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11); pdf.cell(190, 8, text="Team Face Context:"); pdf.ln(8)
    para(res['breakdown'], h=5); pdf.ln(6)
    pdf.set_font("Helvetica", "B", 11); pdf.cell(190, 8, text="Model Evidence:"); pdf.ln(8)
    for f, ev in MODEL_EVIDENCE.items():
        pdf.set_font("Helvetica", "B", 9); pdf.cell(190, 6, text=pdf_safe(f"{f}: AUC={ev['auc']:.3f}; beta={ev['beta']:.3f}; p={ev['p_value']:.4f}; n={ev['n']}; {ev['status']}")); pdf.ln(6)
    pdf.ln(6)
    para("All six faces receive equal weight in the exploratory Composite Cube score. Model AUC, coefficients, p-values, and sample sizes are evidence for the data-tested faces; they are not used as composite weights.", h=5, style="I", size=8)
    para(INSTRUMENT_NOTE, h=5, style="I", size=8)
    pdf.output(str(path))
    if not path.exists() or path.stat().st_size == 0: raise RuntimeError(f"PDF output failed: {path}")
    return str(path)

REFERENCE_STATS={"Team Face": {"auc": 0.677, "p_value": 0.0035, "beta": 0.3294}, "Player Face": {"auc": 0.698, "p_value": 0.0034}}
# Player Face beta is not one of the paper's headline published figures (only AUC/p-value are
# reported there); this is a regression guard against the value this exact dataset produced when
# last verified end-to-end (2026-08-27), so a future data or code change that silently moves it gets caught.
PLAYER_FACE_BETA_REFERENCE = 0.2296

def run_validation_smoke_test():
    """Loads the exact CSVs (via the module-level load_state() that already ran on import) and
    checks the headline regression outputs still match the paper's published statistics."""
    if not DATA_IS_REAL: raise RuntimeError(f"Validation smoke test cannot run: {DATA_MSG}")
    n_total = EXPECTED_N_CHAMPS + EXPECTED_N_LOSERS
    for face, expect in REFERENCE_STATS.items():
        ev = MODEL_EVIDENCE[face]
        assert ev["n"] == n_total, f"{face}: n={ev['n']}, expected {n_total}"
        assert abs(ev["auc"] - expect["auc"]) < 0.02, f"{face}: AUC drifted to {ev['auc']:.3f} (published {expect['auc']})"
        assert ev["p_value"] < 0.01, f"{face}: p-value no longer significant ({ev['p_value']:.4f})"
        assert abs(ev["p_value"] - expect["p_value"]) < 0.0005, f"{face}: p-value drifted to {ev['p_value']:.4f} (reference {expect['p_value']})"
        if "beta" in expect:
            assert abs(ev["beta"] - expect["beta"]) < 0.02, f"{face}: beta drifted to {ev['beta']:.4f} (published {expect['beta']})"
    assert abs(MODEL_EVIDENCE["Player Face"]["beta"] - PLAYER_FACE_BETA_REFERENCE) < 0.02, \
        f"Player Face: beta drifted to {MODEL_EVIDENCE['Player Face']['beta']:.4f} (last verified {PLAYER_FACE_BETA_REFERENCE})"
    coach = MODEL_EVIDENCE["Coach Face"]
    assert coach["p_value"] >= SIGNIFICANCE_ALPHA, f"Coach Face p-value {coach['p_value']:.4f} unexpectedly significant -- published finding was null"
    return "Validation smoke test passed: SRS and BPM regressions match published statistics; Coach Face remains a null result"

def run_smoke_test():
    if not DATA_IS_REAL: raise RuntimeError(f"Smoke test cannot run: {DATA_MSG}")
    demo = {face: ["Yes", "Partial", "Yes"] for face in FACE_QUESTIONS}
    low = run_from_answers("Low SRS", -5.0, demo, team_year=2024, render=False)
    high = run_from_answers("High SRS", 10.0, demo, team_year=2024, render=False)
    assert low["faces"]["Team Face"].score != high["faces"]["Team Face"].score
    assert low["apex_score"] != high["apex_score"]
    assert 0 <= low["apex_score"] <= 100
    assert 0 <= high["apex_score"] <= 100
    assert len(low["faces"]) == len(FACE_COLS)
    assert low["weakest"] in FACE_COLS
    assert np.isclose(sum(WEIGHTS.values()), 1.0)
    assert all(np.isclose(WEIGHTS[f], 1/len(FACE_COLS)) for f in FACE_COLS)
    repeat = run_from_answers("Low SRS", -5.0, demo, team_year=2024, render=False)
    assert low["p50"] == repeat["p50"]
    # Team Face is SRS-only: changing ORtg/DRtg/Pace must not move it
    ctx_a = run_from_answers("Ctx A", 5.0, demo, team_ortg=110, team_drtg=105, team_pace=98, team_year=2024, render=False)
    ctx_b = run_from_answers("Ctx B", 5.0, demo, team_ortg=95, team_drtg=115, team_pace=88, team_year=2024, render=False)
    assert ctx_a["faces"]["Team Face"].score == ctx_b["faces"]["Team Face"].score
    # Missing ORtg/DRtg/Pace must not crash the run
    missing_ctx = run_from_answers("No Context", 5.0, demo, team_year=2024, render=False)
    assert missing_ctx["faces"]["Team Face"].score == ctx_a["faces"]["Team Face"].score
    # Insufficient evidence must reduce confidence, not silently score as 'No'
    full_evidence = {face: ["Yes", "Yes", "Yes"] for face in FACE_QUESTIONS}
    full = run_from_answers("Full Evidence", 5.0, full_evidence, team_year=2024, render=False)
    partial_yy = run_from_answers("Partial Evidence YY", 5.0, {face: ["Yes", INSUFFICIENT, "Yes"] for face in FACE_QUESTIONS}, team_year=2024, render=False)
    for f in FACE_QUESTIONS:
        assert partial_yy["faces"][f].score == full["faces"][f].score, f"{f}: an unscored question should be excluded, not averaged in as a 0 (No)"
        assert partial_yy["faces"][f].confidence < full["faces"][f].confidence, f"{f}: insufficient evidence should lower confidence"
    try:
        run_from_answers("No Evidence", 5.0, {face: [INSUFFICIENT, INSUFFICIENT, INSUFFICIENT] for face in FACE_QUESTIONS}, team_year=2024, render=False)
        raise AssertionError("Expected ValueError when a face has zero substantiated answers")
    except ValueError:
        pass
    # 'no output claiming calibrated probability' guard: the disclosure text must be present verbatim
    assert "not been calibrated" in READINESS_DISCLOSURE and "not a probability of winning" in READINESS_DISCLOSURE
    if FPDF:
        with tempfile.TemporaryDirectory() as temp_dir:
            expected = Path(temp_dir) / "KIRIN_smoke_test.pdf"
            returned = Path(generate_pdf_report(low, str(expected)))
            assert returned == expected and returned.exists() and returned.stat().st_size > 0
    else: raise RuntimeError("fpdf2 is required for the PDF smoke test")
    return "KIRIN smoke test passed"

def launch_guided_ui():
    if widgets is None or display is None: raise ImportError("Guided UI requires ipywidgets and IPython.")
    output = widgets.Output()
    team = widgets.Text(description="Team:", value="My Team"); season = widgets.IntText(description="Season:", value=2026); srs = widgets.FloatText(description="SRS:", value=5.0)
    ortg = widgets.Text(description="ORtg:"); drtg = widgets.Text(description="DRtg:"); pace = widgets.Text(description="Pace:")
    q_widgets = {}
    controls = [widgets.HTML(f"<h2 style='color:gold'>{BRAND_NAME} AUDIT</h2>"), team, season, srs, ortg, drtg, pace]
    for face in [f for f in FACE_COLS if f != 'Team Face']:
        q_widgets[face] = []
        rows = [widgets.HTML(f"<b>{face}</b>")]
        for q in FACE_QUESTIONS[face]:
            dd = widgets.Dropdown(options=['Yes', 'Partial', 'No', INSUFFICIENT], value="Partial")
            note = widgets.Text(placeholder="Evidence / note supporting this answer", layout=widgets.Layout(width="430px"))
            q_widgets[face].append((dd, note))
            rows.append(widgets.HBox([widgets.HTML(f"<span style='width:430px;display:inline-block'>{html.escape(q)}</span>"), dd]))
            rows.append(note)
        controls.append(widgets.VBox(rows))
    controls.append(widgets.HTML(f"<p style='font-size:11px;color:#888'>{SELF_ASSESSED_DISCLOSURE}</p>"))
    btn = widgets.Button(description="RUN AUDIT", button_style="danger"); pdf_btn = widgets.Button(description="EXPORT PDF", button_style="success")
    last_result = {"value": None}
    def on_run(_):
        with output:
            clear_output(wait=True)
            try:
                ans = {f: [{"answer": dd.value, "note": note.value} for dd, note in q_widgets[f]] for f in q_widgets}
                res = run_from_answers(team.value, srs.value, ans, team_year=season.value, team_ortg=ortg.value, team_drtg=drtg.value, team_pace=pace.value)
                last_result["value"] = res
                display(widgets.HTML(f"<h3>Audit complete</h3><p><b>Composite Cube score:</b> {res['apex_score']:.1f}/100</p><p><b>Scenario readiness index:</b> {res['readiness']:.1f}%</p><p style='font-size:10px;color:#a55'>{READINESS_DISCLOSURE}</p><p><b>Scenario range:</b> {res['p10']:.1f}% / {res['p50']:.1f}% / {res['p90']:.1f}%</p><p><b>Weakest face:</b> {html.escape(res['weakest'])}</p>"))
                display(pdf_btn)
            except Exception as e: print(f"Audit failed: {e}")
    def on_pdf(_):
        if last_result["value"]:
            try:
                fn = generate_pdf_report(last_result["value"])
                with output: display(FileLink(fn))
            except Exception as e:
                with output: print(f"PDF export failed: {e}")
    btn.on_click(on_run); pdf_btn.on_click(on_pdf); display(*controls, btn, output)

if __name__ == "__main__":
    print(run_validation_smoke_test())
    launch_guided_ui()
    
