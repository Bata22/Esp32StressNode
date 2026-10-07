"""
Trening: Random Forest (100 stabala, max dubina 10)
Validacija: Leave-One-Subject-Out (LOSO)

Napomena: Random Forest ne zahteva standardizaciju karakteristika.
Stabla odlucivanja dele prostor po pragovima jedne promenljive u jednom
trenutku (npr. "mean_hr > 75?"), pa relativna skala razlicitih
promenljivih ne utice na podelu - za razliku od logisticke regresije,
gde velicina koeficijenata direktno zavisi od skale ulaznih promenljivih.

Pokrenuti tek nakon feature_extraction.py (potreban wesad_features.csv)
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
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

    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, min_samples_leaf=5)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    fold_result = {
        "model": "RandomForest",
        "params": "n_estimators=100, max_depth=10, random_state=42",
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
print("\n=== Random Forest - prosek preko svih LOSO foldova ===")
print(results_df[["auc", "precision", "recall", "f1"]].mean())

results_df.to_csv("results_random_forest01.csv", index=False)
