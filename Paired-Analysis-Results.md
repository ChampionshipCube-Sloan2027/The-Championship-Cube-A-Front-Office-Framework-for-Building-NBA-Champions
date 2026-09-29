# Paired analysis results (auto-generated)

| Predictor | OR per unit (95% CI) | p (cond. logit) | Pairs correct (95% CI) | Sign-test p |
|---|---|---|---|---|
| SRS (Team Face) | 1.37 (1.08-1.75) | 0.0107 | 25/37 = 67.6% (51%-84%) | 0.0470 |
| Top-3 BPM (Player Face) | 1.26 (1.07-1.48) | 0.0051 | 28/37 = 75.7% (62%-89%) | 0.0026 |
| Net Rating | 1.35 (1.07-1.70) | 0.0104 | 26/37 = 70.3% (54%-84%) | 0.0201 |

Franchise-clustered bootstrap 95% CI for coefficient: SRS [0.047, 0.731], BPM [0.029, 0.486]

SRS vs BPM: BPM-only correct 7, SRS-only correct 4, exact McNemar p = 0.549; accuracy difference (BPM - SRS) 95% CI [-0.081, 0.243]; corr of within-pair differences r = 0.55

| Era | pairs | mean SRS gap | 95% CI | paired t p | SRS pairs correct |
|---|---|---|---|---|---|
| Physical | 9 | 0.67 | -1.09 to 2.34 | 0.488 | 5/9 |
| Transition | 13 | 1.87 | 0.51 to 3.18 | 0.024 | 11/13 |
| Analytics | 15 | 2.65 | 0.42 to 4.88 | 0.042 | 9/15 |

Era differences in SRS gap: ANOVA p = 0.43, Kruskal-Wallis p = 0.53, Physical vs Analytics Welch p = 0.20

Coach Face (wins - Pythagorean): mean paired diff 0.32, t p = 0.65, Wilcoxon p = 0.24
Front Office proxy, Payroll / salary cap: mean paired diff 0.059, Wilcoxon p = 0.33
Front Office proxy, Draft hit rate: mean paired diff 0.002, Wilcoxon p = 0.98

Exploratory, post hoc: SRS < 5 in 7 champions vs 17 runners-up; top-3 BPM < 10 in 4 champions vs 15 runners-up.

Out-of-sample checks, two-predictor model (SRS + top-3 BPM):
- Leave-one-pair-out: 26/37 pairs correct (binomial p vs 50% = 0.010)
- Temporal hold-out (train 22 pairs before 2012, test 15 pairs 2012-2026): 11/15 correct, exact 95% CI 45%-92%; single-predictor 'higher wins' on the same test pairs: SRS 9/15, BPM 12/15
- Expanding-window one-step-ahead (pairs 16-37): 16/22 correct
- Pairs where SRS and BPM agree on the better team: 26; champion better on both in 21 (post hoc, descriptive)
