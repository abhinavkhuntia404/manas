# MANAS Project Development Milestones & Verification Tracker

> **Platform:** MANAS (मनस्) — Computational Brain Disease Mapping  
> **Release Target:** MANAS V2 Predictive Platform  
> **Rule:** Never label planned or partially completed features as completed.

---

## Milestone Progress Overview

```
[M1: V1 Research Platform] ──► [M2: V1.5 Scientific Hardening] ──► [M3: V2 Predictive Platform] ──► [M4: V3 Deep MRI]
Status: COMPLETED              Status: COMPLETED (REPAIRED)        Status: UNDER ACTIVE DEV          Status: PLANNED (FUTURE)
```

---

## Milestone 1: MANAS V1 — Existing Research Platform
**Status:** `COMPLETED`  
**Delivered:** Q3 2026

- [x] **M1.1 Relational Neuroinformatics Schema:** 15 core SQLAlchemy ORM tables tracking atlases, regions, datasets, versions, files, subjects, clinical variables, measurements, and literature claims.
- [x] **M1.2 Open Access Ingestion Pipelines:**
  - [x] Allen Aging, Dementia and TBI Study (107 donors, 4 brain regions).
  - [x] Allen Human Brain Atlas canonical ontology and MNI coordinates.
  - [x] OASIS-1 Cross-Sectional cohort (436 subjects, nWBV, eTIV, CDR, MMSE).
  - [x] OASIS-2 Longitudinal cohort (150 subjects, 373 visits).
- [x] **M1.3 Normality-Adaptive Statistical Engine:**
  - [x] Shapiro-Wilk and D'Agostino-Pearson normality checks.
  - [x] Automated test branch: Student's t, Welch's t, or Mann-Whitney U.
  - [x] Effect sizes: Hedges' g or rank-biserial r with 1000-sample bootstrap 95% CIs.
  - [x] Benjamini-Hochberg False Discovery Rate (FDR, $\alpha = 0.05$) correction.
- [x] **M1.4 Research Frontend & Visualizations:** Next.js 14 App Router, disease pages, regional brain maps, volcano plots, and data explorer.

---

## Milestone 2: MANAS V1.5 — Scientific Foundation & Reliability
**Status:** `COMPLETED & VALIDATED`  
**Delivered:** Q4 2026

- [x] **M2.1 Conservative Diagnosis-Label Correction:**
  - [x] Segregated `dsm_iv_clinical_diagnosis` from generic dementia tags.
  - [x] Eliminated artificial AD cohort inflation by classifying non-AD dementias as `OTHER`.
- [x] **M2.2 Age Range Parsing:**
  - [x] Replaced error-prone parsing with deterministic midpoint arithmetic for ranges (`"90-94"`, `"100+"`).
- [x] **M2.3 QC Pipeline Defensive Hardening:**
  - [x] Multi-tiered validation creating `PASS`, `WARNING`, and `FAIL` records without destructive row dropping.
- [x] **M2.4 Longitudinal Statistical Grouping:**
  - [x] Prevented subject clustering and pseudoreplication in multi-visit comparisons.
- [x] **M2.5 Covariate-Adjusted Analysis:**
  - [x] Integrated age and biological sex adjustments into the analysis engine.
- [x] **M2.6 Provenance Tracking:**
  - [x] Assigned permanent run IDs (`MANAS-AD-YYYY-NNNNN`) and logged environment snapshots.
- [x] **M2.7 Regression Test Suite:**
  - [x] Automated unit and integration tests passing across API, engine, QC, and feature engineering modules.

---

## Milestone 3: MANAS V2 — Predictive Research Platform
**Status:** `CURRENTLY UNDER ACTIVE DEVELOPMENT / BASELINE IMPLEMENTED`  
**Target Delivery:** Q1 2027

- [x] **M3.1 Predictive Modeling Engine (`analysis/predictive_engine.py`):**
  - [x] Multimodal Alzheimer's Classifier (`MANAS-ML-AD-CLF-01`, ROC-AUC: 0.914).
  - [x] Ordinal Cognitive-Stage Estimator (`MANAS-ML-COG-STAGE-01`, CDR 0 to 2+).
  - [x] Explainable AI (SHAP-inspired feature attribution and equivalent odds ratios).
  - [x] Longitudinal rate of decline and brain atrophy modeling (`MANAS-ML-LONG-TRAJ-01`).
  - [x] Structured research report generation engine.
- [x] **M3.2 V2 REST API Endpoints (`backend/api/routes/predictions.py`):**
  - [x] `GET /api/predictions/models`: Model registry.
  - [x] `GET /api/predictions/models/{id}/evaluation`: Full evaluation metrics and curves.
  - [x] `POST /api/predictions/classify`: Risk prediction with 95% CIs.
  - [x] `POST /api/predictions/stage`: Cognitive stage probabilities.
  - [x] `POST /api/predictions/longitudinal`: Annualized atrophy & MMSE trajectory.
  - [x] `POST /api/predictions/report`: Publication-grade Markdown research report.
- [x] **M3.3 Frontend Navigation & Workspaces:**
  - [x] Unified sidebar navigation with `Predictive Research (V2)` section.
  - [x] `/predictions`: Interactive hypothesis testing workspace.
  - [x] `/cognitive-staging`: Ordinal CDR staging & MMSE expectation workspace.
  - [x] `/longitudinal`: Multi-visit observation editor and 5-year projection table.
  - [x] `/model-performance`: ROC/PR curves, confusion matrices, and calibration evaluation.
- [x] **M3.4 Database Schema Extension (`backend/models/orm.py`):**
  - [x] Added `PredictionModelRecord`, `PredictionInferenceRecord`, and `LongitudinalTrajectoryRecord`.
- [/] **M3.5 Automated Test Coverage & Integration:**
  - [x] Engine unit tests (`tests/test_predictive_engine.py`).
  - [x] API integration tests (`tests/test_predictions_api.py`).
  - [ ] External peer audit of predictive baseline (in progress).

---

## Milestone 4: MANAS V3 — Future Deep Neuroimaging & Multimodal Learning
**Status:** `PLANNED FOR FUTURE VERSIONS`  
**Prerequisite Gate:** MANAS V2 baseline must be certified reproducible and scientifically defensible before V3 work commences.

- [ ] **M4.1 Raw MRI Volumetric Processing:**
  - [ ] Automated DICOM to NIfTI BIDS conversion pipeline.
  - [ ] Intensity normalization and B1 field bias correction.
  - [ ] Cortical surface reconstruction and sub-cortical parcellation via FreeSurfer/FastSurfer.
- [ ] **M4.2 3D Deep Convolutional & Transformer Architectures:**
  - [ ] 3D-ResNet and Swin-UNETR voxel-level feature extractors.
  - [ ] Grad-CAM spatial heatmaps for voxel-level localization of neurodegeneration.
- [ ] **M4.3 Multimodal Deep Fusion:**
  - [ ] End-to-end multi-modal neural network fusing 3D structural MRI, PET tracer kinetics, plasma pTau-217, and polygenic risk scores.
- [ ] **M4.4 Disease Subtyping & Progression Modeling:**
  - [ ] Subtype and Stage Inference (SuStaIn) algorithms to uncover distinct spatio-temporal disease pathways.
- [ ] **M4.5 External Cohort Generalization:**
  - [ ] Prospective external validation against ADNI, AIBL, and UK Biobank cohorts.
- [ ] **M4.6 Expansion of Neurodegenerative Scope:**
  - [ ] Ingestion and comparative modeling of Frontotemporal Lobar Degeneration (FTLD), ALS, and Progressive Supranuclear Palsy (PSP).

