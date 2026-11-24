"""Configuration du projet, lue depuis l'environnement (``.env.local`` puis ``.env``).

Toutes les adresses passent par ici : passer du palier 1 (local) aux paliers 2 et 3
(en ligne) ne demande que de changer les variables d'environnement.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent

# .env.local a priorité sur .env ; les variables déjà définies dans l'environnement gagnent.
load_dotenv(ROOT / ".env.local")
load_dotenv(ROOT / ".env")


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


# Paramètres versionnés (scénario simulé) : une seule source, lue aussi par DVC.
_SCENARIO = yaml.safe_load((ROOT / "params.yaml").read_text(encoding="utf-8"))["scenario"]


@dataclass(frozen=True)
class Paths:
    """Emplacements des données (versionnées par DVC, pas par Git)."""

    data: Path = ROOT / "data"

    @property
    def raw_csv(self) -> Path:
        return self.data / "raw" / "application_train.csv"

    @property
    def reference(self) -> Path:
        return self.data / "reference.parquet"

    @property
    def batches(self) -> Path:
        return self.data / "batches"

    def batch_features(self, k: int) -> Path:
        return self.batches / f"batch_{k:02d}.parquet"

    def batch_labels(self, k: int) -> Path:
        return self.batches / f"labels_{k:02d}.parquet"


@dataclass(frozen=True)
class Settings:
    mlflow_tracking_uri: str = _env("MLFLOW_TRACKING_URI", "http://localhost:5000")
    model_name: str = _env("MODEL_NAME", "credit-scoring")
    model_alias: str = _env("MODEL_ALIAS", "champion")
    database_url: str = _env("DATABASE_URL", "postgresql://scoring:scoring@localhost:5432/scoring")

    # Seuil métier repris du Projet 6 (FN = 10 × FP), recalculé à chaque entraînement.
    decision_threshold: float = float(_env("DECISION_THRESHOLD", "0.49"))
    cost_fn: float = 10.0
    cost_fp: float = 1.0

    # Scénario simulé (étape 1) : lu dans params.yaml, suivi par DVC.
    random_seed: int = _SCENARIO["random_seed"]
    reference_size: int = _SCENARIO["reference_size"]
    n_batches: int = _SCENARIO["n_batches"]
    batch_size: int = _SCENARIO["batch_size"]
    drift_start_batch: int = _SCENARIO["drift_start_batch"]

    paths: Paths = Paths()


settings = Settings()
