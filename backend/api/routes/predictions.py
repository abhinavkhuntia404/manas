"""
Predictions API router — MANAS V2 Predictive Platform.
Provides endpoints for:
- Alzheimer's research classification & explainability (SHAP attributions)
- Cognitive-stage estimation (CDR & continuous MMSE)
- Longitudinal progression and brain atrophy trajectory modeling
- Model evaluation metrics, ROC/PR curves, confusion matrices & calibration
- Research report generation
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from backend.database.session import get_db
from backend.models.orm import (
    PredictionModelRecord, PredictionInferenceRecord,
    LongitudinalTrajectoryRecord, Subject
)
from backend.schemas.prediction import (
    ClassificationRequest, ClassificationResponse,
    CognitiveStagingRequest, CognitiveStagingResponse,
    LongitudinalAnalysisRequest, LongitudinalAnalysisResponse,
    ModelMetadataResponse, ModelEvaluationResponse,
    ResearchReportRequest, ResearchReportResponse,
)
from analysis.predictive_engine import PredictiveEngine

router = APIRouter()


@router.get("/models", response_model=List[ModelMetadataResponse])
def list_predictive_models():
    """List all registered and trained V2 predictive machine learning models."""
    models = []
    for m in PredictiveEngine.MODELS_METADATA.values():
        models.append(ModelMetadataResponse(
            model_id=m["model_id"],
            name=m["name"],
            version=m["version"],
            target_variable=m["target_variable"],
            algorithm=m["algorithm"],
            training_dataset=m["training_dataset"],
            n_train=m["n_train"],
            n_features=m["n_features"],
            features=m["features"],
            metrics=m["metrics"],
            cv_method=m["cv_method"],
            is_active=m["is_active"],
            created_at=m["created_at"],
        ))
    return models


@router.get("/models/{model_id}/evaluation", response_model=ModelEvaluationResponse)
def get_model_evaluation(model_id: str):
    """
    Get in-depth model performance evaluation: ROC curves, Precision-Recall curves,
    confusion matrix, calibration points, and feature importance rankings.
    """
    if model_id not in PredictiveEngine.MODELS_METADATA:
        # Default to primary AD classifier if not matched exactly
        model_id = "MANAS-ML-AD-CLF-01"

    eval_data = PredictiveEngine.get_model_evaluation(model_id)
    return ModelEvaluationResponse(**eval_data)


@router.post("/classify", response_model=ClassificationResponse)
def predict_ad_classification(
    req: ClassificationRequest,
    db: Session = Depends(get_db),
):
    """
    Classify Alzheimer's Disease phenotype risk with uncertainty confidence intervals
    and explainable feature attributions (marginal log-odds & odds ratios).
    """
    try:
        res = PredictiveEngine.classify_ad_risk(
            age=req.age,
            sex=req.sex,
            mmse=req.mmse,
            cdr=req.cdr,
            nwbv=req.nwbv,
            etiv=req.etiv,
            apoe4_carrier=req.apoe4_carrier,
            education_years=req.education_years,
            ihc_at8_ffpe=req.ihc_at8_ffpe,
            ihc_a_beta_ffpe=req.ihc_a_beta_ffpe,
            ptau_ratio=req.ptau_ratio,
            model_id=req.model_id or "MANAS-ML-AD-CLF-01",
        )

        # Log inference to database provenance record
        try:
            inference_record = PredictionInferenceRecord(
                inference_id=res["inference_id"],
                model_id=res["model_id"],
                input_features=req.model_dump(),
                predicted_class=res["predicted_class"],
                prediction_probability=res["probability"],
                confidence_interval_low=res["confidence_interval_low"],
                confidence_interval_high=res["confidence_interval_high"],
                feature_attributions=res["feature_attributions"],
                risk_tier=res["risk_tier"],
            )
            db.add(inference_record)
            db.commit()
        except Exception:
            db.rollback()  # Non-fatal if DB table is syncing

        return ClassificationResponse(**res)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.post("/stage", response_model=CognitiveStagingResponse)
def estimate_cognitive_stage(req: CognitiveStagingRequest):
    """
    Estimate multi-class cognitive stage distribution (CDR 0, CDR 0.5, CDR 1, CDR 2+)
    and predicted continuous MMSE score.
    """
    try:
        res = PredictiveEngine.estimate_cognitive_stage(
            age=req.age,
            sex=req.sex,
            mmse=req.mmse,
            nwbv=req.nwbv,
            etiv=req.etiv,
            apoe4_carrier=req.apoe4_carrier,
            composite_pathology_z=req.composite_pathology_z,
            braak_stage=req.braak_stage,
        )
        return CognitiveStagingResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cognitive staging failed: {str(e)}")


@router.post("/longitudinal", response_model=LongitudinalAnalysisResponse)
def analyze_longitudinal_trajectory(req: LongitudinalAnalysisRequest):
    """
    Analyze sequential visit observations to compute annualized brain atrophy rates (% nWBV/year),
    MMSE decline slopes, and 5-year conversion risk.
    """
    try:
        visits_dict = [v.model_dump() for v in req.visits]
        res = PredictiveEngine.analyze_longitudinal_trajectory(
            subject_id=req.subject_id or "SUBJECT-001",
            visits=visits_dict,
        )
        return LongitudinalAnalysisResponse(**res)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Longitudinal analysis failed: {str(e)}")


@router.post("/report", response_model=ResearchReportResponse)
def generate_research_report(req: ResearchReportRequest):
    """
    Synthesize an exportable, reproducible scientific research report covering
    clinical input profile, classification, staging, and longitudinal decline.
    """
    try:
        res = PredictiveEngine.generate_research_report(
            subject_id=req.subject_identifier,
            clinical_inputs=req.clinical_inputs,
            classification=req.classification,
            staging=req.cognitive_staging,
            longitudinal=req.longitudinal,
            investigator_notes=req.investigator_notes,
        )
        return ResearchReportResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

