"""Tests de la préparation des données et de la dérive simulée (mlops/data.py)."""

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from mlops import data
from mlops.config import Paths


def _raw(n: int, seed: int = 0) -> pd.DataFrame:
    """Faux extrait d'application_train.csv avec les colonnes lues par load_raw."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({col: rng.uniform(0.1, 0.9, n) for col in data.RAW_NUMERIC})
    for col in data.AMOUNT_COLS:
        df[col] = rng.uniform(10_000, 500_000, n)
    df["DAYS_BIRTH"] = -rng.integers(7_000, 25_000, n)
    df["DAYS_EMPLOYED"] = -rng.integers(0, 7_000, n)
    df.loc[0, "DAYS_EMPLOYED"] = data.DAYS_EMPLOYED_SENTINEL
    df[data.ID_COL] = np.arange(n)
    df[data.TARGET_COL] = rng.integers(0, 2, n)
    df["CODE_GENDER"] = rng.choice(["F", "M", "XNA"], n)
    df["NAME_EDUCATION_TYPE"] = rng.choice(list(data.EDUCATION_ORDER), n)
    df["NAME_FAMILY_STATUS"] = rng.choice(["Married", "Single / not married"], n)
    return df


@pytest.fixture
def small_settings(monkeypatch, tmp_path):
    s = replace(
        data.settings,
        reference_size=100,
        n_batches=5,
        batch_size=20,
        drift_start_batch=3,
        paths=Paths(data=tmp_path),
    )
    monkeypatch.setattr(data, "settings", s)
    return s


def test_encode_cleans_and_encodes():
    raw = _raw(50)
    df = data.encode(raw)
    assert np.isnan(df.loc[0, "DAYS_EMPLOYED"])  # sentinelle 365243 -> NaN
    xna = raw["CODE_GENDER"] == "XNA"
    assert df.loc[xna, "CODE_GENDER_F"].isna().all()
    assert set(df.loc[~xna, "CODE_GENDER_F"]) <= {0.0, 1.0}
    assert df["EDUCATION_LEVEL"].between(0, 4).all()


def test_domain_features():
    df = pd.DataFrame(
        {
            "AMT_ANNUITY": [10.0],
            "AMT_CREDIT": [200.0],
            "AMT_INCOME_TOTAL": [100.0],
            "DAYS_EMPLOYED": [-1000.0],
            "DAYS_BIRTH": [-10000.0],
        }
    )
    out = data.add_domain_features(df)
    assert out.loc[0, "CREDIT_TERM"] == pytest.approx(0.05)
    assert out.loc[0, "ANNUITY_INCOME_PERCENT"] == pytest.approx(0.1)
    assert out.loc[0, "CREDIT_INCOME_PERCENT"] == pytest.approx(2.0)
    assert out.loc[0, "DAYS_EMPLOYED_PERCENT"] == pytest.approx(0.1)


@pytest.mark.parametrize(
    ("k", "expected"),
    [(1, 0.0), (2, 0.0), (3, 1 / 6), (5, 0.5), (8, 1.0), (10, 1.0)],
)
def test_drift_intensity_is_progressive(k, expected):
    assert data.drift_intensity(k, n_batches=8, start=3) == pytest.approx(expected)


def test_inject_drift():
    df = data.encode(_raw(200))
    assert data.inject_drift(df, 0.0) is df  # pas de dérive : rien ne change

    drifted = data.inject_drift(df, 1.0)
    for col in data.DRIFTED_SCORES:
        # les scores baissent, mais l'ordre est conservé (transformation monotone)
        assert (drifted[col] <= df[col]).all()
        assert drifted[col].rank().equals(df[col].rank())
    assert np.allclose(drifted["AMT_CREDIT"], df["AMT_CREDIT"] * 1.15)
    # l'inflation touche tous les montants : les ratios métier ne bougent pas
    before = data.add_domain_features(df)["CREDIT_INCOME_PERCENT"]
    after = data.add_domain_features(drifted)["CREDIT_INCOME_PERCENT"]
    assert np.allclose(before, after)
    # la cible n'est jamais modifiée
    assert drifted[data.TARGET_COL].equals(df[data.TARGET_COL])


def test_build_scenario(small_settings):
    reference, batches = data.build_scenario(_raw(300))
    assert len(reference) == 100
    assert list(reference.columns) == [data.ID_COL, *data.FEATURES, data.TARGET_COL]
    assert len(batches) == 5
    assert all(len(b) == 20 for b in batches)
    # aucun client dans deux jeux à la fois
    ids = pd.concat([reference[data.ID_COL], *[b[data.ID_COL] for b in batches]])
    assert ids.is_unique


def test_build_scenario_needs_enough_rows(small_settings):
    with pytest.raises(ValueError):
        data.build_scenario(_raw(150))


def test_labels_arrive_one_batch_late(small_settings):
    reference, batches = data.build_scenario(_raw(300))
    data.save_scenario(reference, batches)

    assert data.TARGET_COL not in data.load_batch(2).columns  # l'API ne voit pas les labels
    labels = data.load_labels(2, current_batch=3)
    assert len(labels) == 20
    with pytest.raises(ValueError):
        data.load_labels(3, current_batch=3)
