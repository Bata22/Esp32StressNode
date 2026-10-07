"""
LOSO eksperiment: uticaj normalizacije po ispitaniku i duzine kalibracije
na tri modela (LR, RF, XGBoost).

Uslovi:
  raw   - bez normalizacije po ispitaniku (kao dosadasnji rezultati)
  30s   - kalibracija 30 s  (6 prozora)   - vrednost iz ICEST rada
  2min  - kalibracija 2 min (24 prozora)
  5min  - kalibracija 5 min (60 prozora)

Pravedno poredjenje: prvih EVAL_SKIP prozora svakog TEST ispitanika se ne
ocenjuje ni u jednom uslovu. Na Pi-ju se tokom kalibracije ne predvidja,
a sa istim test skupom za sve uslove razlika u metrikama dolazi samo od
normalizacije, ne od toga koji su prozori ocenjeni.


Pokretanje: python train_calibration_experiment.py čita iz ml/data 
i normalization.py. Rezultat: piše ml/results
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
from xgboost import XGBClassifier
import sys, sklearn, xgboost

from config import FEATURES_CSV,RESULTS_DIR
from normalization import FEATURES, normalize_subject

WINDOW_SEC = 5
CALIB_SECONDS = {"raw": None, "30s": 30, "2min": 120, "5min": 300}
EVAL_SKIP = max(s for s in CALIB_SECONDS.values() if s) // WINDOW_SEC
BALANCED = False  # True = class_weight="balanced" / scale_pos_weight


def make_models(y_train: np.ndarray) -> dict:
    cw = "balanced" if BALANCED else None
    spw = (y_train == 0).sum() / (y_train == 1).sum() if BALANCED else 1.0
    return {
        "LogisticRegression": make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=1000, class_weight=cw)
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42, class_weight=cw
        ),
        "XGBoost": XGBClassifier(
            n_estimators=150, random_state=42, scale_pos_weight=spw
        ),
    }


def prepare(df: pd.DataFrame, calib_sec) -> pd.DataFrame:
    if calib_sec is None:
        return df.copy()
    n_calib = calib_sec // WINDOW_SEC
    parts = [normalize_subject(g, n_calib) for _, g in df.groupby("subject", sort=False)]
    return pd.concat(parts)


def main():
    env_info = (f"Python {sys.version.split()[0]} | numpy {np.__version__} | "
            f"sklearn {sklearn.__version__} | xgboost {xgboost.__version__}")
    print(env_info)
    df = pd.read_csv(FEATURES_CSV)
    if "window_idx" in df.columns:
        df = df.sort_values(["subject", "window_idx"])
    subjects = df["subject"].unique()
    results = []

    for cond, calib_sec in CALIB_SECONDS.items():
        data = prepare(df, calib_sec)
        position = data.groupby("subject", sort=False).cumcount()

        for test_s in subjects:
            train = data[data["subject"] != test_s]
            test = data[(data["subject"] == test_s) & (position >= EVAL_SKIP)]
            X_tr, y_tr = train[FEATURES].values, train["label"].values
            X_te, y_te = test[FEATURES].values, test["label"].values

            for name, model in make_models(y_tr).items():
                model.fit(X_tr, y_tr)
                y_pred = model.predict(X_te)
                y_proba = model.predict_proba(X_te)[:, 1]
                results.append({
                    "condition": cond,
                    "model": name,
                    "test_subject": test_s,
                    "auc": roc_auc_score(y_te, y_proba) if len(np.unique(y_te)) > 1 else np.nan,
                    "precision": precision_score(y_te, y_pred, zero_division=0),
                    "recall": recall_score(y_te, y_pred, zero_division=0),
                    "f1": f1_score(y_te, y_pred, zero_division=0),
                })
        print(f"Zavrsen uslov: {cond}")

    res = pd.DataFrame(results)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    res.to_csv(RESULTS_DIR/"results_calibration_experiment.csv", index=False)

    summary = res.groupby(["model", "condition"])[["auc", "f1"]].agg(["mean", "std"]).round(3)
    order = list(CALIB_SECONDS)
    summary = summary.reindex(order, level="condition")
    print(f"\nBALANCED={BALANCED}, ocenjeno od prozora {EVAL_SKIP} svakog test ispitanika")
    print(summary)


if __name__ == "__main__":
    main()

