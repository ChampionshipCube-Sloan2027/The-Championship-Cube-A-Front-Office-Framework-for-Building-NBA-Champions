"""Championship Cube: matched-pair analysis (37 champion / runner-up pairs).

Reproduces every number in the abstract. Needs only numpy, pandas, scipy.
Run from the repo root:  python Championship-Cube-Paired-Analysis.py
Reads the three CSVs from ./Data/ if it exists, otherwise from the repo root.
Writes: Paired-Analysis-Results.md

Design notes
- Each Finals is one pair, so we analyse WITHIN-PAIR differences (champion minus
  runner-up). Conditional logistic regression with one predictor and no intercept
  is exactly a logistic model on those differences; we fit it by maximum likelihood.
- 'Pairs correct' uses a parameter-free rule (higher value wins). It is not
  cross-validated because nothing is fitted; predictors were nonetheless chosen
  with the data in view, so treat it as descriptive, not out-of-sample.
- Franchises recur (e.g. CHI, LAL, SAS), so we also report a franchise-clustered
  bootstrap on the champion franchise.
- The 'AUC' values in kirin_prototype.py are 5-fold cross-validated pooled AUCs
  and differ slightly from in-sample pooled AUCs reported here.
"""
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
from scipy.optimize import minimize_scalar

D = Path("Data") if Path("Data").is_dir() else Path(".")   # CSVs live in Data/ or the repo root
W = pd.read_csv(D / "Championship-Cube-Master-Dataset(Winner).csv")
L = pd.read_csv(D / "Championship-Cube-Master-Dataset(Lossers).csv")
C = pd.read_csv(D / "Championship-Cube-Coach-Face.csv")
W, L = (x.sort_values("Year").reset_index(drop=True) for x in (W, L))
assert len(W) == len(L) == 37 and (W.Year == L.Year).all(), "pairs must align by year"

for d in (W, L):
    d["top3"] = d[["BMP 1", "BMP 2", "BMP 3"]].astype(float).sum(axis=1)
    d["pay_cap"] = d["Payroll"].str.replace(r"[$,]", "", regex=True).astype(float) / \
                   d["Salary cap"].str.replace(r"[$,]", "", regex=True).astype(float)
    h = d["Draft Hit Rate"].astype(str).str.split("/", expand=True).astype(float)
    d["draft_hit"] = h[0] / h[1]

# Coach Face CSV stacks two tables with repeated header rows: keep data rows only.
C = C[C.Result.isin(["Champion", "Runner-Up"])].copy()
C["s"] = pd.to_numeric(C["Coach Face Score"])
cw = C[C.Result == "Champion"].sort_values("Year"); cl = C[C.Result == "Runner-Up"].sort_values("Year")
assert (cw.Year.values == cl.Year.values).all()

rng = np.random.default_rng(2027)
N = len(W)

def cond_logit(d):
    b = minimize_scalar(lambda b: np.sum(np.log1p(np.exp(-b * d))), bounds=(-5, 5), method="bounded").x
    p = 1 / (1 + np.exp(-b * d)); se = 1 / np.sqrt(np.sum(p * (1 - p) * d ** 2))
    return b, se

def summarise(name, d, lines):
    b, se = cond_logit(d)
    lo, hi = np.exp(b - 1.96 * se), np.exp(b + 1.96 * se)
    p = 2 * stats.norm.sf(abs(b / se))
    k = int((d > 0).sum())
    acc = [(d[rng.integers(0, N, N)] > 0).mean() for _ in range(10000)]
    lines.append(f"| {name} | {np.exp(b):.2f} ({lo:.2f}-{hi:.2f}) | {p:.4f} | "
                 f"{k}/{N} = {k/N:.1%} ({np.percentile(acc,2.5):.0%}-{np.percentile(acc,97.5):.0%}) | "
                 f"{stats.binomtest(k, N).pvalue:.4f} |")
    return b

dS, dB = (W.SRS - L.SRS).values, (W.top3 - L.top3).values
out = ["# Paired analysis results (auto-generated)", "",
       "| Predictor | OR per unit (95% CI) | p (cond. logit) | Pairs correct (95% CI) | Sign-test p |",
       "|---|---|---|---|---|"]
summarise("SRS (Team Face)", dS, out); summarise("Top-3 BPM (Player Face)", dB, out)
summarise("Net Rating", (W["Net Rating"] - L["Net Rating"]).values, out)

# franchise-clustered bootstrap of the coefficient
teams = W.Team.values; uniq = np.unique(teams)
def clustered(d):
    bs = []
    for _ in range(3000):
        pick = rng.choice(uniq, len(uniq))
        idx = np.concatenate([np.where(teams == t)[0] for t in pick])
        bs.append(cond_logit(d[idx])[0])
    return np.percentile(bs, [2.5, 97.5])
out += ["", f"Franchise-clustered bootstrap 95% CI for coefficient: SRS {clustered(dS).round(3).tolist()}, "
            f"BPM {clustered(dB).round(3).tolist()}"]

# SRS vs BPM
b_only = int(((dB > 0) & (dS <= 0)).sum()); s_only = int(((dB <= 0) & (dS > 0)).sum())
diff = [((dB[i] > 0).mean() - (dS[i] > 0).mean()) for i in (rng.integers(0, N, N) for _ in range(10000))]
X = np.c_[dS / dS.std(), dB / dB.std()]
out += ["", f"SRS vs BPM: BPM-only correct {b_only}, SRS-only correct {s_only}, "
            f"exact McNemar p = {stats.binomtest(b_only, b_only + s_only).pvalue:.3f}; "
            f"accuracy difference (BPM - SRS) 95% CI {np.percentile(diff,[2.5,97.5]).round(3).tolist()}; "
            f"corr of within-pair differences r = {np.corrcoef(dS, dB)[0,1]:.2f}"]

# eras
out += ["", "| Era | pairs | mean SRS gap | 95% CI | paired t p | SRS pairs correct |", "|---|---|---|---|---|---|"]
era = W.Era.values
for e, label in [("P", "Physical"), ("T", "Transition"), ("A", "Analytics")]:
    m = era == e; x = dS[m]
    ci = np.percentile([x[rng.integers(0, len(x), len(x))].mean() for _ in range(5000)], [2.5, 97.5])
    out.append(f"| {label} | {m.sum()} | {x.mean():.2f} | {ci[0]:.2f} to {ci[1]:.2f} | "
               f"{stats.ttest_1samp(x, 0).pvalue:.3f} | {(x>0).sum()}/{m.sum()} |")
groups = [dS[era == e] for e in "PTA"]
out += ["", f"Era differences in SRS gap: ANOVA p = {stats.f_oneway(*groups).pvalue:.2f}, "
            f"Kruskal-Wallis p = {stats.kruskal(*groups).pvalue:.2f}, "
            f"Physical vs Analytics Welch p = {stats.ttest_ind(groups[2], groups[0], equal_var=False).pvalue:.2f}"]

# coach face + front-office proxies
d = cw.s.values - cl.s.values
out += ["", f"Coach Face (wins - Pythagorean): mean paired diff {d.mean():.2f}, t p = {stats.ttest_1samp(d,0).pvalue:.2f}, "
            f"Wilcoxon p = {stats.wilcoxon(d).pvalue:.2f}"]
for col, nm in [("pay_cap", "Payroll / salary cap"), ("draft_hit", "Draft hit rate")]:
    x = (W[col] - L[col]).values
    out.append(f"Front Office proxy, {nm}: mean paired diff {x.mean():.3f}, Wilcoxon p = {stats.wilcoxon(x).pvalue:.2f}")

# exploratory thresholds (post hoc)
out += ["", "Exploratory, post hoc: SRS < 5 in "
        f"{(W.SRS<5).sum()} champions vs {(L.SRS<5).sum()} runners-up; top-3 BPM < 10 in "
        f"{(W.top3<10).sum()} champions vs {(L.top3<10).sum()} runners-up."]

# ---- Out-of-sample checks for the two-predictor (SRS + top-3 BPM) model ----
# Weights are fitted on training pairs only (tiny ridge for stability) and used to predict
# held-out pairs. The single-predictor 'higher wins' rules have nothing to fit, so they are
# reported for comparison on the same held-out pairs.
from scipy.optimize import minimize
XX = np.c_[dS, dB]; yrs = W.Year.values
def _fit(X):
    return minimize(lambda b: np.sum(np.log1p(np.exp(-X @ b))) + 0.0005 * np.sum(b ** 2), [0, 0]).x
lopo = sum(int(XX[i] @ _fit(np.delete(XX, i, axis=0)) > 0) for i in range(N))
tr, te = np.where(yrs < 2012)[0], np.where(yrs >= 2012)[0]
hold = int(((XX[te] @ _fit(XX[tr])) > 0).sum()); ci = stats.binomtest(hold, len(te)).proportion_ci(method="exact")
walk = sum(int(XX[i] @ _fit(XX[:i]) > 0) for i in range(15, N))
out += ["", "Out-of-sample checks, two-predictor model (SRS + top-3 BPM):",
        f"- Leave-one-pair-out: {lopo}/{N} pairs correct (binomial p vs 50% = {stats.binomtest(lopo, N, 0.5, alternative='greater').pvalue:.3f})",
        f"- Temporal hold-out (train {len(tr)} pairs before 2012, test {len(te)} pairs 2012-2026): {hold}/{len(te)} correct, exact 95% CI {ci.low:.0%}-{ci.high:.0%}; "
        f"single-predictor 'higher wins' on the same test pairs: SRS {(dS[te]>0).sum()}/{len(te)}, BPM {(dB[te]>0).sum()}/{len(te)}",
        f"- Expanding-window one-step-ahead (pairs 16-{N}): {walk}/{N-15} correct",
        f"- Pairs where SRS and BPM agree on the better team: {int((np.sign(dS)==np.sign(dB)).sum())}; champion better on both in {int(((dS>0)&(dB>0)).sum())} (post hoc, descriptive)"]

Path("Paired-Analysis-Results.md").write_text("\n".join(out) + "\n")
print("\n".join(out))
