"""Putanje za ML deo, relativne u odnosu na ovaj fajl,
pa skripte rade iz bilo kog foldera."""
import os
from pathlib import Path

ML_DIR = Path(__file__).resolve().parent
DATA_DIR = ML_DIR / "data"
RESULTS_DIR = ML_DIR / "results"
MODELS_DIR = ML_DIR / "models"

# Sirovi WESAD je velik i ne ide u repo. Podrazumevano ml/data/WESAD,
# ili postavi promenljivu okruzenja WESAD_PATH na postojecu lokaciju.
WESAD_PATH = Path(os.environ.get("WESAD_PATH", DATA_DIR / "WESAD"))
FEATURES_CSV = DATA_DIR / "wesad_features.csv"