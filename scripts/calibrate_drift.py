"""Calibration de la dérive simulée (étape 1, décision D2).

Vérifie, avant de construire la boucle, que la dérive injectée par ``mlops/data.py`` :

1. n'est pas détectée sur les lots 1 et 2 (pas de fausse alerte) ;
2. est détectée à partir du lot 3 (test KS sur le score prédit) ;
3. dégrade le champion (AUC en baisse, coût métier en hausse) ;
4. peut être corrigée par un réentraînement (challenger = référence + 2 derniers lots labellisés).

Prérequis : ``uv run dvc repro`` (référence et lots dans ``data/``).

Usage ::

    uv run python scripts/calibrate_drift.py
"""

from __future__ import annotations

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from mlops.config import settings
from mlops.data import FEATURES, ID_COL, TARGET_COL, load_reference

LGBM_PARAMS = dict(
    n_estimators=400,
    learning_rate=0.05,
    num_leaves=31,
    min_child_samples=50,
    subsample=0.8,
    subsample_freq=1,
    colsample_bytree=0.8,
    class_weight="balanced",
    random_state=42,
    verbose=-1,
)


def business_cost(y: np.ndarray, proba: np.ndarray, threshold: float) -> float:
    """Coût métier moyen par demande : (10 × FN + 1 × FP) / n."""
    pred = proba >= threshold
    fn = np.sum(~pred & (y == 1))
    fp = np.sum(pred & (y == 0))
    return float(settings.cost_fn * fn + settings.cost_fp * fp) / len(y)


def best_threshold(y: np.ndarray, proba: np.ndarray) -> float:
    """Seuil de décision qui minimise le coût métier."""
    grid = np.linspace(0.05, 0.95, 91)
    return float(grid[np.argmin([business_cost(y, proba, t) for t in grid])])


def fit(df: pd.DataFrame) -> lgb.LGBMClassifier:
    return lgb.LGBMClassifier(**LGBM_PARAMS).fit(df[FEATURES], df[TARGET_COL])


def load_labeled_batch(k: int) -> pd.DataFrame:
    """Lot k avec ses labels (lecture directe : la calibration voit tout, la boucle non)."""
    features = pd.read_parquet(settings.paths.batch_features(k))
    labels = pd.read_parquet(settings.paths.batch_labels(k))
    return features.merge(labels, on=ID_COL)


def main() -> None:
    reference = load_reference()
    train, valid = train_test_split(
        reference, test_size=0.2, stratify=reference[TARGET_COL], random_state=42
    )
    champion = fit(train)
    p_valid = champion.predict_proba(valid[FEATURES])[:, 1]
    y_valid = valid[TARGET_COL].to_numpy()
    threshold = best_threshold(y_valid, p_valid)
    print(
        f"Champion (référence) : AUC {roc_auc_score(y_valid, p_valid):.3f}, "
        f"seuil {threshold:.2f}, coût {business_cost(y_valid, p_valid, threshold):.3f}\n"
    )

    batches = {k: load_labeled_batch(k) for k in range(1, settings.n_batches + 1)}

    print(
        "| Lot | AUC champion | Coût champion | KS du score (p) "
        "| AUC challenger | Coût challenger |"
    )
    print("|---|---|---|---|---|---|")
    for k, batch in batches.items():
        y = batch[TARGET_COL].to_numpy()
        p = champion.predict_proba(batch[FEATURES])[:, 1]
        ks_p = ks_2samp(p_valid, p).pvalue
        row = (
            f"| {k} | {roc_auc_score(y, p):.3f} | {business_cost(y, p, threshold):.3f} "
            f"| {ks_p:.1e} |"
        )
        if k >= 3:
            # Challenger : référence + les 2 derniers lots dont les labels sont connus au lot k.
            challenger = fit(pd.concat([reference, batches[k - 2], batches[k - 1]]))
            last = batches[k - 1]
            t_ch = best_threshold(
                last[TARGET_COL].to_numpy(), challenger.predict_proba(last[FEATURES])[:, 1]
            )
            p_ch = challenger.predict_proba(batch[FEATURES])[:, 1]
            row += f" {roc_auc_score(y, p_ch):.3f} | {business_cost(y, p_ch, t_ch):.3f} |"
        else:
            row += " — | — |"
        print(row)


if __name__ == "__main__":
    main()
