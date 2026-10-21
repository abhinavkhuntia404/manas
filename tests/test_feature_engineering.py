"""
Unit tests for Biomarker Feature Engineering and Preprocessing Harmonization.
"""

import numpy as np
import pandas as pd
import pytest

from feature_engineering.biomarkers import (
    compute_tau_phosphorylation_ratio,
    compute_composite_pathology_score,
    map_braak_staging,
)
from preprocessing.harmonizer import DataHarmonizer


def test_tau_phosphorylation_ratio():
    df = pd.DataFrame({
        "tau_ng_per_mg": [10.0, 20.0, 0.0],
        "ptau_ng_per_mg": [2.0, 8.0, 1.0],
    })
    ratio = compute_tau_phosphorylation_ratio(df)
    assert ratio.iloc[0] == pytest.approx(0.20)
    assert ratio.iloc[1] == pytest.approx(0.40)
    assert np.isnan(ratio.iloc[2])  # Division by zero avoided


def test_composite_pathology_score():
    df = pd.DataFrame({
        "ihc_at8_ffpe": [1.0, 2.0, 3.0],
        "ihc_a_beta_ffpe": [10.0, 20.0, 30.0],
    })
    score = compute_composite_pathology_score(df)
    assert len(score) == 3
    # Midpoint should have Z-score of 0
    assert score.iloc[1] == pytest.approx(0.0, abs=1e-5)


def test_braak_staging():
    series = pd.Series(["Stage I", "Braak 4", "VI", "0", None])
    staged = map_braak_staging(series)
    assert staged["braak_anatomical_stage"].iloc[0] == "STAGE_I_II_TRANSENTORHINAL"
    assert staged["braak_anatomical_stage"].iloc[1] == "STAGE_III_IV_LIMBIC"
    assert staged["braak_anatomical_stage"].iloc[2] == "STAGE_V_VI_ISOCORTICAL"
    assert staged["braak_anatomical_stage"].iloc[3] == "STAGE_0_NONE"
    assert staged["braak_anatomical_stage"].iloc[4] == "UNKNOWN"


def test_harmonizer_winsorize():
    series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 100.0])  # 100 is extreme outlier
    winsorized = DataHarmonizer.winsorize_outliers(series, 0.05, 0.95)
    assert winsorized.max() < 100.0
