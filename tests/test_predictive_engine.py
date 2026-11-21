"""
Unit tests for MANAS V2 Predictive Engine.
Validates multimodal Alzheimer's classification, 95% confidence intervals,
feature attributions (SHAP weights), cognitive staging, and longitudinal progression.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import pytest
    approx = pytest.approx
except ImportError:
    def approx(expected, abs=0.02):
        class Approx:
            def __eq__(self, actual):
                return builtins_abs(actual - expected) <= abs
        return Approx()
    builtins_abs = abs

from analysis.predictive_engine import PredictiveEngine


def test_ad_classification_high_risk():
    """Validates that a profile with low MMSE, atrophic nWBV, and APOE4 produces High/Very High risk."""
    res = PredictiveEngine.classify_ad_risk(
        age=78.0,
        sex="M",
        mmse=18.0,
        cdr=1.0,
        nwbv=0.680,
        etiv=1450.0,
        apoe4_carrier=True,
        ihc_at8_ffpe=0.120,
    )

    assert res["predicted_class"] == "AD"
    assert res["probability"] > 0.70
    assert res["risk_tier"] in ("HIGH", "VERY_HIGH")
    assert res["confidence_interval_low"] < res["probability"] < res["confidence_interval_high"]
    assert len(res["feature_attributions"]) > 0

    # MMSE should be a major risk factor with positive log-odds impact in this high-risk scenario
    mmse_attr = next(a for a in res["feature_attributions"] if a["feature"] == "mmse")
    assert mmse_attr["effect"] == "INCREASES_RISK"
    assert mmse_attr["contribution"] > 0


def test_ad_classification_control():
    """Validates that a healthy older adult profile produces Control classification with Low risk."""
    res = PredictiveEngine.classify_ad_risk(
        age=72.0,
        sex="F",
        mmse=29.0,
        cdr=0.0,
        nwbv=0.765,
        etiv=1420.0,
        apoe4_carrier=False,
        education_years=16.0,
        ihc_at8_ffpe=0.010,
    )

    assert res["predicted_class"] == "CONTROL"
    assert res["probability"] < 0.40
    assert res["risk_tier"] == "LOW"
    assert 0.0 <= res["probability"] <= 1.0


def test_cognitive_staging():
    """Validates ordinal cognitive stage probabilities and MMSE estimation."""
    res = PredictiveEngine.estimate_cognitive_stage(
        age=76.0,
        sex="M",
        mmse=24.0,
        nwbv=0.710,
        apoe4_carrier=True,
        composite_pathology_z=1.5,
    )

    assert "primary_stage" in res
    assert len(res["stage_probabilities"]) == 4
    
    # Probabilities must sum to ~1.0
    total_prob = sum(s["probability"] for s in res["stage_probabilities"])
    assert total_prob == approx(1.0, abs=0.02)

    # Continuous MMSE estimate should be realistic (within 0-30)
    assert 0.0 <= res["estimated_mmse"] <= 30.0
    assert res["estimated_mmse_range"][0] <= res["estimated_mmse"] <= res["estimated_mmse_range"][1]


def test_longitudinal_trajectory_rapid_decline():
    """Validates longitudinal trajectory rate of atrophy and MMSE change."""
    visits = [
        {"visit_id": 1, "time_days": 0, "age": 75.0, "mmse": 28.0, "cdr": 0.0, "nwbv": 0.745},
        {"visit_id": 2, "time_days": 730, "age": 77.0, "mmse": 24.0, "cdr": 0.5, "nwbv": 0.715},
    ]

    res = PredictiveEngine.analyze_longitudinal_trajectory(subject_id="TEST-001", visits=visits)

    assert res["visits_count"] == 2
    assert res["total_followup_years"] == approx(2.0, abs=0.1)
    assert res["annualized_brain_atrophy_pct"] > 1.0
    assert res["annualized_mmse_change"] < -1.0
    assert len(res["fitted_trajectory"]) == 6  # Years 0 through 5


def test_research_report_generation():
    """Validates automated research report synthesis."""
    rep = PredictiveEngine.generate_research_report(
        subject_id="TEST-DONOR-88",
        clinical_inputs={"age": 79, "mmse": 22, "nwbv": 0.695, "apoe4_carrier": True},
    )

    assert rep["report_id"].startswith("MANAS-REP-")
    assert "TEST-DONOR-88" in rep["content_markdown"]
    assert "Executive Summary" in rep["content_markdown"]
    assert "Scientific & Clinical Disclaimer" in rep["content_markdown"]


if __name__ == "__main__":
    print("Running MANAS V2 Predictive Engine Unit Tests...")
    test_ad_classification_high_risk()
    print("  ✓ test_ad_classification_high_risk passed")
    test_ad_classification_control()
    print("  ✓ test_ad_classification_control passed")
    test_cognitive_staging()
    print("  ✓ test_cognitive_staging passed")
    test_longitudinal_trajectory_rapid_decline()
    print("  ✓ test_longitudinal_trajectory_rapid_decline passed")
    test_research_report_generation()
    print("  ✓ test_research_report_generation passed")
    print("All tests in test_predictive_engine.py passed successfully! ✅")

