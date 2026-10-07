"""
Finalni modeli za Pi: trening na SVIM WESAD ispitanicima, sa
normalizacijom po osobi. Hiperparametri iz train_calibration_experiment.py.
Pokretanje: python ml/train_final_models.py  -> ml/models/*.pkl
"""
import sys
from datetime import date
import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost

from config import FEATURES_CSV, MODELS_DIR
from normalization import FEATURES
from train_calibration_experiment import make_models, prepare, WINDOW_SEC

CALIB_SEC = 120  # najbolji F1 u LOSO eksperimentu (2 min)


def main():
    df = pd.read_csv(FEATURES_CSV)
    data = prepare(df, CALIB_SEC)
    X = data[FEATURES].values
    y = data["label"].values

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    versions = {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "sklearn": sklearn.__version__,
        "xgboost": xgboost.__version__,
    }

    for name, model in make_models(y).items():
        model.fit(X, y)
        artifact = {
            "model": model,
            "features": FEATURES,
            "calib_sec": CALIB_SEC,
            "window_sec": WINDOW_SEC,
            "versions": versions,
            "trained_on": str(date.today()),
        }
        path = MODELS_DIR / f"{name}.pkl"
        joblib.dump(artifact, path)
        print(f"Sacuvano: 01{path}")

    print(f"Trenirano na {len(X)} prozora, {df['subject'].nunique()} ispitanika.")


if __name__ == "__main__":
    main()