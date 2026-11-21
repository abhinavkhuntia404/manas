"""
Standalone Test Runner for MANAS V2 Predictive Engine.
Executes test cases for:
  1. Multimodal Alzheimer's Classifier (High Risk vs Control)
  2. Cognitive-Stage Estimation (CDR 0, 0.5, 1, 2+ and continuous MMSE)
  3. Explainable Machine Learning (SHAP marginal log-odds & odds ratios)
  4. Longitudinal Trajectory Modeling (Atrophy rate & decline slope)
  5. Scientific Research Report Synthesizer
"""

import sys
import os

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analysis.predictive_engine import PredictiveEngine


def test_1_high_risk_classification():
    print("\n--- Test 1: Alzheimer's Classification (High-Risk AD Profile) ---")
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
    print(f"Inference ID:     {res['inference_id']}")
    print(f"Predicted Class:  {res['predicted_class']} ({res['predicted_class_label']})")
    print(f"Probability:      {res['probability']*100:.1f}%")
    print(f"95% CI:           [{res['confidence_interval_low']*100:.1f}% - {res['confidence_interval_high']*100:.1f}%]")
    print(f"Risk Tier:        {res['risk_tier']}")
    print(f"Top 3 Attributions:")
    for a in res['feature_attributions'][:3]:
        print(f"  - {a['feature_label']}: {a['contribution']:+.3f} log-odds (Effect: {a['effect']}, OR: {a['odds_ratio']}x)")

    assert res["predicted_class"] == "AD", f"Expected AD, got {res['predicted_class']}"
    assert res["probability"] > 0.70, f"Expected probability > 0.70, got {res['probability']}"
    assert res["risk_tier"] in ("HIGH", "VERY_HIGH")
    assert res["confidence_interval_low"] < res["probability"] < res["confidence_interval_high"]
    print(">>> Test 1 PASSED!")


def test_2_healthy_control_classification():
    print("\n--- Test 2: Alzheimer's Classification (Healthy Control Profile) ---")
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
    print(f"Inference ID:     {res['inference_id']}")
    print(f"Predicted Class:  {res['predicted_class']} ({res['predicted_class_label']})")
    print(f"Probability:      {res['probability']*100:.1f}%")
    print(f"95% CI:           [{res['confidence_interval_low']*100:.1f}% - {res['confidence_interval_high']*100:.1f}%]")
    print(f"Risk Tier:        {res['risk_tier']}")

    assert res["predicted_class"] == "CONTROL", f"Expected CONTROL, got {res['predicted_class']}"
    assert res["probability"] < 0.40, f"Expected probability < 0.40, got {res['probability']}"
    assert res["risk_tier"] == "LOW"
    print(">>> Test 2 PASSED!")


def test_3_cognitive_staging():
    print("\n--- Test 3: Ordinal Cognitive Staging & Continuous MMSE Estimation ---")
    res = PredictiveEngine.estimate_cognitive_stage(
        age=76.0,
        sex="M",
        mmse=24.0,
        nwbv=0.710,
        apoe4_carrier=True,
        composite_pathology_z=1.5,
    )
    print(f"Primary Stage:    {res['primary_stage']} ({res['primary_stage_label']})")
    print(f"Estimated MMSE:   {res['estimated_mmse']} (Range: {res['estimated_mmse_range'][0]} - {res['estimated_mmse_range'][1]})")
    print(f"Braak Staging:    {res['braak_anatomical_correlation']}")
    print(f"Velocity:         {res['progression_velocity']}")
    print("Stage Probabilities:")
    for sp in res["stage_probabilities"]:
        print(f"  - {sp['stage_name']}: {sp['probability']*100:.1f}%")

    assert "primary_stage" in res
    assert len(res["stage_probabilities"]) == 4
    tot_p = sum(sp["probability"] for sp in res["stage_probabilities"])
    assert abs(tot_p - 1.0) < 0.02, f"Probabilities do not sum to 1.0: {tot_p}"
    assert 0.0 <= res["estimated_mmse"] <= 30.0
    print(">>> Test 3 PASSED!")


def test_4_longitudinal_trajectory():
    print("\n--- Test 4: Longitudinal Trajectory & Progression Modeling ---")
    visits = [
        {"visit_id": 1, "time_days": 0, "age": 78.0, "mmse": 28.0, "cdr": 0.0, "nwbv": 0.748},
        {"visit_id": 2, "time_days": 706, "age": 79.9, "mmse": 26.0, "cdr": 0.5, "nwbv": 0.729},
        {"visit_id": 3, "time_days": 1461, "age": 82.0, "mmse": 22.0, "cdr": 1.0, "nwbv": 0.704},
    ]
    res = PredictiveEngine.analyze_longitudinal_trajectory(subject_id="OAS2_0031", visits=visits)
    print(f"Subject:          {res['subject_id']}")
    print(f"Total Follow-up:  {res['total_followup_years']} years across {res['visits_count']} visits")
    print(f"Atrophy Rate:     {res['annualized_brain_atrophy_pct']:.2f}% per year")
    print(f"MMSE Decline:     {res['annualized_mmse_change']:.2f} points per year")
    print(f"Trajectory Type:  {res['trajectory_type']}")
    print(f"5-Year Conv Risk: {res['conversion_risk_5year']*100:.1f}%")
    print("Projected Curve:")
    for pt in res["fitted_trajectory"][:4]:
        print(f"  - Year +{pt['year']:.0f}: nWBV={pt['predicted_nwbv']:.4f}, MMSE={pt['predicted_mmse']:.1f} (CI: [{pt['ci_lower']} - {pt['ci_upper']}])")

    assert res["visits_count"] == 3
    assert res["annualized_brain_atrophy_pct"] > 1.0
    assert res["annualized_mmse_change"] < -1.0
    assert len(res["fitted_trajectory"]) == 6
    print(">>> Test 4 PASSED!")


def test_5_research_report():
    print("\n--- Test 5: Scientific Research Report Synthesizer ---")
    rep = PredictiveEngine.generate_research_report(
        subject_id="TEST-DONOR-042",
        clinical_inputs={"age": 80, "mmse": 20, "nwbv": 0.69, "apoe4_carrier": True, "ihc_at8_ffpe": 0.08},
    )
    print(f"Report ID:        {rep['report_id']}")
    print(f"Title:            {rep['title']}")
    print(f"Generated At:     {rep['generated_at']}")
    print(f"Markdown Length:  {len(rep['content_markdown'])} chars")
    assert "Executive Summary" in rep["content_markdown"]
    assert "Explainable Machine Learning" in rep["content_markdown"]
    assert "Scientific & Clinical Disclaimer" in rep["content_markdown"]
    print(">>> Test 5 PASSED!")


def test_6_model_evaluation_metrics():
    print("\n--- Test 6: Model Evaluation & Calibration Dashboards ---")
    ev = PredictiveEngine.get_model_evaluation("MANAS-ML-AD-CLF-01")
    print(f"Model ID:         {ev['model_id']}")
    print(f"ROC-AUC:          {ev['metrics']['roc_auc']}")
    print(f"PR-AUC:           {ev['metrics']['pr_auc']}")
    print(f"Accuracy:         {ev['metrics']['accuracy']*100:.1f}%")
    print(f"Brier Score:      {ev['metrics']['brier_score']}")
    print(f"Confusion Matrix: Tested n={ev['confusion_matrix']['total_tested']}")
    assert ev["metrics"]["roc_auc"] > 0.85
    assert len(ev["roc_curve"]["fpr"]) > 5
    assert len(ev["calibration_curve"]["prob_pred"]) > 5
    print(">>> Test 6 PASSED!")


if __name__ == "__main__":
    print("==================================================")
    print("MANAS V2 PREDICTIVE ENGINE — COMPREHENSIVE TEST RUN")
    print("==================================================")
    try:
        test_1_high_risk_classification()
        test_2_healthy_control_classification()
        test_3_cognitive_staging()
        test_4_longitudinal_trajectory()
        test_5_research_report()
        test_6_model_evaluation_metrics()
        print("\n==================================================")
        print("ALL 6 PREDICTION ENGINE SUITES PASSED CLEANLY! ✅")
        print("==================================================")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

