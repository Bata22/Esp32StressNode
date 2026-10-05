"""
Trening: XGBoost sa early stopping
Validacija: Leave-One-Subject-Out (LOSO)

Za early stopping potreban je validacioni skup odvojen od test skupa.
Unutar svakog LOSO folda, jedan dodatni ispitanik iz trening skupa se
izdvaja kao validacija (da bismo znali kada da zaustavimo trening),
dok test ispitanik ostaje potpuno nevidjen do finalne evaluacije.

Pokrenuti tek nakon feature_extraction.py (potreban wesad_features.csv)
Instalacija: pip install xgboost
"""

import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score

FEATURES = ["mean_hr", "eda_mean", "eda_std", "temp_mean", "temp_slope"]

df = pd.read_csv("wesad_features.csv")
X = df[FEATURES].values
y = df["label"].values
groups = df["subject"].values

logo = LeaveOneGroupOut()
results = []

for train_idx, test_idx in logo.split(X, y, groups):
    test_subject = groups[test_idx][0]

    train_subjects = np.unique(groups[train_idx])
    val_subject = train_subjects[0]  # jedan ispitanik iz treninga -> validacija

    val_mask = groups[train_idx] == val_subject
    fit_mask = ~val_mask

    X_fit = X[train_idx][fit_mask]
    y_fit = y[train_idx][fit_mask]
    X_val = X[train_idx][val_mask]
    y_val = y[train_idx][val_mask]
    X_test, y_test = X[test_idx], y[test_idx]

    model = XGBClassifier(
        n_estimators=300,
        early_stopping_rounds=20,
        eval_metric="auc",
        random_state=42,
    )
    model.fit(X_fit, y_fit, eval_set=[(X_val, y_val)], verbose=False)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    fold_result = {
        "model": "XGBoost",
        "params": "n_estimators=300, early_stopping_rounds=20, eval_metric=auc, random_state=42",
        "test_subject": test_subject,
        "auc": roc_auc_score(y_test, y_proba) if len(np.unique(y_test)) > 1 else np.nan,
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "best_iteration": model.best_iteration,
    }
    results.append(fold_result)
    print(f"[{test_subject}] AUC={fold_result['auc']:.3f}  "
          f"Precision={fold_result['precision']:.3f}  "
          f"Recall={fold_result['recall']:.3f}  F1={fold_result['f1']:.3f}  "
          f"(zaustavljeno na iteraciji {fold_result['best_iteration']})")

results_df = pd.DataFrame(results)
print("\n=== XGBoost - prosek preko svih LOSO foldova ===")
print(results_df[["auc", "precision", "recall", "f1"]].mean())

results_df.to_csv("results_xgboost.csv", index=False)
