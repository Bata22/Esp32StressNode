"""
S1 - statisticka analiza pilota bez ML-a i poredjenje sa WESAD-om.

Sta radi i zasto:
  1. Opis faza (srednja, SD, medijana, IQR) u fizickim jedinicama.
  2. Cohen's d (stres prema baseline-u): velicina promene u jedinicama
     normalnog kolebanja. Ne zavisi od broja prozora, pa se poredi sa WESAD-om.
  3. d posle uklanjanja trenda: trend iz baseline faze se produzi kroz stres;
     meri se odstupanje od trenda. Odvaja odziv na stres od drifta.
  4. Mann-Whitney na nivou prozora i na nivou minutnih proseka: pokazuje
     koliko nezavisnost prozora (koja ne vazi) umanjuje p-vrednosti.
  5. AUC jednog signala i detektor sa pragom (z < -2 za temperaturu):
     detekcija bez ML-a, ista metrika i isto pravilo alarma kao kod modela.
  6. Spearman korelacije izmedju signala.
  7. WESAD: Cohen's d po ispitaniku, da se vidi gde pilot pada u raspon.

Pokretanje (iz korena repoa): python ml/s1_statistics.py
"""
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr
from sklearn.metrics import roc_auc_score

from analyze_pilot import evaluate
from config import MODELS_DIR
from study_common import FEATURES, cohens_d, load_pilot, load_wesad, pilot_masks, results_dir

OUT = results_dir("s1")
PHASES = ["baseline", "stress", "recovery"]
# Ocekivani smer pod stresom (fiziologija). eda_mean u pilotu je -ADC
# (konvencija proizvodjaca: manji ADC = veca provodljivost).
DIRECTION = {"mean_hr": 1, "eda_mean": 1, "eda_std": 1, "temp_mean": -1, "temp_slope": -1}
TEMP_RESOLUTION = 0.0625   # DS18B20, 12 bita
Z_THRESHOLD = -2.0         # prag na z-score temperature (2 SD ispod kalibracije)


def describe_phases(df, X):
    rows = []
    for f in FEATURES:
        for ph in PHASES:
            v = X.loc[df.phase == ph, f].dropna()
            rows.append({"feature": f, "phase": ph, "n": len(v), "mean": v.mean(),
                         "sd": v.std(), "median": v.median(),
                         "q25": v.quantile(.25), "q75": v.quantile(.75)})
    return pd.DataFrame(rows)


def detrended_d(df, x):
    """
    Odstupanje stresa i oporavka od linearnog trenda baseline faze, u SD reziduala.
    Ako je promena samo drift, odstupanje je blizu 0 u obe faze.
    """
    base = (df.phase == "baseline") & x.notna()
    t = df.min_from_baseline
    slope, intercept = np.polyfit(t[base], x[base], 1)
    resid_sd = (x[base] - (slope * t[base] + intercept)).std(ddof=2)
    out = {}
    for phase in ["stress", "recovery"]:
        sel = (df.phase == phase) & x.notna()
        out[phase] = (x[sel] - (slope * t[sel] + intercept)).mean() / resid_sd
    return out["stress"], out["recovery"], slope


def minute_table(df, X_adc):
    """Minutni proseci temperature i GSR-a od pocetka baseline-a (za vremenski tok)."""
    sel = df.phase.isin(PHASES)
    minute = np.floor(df.loc[sel, "min_from_baseline"]).astype(int)
    return (pd.DataFrame({"minute": minute, "phase": df.loc[sel, "phase"],
                          "temp_c": X_adc.loc[sel, "temp_mean"],
                          "gsr_adc": X_adc.loc[sel, "eda_mean"]})
            .groupby("minute").agg(phase=("phase", "first"), temp_c=("temp_c", "mean"),
                                   gsr_adc=("gsr_adc", "mean")))


def minute_means(df, x, phase):
    sel = (df.phase == phase) & x.notna()
    start = df.loc[df.phase == phase, "min_from_baseline"].min()
    minute = np.floor(df.loc[sel, "min_from_baseline"] - start)
    return x[sel].groupby(minute).mean()


def pilot_effects(df, X_adc):
    rows = []
    for f in FEATURES:
        x = X_adc[f]
        b = x[df.phase == "baseline"]
        s = x[df.phase == "stress"]
        d_detr, d_detr_rec, base_slope = detrended_d(df, x)
        p_win = mannwhitneyu(b.dropna(), s.dropna(), alternative="two-sided").pvalue
        p_min = mannwhitneyu(minute_means(df, x, "baseline"), minute_means(df, x, "stress"),
                             alternative="two-sided", method="exact").pvalue
        rows.append({
            "feature": f,
            "d_stress": cohens_d(b, s),
            "d_recovery": cohens_d(b, x[df.phase == "recovery"]),
            "d_stress_detrended": d_detr,
            "d_recovery_detrended": d_detr_rec,
            "baseline_trend_per_min": base_slope,
            "diff_stress_minus_baseline": s.mean() - b.mean(),
            "p_mannwhitney_windows": p_win,
            "p_mannwhitney_minutes": p_min,
        })
    return pd.DataFrame(rows)


def univariate_auc(df, Z, calib, valid):
    base, stress, _ = pilot_masks(df, calib, valid)
    ev = base | stress
    y = stress[ev].astype(int)
    return {f: roc_auc_score(y, DIRECTION[f] * Z.loc[ev, f]) for f in FEATURES}


def threshold_detector(df, Z, calib, valid):
    """Bez ML-a: 'stres' kad je temperatura 2 SD ispod kalibracije."""
    score = pd.Series(np.nan, index=df.index)
    score[valid] = (Z.loc[valid, "temp_mean"] < Z_THRESHOLD).astype(float)
    metrics, _ = evaluate(df, score, calib)
    return metrics


def model_metrics():
    rows = []
    df, _, Z, calib, valid = load_pilot(eda_sign=-1)
    for path in sorted(MODELS_DIR.glob("*.pkl")):
        art = joblib.load(path)
        proba = pd.Series(np.nan, index=df.index)
        proba[valid] = art["model"].predict_proba(Z.loc[valid, art["features"]].values)[:, 1]
        metrics, _ = evaluate(df, proba, calib)
        rows.append({"detector": path.stem, **metrics})
    return rows


def wesad_effects(w):
    rows = []
    for subj, g in w.groupby("subject", sort=False):
        b, s = g[g.label == 0], g[g.label == 1]
        row = {"subject": subj}
        for f in FEATURES:
            row[f"d_{f}"] = cohens_d(b[f], s[f])
        row["diff_temp_mean"] = s.temp_mean.mean() - b.temp_mean.mean()
        row["spearman_eda_temp"] = spearmanr(g.eda_mean, g.temp_mean).statistic
        rows.append(row)
    return pd.DataFrame(rows)


def plot_effects(wes, pilot_neg, pilot_pos):
    labels = {"mean_hr": "HR", "eda_mean": "EDA nivo", "eda_std": "EDA varijabilnost",
              "temp_mean": "Temperatura", "temp_slope": "Nagib temperature"}
    fig, ax = plt.subplots(figsize=(8, 4.6))
    rng = np.random.default_rng(0)
    for i, f in enumerate(FEATURES):
        y = len(FEATURES) - 1 - i
        d = wes[f"d_{f}"].values
        ax.scatter(d, y + rng.uniform(-0.12, 0.12, len(d)), s=22, color="#9b9a95",
                   zorder=2, label="WESAD ispitanici (n = 15)" if i == 0 else None)
        ax.scatter(pilot_neg[f], y, s=90, marker="D", color="#2a78d6", zorder=3,
                   label="pilot (GSR po formuli proizvođača)" if i == 0 else None)
        if f == "eda_mean":
            ax.scatter(pilot_pos[f], y, s=90, marker="D", facecolor="none",
                       edgecolor="#2a78d6", lw=1.5, zorder=3, label="pilot (GSR obrnutog smera)")
    ax.axvline(0, color="#52514e", lw=1)
    ax.set_yticks(range(len(FEATURES)))
    ax.set_yticklabels([labels[f] for f in reversed(FEATURES)], fontsize=9)
    ax.set_xlabel("Cohen's d, stres prema baseline-u (pozitivno = raste pod stresom)", fontsize=9)
    ax.set_xscale("symlog", linthresh=1)
    ticks = [-8, -4, -2, -1, 0, 1, 2, 4, 8, 14]
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(t) for t in ticks], fontsize=8)
    ax.grid(axis="x", color="#e6e5e1", lw=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.45, -0.18), ncol=3)
    ax.set_title("Veličina odziva na stres: pilot u odnosu na WESAD", loc="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "s1_effect_sizes.png", dpi=150)


def main():
    # Fizicke jedinice: eda_mean = sirovi ADC (eda_sign=+1)
    df, X_adc, _, _, _ = load_pilot(eda_sign=+1)
    # z-score u konvenciji proizvodjaca (eda_mean = -ADC), kao kod modela
    _, X_neg, Z, calib, valid = load_pilot(eda_sign=-1)

    describe_phases(df, X_adc).to_csv(OUT / "pilot_phase_stats.csv", index=False)
    minutes = minute_table(df, X_adc)
    minutes.to_csv(OUT / "pilot_minute_means.csv")

    eff = pilot_effects(df, X_adc)
    auc = univariate_auc(df, Z, calib, valid)
    eff["auc_single_feature"] = eff.feature.map(auc)
    eff["gsr_noise_within_window_adc"] = np.where(
        eff.feature == "eda_mean", df.gsr_std.median(), np.nan)
    eff.to_csv(OUT / "pilot_effects.csv", index=False)

    detectors = model_metrics() + [{"detector": "Prag temperature (z < -2)",
                                    **threshold_detector(df, Z, calib, valid)}]
    detectors = pd.DataFrame(detectors)
    detectors.to_csv(OUT / "detectors_pilot.csv", index=False)

    pilot_rows = df.phase.isin(["baseline", "stress"])   # isti skup faza kao WESAD
    corr = {
        "temp_vs_gsr": spearmanr(X_adc.temp_mean[pilot_rows], X_adc.eda_mean[pilot_rows]).statistic,
        "temp_vs_hr": spearmanr(X_adc.temp_mean[pilot_rows], X_adc.mean_hr[pilot_rows],
                                nan_policy="omit").statistic,
        "gsr_vs_hr": spearmanr(X_adc.eda_mean[pilot_rows], X_adc.mean_hr[pilot_rows],
                               nan_policy="omit").statistic,
    }
    pd.Series(corr, name="spearman").to_csv(OUT / "pilot_correlations.csv")

    w = load_wesad()
    wes = wesad_effects(w)
    wes.to_csv(OUT / "wesad_effects_per_subject.csv", index=False)

    pilot_d_neg = {f: cohens_d(X_neg.loc[df.phase == "baseline", f],
                               X_neg.loc[df.phase == "stress", f]) for f in FEATURES}
    pilot_d_pos = dict(zip(eff.feature, eff.d_stress))
    plot_effects(wes, pilot_d_neg, pilot_d_pos)

    print("PILOT: velicina efekta (eda_mean = sirovi ADC)")
    print(eff.drop(columns="gsr_noise_within_window_adc").to_string(
        index=False, float_format=lambda v: f"{v:.3g}"))
    print(f"\nGSR sum unutar prozora (medijana SD): {df.gsr_std.median():.1f} ADC")
    print(f"Rezolucija DS18B20: {TEMP_RESOLUTION} C")
    print("\nWESAD: Cohen's d po ispitaniku (min / medijana / max)")
    summary = wes.filter(like="d_").agg(["min", "median", "max"]).T
    summary["pilot (eda: -ADC)"] = [pilot_d_neg[c[2:]] for c in summary.index]
    print(summary.round(2).to_string())
    print(f"WESAD razlika temperature stres-baseline (C): medijana "
          f"{wes.diff_temp_mean.median():.2f}, raspon {wes.diff_temp_mean.min():.2f} "
          f"do {wes.diff_temp_mean.max():.2f}")
    print(f"WESAD Spearman EDA-temperatura (medijana po ispitaniku): "
          f"{wes.spearman_eda_temp.median():.2f}; ispod -0,5: "
          f"{(wes.spearman_eda_temp < -0.5).sum()}, pozitivna: {(wes.spearman_eda_temp > 0).sum()}")
    raste = {f: int((wes[f"d_{f}"] > 0).sum()) for f in FEATURES}
    print(f"WESAD broj ispitanika kod kojih atribut raste pod stresom (od {len(wes)}): {raste}")
    print("\nPILOT Spearman:", {k: round(v, 2) for k, v in corr.items()})
    print("\nPILOT minutni proseci (minut od pocetka baseline-a)")
    print(minutes.round(2).to_string())
    cols = ["detector", "auc", "f1", "precision", "recall",
            "alert_rate_baseline", "alert_rate_stress", "alert_rate_recovery"]
    print("\nDETEKTORI NA PILOTU (isti test skup)")
    print(detectors[cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
