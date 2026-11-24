"""Préparation des données du scénario simulé (étape 1).

``application_train.csv`` (Home Credit) est réduit à 21 features, mélangé, puis découpé en :

- une **référence** : entraînement du premier modèle et référence de dérive ;
- **N lots « hebdomadaires »** de demandes, dont les labels ne sont connus qu'au lot suivant.

À partir du lot ``DRIFT_START_BATCH``, une **dérive progressive** est injectée. Scénario métier :
le bureau de crédit externe change sa méthode de calcul des scores ``EXT_SOURCE_2`` et
``EXT_SOURCE_3`` (les valeurs baissent, le modèle en place les lit comme un risque plus élevé),
et les montants suivent l'inflation. Les labels (``TARGET``) ne sont pas modifiés : seul ce que
voit le modèle change, ce qui laisse au réentraînement la possibilité de récupérer la performance.

Usage (étape ``prepare`` du pipeline DVC) ::

    uv run python -m mlops.data
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from mlops.config import settings

ID_COL = "SK_ID_CURR"
TARGET_COL = "TARGET"
BATCH_COL = "batch"

# Colonnes brutes lues dans application_train.csv.
RAW_NUMERIC = [
    "EXT_SOURCE_1",
    "EXT_SOURCE_2",
    "EXT_SOURCE_3",
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "AMT_GOODS_PRICE",
    "DAYS_BIRTH",
    "DAYS_EMPLOYED",
    "DAYS_ID_PUBLISH",
    "DAYS_REGISTRATION",
    "DAYS_LAST_PHONE_CHANGE",
    "OWN_CAR_AGE",
    "REGION_RATING_CLIENT_W_CITY",
]
RAW_CATEGORICAL = ["CODE_GENDER", "NAME_EDUCATION_TYPE", "NAME_FAMILY_STATUS"]

# Ratios métier repris du Projet 6 (src/features/domain.py).
DOMAIN_FEATURES = [
    "CREDIT_TERM",
    "ANNUITY_INCOME_PERCENT",
    "CREDIT_INCOME_PERCENT",
    "DAYS_EMPLOYED_PERCENT",
]

# Features vues par le modèle : uniquement numériques (pas d'encodage côté API).
FEATURES = (
    RAW_NUMERIC
    + ["CODE_GENDER_F", "EDUCATION_LEVEL", "NAME_FAMILY_STATUS_Married"]
    + DOMAIN_FEATURES
)

EDUCATION_ORDER = {
    "Lower secondary": 0,
    "Secondary / secondary special": 1,
    "Incomplete higher": 2,
    "Higher education": 3,
    "Academic degree": 4,
}

DAYS_EMPLOYED_SENTINEL = 365243  # « sans emploi / retraité » dans Home Credit
DRIFTED_SCORES = ["EXT_SOURCE_2", "EXT_SOURCE_3"]
AMOUNT_COLS = ["AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY", "AMT_GOODS_PRICE"]


# --------------------------------------------------------------------------- préparation


def load_raw(path=None) -> pd.DataFrame:
    """Lit uniquement les colonnes utiles d'``application_train.csv``."""
    path = path or settings.paths.raw_csv
    cols = [ID_COL, TARGET_COL, *RAW_NUMERIC, *RAW_CATEGORICAL]
    return pd.read_csv(path, usecols=cols)


def encode(raw: pd.DataFrame) -> pd.DataFrame:
    """Nettoie et encode les colonnes brutes (sans les ratios métier)."""
    df = raw[[ID_COL, TARGET_COL, *RAW_NUMERIC]].copy()
    df["DAYS_EMPLOYED"] = df["DAYS_EMPLOYED"].replace(DAYS_EMPLOYED_SENTINEL, np.nan)
    df["CODE_GENDER_F"] = raw["CODE_GENDER"].map({"F": 1.0, "M": 0.0})  # « XNA » -> NaN
    df["EDUCATION_LEVEL"] = raw["NAME_EDUCATION_TYPE"].map(EDUCATION_ORDER).astype(float)
    df["NAME_FAMILY_STATUS_Married"] = (raw["NAME_FAMILY_STATUS"] == "Married").astype(float)
    return df


def add_domain_features(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les ratios métier du Projet 6. Utilisé aussi par l'API."""
    df = df.copy()
    df["CREDIT_TERM"] = df["AMT_ANNUITY"] / df["AMT_CREDIT"]
    df["ANNUITY_INCOME_PERCENT"] = df["AMT_ANNUITY"] / df["AMT_INCOME_TOTAL"]
    df["CREDIT_INCOME_PERCENT"] = df["AMT_CREDIT"] / df["AMT_INCOME_TOTAL"]
    df["DAYS_EMPLOYED_PERCENT"] = df["DAYS_EMPLOYED"] / df["DAYS_BIRTH"]
    return df


# ------------------------------------------------------------------------------- dérive


def drift_intensity(k: int, n_batches: int | None = None, start: int | None = None) -> float:
    """Intensité de la dérive au lot ``k`` : 0 avant ``start``, puis croissante jusqu'à 1."""
    n_batches = n_batches or settings.n_batches
    start = start or settings.drift_start_batch
    if k < start:
        return 0.0
    return min(1.0, (k - start + 1) / (n_batches - start + 1))


def inject_drift(df: pd.DataFrame, intensity: float) -> pd.DataFrame:
    """Applique la dérive simulée aux colonnes brutes (avant le calcul des ratios).

    - ``EXT_SOURCE_2`` et ``EXT_SOURCE_3`` : nouvelle échelle du bureau de crédit,
      ``x -> x ** (1 + 2 * intensité)`` (transformation monotone : l'information reste là,
      seul le modèle en place ne sait plus la lire).
    - Montants : inflation de 15 % à intensité maximale. Les ratios métier ne bougent pas,
      ce qui donne des features qui dérivent sans effet sur la performance.
    """
    if intensity <= 0:
        return df
    df = df.copy()
    exponent = 1.0 + 2.0 * intensity
    for col in DRIFTED_SCORES:
        df[col] = df[col] ** exponent
    for col in AMOUNT_COLS:
        df[col] = df[col] * (1.0 + 0.15 * intensity)
    return df


# ----------------------------------------------------------------------------- découpage


def build_scenario(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[pd.DataFrame]]:
    """Mélange, découpe en référence + lots, injecte la dérive. Renvoie (référence, lots)."""
    s = settings
    needed = s.reference_size + s.n_batches * s.batch_size
    if len(raw) < needed:
        raise ValueError(f"{len(raw)} lignes disponibles, {needed} nécessaires")

    df = encode(raw).sample(frac=1.0, random_state=s.random_seed).reset_index(drop=True)

    reference = add_domain_features(df.iloc[: s.reference_size])
    reference = reference[[ID_COL, *FEATURES, TARGET_COL]].reset_index(drop=True)

    batches = []
    for k in range(1, s.n_batches + 1):
        start = s.reference_size + (k - 1) * s.batch_size
        chunk = df.iloc[start : start + s.batch_size]
        chunk = add_domain_features(inject_drift(chunk, drift_intensity(k)))
        chunk = chunk[[ID_COL, *FEATURES, TARGET_COL]].reset_index(drop=True)
        chunk.insert(1, BATCH_COL, k)
        batches.append(chunk)
    return reference, batches


def save_scenario(reference: pd.DataFrame, batches: list[pd.DataFrame]) -> None:
    """Écrit la référence et, pour chaque lot, les demandes et les labels séparément."""
    paths = settings.paths
    paths.batches.mkdir(parents=True, exist_ok=True)
    reference.to_parquet(paths.reference, index=False)
    for k, batch in enumerate(batches, start=1):
        batch.drop(columns=[TARGET_COL]).to_parquet(paths.batch_features(k), index=False)
        batch[[ID_COL, TARGET_COL]].to_parquet(paths.batch_labels(k), index=False)


# ------------------------------------------------------------------------------- lecture


def load_reference() -> pd.DataFrame:
    return pd.read_parquet(settings.paths.reference)


def load_batch(k: int) -> pd.DataFrame:
    """Demandes du lot ``k`` (sans labels) : ce que reçoit l'API."""
    return pd.read_parquet(settings.paths.batch_features(k))


def load_labels(k: int, current_batch: int) -> pd.DataFrame:
    """Labels du lot ``k``, connus seulement à partir du lot ``k + 1`` (un lot de retard)."""
    if k >= current_batch:
        raise ValueError(
            f"Labels du lot {k} indisponibles au lot {current_batch} : ils arrivent au lot {k + 1}"
        )
    return pd.read_parquet(settings.paths.batch_labels(k))


def main() -> None:
    raw = load_raw()
    reference, batches = build_scenario(raw)
    save_scenario(reference, batches)
    print(f"Référence : {len(reference)} lignes, {len(FEATURES)} features")
    for k, batch in enumerate(batches, start=1):
        print(
            f"Lot {k} : {len(batch)} demandes, taux de défaut {batch[TARGET_COL].mean():.1%}, "
            f"dérive {drift_intensity(k):.2f}"
        )


if __name__ == "__main__":
    main()
