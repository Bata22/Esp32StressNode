"""
Trening: Logisticka regresija sa standardizacijom (bazni model za poredjenje)
Validacija: Leave-One-Subject-Out (LOSO)

Pokrenuti tek nakon feature_extraction.py (potreban wesad_features.csv)
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
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
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    test_subject = groups[test_idx][0]

    # VAZNO: scaler se fituje SAMO na trening delu.
    # Fitovanje na celom skupu pre podele bi "procurilo" informaciju
    # o test ispitaniku u trening fazu - data leakage.
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = LogisticRegression(max_iter=1000, C= 10, l1_ratio=1, solver="liblinear")
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    y_proba = model.predict_proba(X_test_scaled)[:, 1]

    fold_result = {
        "model": "LogisticRegression",
        "params": "max_iter=1000, StandardScaler(fit per fold)",
        "test_subject": test_subject,
        "auc": roc_auc_score(y_test, y_proba) if len(np.unique(y_test)) > 1 else np.nan,
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
    }
    results.append(fold_result)
    print(f"[{test_subject}] AUC={fold_result['auc']:.3f}  "
          f"Precision={fold_result['precision']:.3f}  "
          f"Recall={fold_result['recall']:.3f}  F1={fold_result['f1']:.3f}")

results_df = pd.DataFrame(results)
print("\n=== Logisticka regresija - prosek preko svih LOSO foldova ===")
print(results_df[["auc", "precision", "recall", "f1"]].mean())

results_df.to_csv("results_logistic_regression03.csv", index=False)
