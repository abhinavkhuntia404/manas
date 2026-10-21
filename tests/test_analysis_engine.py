"""
Unit tests for MANAS Statistical Analysis Engine.
Validates statistical calculations, effect sizes, bootstrap CIs, and FDR corrections.
"""

import pytest
import numpy as np
from scipy import stats

from analysis.engine import AnalysisEngine


class DummyEngine(AnalysisEngine):
    """Subclass without needing a DB session for mathematical unit testing."""
    def __init__(self):
        super().__init__(db=None)


def test_cohens_d_hedges_g():
    engine = DummyEngine()
    # Group 1: mean ~ 10, Group 2: mean ~ 12, sd ~ 1
    np.random.seed(42)
    g1 = np.array([10.0, 10.2, 9.8, 10.1, 9.9, 10.0])
    g2 = np.array([12.0, 11.9, 12.1, 12.0, 11.8, 12.2])

    d = engine._cohens_d(g2, g1)
    # Mean difference is ~2.0, pooled SD is ~0.15, d should be large positive
    assert d > 5.0


def test_rank_biserial():
    engine = DummyEngine()
    g1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    g2 = np.array([6.0, 7.0, 8.0, 9.0, 10.0])

    r = engine._rank_biserial(g2, g1)
    # Perfect separation between g2 and g1 -> r should be exactly 1.0
    assert pytest.approx(r, 0.01) == 1.0


def test_fdr_correction():
    engine = DummyEngine()
    # Raw p-values: 0.001, 0.01, 0.04, 0.20
    results = [
        {"p_value": 0.001, "significance_status": "TESTED"},
        {"p_value": 0.01, "significance_status": "TESTED"},
        {"p_value": 0.04, "significance_status": "TESTED"},
        {"p_value": 0.20, "significance_status": "TESTED"},
    ]

    corrected = engine._apply_fdr_correction(results)

    # All adjusted p-values must be >= raw p-values
    for r in corrected:
        assert r["adjusted_p_value"] >= r["p_value"]
        assert 0.0 <= r["adjusted_p_value"] <= 1.0

    # First two should be FDR significant at 0.05
    assert corrected[0]["significance_status"] == "FDR_SIGNIFICANT"
    assert corrected[1]["significance_status"] == "FDR_SIGNIFICANT"
    assert corrected[3]["significance_status"] == "NOT_FDR_SIGNIFICANT"


def test_bootstrap_ci():
    engine = DummyEngine()
    np.random.seed(42)
    g1 = np.random.normal(5, 1, 30)
    g2 = np.random.normal(7, 1, 30)

    lower, upper = engine._bootstrap_effect_ci(g2, g1, engine._cohens_d, n=200)
    assert lower < upper
    # True effect difference is around 2.0
    assert lower > 1.0
    assert upper < 3.5
