"""
Pydantic Schemas for MANAS V2 Predictive Platform API.
Covers Alzheimer's disease classification, cognitive-stage estimation,
explainable AI feature attributions, longitudinal progression, and model evaluation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class FeatureAttributionItem(BaseModel):
    feature: str
    feature_label: str
    value: Optional[float] = None
    importance: float
    contribution: float  # Directional attribution (+ increases AD risk, - decreases risk)
    effect: str          # "INCREASES_RISK", "DECREASES_RISK", "NEUTRAL"
    odds_ratio: Optional[float] = None


class ClassificationRequest(BaseModel):
    age: Optional[float] = Field(None, ge=40, le=115, description="Donor or patient age in years")
    sex: Optional[str] = Field("M", description="Biological sex ('M' or 'F')")
    mmse: Optional[float] = Field(None, ge=0, le=30, description="Mini-Mental State Exam score (0-30)")
    cdr: Optional[float] = Field(None, ge=0, le=3, description="Clinical Dementia Rating (0, 0.5, 1, 2, 3)")
    nwbv: Optional[float] = Field(None, ge=0.50, le=0.90, description="Normalized Whole Brain Volume proportion")
    etiv: Optional[float] = Field(None, ge=800, le=2500, description="Estimated Total Intracranial Volume in mm³")
    apoe4_carrier: Optional[bool] = Field(None, description="Whether subject carries at least one APOE ε4 allele")
    education_years: Optional[float] = Field(None, ge=0, le=30, description="Years of formal education")
    ihc_at8_ffpe: Optional[float] = Field(None, ge=0, description="Hippocampal / temporal pTau AT8 area fraction")
    ihc_a_beta_ffpe: Optional[float] = Field(None, ge=0, description="Amyloid-beta area fraction")
    ptau_ratio: Optional[float] = Field(None, ge=0, description="pTau/Total Tau ratio")
    model_id: Optional[str] = Field("MANAS-ML-AD-CLF-01", description="Identifier of predictive model to use")


class ClassificationResponse(BaseModel):
    inference_id: str
    model_id: str
    predicted_class: str         # "AD", "CONTROL", "MCI"
    predicted_class_label: str
    probability: float          # 0.0 to 1.0 (probability of AD phenotype)
    confidence_interval_low: float
    confidence_interval_high: float
    risk_tier: str              # "LOW", "MODERATE", "HIGH", "VERY_HIGH"
    risk_summary: str
    feature_attributions: List[FeatureAttributionItem]
    model_version: str
    model_accuracy: float
    model_roc_auc: float
    disclaimer: str


class CognitiveStagingRequest(BaseModel):
    age: Optional[float] = Field(None, ge=40, le=115)
    sex: Optional[str] = Field("M")
    mmse: Optional[float] = Field(None, ge=0, le=30)
    nwbv: Optional[float] = Field(None, ge=0.50, le=0.90)
    etiv: Optional[float] = Field(None, ge=800, le=2500)
    apoe4_carrier: Optional[bool] = None
    composite_pathology_z: Optional[float] = Field(None, description="Composite pathology Z-score (AT8 + Aβ)")
    braak_stage: Optional[str] = Field(None, description="Braak stage e.g. 'Stage III-IV'")


class StageProbability(BaseModel):
    stage: str
    stage_name: str
    probability: float
    clinical_description: str


class CognitiveStagingResponse(BaseModel):
    inference_id: str
    primary_stage: str
    primary_stage_label: str
    stage_probabilities: List[StageProbability]
    estimated_mmse: float
    estimated_mmse_range: List[float]
    braak_anatomical_correlation: str
    progression_velocity: str
    recommended_monitoring_interval: str


class VisitPoint(BaseModel):
    visit_id: int
    time_days: float = Field(0.0, description="Days from baseline visit")
    age: float
    mmse: Optional[float] = None
    cdr: Optional[float] = None
    nwbv: Optional[float] = None
    etiv: Optional[float] = None


class LongitudinalAnalysisRequest(BaseModel):
    subject_id: Optional[str] = Field("SUBJ-SIM-001", description="Identifier of subject")
    visits: List[VisitPoint] = Field(..., min_length=2, description="At least two longitudinal observation visits")


class FittedTrajectoryPoint(BaseModel):
    year: float
    predicted_nwbv: float
    predicted_mmse: float
    ci_lower: float
    ci_upper: float


class LongitudinalAnalysisResponse(BaseModel):
    subject_id: str
    visits_count: int
    total_followup_years: float
    annualized_brain_atrophy_pct: float
    annualized_mmse_change: float
    trajectory_type: str        # "STABLE_NORMAL", "TYPICAL_AGING", "ACCELERATED_ATROPHY", "RAPID_COGNITIVE_DECLINE"
    trajectory_description: str
    conversion_risk_5year: float
    fitted_trajectory: List[FittedTrajectoryPoint]
    clinical_interpretation: str


class ModelMetadataResponse(BaseModel):
    model_id: str
    name: str
    version: str
    target_variable: str
    algorithm: str
    training_dataset: str
    n_train: int
    n_features: int
    features: List[str]
    metrics: Dict[str, float]
    cv_method: str
    is_active: bool
    created_at: str


class ModelEvaluationResponse(BaseModel):
    model_id: str
    name: str
    algorithm: str
    target_variable: str
    roc_curve: Dict[str, List[float]]          # "fpr", "tpr", "thresholds"
    pr_curve: Dict[str, List[float]]           # "recall", "precision"
    confusion_matrix: Dict[str, Any]           # "matrix", "labels"
    calibration_curve: Dict[str, List[float]]  # "prob_pred", "prob_true"
    feature_importances: List[Dict[str, Any]]  # "feature", "importance", "direction"
    metrics: Dict[str, float]


class ResearchReportRequest(BaseModel):
    subject_identifier: str = "RESEARCH-DONOR-001"
    clinical_inputs: Dict[str, Any]
    classification: Optional[Dict[str, Any]] = None
    cognitive_staging: Optional[Dict[str, Any]] = None
    longitudinal: Optional[Dict[str, Any]] = None
    investigator_notes: Optional[str] = None


class ResearchReportResponse(BaseModel):
    report_id: str
    generated_at: str
    subject_identifier: str
    title: str
    executive_summary: str
    content_markdown: str
    risk_profile: Dict[str, Any]
    disclaimer: str

