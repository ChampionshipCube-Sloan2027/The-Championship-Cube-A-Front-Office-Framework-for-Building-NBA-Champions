"""Regenerates Figure 1 (champion vs runner-up within each Finals: SRS and combined top-3 BPM).
Run from the repo root:  python Championship-Cube-Figure1.py   ->  Figure1_paired_finals.png
Reads the two master CSVs from ./Data/ if it exists, otherwise from the repo root.
Note: the source CSVs label the BPM columns 'BMP 1/2/3'; they hold Box Plus/Minus values."""
from pathlib import Path
import pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
D = Path("Data") if Path("Data").is_dir() else Path(".")
W = pd.read_csv(D / "Championship-Cube-Master-Dataset(Winner).csv").sort_values("Year").reset_index(drop=True)
L = pd.read_csv(D / "Championship-Cube-Master-Dataset(Lossers).csv").sort_values("Year").reset_index(drop=True)
for d in (W, L): d["top3"] = d[["BMP 1", "BMP 2", "BMP 3"]].astype(float).sum(axis=1)
yr = W.Year.values
fig, axs = plt.subplots(2, 1, figsize=(9, 6.4), sharex=True)
for ax, col, lab in [(axs[0], "SRS", "Team Face: SRS"), (axs[1], "top3", "Player Face: combined top-3 BPM")]:
    for i in range(len(W)):
        ax.plot([yr[i]] * 2, [W[col][i], L[col][i]], color="#2a7f62" if W[col][i] > L[col][i] else "#b5483a", lw=1.6, zorder=1)
    ax.scatter(yr, W[col], s=34, color="black", zorder=2, label="Champion")
    ax.scatter(yr, L[col], s=34, facecolors="white", edgecolors="black", zorder=2, label="Runner-up")
    for x in (1998.5, 2011.5): ax.axvline(x, color="grey", ls=":", lw=1)
    ax.set_ylabel(lab); ax.spines[["top", "right"]].set_visible(False)
axs[0].legend(frameon=False, loc="lower left", fontsize=9)
for x, t in [(1994, "Physical Era"), (2005, "Transition Era"), (2019, "Analytics Era")]:
    axs[1].text(x, axs[1].get_ylim()[0] + 0.2, t, ha="center", fontsize=9, color="grey")
axs[1].set_xlabel("Finals season (end year)")
fig.suptitle("Figure 1. Champion vs runner-up within each Finals (green = champion higher; red = lower)\n"
             "SRS: champion higher in 25/37 pairs; top-3 BPM: 28/37", fontsize=10, x=0.02, ha="left")
plt.tight_layout(rect=[0, 0, 1, 0.93]); plt.savefig("Figure1_paired_finals.png", dpi=200)
