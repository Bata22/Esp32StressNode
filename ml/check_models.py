
import joblib
import numpy as np
from config import MODELS_DIR

# Fiksni z-score ulazi (redosled kolona = artifact["features"])
X = np.array([
    [0.0, 0.0, 0.0, 0.0, 0.0],   # tacno baseline
    [2.0, 2.0, 2.0, 0.0, 0.0],   # povisen HR i EDA
    [-1.0, 0.5, 1.0, -0.5, 0.1],
])

for path in sorted(MODELS_DIR.glob("*.pkl")):
    art = joblib.load(path)
    proba = art["model"].predict_proba(X)[:, 1]
    print(f"{path.stem:20s} sklearn {art['versions']['sklearn']}  {np.round(proba, 10)}")