"""
Normalizacija po ispitaniku: z = (x - mu) / sigma, gde su mu i sigma
izracunati iz KALIBRACIJE te osobe (mirno stanje na pocetku sesije).

Isti modul koriste i trening (WESAD) i Pi (realno vreme). Ako bi trening
i Pi normalizovali makar malo drugacije, model bi na Pi-ju dobijao brojeve
koje nikad nije video (training/serving skew). Zato postoji samo jedno
mesto gde je ova logika napisana (DRY).

Tok na Pi-ju:   baseline = fit_baseline(kalibracioni_prozori)
                z = transform(novi_prozor, baseline)
Tok u treningu: normalize_subject(prozori_ispitanika, n_calib)
"""

import pandas as pd

FEATURES = ["mean_hr", "eda_mean", "eda_std", "temp_mean", "temp_slope"]

# Donja granica za sigma. Feature koji se tokom kalibracije ne pomeri
# (DS18B20 ima korak 0.0625 C, pa temperatura po nekoliko minuta stoji
# na istoj vrednosti) dao bi sigma = 0 -> deljenje nulom.
# temp_mean: rezolucija DS18B20 - promene manje od koraka senzor ne vidi.
# Ostalo: samo zastita od nule.
# TODO: granicu za EDA revidirati kad se odluci jedinica (ADC ili uS).
SIGMA_FLOOR = {
    "mean_hr": 1e-6,
    "eda_mean": 1e-6,
    "eda_std": 1e-6,
    "temp_mean": 0.0625,
    "temp_slope": 1e-6,
}


def fit_baseline(calib: pd.DataFrame, features=FEATURES) -> dict:
    """Iz kalibracionih prozora JEDNE osobe racuna mu i sigma po feature-u."""
    if len(calib) < 2:
        raise ValueError("Za sigma su potrebna bar 2 kalibraciona prozora.")
    mu = calib[features].mean()
    sigma = calib[features].std(ddof=1)
    floor = pd.Series(SIGMA_FLOOR)[features]
    sigma = sigma.where(sigma > floor, floor)
    return {"mu": mu, "sigma": sigma}


def transform(windows: pd.DataFrame, baseline: dict, features=FEATURES) -> pd.DataFrame:
    """Z-score za bilo koliko prozora: jedan na Pi-ju, sve u treningu."""
    out = windows.copy()
    out[features] = (windows[features] - baseline["mu"]) / baseline["sigma"]
    return out


def normalize_subject(subject_df: pd.DataFrame, n_calib: int, features=FEATURES) -> pd.DataFrame:
    """
    Offline (WESAD): kalibracija = prvih n_calib BASELINE prozora ispitanika,
    sto odgovara mirnoj kalibraciji na pocetku sesije na Pi-ju.
    Ocekuje da su redovi u vremenskom redosledu (ili kolonu window_idx).
    """
    if "window_idx" in subject_df.columns:
        subject_df = subject_df.sort_values("window_idx")
    calib = subject_df[subject_df["label"] == 0].head(n_calib)
    return transform(subject_df, fit_baseline(calib, features), features)
