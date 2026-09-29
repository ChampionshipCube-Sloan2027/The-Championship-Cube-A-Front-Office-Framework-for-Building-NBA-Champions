"""Pilot analysis: run after both coders finish.
Usage: python pilot_analysis.py coder1.xlsx coder2.xlsx PRIVATE_answer_key.csv
Reads 'Coder Sheet' from each workbook. Needs pandas, numpy, scipy, openpyxl.
Outputs: agreement (quadratic-weighted kappa, exact and within-1 agreement) per face,
then champion-minus-runner-up differences per face (mean, sign test) using each coder
and using the average of the two coders. Pre-specified: primary = paired difference,
secondary = share of champions scoring 2 (README threshold rule).
"""
import sys, numpy as np, pandas as pd
from scipy import stats
FACES={"Front Office":"Front Office score (0/1/2/NA)","Controllable External":"Controllable External score (0/1/2/NA)","Uncontrollable External":"Uncontrollable External score (0/1/2/NA)"}
def load(p):
    d=pd.read_excel(p,sheet_name="Coder Sheet").set_index("ID")
    return {f:pd.to_numeric(d[c],errors="coerce") for f,c in FACES.items()}, d
def wkappa(a,b,k=3):
    m=a.notna()&b.notna(); a,b=a[m].astype(int).values,b[m].astype(int).values
    if len(a)<3: return np.nan
    O=np.zeros((k,k)); 
    for i,j in zip(a,b): O[i,j]+=1
    E=np.outer(O.sum(1),O.sum(0))/O.sum(); w=np.array([[(i-j)**2 for j in range(k)] for i in range(k)])/(k-1)**2
    return 1-(w*O).sum()/(w*E).sum() if (w*E).sum()>0 else np.nan
c1,_=load(sys.argv[1]); c2,_=load(sys.argv[2]); key=pd.read_csv(sys.argv[3]).set_index("id")
rng=np.random.default_rng(7)
print("== Inter-rater agreement ==")
for f in FACES:
    a,b=c1[f],c2[f]; m=a.notna()&b.notna()
    ks=[wkappa(a[m].sample(frac=1,replace=True,random_state=int(s)),b[m].reindex(a[m].sample(frac=1,replace=True,random_state=int(s)).index)) for s in range(2000)] if m.sum()>=3 else []
    ks=[k for k in ks if np.isfinite(k)]
    ci=np.percentile(ks,[2.5,97.5]).round(2) if ks else "n/a"
    print(f"{f}: n={m.sum()}, weighted kappa={wkappa(a,b):.2f} (bootstrap 95% CI {ci}), exact agreement={(a[m]==b[m]).mean():.0%}, within 1 point={((a[m]-b[m]).abs()<=1).mean():.0%}, NA coder1={a.isna().sum()}, NA coder2={b.isna().sum()}")
print("\n== Champion minus runner-up (paired) ==")
for label,get in [("Coder 1",lambda f:c1[f]),("Coder 2",lambda f:c2[f]),("Mean of coders",lambda f:(c1[f]+c2[f])/2)]:
    for f in FACES:
        s=get(f); df=pd.DataFrame({"pair":key.pair,"role":key.role,"s":s}).dropna()
        p=df.pivot(index="pair",columns="role",values="s").dropna(); d=(p["Champion"]-p["Runner-Up"])
        pos,neg=(d>0).sum(),(d<0).sum(); pv=stats.binomtest(pos,pos+neg).pvalue if pos+neg>0 else np.nan
        print(f"{label:15s} {f:24s} pairs={len(d)} mean diff={d.mean():+.2f} champion higher {pos}, lower {neg}, tied {(d==0).sum()}, exact sign-test p={pv:.3f}")
print("\nReminder: 10 pairs is a pilot. Report counts and direction, not a validated Four-of-Six result.")
