"""
Zajednicki kod za studije S1-S3 (DRY): ucitavanje pilota i WESAD-a,
LOSO petlja, ocena na pilotu i velicina efekta. Studije ovu logiku
uvoze, ne kopiraju, pa sve tri rade nad istim podacima na isti nacin.
"""
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import f1_score, roc_auc_score

from analyze_pilot import build_features, evaluate, label_phases, parse_log
from config import DATA_DIR, FEATURES_CSV, RESULTS_DIR
from normalization import FEATURES, fit_baseline, transform
from train_calibration_experiment import EVAL_SKIP, WINDOW_SEC, make_models, prepare

# Ako se tvoj log zove drugacije, promeni samo ovde: vazi za sve tri studije.
PILOT_LOG = DATA_DIR / "pilot" / "2026-10-17_pilot01.log"
CALIB_SEC = 120                       # izabrano u LOSO eksperimentu
N_CALIB = CALIB_SEC // WINDOW_SEC     # 24 prozora


def results_dir(study):
    path = RESULTS_DIR / study
    path.mkdir(parents=True, exist_ok=True)
    return path


# ---------- pilot ----------

def load_pilot(eda_sign=-1, log=PILOT_LOG):
    """Pilot po prozorima: faze, sirovi atributi X i z-score Z prema kalibraciji."""
    df, markers = parse_log(log)
    df = label_phases(df, markers)
    X = build_features(df, eda_sign)
    calib = pd.Series(False, index=df.index)
    calib[df.index[df.phase == "baseline"][:N_CALIB]] = True
    valid = X.notna().all(axis=1)
    Z = transform(X, fit_baseline(X[calib & valid]))
    return df, X, Z, calib, valid


def pilot_masks(df, calib, valid):
    """Isti skupovi kao u analyze_pilot: baseline posle kalibracije, stres, oporavak."""
    base = (df.phase == "baseline") & ~calib & valid
    stress = (df.phase == "stress") & valid
    recovery = (df.phase == "recovery") & valid
    return base, stress, recovery


def pilot_proba(model, Z, valid, features):
    proba = pd.Series(np.nan, index=Z.index)
    proba[valid] = model.predict_proba(Z.loc[valid, features].values)[:, 1]
    return proba


def evaluate_on_pilot(model, features, eda_sign=-1):
    df, _, Z, calib, valid = load_pilot(eda_sign)
    metrics, _ = evaluate(df, pilot_proba(model, Z, valid, features), calib)
    return metrics


# ---------- WESAD ----------

def load_wesad():
    df = pd.read_csv(FEATURES_CSV)
    if "window_idx" in df.columns:
        df = df.sort_values(["subject", "window_idx"])
    return df


def run_loso(data, features=FEATURES, make=make_models, perm_repeats=0, seed=42):
    """
    Leave-one-subject-out nad vec normalizovanim podacima (rezultat prepare()).
    Isti test skup kao u train_calibration_experiment: prvih EVAL_SKIP prozora
    test ispitanika se ne ocenjuje. Vraca jedan red po (ispitanik, model).
    """
    position = data.groupby("subject", sort=False).cumcount()
    rows = []
    for test_s in data["subject"].unique():
        train = data[data["subject"] != test_s]
        test = data[(data["subject"] == test_s) & (position >= EVAL_SKIP)]
        X_tr, y_tr = train[features].values, train["label"].values
        X_te, y_te = test[features].values, test["label"].values
        for name, model in make(y_tr).items():
            model.fit(X_tr, y_tr)
            proba = model.predict_proba(X_te)[:, 1]
            row = {
                "model": name, "test_subject": test_s,
                "auc": roc_auc_score(y_te, proba) if len(np.unique(y_te)) > 1 else np.nan,
                "f1": f1_score(y_te, (proba >= 0.5).astype(int), zero_division=0),
                "train_auc": roc_auc_score(y_tr, model.predict_proba(X_tr)[:, 1]),
            }
            if perm_repeats:
                imp = permutation_importance(model, X_te, y_te, scoring="roc_auc",
                                             n_repeats=perm_repeats, random_state=seed)
                row.update({f"imp_{f}": v for f, v in zip(features, imp.importances_mean)})
            rows.append(row)
    return pd.DataFrame(rows)


def fit_all(data, features=FEATURES, make=make_models):
    """Trening na svih 15 ispitanika (kao train_final_models.py)."""
    y = data["label"].values
    models = make(y)
    for model in models.values():
        model.fit(data[features].values, y)
    return models


# ---------- statistika ----------

def cohens_d(reference, other):
    """(srednja(other) - srednja(reference)) / zajednicka SD."""
    a = np.asarray(reference, float)
    b = np.asarray(other, float)
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    pooled = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1))
                     / (len(a) + len(b) - 2))
    return (b.mean() - a.mean()) / pooled if pooled > 0 else np.nan


__all__ = ["FEATURES", "CALIB_SEC", "N_CALIB", "WINDOW_SEC", "prepare", "make_models",
           "load_pilot", "pilot_masks", "pilot_proba", "evaluate_on_pilot",
           "load_wesad", "run_loso", "fit_all", "cohens_d", "results_dir"]
