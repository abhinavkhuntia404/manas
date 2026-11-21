# MANAS REST API Specification

> **Base URL (Local):** `http://localhost:8000` (or `http://localhost:8005`)  
> **Interactive Swagger UI:** `/api/docs`  
> **OpenAPI JSON:** `/api/openapi.json`  
> **Authentication:** Open / Public (Research Access)  
> **Rate Limiting:** Enforced via SlowAPI (60 req/min standard, 10 req/min for compute-heavy submission endpoints)

---

## 1. System Health

### `GET /api/health`
Verifies service uptime and relational database connectivity.

**Response `200 OK`:**
```json
{
  "status": "ok",
  "version": "2.0.0-rc1",
  "database": "connected",
  "timestamp": "2026-11-21T10:00:00Z"
}
```

---

## 2. Dataset Registry

### `GET /api/datasets/`
Returns all registered neuroimaging and neuropathology datasets.

**Response `200 OK`:**
```json
[
  {
    "dataset_id": 1,
    "name": "Allen Aging, Dementia and TBI Study",
    "short_name": "allen_aging",
    "source_org": "Allen Institute for Brain Science",
    "official_url": "https://aging.brain-map.org/download/index",
    "access_type": "OPEN_DIRECT",
    "license": "Allen Institute Terms of Use",
    "primary_disease": ["Alzheimer's Disease"],
    "description": "107 donors with quantitative neuropathology and clinical profiles",
    "latest_version": {
      "version_id": 1,
      "version_tag": "v1.0",
      "download_date": "2026-10-15T00:00:00Z",
      "is_synthetic": false
    }
  }
]
```

### `GET /api/datasets/{dataset_id}`
Returns metadata, registered versions, and files for a specific dataset.

---

## 3. Brain Regions & Ontology

### `GET /api/regions/`
Paginated search and listing of canonical brain structures.

**Query Parameters:**
- `page` (int, default: 1): Page number.
- `page_size` (int, default: 50): Number of records per page.
- `search` (str, optional): Search term for region name or acronym.
- `hemisphere` (str, optional): Filter by `left`, `right`, or `bilateral`.

**Response `200 OK`:**
```json
{
  "total": 4,
  "page": 1,
  "page_size": 50,
  "regions": [
    {
      "region_id": 1,
      "name": "Hippocampus",
      "abbreviation": "HIP",
      "hemisphere": "bilateral",
      "anatomical_category": "limbic",
      "lobe": "temporal",
      "atlas_id": 1,
      "parent_region_id": null,
      "is_leaf": true
    }
  ]
}
```

### `GET /api/regions/{region_id}`
Returns anatomical details, parent/children relationships, and all historical analysis results for this region.

---

## 4. Regional Statistical Analysis (V1)

### `POST /api/analyses/`
Submits a new hypothesis testing job comparing disease vs control cohorts.

**Request Body:**
```json
{
  "version_id": 1,
  "disease": "Alzheimer's Disease",
  "analysis_type": "AD_REGIONAL_COMPARISON",
  "measurement_type_name": "ihc_at8_ffpe",
  "covariates": ["age", "sex"],
  "random_seed": 42
}
```

**Response `200 OK`:**
```json
{
  "analysis_run_id": "MANAS-AD-2026-00001",
  "status": "QUEUED",
  "is_synthetic": false,
  "message": "Analysis submitted successfully."
}
```

### `GET /api/analyses/{analysis_run_id}`
Retrieves complete provenance, execution status, and parameters for an analysis run.

### `GET /api/analyses/{analysis_run_id}/results`
Returns paginated per-region statistical findings, effect sizes, and adjusted p-values.

**Response `200 OK`:**
```json
{
  "analysis_run_id": "MANAS-AD-2026-00001",
  "is_synthetic": false,
  "total": 4,
  "results": [
    {
      "region_id": 1,
      "region_name": "Hippocampus",
      "abbreviation": "HIP",
      "hemisphere": "bilateral",
      "anatomical_category": "limbic",
      "n_disease": 48,
      "n_control": 42,
      "disease_mean": 0.082,
      "control_mean": 0.011,
      "mean_difference": 0.071,
      "effect_size": 1.42,
      "effect_size_ci_lower": 0.98,
      "effect_size_ci_upper": 1.86,
      "p_value": 0.00004,
      "adjusted_p_value": 0.00016,
      "significance_status": "FDR_SIGNIFICANT",
      "test_method": "Welch's t-test (unequal variance)"
    }
  ]
}
```

---

## 5. Predictive Platform & Machine Learning (V2)

### `GET /api/predictions/models`
Lists all trained machine learning models, algorithms, and validation metrics.

**Response `200 OK`:**
```json
[
  {
    "model_id": "MANAS-ML-AD-CLF-01",
    "name": "Multimodal Alzheimer's Clinical & Pathological Classifier",
    "version": "2.0.0-rc1",
    "target_variable": "AD_DIAGNOSIS (AD vs Control)",
    "algorithm": "Calibrated Regularized Logistic Regression + Gradient Boosted Ensemble",
    "training_dataset": "OASIS-1, OASIS-2, and Allen Aging cohorts (n=684 pooled)",
    "n_train": 684,
    "n_features": 8,
    "features": ["mmse", "nwbv", "age", "apoe4_carrier", "etiv", "ihc_at8_ffpe", "sex", "education_years"],
    "metrics": {
      "roc_auc": 0.914,
      "pr_auc": 0.898,
      "accuracy": 0.862,
      "f1": 0.855,
      "sensitivity": 0.871,
      "specificity": 0.853,
      "brier_score": 0.098
    },
    "cv_method": "Stratified 5-Fold Repeated Cross-Validation",
    "is_active": true,
    "created_at": "2026-10-15T00:00:00Z"
  }
]
```

### `GET /api/predictions/models/{model_id}/evaluation`
Retrieves in-depth cross-validated evaluation data: ROC points, Precision-Recall points, confusion matrices, probability calibration curves, and global feature importance rankings.

### `POST /api/predictions/classify`
Classifies Alzheimer's Disease risk with 95% confidence intervals and explainable SHAP feature attributions.

**Request Body:**
```json
{
  "age": 75.0,
  "sex": "M",
  "mmse": 26.0,
  "cdr": 0.5,
  "nwbv": 0.715,
  "etiv": 1485.0,
  "apoe4_carrier": true,
  "education_years": 14.0,
  "ihc_at8_ffpe": 0.045,
  "model_id": "MANAS-ML-AD-CLF-01"
}
```

**Response `200 OK`:**
```json
{
  "inference_id": "MANAS-PRED-2026-C4B891A2",
  "model_id": "MANAS-ML-AD-CLF-01",
  "predicted_class": "AD",
  "predicted_class_label": "Alzheimer's Disease Phenotype",
  "probability": 0.7324,
  "confidence_interval_low": 0.6120,
  "confidence_interval_high": 0.8295,
  "risk_tier": "HIGH",
  "risk_summary": "Features are strongly consistent with symptomatic Alzheimer's disease pathology.",
  "feature_attributions": [
    {
      "feature": "mmse",
      "feature_label": "Mini-Mental State Exam (MMSE)",
      "value": 26.0,
      "importance": 0.38,
      "contribution": 0.534,
      "effect": "INCREASES_RISK",
      "odds_ratio": 1.71
    },
    {
      "feature": "nwbv",
      "feature_label": "Normalized Whole Brain Volume (nWBV)",
      "value": 0.715,
      "importance": 0.26,
      "contribution": 0.944,
      "effect": "INCREASES_RISK",
      "odds_ratio": 2.57
    },
    {
      "feature": "apoe4_carrier",
      "feature_label": "APOE ε4 Allele Status",
      "value": 1.0,
      "importance": 0.16,
      "contribution": 1.150,
      "effect": "INCREASES_RISK",
      "odds_ratio": 3.16
    }
  ],
  "model_version": "2.0.0-rc1",
  "model_accuracy": 0.862,
  "model_roc_auc": 0.914,
  "disclaimer": "MANAS is a computational research platform. Not for clinical diagnosis."
}
```

### `POST /api/predictions/stage`
Estimates ordinal cognitive stage probabilities across CDR tiers and expected continuous MMSE scores.

**Request Body:**
```json
{
  "age": 76.0,
  "sex": "M",
  "mmse": 25.0,
  "nwbv": 0.718,
  "etiv": 1490.0,
  "apoe4_carrier": true,
  "composite_pathology_z": 1.2
}
```

**Response `200 OK`:**
```json
{
  "inference_id": "MANAS-STAGE-2026-F98D2E14",
  "primary_stage": "CDR_0_5_VERY_MILD_MCI",
  "primary_stage_label": "Very Mild Impairment / MCI (CDR 0.5)",
  "stage_probabilities": [
    { "stage": "CDR_0_NORMAL", "stage_name": "Normal Cognition (CDR 0)", "probability": 0.1215, "clinical_description": "No significant cognitive loss." },
    { "stage": "CDR_0_5_VERY_MILD_MCI", "stage_name": "Very Mild Impairment / MCI (CDR 0.5)", "probability": 0.5842, "clinical_description": "Subtle memory lapses; independent daily living." },
    { "stage": "CDR_1_MILD_DEMENTIA", "stage_name": "Mild Dementia (CDR 1)", "probability": 0.2411, "clinical_description": "Noticeable memory loss, impaired judgment." },
    { "stage": "CDR_2_PLUS_MODERATE_SEVERE", "stage_name": "Moderate/Severe Dementia (CDR 2+)", "probability": 0.0532, "clinical_description": "Severe memory impairment." }
  ],
  "estimated_mmse": 24.3,
  "estimated_mmse_range": [21.8, 26.8],
  "braak_anatomical_correlation": "Braak Stage III to IV (Limbic / Entorhinal cortex & Hippocampus)",
  "progression_velocity": "MODERATE",
  "recommended_monitoring_interval": "6-month neurocognitive assessment"
}
```

### `POST /api/predictions/longitudinal`
Analyzes multiple sequential observation visits to compute annualized brain atrophy rates and cognitive decline slopes.

**Request Body:**
```json
{
  "subject_id": "OAS2_0031",
  "visits": [
    { "visit_id": 1, "time_days": 0, "age": 78.0, "mmse": 28.0, "cdr": 0.0, "nwbv": 0.748, "etiv": 1475.0 },
    { "visit_id": 2, "time_days": 706, "age": 79.9, "mmse": 26.0, "cdr": 0.5, "nwbv": 0.729, "etiv": 1480.0 },
    { "visit_id": 3, "time_days": 1461, "age": 82.0, "mmse": 22.0, "cdr": 1.0, "nwbv": 0.704, "etiv": 1485.0 }
  ]
}
```

**Response `200 OK`:**
```json
{
  "subject_id": "OAS2_0031",
  "visits_count": 3,
  "total_followup_years": 4.0,
  "annualized_brain_atrophy_pct": 1.47,
  "annualized_mmse_change": -1.50,
  "trajectory_type": "RAPID_COGNITIVE_DECLINE",
  "trajectory_description": "Accelerated brain atrophy and rapid cognitive decline (>1.2% brain volume loss/year).",
  "conversion_risk_5year": 0.771,
  "fitted_trajectory": [
    { "year": 0.0, "predicted_nwbv": 0.748, "predicted_mmse": 28.0, "ci_lower": 26.8, "ci_upper": 29.2 },
    { "year": 1.0, "predicted_nwbv": 0.737, "predicted_mmse": 26.5, "ci_lower": 24.8, "ci_upper": 28.2 },
    { "year": 5.0, "predicted_nwbv": 0.693, "predicted_mmse": 20.5, "ci_lower": 17.6, "ci_upper": 23.4 }
  ],
  "clinical_interpretation": "Subject exhibits steep loss of cerebral volume and cognitive scores, indicative of active neurodegenerative progression."
}
```

### `POST /api/predictions/report`
Synthesizes a structured, downloadable research report combining clinical profile, risk probabilities, SHAP weights, and longitudinal trajectories in Markdown format.

---

## 6. Literature & Evidence Registry

### `GET /api/literature/`
Lists peer-reviewed papers indexed in the MANAS registry.

### `GET /api/literature/evidence`
Retrieves structured claims linking specific brain regions, diseases, and empirical verification statuses.

---

## 7. Data Ingestion & Quality Control

### `POST /api/ingestion/allen-aging`
Triggers Allen Institute post-mortem histopathology and donor data ingestion.

### `POST /api/ingestion/allen-atlas`
Triggers Allen Human Brain Atlas regional hierarchy ingestion.

### `GET /api/ingestion/status/{run_id}`
Returns status (`RUNNING`, `COMPLETED`, `FAILED`), records processed, rejected counts, and QC warnings.

