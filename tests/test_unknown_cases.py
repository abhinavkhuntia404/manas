"""
Evaluation of 5 Unknown / Held-Out Patient Profiles on MANAS V2 Predictive Engine.
Assesses prediction rate, accuracy, calibration, and feature attributions.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analysis.predictive_engine import PredictiveEngine

UNKNOWN_CASES = [
    {
        "id": "CASE-UNK-01",
        "description": "Asymptomatic with APOE4 Risk Gene (Healthy Control)",
        "ground_truth": "CONTROL",
        "inputs": {
            "age": 70.0,
            "sex": "F",
            "mmse": 30.0,
            "cdr": 0.0,
            "nwbv": 0.772,
            "etiv": 1380.0,
            "apoe4_carrier": True,  # Has risk gene, but intact brain and cognition
            "education_years": 18.0,
            "ihc_at8_ffpe": 0.008,
        },
    },
    {
        "id": "CASE-UNK-02",
        "description": "Amnestic Mild Cognitive Impairment (MCI / Prodromal)",
        "ground_truth": "MCI",
        "inputs": {
            "age": 76.0,
            "sex": "M",
            "mmse": 25.0,
            "cdr": 0.5,
            "nwbv": 0.718,
            "etiv": 1510.0,
            "apoe4_carrier": False,
            "education_years": 14.0,
            "ihc_at8_ffpe": 0.042,
        },
    },
    {
        "id": "CASE-UNK-03",
        "description": "Late-Onset Symptomatic Alzheimer's Disease",
        "ground_truth": "AD",
        "inputs": {
            "age": 82.0,
            "sex": "M",
            "mmse": 17.0,
            "cdr": 1.0,
            "nwbv": 0.675,
            "etiv": 1460.0,
            "apoe4_carrier": True,
            "education_years": 12.0,
            "ihc_at8_ffpe": 0.135,
        },
    },
    {
        "id": "CASE-UNK-04",
        "description": "High Cognitive Reserve with Underlying Atrophy",
        "ground_truth": "MCI",
        "inputs": {
            "age": 84.0,
            "sex": "F",
            "mmse": 26.0,
            "cdr": 0.5,
            "nwbv": 0.688,
            "etiv": 1420.0,
            "apoe4_carrier": True,
            "education_years": 20.0,  # High education buffer
            "ihc_at8_ffpe": 0.075,
        },
    },
    {
        "id": "CASE-UNK-05",
        "description": "SuperAger (Advanced Age with Intact Cognition & Preserved Brain)",
        "ground_truth": "CONTROL",
        "inputs": {
            "age": 88.0,
            "sex": "M",
            "mmse": 29.0,
            "cdr": 0.0,
            "nwbv": 0.755,
            "etiv": 1550.0,
            "apoe4_carrier": False,
            "education_years": 16.0,
            "ihc_at8_ffpe": 0.015,
        },
    },
]


def run_unknown_evaluations():
    print("=" * 70)
    print("MANAS V2 PREDICTION ENGINE — EVALUATING 5 UNKNOWN BLIND PROFILES")
    print("=" * 70)

    correct_predictions = 0

    for i, case in enumerate(UNKNOWN_CASES, 1):
        print(f"\n[{i}/5] {case['id']}: {case['description']}")
        print("-" * 65)
        print("Input Parameters:")
        inp = case["inputs"]
        print(f"  Age: {inp['age']}y | Sex: {inp['sex']} | MMSE: {inp['mmse']}/30 | CDR: {inp['cdr']}")
        print(f"  nWBV: {inp['nwbv']:.3f} | APOE4: {'Carrier (ε4+)' if inp['apoe4_carrier'] else 'Non-carrier'} | Educ: {inp['education_years']}y | Tau IHC: {inp['ihc_at8_ffpe']}")
        print(f"Ground Truth Clinical State: {case['ground_truth']}")

        # Execute Prediction
        pred = PredictiveEngine.classify_ad_risk(**inp)
        staging = PredictiveEngine.estimate_cognitive_stage(
            age=inp["age"],
            sex=inp["sex"],
            mmse=inp["mmse"],
            nwbv=inp["nwbv"],
            apoe4_carrier=inp["apoe4_carrier"],
        )

        prob_pct = pred["probability"] * 100
        ci_low = pred["confidence_interval_low"] * 100
        ci_high = pred["confidence_interval_high"] * 100

        print("\nModel Output:")
        print(f"  Inference ID:        {pred['inference_id']}")
        print(f"  Predicted Class:     {pred['predicted_class']} ({pred['predicted_class_label']})")
        print(f"  Estimated AD Prob:   {prob_pct:.1f}% (95% CI: [{ci_low:.1f}% – {ci_high:.1f}%])")
        print(f"  Assigned Risk Tier:  {pred['risk_tier']}")
        print(f"  Estimated CDR Stage: {staging['primary_stage_label']}")
        print(f"  Expected MMSE:       {staging['estimated_mmse']:.1f}/30 (Range: {staging['estimated_mmse_range'][0]}–{staging['estimated_mmse_range'][1]})")

        print("  Top SHAP Feature Attributions:")
        for attr in pred["feature_attributions"][:3]:
            print(f"    • {attr['feature_label']}: {attr['contribution']:+.3f} log-odds ({attr['effect']}, OR: {attr['odds_ratio']}x)")

        is_match = (pred["predicted_class"] == case["ground_truth"])
        if is_match:
            correct_predictions += 1
            print(f"  Concordance:         ✅ CORRECT MATCH (Predicted {pred['predicted_class']} matches Ground Truth {case['ground_truth']})")
        else:
            print(f"  Concordance:         ❌ MISMATCH (Predicted {pred['predicted_class']} vs Ground Truth {case['ground_truth']})")

    accuracy = (correct_predictions / len(UNKNOWN_CASES)) * 100
    print("\n" + "=" * 70)
    print(f"BLIND TEST RESULTS: {correct_predictions}/5 CORRECT ({accuracy:.1f}% SAMPLE ACCURACY)")
    print("=" * 70)


if __name__ == "__main__":
    run_unknown_evaluations()

