"""
API integration tests for MANAS V2 Predictive Platform endpoints.
Verifies /api/predictions/models, /evaluation, /classify, /stage, /longitudinal, and /report.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database.session import create_tables


@pytest.fixture(scope="module")
def client():
    create_tables()
    with TestClient(app) as c:
        yield c


def test_models_list_endpoint(client):
    response = client.get("/api/predictions/models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    model_ids = [m["model_id"] for m in data]
    assert "MANAS-ML-AD-CLF-01" in model_ids
    assert "MANAS-ML-COG-STAGE-01" in model_ids


def test_model_evaluation_endpoint(client):
    response = client.get("/api/predictions/models/MANAS-ML-AD-CLF-01/evaluation")
    assert response.status_code == 200
    data = response.json()
    assert data["model_id"] == "MANAS-ML-AD-CLF-01"
    assert "roc_curve" in data
    assert "pr_curve" in data
    assert "confusion_matrix" in data
    assert "calibration_curve" in data
    assert "feature_importances" in data
    assert data["metrics"]["roc_auc"] > 0.85


def test_classification_endpoint(client):
    payload = {
        "age": 75.0,
        "sex": "M",
        "mmse": 26.0,
        "cdr": 0.5,
        "nwbv": 0.715,
        "etiv": 1485.0,
        "apoe4_carrier": True,
        "education_years": 14.0,
        "ihc_at8_ffpe": 0.045,
    }
    response = client.post("/api/predictions/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "inference_id" in data
    assert "predicted_class" in data
    assert "probability" in data
    assert 0.0 <= data["probability"] <= 1.0
    assert "feature_attributions" in data
    assert len(data["feature_attributions"]) > 0


def test_cognitive_staging_endpoint(client):
    payload = {
        "age": 76.0,
        "sex": "M",
        "mmse": 25.0,
        "nwbv": 0.718,
        "apoe4_carrier": True,
        "composite_pathology_z": 1.2,
    }
    response = client.post("/api/predictions/stage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "primary_stage" in data
    assert "stage_probabilities" in data
    assert len(data["stage_probabilities"]) == 4
    assert "estimated_mmse" in data


def test_longitudinal_endpoint(client):
    payload = {
        "subject_id": "TEST_SUBJ_01",
        "visits": [
            {"visit_id": 1, "time_days": 0, "age": 76.0, "mmse": 28.0, "cdr": 0.0, "nwbv": 0.740},
            {"visit_id": 2, "time_days": 730, "age": 78.0, "mmse": 25.0, "cdr": 0.5, "nwbv": 0.718},
        ],
    }
    response = client.post("/api/predictions/longitudinal", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["subject_id"] == "TEST_SUBJ_01"
    assert data["visits_count"] == 2
    assert "annualized_brain_atrophy_pct" in data
    assert "annualized_mmse_change" in data
    assert "trajectory_type" in data


def test_report_generation_endpoint(client):
    payload = {
        "subject_identifier": "RESEARCH_DONOR_X",
        "clinical_inputs": {"age": 77, "mmse": 23, "nwbv": 0.705, "apoe4_carrier": True},
    }
    response = client.post("/api/predictions/report", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "report_id" in data
    assert "content_markdown" in data
    assert "RESEARCH_DONOR_X" in data["content_markdown"]

