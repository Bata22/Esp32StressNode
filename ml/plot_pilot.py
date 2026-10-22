"""
Grafik pilot sesije iz CSV-a koji pravi analyze_pilot.py (crtanje je odvojeno
od analize: ortogonalnost). Paneli dele vremensku osu, svaki ima svoju y-osu.

Pokretanje: python ml/plot_pilot.py ml/results/<tag>_windows.csv
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
MODELS = {"LogisticRegression": ("#2a78d6", "LR"),
          "RandomForest": ("#eb6834", "RF"),
          "XGBoost": ("#1baf7a", "XGB")}
REF_HR = None #(125, 65)  # rucno izmeren puls na kraju oporavka (beleske ispitanika)
PHASE_STYLE = {"baseline": ("Baseline", "#f3f2ef"), "stress": ("Stres", "#e3e1db"),
               "recovery": ("Oporavak", "#f3f2ef")}


def phase_spans(w):
    spans = {}
    for phase in PHASE_STYLE:
        x = w.loc[w.phase == phase, "min_from_baseline"]
        if len(x):
            spans[phase] = (x.min(), x.max() + 5 / 60)
    return spans


def main(csv_path):
    w = pd.read_csv(csv_path)
    w = w[w.min_from_baseline >= -2]
    spans = phase_spans(w)
    calib = w.loc[w.calibration, "min_from_baseline"]

    fig, axes = plt.subplots(4, 1, figsize=(10, 9), sharex=True,
                             gridspec_kw={"height_ratios": [1, 1, 1, 1.4]})
    for ax in axes:
        for phase, (x0, x1) in spans.items():
            ax.axvspan(x0, x1, color=PHASE_STYLE[phase][1], zorder=0, lw=0)
        ax.axvspan(calib.min(), calib.max() + 5 / 60, facecolor="none",
                   edgecolor="#b8b6af", hatch="///", lw=0, zorder=0)
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color(INK_2)
        ax.tick_params(colors=INK_2, labelsize=9)
    for phase, (x0, x1) in spans.items():
        axes[0].text((x0 + x1) / 2, 1.04, PHASE_STYLE[phase][0], transform=axes[0].get_xaxis_transform(),
                     ha="center", va="bottom", fontsize=10, color=INK)
    after = w.loc[w.phase == "after", "min_from_baseline"]
    if len(after):
        axes[0].text(after.mean(), 1.04, "posle\nkraja", transform=axes[0].get_xaxis_transform(),
                     ha="center", va="bottom", fontsize=8, color=INK_2)
    axes[0].text(calib.mean(), 0.95, "kalibracija\n2 min", transform=axes[0].get_xaxis_transform(),
                 ha="center", va="top", fontsize=8, color=INK_2)

    hr = w[w.hr_valid == 1]
    axes[0].scatter(hr.min_from_baseline, hr.hr, s=10, color=INK_2, zorder=3)
    if REF_HR and "recovery" in spans:
        x1 = spans["recovery"][1]
        axes[0].fill_between([x1 - 1, x1], REF_HR[0], REF_HR[1], color=INK, alpha=0.25, lw=0, zorder=2)
        axes[0].text(x1 - 1.1, REF_HR[0] - 2, f"referentni puls {REF_HR[0]}–{REF_HR[1]}", ha="right",
                     va="center", fontsize=8, color=INK)
    axes[0].set_ylabel("HR sa čvora\n(bpm)", color=INK, fontsize=9)
    axes[1].plot(w.min_from_baseline, w.gsr_mean, color=INK_2, lw=1.5)
    axes[1].set_ylabel("GSR\n(ADC, sirovo)", color=INK, fontsize=9)
    axes[2].plot(w.min_from_baseline, w.temp, color=INK_2, lw=1.5)
    axes[2].set_ylabel("Temperatura\nkože (°C)", color=INK, fontsize=9)

    ax = axes[3]
    ax.axhline(0.5, color=INK_2, lw=1, ls="--", zorder=1)
    ax.text(w.min_from_baseline.min(), 0.52, "prag 0.5", fontsize=8, color=INK_2)
    ends = []
    for col, (color, label) in MODELS.items():
        p = w[f"p_{col}"].rolling(3, min_periods=1).mean()
        ax.plot(w.min_from_baseline, p, color=color, lw=1.5, label=label, zorder=3)
        ends.append([p.dropna().iloc[-1], label])
    ends.sort(reverse=True)                      # direktne oznake bez preklapanja
    for i in range(1, len(ends)):
        ends[i][0] = min(ends[i][0], ends[i - 1][0] - 0.09)
    for y, label in ends:
        ax.text(w.min_from_baseline.max() + 0.25, y, label, color=INK, fontsize=9, va="center")
    ax.set_ylim(-0.02, 1.02)
    ax.set_ylabel("P(stres)\n(klizni prosek 3 prozora)", color=INK, fontsize=9)
    ax.set_xlabel("minuta od početka baseline faze", color=INK, fontsize=9)
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.0), frameon=False, fontsize=9, ncol=3)

    fig.suptitle("Pilot 01: jedan ispitanik, signali i izlaz modela po fazama",
                 x=0.07, ha="left", fontsize=12, color=INK)
    fig.tight_layout()
    out = Path(csv_path).with_name(Path(csv_path).stem.replace("_windows", "_figure") + ".png")
    fig.savefig(out, dpi=150)
    print("Sacuvano:", out)


if __name__ == "__main__":
    main(sys.argv[1])
