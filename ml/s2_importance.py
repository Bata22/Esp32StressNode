"""
S2 - vaznost atributa i unapred zapisane konfiguracije modela.

Pravilo: odluke na WESAD-u (LOSO), provera na pilotu jednom po konfiguraciji.
Pilot se ne koristi za podesavanje, inace prestaje da bude test skup.

Sta radi i zasto:
  1. Permutaciona vaznost na WESAD-u: u test foldu se izmesa jedan atribut i
     meri pad AUC. Velik pad = model se na taj atribut oslanja.
  2. Ista mera na pilotu, za finalne modele: na sta se modeli oslanjaju
     kad rade na nasem hardveru.
  3. Konfiguracije C0-C5 (vidi ml/studies/S2_importance.md): svaka se oceni
     LOSO-om na WESAD-u, pa se istrenira na svih 15 ispitanika i proveri na
     pilotu, za oba moguca smera GSR signala.
  4. C5 koristi monotona ograničenja: model sme da poveca verovatnocu stresa
     samo kad EDA raste i samo kad temperatura pada. Tako se fizioloske
     pretpostavke ugradjuju u model umesto rucnih tezina.

Pokretanje (iz korena repoa): python ml/s2_importance.py
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from xgboost import XGBClassifier

from study_common import (CALIB_SEC, FEATURES, evaluate_on_pilot, fit_all, load_pilot,
                          load_wesad, make_models, pilot_masks, prepare, results_dir, run_loso)

OUT = results_dir("s2")
NO_HR = ["eda_mean", "eda_std", "temp_mean", "temp_slope"]
MONOTONE = [1, 1, -1, 0]   # EDA nivo i varijabilnost rastu, temperatura pada, nagib slobodan


def make_monotone(y_train):
    """Isti hiperparametri kao make_models, plus monotona ogranicenja."""
    return {
        "RandomForest": RandomForestClassifier(n_estimators=100, max_depth=10,
                                               random_state=42, monotonic_cst=MONOTONE),
        "XGBoost": XGBClassifier(n_estimators=150, random_state=42,
                                 monotone_constraints=tuple(MONOTONE)),
    }


CONFIGS = {
    "C0 svih 5": (FEATURES, make_models),
    "C1 bez HR": (NO_HR, make_models),
    "C2 bez temperature": (["mean_hr", "eda_mean", "eda_std"], make_models),
    "C3 samo EDA": (["eda_mean", "eda_std"], make_models),
    "C4 samo temperatura": (["temp_mean", "temp_slope"], make_models),
    "C5 bez HR, monotono": (NO_HR, make_monotone),
}


def pilot_importance(models, features, eda_sign=-1, repeats=30):
    df, _, Z, calib, valid = load_pilot(eda_sign)
    base, stress, _ = pilot_masks(df, calib, valid)
    ev = base | stress
    X, y = Z.loc[ev, features].values, stress[ev].astype(int).values
    rows = []
    for name, model in models.items():
        imp = permutation_importance(model, X, y, scoring="roc_auc",
                                     n_repeats=repeats, random_state=42)
        rows += [{"model": name, "feature": f, "pilot_importance": v}
                 for f, v in zip(features, imp.importances_mean)]
    return pd.DataFrame(rows)


def main():
    data = prepare(load_wesad(), CALIB_SEC)
    summary, per_subject = [], []
    for cfg, (features, make) in CONFIGS.items():
        loso = run_loso(data, features, make, perm_repeats=10 if cfg.startswith("C0") else 0)
        loso.insert(0, "config", cfg)
        per_subject.append(loso)
        models = fit_all(data, features, make)
        for name, model in models.items():
            w = loso[loso.model == name]
            row = {"config": cfg, "model": name,
                   "wesad_auc": w.auc.mean(), "wesad_f1": w.f1.mean()}
            for sign, tag in [(-1, "formula"), (1, "obrnut")]:
                m = evaluate_on_pilot(model, features, sign)
                row.update({f"pilot_auc_{tag}": m["auc"], f"pilot_f1_{tag}": m["f1"],
                            f"alarm_baseline_{tag}": m["alert_rate_baseline"],
                            f"alarm_oporavak_{tag}": m["alert_rate_recovery"]})
            summary.append(row)
        if cfg.startswith("C0"):
            wes_imp = (loso.groupby("model")[[f"imp_{f}" for f in FEATURES]].mean()
                       .rename(columns=lambda c: c[4:]).stack().rename("wesad_importance")
                       .rename_axis(["model", "feature"]).reset_index())
            importance = wes_imp.merge(pilot_importance(models, FEATURES), on=["model", "feature"])
        print(f"Zavrsena konfiguracija: {cfg}")

    summary = pd.DataFrame(summary)
    summary.to_csv(OUT / "summary_by_config.csv", index=False)
    pd.concat(per_subject).to_csv(OUT / "wesad_loso_per_subject.csv", index=False)
    importance.to_csv(OUT / "importance_wesad_vs_pilot.csv", index=False)

    pd.set_option("display.width", 200)
    print("\nPERMUTACIONA VAZNOST (pad AUC kad se atribut izmesa), C0")
    print(importance.pivot(index="feature", columns="model").round(3).to_string())
    print("\nKONFIGURACIJE: WESAD LOSO i pilot (GSR po formuli / obrnut smer)")
    cols = ["config", "model", "wesad_auc", "wesad_f1", "pilot_auc_formula", "pilot_f1_formula",
            "alarm_baseline_formula", "pilot_auc_obrnut", "pilot_f1_obrnut"]
    print(summary[cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
