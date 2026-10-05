"""
WESAD - Ekstrakcija karakteristika za fiziolosku klasifikaciju stresa
Prozor: 5 sekundi, bez preklapanja
Signali: BVP (64 Hz), EDA (4 Hz), TEMP (4 Hz)
Labela: baseline (0) vs stress (1) - iz WESAD labela 1 i 2

VAZNA NAPOMENA: WESAD wrist uredjaj (Empatica E4) NEMA SpO2 senzor,
za razliku od MAX30102 koji se koristi na hardveru (crveni + IR LED).
Empatica E4 ima samo zeleni PPG senzor za BVP. Zato se iz BVP signala
izvlaci samo srcani ritam (HR), ne i SpO2. Ovo je svesno metodolosko
ogranicenje uslovljeno izborom dataseta, ne propust.

Instalacija: pip install pandas numpy scipy scikit-learn
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.signal import find_peaks

WESAD_PATH = Path("./WESAD")

FS_LABEL = 700  # Hz - labele su sinhronizovane na chest sampling rate
FS_BVP = 64     # Hz
FS_EDA = 4      # Hz
FS_TEMP = 4     # Hz

WINDOW_SEC = 5

# WESAD labele koje nas zanimaju: 1 = baseline, 2 = stress.
# Sve ostalo (0=undefined, 3=amusement, 4=meditation, 5/6/7=ignore) se odbacuje.
LABEL_MAP = {1: 0, 2: 1}  # baseline -> 0, stress -> 1


def load_subject(subject_id: str) -> dict:
    pkl_path = WESAD_PATH / subject_id / f"{subject_id}.pkl"
    with open(pkl_path, "rb") as f:
        return pickle.load(f, encoding="latin1")


def extract_hr_from_bvp(bvp_window: np.ndarray, fs: int = FS_BVP) -> float:
    """
    Racuna prosecan srcani ritam (HR, otkucaja u minuti) iz BVP prozora
    detekcijom pikova - isti princip kao checkForBeat() na ESP32,
    samo primenjen na vec snimljeni signal.

    Napomena: u 5s prozoru pri HR ~60-100 bpm ocekuje se svega 5-8 otkucaja,
    sto cini procenu osetljivom na sum. Ovo je poznato ogranicenje kratkih
    prozora i vredno je pomenuti profesoru kao diskusionu tacku.
    """
    bvp_flat = bvp_window.flatten()
    min_distance = int(fs * 60 / 200)  # HR nece preci 200 bpm
    peaks, _ = find_peaks(bvp_flat, distance=min_distance)

    if len(peaks) < 2:
        return np.nan  # nedovoljno pikova za procenu u ovom prozoru

    ibi = np.diff(peaks) / fs  # vreme izmedju otkucaja, u sekundama
    return 60.0 / np.mean(ibi)


def extract_eda_features(eda_window: np.ndarray) -> tuple:
    """
    mean = tonicki (bazni) nivo provodljivosti koze
    std  = gruba mera fazicke aktivnosti (SCR talasa) u prozoru
    """
    eda_flat = eda_window.flatten()
    return float(np.mean(eda_flat)), float(np.std(eda_flat))


def extract_temp_features(temp_window: np.ndarray) -> tuple:
    """
    mean  = prosecna temperatura koze u prozoru
    slope = brzina promene temperature (linearni fit), u C/s
    """
    temp_flat = temp_window.flatten()
    mean_temp = float(np.mean(temp_flat))

    x = np.arange(len(temp_flat))
    if len(temp_flat) >= 2:
        slope, _ = np.polyfit(x, temp_flat, 1)
        slope_per_sec = float(slope * FS_TEMP)
    else:
        slope_per_sec = 0.0

    return mean_temp, slope_per_sec


def process_subject(subject_id: str) -> pd.DataFrame:
    """Prolazi kroz jednog ispitanika i sece signale na 5s prozore bez preklapanja."""
    data = load_subject(subject_id)
    labels = data["label"]
    bvp = data["signal"]["wrist"]["BVP"].flatten()
    eda = data["signal"]["wrist"]["EDA"].flatten()
    temp = data["signal"]["wrist"]["TEMP"].flatten()

    win_label = WINDOW_SEC * FS_LABEL
    win_bvp = WINDOW_SEC * FS_BVP
    win_eda = WINDOW_SEC * FS_EDA
    win_temp = WINDOW_SEC * FS_TEMP

    n_windows = min(
        len(labels) // win_label,
        len(bvp) // win_bvp,
        len(eda) // win_eda,
        len(temp) // win_temp,
    )

    rows = []
    for i in range(n_windows):
        label_segment = labels[i * win_label: (i + 1) * win_label]
        values, counts = np.unique(label_segment, return_counts=True)
        window_label = values[np.argmax(counts)]  # najcesca vrednost u prozoru

        if window_label not in LABEL_MAP:
            continue

        bvp_seg = bvp[i * win_bvp: (i + 1) * win_bvp]
        eda_seg = eda[i * win_eda: (i + 1) * win_eda]
        temp_seg = temp[i * win_temp: (i + 1) * win_temp]

        mean_hr = extract_hr_from_bvp(bvp_seg)
        eda_mean, eda_std = extract_eda_features(eda_seg)
        temp_mean, temp_slope = extract_temp_features(temp_seg)

        rows.append({
            "subject": subject_id,
            "mean_hr": mean_hr,
            "eda_mean": eda_mean,
            "eda_std": eda_std,
            "temp_mean": temp_mean,
            "temp_slope": temp_slope,
            "label": LABEL_MAP[window_label],
        })

    return pd.DataFrame(rows)


def build_dataset() -> pd.DataFrame:
    """Prolazi kroz sve ispitanike (S2-S17, bez S12) i pravi jedinstven dataset."""
    subject_ids = [f"S{i}" for i in range(2, 18) if i != 12]
    frames = [process_subject(sid) for sid in subject_ids]
    dataset = pd.concat(frames, ignore_index=True)

    before = len(dataset)
    dataset = dataset.dropna()
    after = len(dataset)
    print(f"Odbaceno {before - after} prozora zbog nedovoljno pikova za HR procenu.")

    return dataset


if __name__ == "__main__":
    df = build_dataset()
    print(f"\nUkupno prozora: {len(df)}")
    print(f"Distribucija labela:\n{df['label'].value_counts()}")
    print(f"\nBroj prozora po ispitaniku:\n{df.groupby('subject').size()}")

    df.to_csv("wesad_features.csv", index=False)
    print("\nSacuvano u wesad_features.csv")
