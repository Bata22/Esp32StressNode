"""
Offline, KAUZALNA analiza pilot snimka (mosquitto_sub log sa oznakama faza).

Kauzalno = svaki prozor koristi samo podatke dostupne do tog trenutka, pa je
rezultat isti kao da je sistem radio uzivo:
  - kalibracija = prvih N prozora posle baseline_start (N iz .pkl modela)
  - temp_slope  = razlika u odnosu na PRETHODNI prozor
  - alarm       = 3 uzastopna prozora sa P(stres) >= 0.5 (pravilo iz ICEST rada)

Labele: baseline posle kalibracije = 0, stres = 1. Oporavak se NE koristi u
AUC/F1, nego posebno, kao kontrola: ako model oporavak oznacava kao stres,
hvata proteklo vreme, a ne stres.

Pokretanje (iz korena repoa):
  python ml/analyze_pilot.py ml/data/pilot/2026-10-17_pilot01.log
  python ml/analyze_pilot.py <log> --eda-sign +1      # osetljivost na smer GSR
  python ml/analyze_pilot.py <log> --neutralize-hr    # HR z-score = 0
"""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score

from config import MODELS_DIR, RESULTS_DIR
from normalization import FEATURES, fit_baseline, transform

HR_RANGE = (40, 200)   # isti opseg kao u WESAD ekstrakciji (HR <= 200)
THRESHOLD = 0.5
ALERT_RUN = 3          # uzastopnih prozora za alarm
PHASES = ["setup", "baseline", "stress", "recovery", "after"]


def parse_log(path):
    """Vraca (telemetrija po prozoru, recnik oznaka faza)."""
    rows, markers = [], {}
    for line in open(path, encoding="utf-8"):
        parts = line.strip().split(" ", 2)
        if len(parts) < 3:
            continue
        ts, topic, payload = parts
        if topic.endswith("/marker"):
            markers[payload.strip(" ,")] = pd.Timestamp(ts)
        elif topic.endswith("/telemetry"):
            d = json.loads(payload)
            s = d["sensorData"]
            gsr = np.asarray(s["GSR"], dtype=float)
            rows.append({
                "t": pd.Timestamp(ts), "seq": d["seq"], "node_ms": d["node_ms"],
                "hr": s["HeartRate"], "hr_valid": s["heartRateValid"],
                "temp": s["Temperature"],
                "gsr_mean": gsr.mean(), "gsr_std": gsr.std(), "gsr_n": len(gsr),
            })
    df = pd.DataFrame(rows).sort_values("seq").reset_index(drop=True)
    return df, markers


def label_phases(df, m):
    edges = [m["baseline_start"], m["stress_start"], m["recovery_start"], m["end"]]
    conds = [df.t < e for e in edges]
    df["phase"] = np.select(conds, PHASES[:4], default=PHASES[4])
    df["min_from_baseline"] = (df.t - m["baseline_start"]).dt.total_seconds() / 60
    return df


def build_features(df, eda_sign):
    """Pet feature-a u istim jedinicama/smislu kao WESAD, NaN = nevalidan prozor."""
    hr_ok = (df.hr_valid == 1) & df.hr.between(*HR_RANGE)
    dt_sec = df.node_ms.diff() / 1000.0
    return pd.DataFrame({
        "mean_hr": df.hr.where(hr_ok),
        # Grove GSR daje ADC, ne provodljivost. eda_sign=-1: manji ADC = veca
        # provodljivost (po formuli proizvodjaca). Proveriti testom dubokog udaha.
        "eda_mean": eda_sign * df.gsr_mean,
        "eda_std": df.gsr_std,
        "temp_mean": df.temp,
        "temp_slope": df.temp.diff() / dt_sec,   # kauzalno: prema prethodnom prozoru
    })


def alert_state(proba):
    """True kad su poslednja ALERT_RUN validna prozora iznad praga."""
    above = (proba >= THRESHOLD).astype(float)
    return above.rolling(ALERT_RUN, min_periods=ALERT_RUN).min() == 1


def evaluate(df, proba, calib_mask):
    valid = proba.notna()
    base = (df.phase == "baseline") & ~calib_mask & valid
    stress = (df.phase == "stress") & valid
    rec = (df.phase == "recovery") & valid
    ev = base | stress
    y = stress[ev].astype(int)
    pred = (proba[ev] >= THRESHOLD).astype(int)

    alerts = pd.Series(False, index=df.index)
    alerts[valid] = alert_state(proba[valid]).values

    out = {
        "auc": roc_auc_score(y, proba[ev]),
        "f1": f1_score(y, pred, zero_division=0),
        "precision": precision_score(y, pred, zero_division=0),
        "recall": recall_score(y, pred, zero_division=0),
    }
    for name, mask in [("baseline", base), ("stress", stress), ("recovery", rec)]:
        out[f"p_mean_{name}"] = proba[mask].mean()
        out[f"pos_rate_{name}"] = (proba[mask] >= THRESHOLD).mean()
        out[f"alert_rate_{name}"] = alerts[mask].mean()
    return out, alerts


def data_quality(df, X):
    seq_gaps = int((df.seq.diff().dropna() != 1).sum())
    return {
        "packets": len(df),
        "seq_first": int(df.seq.min()), "seq_last": int(df.seq.max()),
        "seq_gaps": seq_gaps,
        "hr_valid_rate": float(X.mean_hr.notna().mean()),
        "gsr_samples_per_window": float(df.gsr_n.median()),
        # Maxim algoritam: HR = floor(25 Hz * 60 / razmak_pikova_u_uzorcima)
        "hr_values_all_1500_over_k": bool(df.hr[df.hr_valid == 1].isin(
            {1500 // k for k in range(1, 200)}).all()),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("--eda-sign", type=int, choices=[-1, 1], default=-1)
    ap.add_argument("--neutralize-hr", action="store_true")
    args = ap.parse_args()

    df, markers = parse_log(args.log)
    df = label_phases(df, markers)
    X = build_features(df, args.eda_sign)

    artifacts = {p.stem: joblib.load(p) for p in sorted(MODELS_DIR.glob("*.pkl"))}
    first = next(iter(artifacts.values()))
    n_calib = first["calib_sec"] // first["window_sec"]

    calib_mask = pd.Series(False, index=df.index)
    calib_mask[df.index[df.phase == "baseline"][:n_calib]] = True
    valid = X.notna().all(axis=1)
    baseline = fit_baseline(X[calib_mask & valid])
    Z = transform(X, baseline)
    if args.neutralize_hr:
        Z["mean_hr"] = 0.0

    tag = f"{args.log.stem}_eda{args.eda_sign:+d}" + ("_hr0" if args.neutralize_hr else "")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    windows = df.join(Z.add_prefix("z_"))
    windows["calibration"] = calib_mask
    summary = []
    for name, art in artifacts.items():
        proba = pd.Series(np.nan, index=df.index)
        proba[valid] = art["model"].predict_proba(Z.loc[valid, art["features"]].values)[:, 1]
        metrics, alerts = evaluate(df, proba, calib_mask)
        summary.append({"model": name, **metrics})
        windows[f"p_{name}"] = proba
        windows[f"alert_{name}"] = alerts

    quality = data_quality(df, X)
    summary = pd.DataFrame(summary)
    summary.to_csv(RESULTS_DIR / f"{tag}_summary.csv", index=False)
    windows.to_csv(RESULTS_DIR / f"{tag}_windows.csv", index=False)

    phase_lengths = df.groupby("phase").size().reindex(PHASES).fillna(0).astype(int)
    print(f"[{tag}] kalibracija: {int((calib_mask & valid).sum())} prozora, "
          f"faze: {phase_lengths.to_dict()}")
    print("Kvalitet podataka:", quality)
    print("Kalibracija mu:", baseline["mu"].round(4).to_dict())
    print("Kalibracija sigma:", baseline["sigma"].round(4).to_dict())
    cols = ["model", "auc", "f1", "p_mean_baseline", "p_mean_stress", "p_mean_recovery",
            "alert_rate_baseline", "alert_rate_stress", "alert_rate_recovery"]
    print(summary[cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
