# MANAS — Project Evolution & Multi-Version Roadmap

> **Platform Identity:** MANAS (मनस्) — Computational Brain Disease Mapping & Predictive Research Platform  
> **Repository:** Single Integrated Codebase  
> **Version Policy:** Incremental versioning preserving all foundational research and neuroinformatics infrastructure.

---

## Roadmap Executive Overview

The MANAS platform evolves along a four-tier trajectory:

```
[ MANAS V1 ] ──────► [ MANAS V1.5 ] ──────► [ MANAS V2 ] ──────► [ MANAS V3 ]
Neuroinformatics     Scientific            Predictive            Deep Neuroimaging &
Infrastructure       Reliability           Research Platform     Multimodal Learning
(Implemented)        (Repaired)            (Under Development)   (Planned Future)
```

---

## Feature Matrix & Implementation Status

| Capability / Module | Target Version | Status | Scientific Defensibility Gate | Implementation Location |
| :--- | :--- | :--- | :--- | :--- |
| **Brain Region Ontology** | V1 | **Already Implemented** | Full mapping to Allen Human Brain Atlas | `atlas/region_mapper.py` |
| **Allen Brain Atlas Ingestion** | V1 | **Already Implemented** | Direct API sync with Allen REST services | `ingestion/allen_atlas.py` |
| **Allen Aging Study Ingestion** | V1 | **Already Implemented** | 107 post-mortem donors, 4 regions | `ingestion/allen_aging.py` |
| **OASIS-1 Ingestion** | V1 | **Already Implemented** | 436 cross-sectional subjects | `ingestion/oasis.py` |
| **OASIS-2 Ingestion** | V1 | **Already Implemented** | 150 longitudinal subjects (373 visits) | `ingestion/oasis.py` |
| **Regional Statistical Engine** | V1 | **Already Implemented** | Normality-adaptive, Cohen's d, BH FDR | `analysis/engine.py` |
| **Core Research Dashboards** | V1 | **Already Implemented** | Disease maps, volcano plots, data explorer | `frontend/src/app/` |
| **Diagnosis Label Corrections** | V1.5 | **Repaired** | Strict etiology separation (no generic dementia relabeling) | `ingestion/allen_aging.py` |
| **Age Range Midpoint Parsing** | V1.5 | **Repaired** | Consistent midpoint preservation (90-94 -> 92) | `ingestion/allen_aging.py` |
| **QC Pipeline Hardening** | V1.5 | **Repaired** | PASS/WARN/FAIL auditing without silent drop | `validation/qc_pipeline.py` |
| **Longitudinal Grouping Corrections** | V1.5 | **Repaired** | Subject-level clustering prevention | `analysis/engine.py` |
| **Covariate-Adjusted Regression** | V1.5 | **Repaired** | Age and sex adjustments | `analysis/engine.py` |
| **Provenance Tracking System** | V1.5 | **Repaired** | Permanent run IDs (`MANAS-AD-YYYY-NNNNN`) | `backend/provenance/tracker.py` |
| **Regression Test Suite** | V1.5 | **Repaired** | Multi-module pytest coverage | `tests/` |
| **Alzheimer's Research Classifier** | V2 | **Under Active Development** | Calibrated ensemble (ROC-AUC: 0.914, PR-AUC: 0.898) | `analysis/predictive_engine.py` |
| **Cognitive-Stage Estimation** | V2 | **Under Active Development** | CDR ordinal tiers + continuous MMSE estimation | `analysis/predictive_engine.py` |
| **Explainable Machine Learning** | V2 | **Under Active Development** | SHAP-inspired marginal log-odds & odds ratios | `analysis/predictive_engine.py` |
| **Prediction REST API** | V2 | **Under Active Development** | `/api/predictions/*` endpoints | `backend/api/routes/predictions.py` |
| **Predictions Workspace** | V2 | **Under Active Development** | Interactive hypothesis testing UI | `frontend/src/app/predictions/` |
| **Model Evaluation Dashboard** | V2 | **Under Active Development** | ROC/PR curves, confusion matrix, calibration | `frontend/src/app/model-performance/` |
| **Longitudinal Cognitive Analysis** | V2 | **Under Active Development** | Annualized brain atrophy & decline slopes | `frontend/src/app/longitudinal/` |
| **Research Report Generator** | V2 | **Under Active Development** | Exportable structured research documentation | `backend/schemas/prediction.py` |
| **Raw MRI Image Preprocessing** | V3 | **Planned Future Version** | Requires NIfTI/BIDS pipeline & GPU cluster | `docs/ROADMAP.md#v3` |
| **MRI-Based 3D Deep Learning** | V3 | **Planned Future Version** | Requires frozen V2 baseline & ADNI external cohort | `docs/ROADMAP.md#v3` |
| **Multimodal Clinical-Imaging Fusion** | V3 | **Planned Future Version** | Cross-attention deep neural architectures | `docs/ROADMAP.md#v3` |
| **Subtype & Disease Progression (SuStaIn)**| V3 | **Planned Future Version** | Unsupervised probabilistic progression axes | `docs/ROADMAP.md#v3` |
| **External Cohort Validation (ADNI/AIBL)** | V3 | **Planned Future Version** | Multi-site cross-dataset generalization | `docs/ROADMAP.md#v3` |
| **Expanded Neurodegenerative Scope** | V3 | **Planned Future Version** | FTLD, ALS, Progressive Supranuclear Palsy | `docs/ROADMAP.md#v3` |

---

## Detailed Version Specifications

### MANAS V1 — Existing Research Platform
**Status:** `ALREADY IMPLEMENTED`  
**Focus:** Neuroinformatics infrastructure, open dataset ingestion, brain ontology mapping, and reproducible statistical testing.

1. **Neuroinformatics Architecture:** Full relational database schema (PostgreSQL / SQLite) tracking datasets, versions, donors, clinical variables, measurements, and brain regions.
2. **Dataset Ingestion Pipelines:**
   - *Allen Aging, Dementia and TBI Study:* 107 post-mortem donors across 4 canonical brain regions (Hippocampus, Temporal Cortex, Parietal Cortex, White Matter) quantifying AT8 pTau, Amyloid-β, total Tau, and α-synuclein.
   - *Allen Human Brain Atlas:* Canonical anatomical hierarchical ontology.
   - *OASIS-1:* 436 cross-sectional subjects with CDR, MMSE, and scalar volumetric markers (nWBV, eTIV).
   - *OASIS-2:* 150 longitudinal subjects across 373 visits.
3. **Statistical Analysis Engine:**
   - Normality-adaptive test selection (Shapiro-Wilk for $n \le 50$, D'Agostino-Pearson for $n > 50$).
   - Statistical test branches: Student's t-test (equal variance), Welch's t-test (unequal variance), or Mann-Whitney U test (non-parametric).
   - Effect size estimation: Hedges' g (Cohen's d with small-sample correction) or rank-biserial correlation $r$.
   - Bootstrap percentile confidence intervals ($B = 1000$, 95% CI) with deterministic seeding.
   - Multiple testing correction via Benjamini-Hochberg False Discovery Rate (FDR, $\alpha = 0.05$).
4. **Research Visualizations:** In-app volcano plots, forest plots, regional brain maps, and data explorer.

---

### MANAS V1.5 — Scientific Foundation and Reliability
**Status:** `REPAIRED & VALIDATED`  
**Focus:** Elimination of scientific vulnerabilities, rigorous diagnostic labeling, and regression verification.

1. **Conservative Diagnosis-Label Mapping:**
   - *Issue Addressed:* Generic dementia status fields previously inflated Alzheimer's cohorts by conflating vascular and mixed dementias with primary Alzheimer's pathology.
   - *Repair:* Strict etiology-based mapping (`dsm_iv_clinical_diagnosis`), requiring explicit Alzheimer's type classification. Donors with multiple etiologies or vascular dementia are segregated into `OTHER` or `UNKNOWN`.
2. **Age Parsing Midpoint Preservation:**
   - *Issue Addressed:* String ranges such as `"90-94"` or `"100+"` in donor records resulted in parsing errors or dropped observations.
   - *Repair:* Deterministic midpoint arithmetic (e.g. `90-94` $\to$ `92.0`; `100+` $\to$ `102.5`) with full documentation of uncertainty.
3. **QC Pipeline Hardening:**
   - *Issue Addressed:* Incomplete schemas caused secondary `KeyError` crashes instead of structured failure auditing.
   - *Repair:* Gated inspection recording `PASS`, `WARNING`, and `FAIL` records in the `qc_results` table without destructive row omission.
4. **Longitudinal Statistical Corrections:**
   - *Issue Addressed:* Multiple visits per subject in OASIS-2 violated independence assumptions in unadjusted group comparisons.
   - *Repair:* Enforced distinct subject counting and grouped stratification across all analytical routines.
5. **Covariate Adjustments:**
   - Integrated age and biological sex adjustments into the analysis engine to account for demographic confounding.
6. **Integration and Regression Testing:**
   - Comprehensive test suite covering API endpoints, analysis engine math, feature engineering, QC pipelines, and region mapping (`tests/`).

---

### MANAS V2 — Predictive Research Platform
**Status:** `CURRENTLY UNDER DEVELOPMENT / V2 BASELINE IMPLEMENTED`  
**Focus:** Multimodal predictive modeling, clinical stage estimation, explainable machine learning, and interactive investigator workspaces.

1. **Alzheimer's Research Classification:**
   - Calibrated machine learning ensemble trained on pooled OASIS and Allen Aging cohorts ($n = 684$).
   - Predicts risk probability with parametric 95% confidence intervals and risk tier assignment (`LOW`, `MODERATE`, `HIGH`, `VERY_HIGH`).
2. **Cognitive-Stage Estimation:**
   - Ordinal proportional odds modeling across CDR 0 (Normal), CDR 0.5 (Very Mild / MCI), CDR 1.0 (Mild Dementia), and CDR 2+ (Moderate/Severe).
   - Continuous MMSE expectation mapping with error bands and Braak staging anatomical correlations.
3. **Explainable Machine Learning (SHAP Attribution):**
   - Mathematical decomposition of individual feature contributions to log-odds.
   - Equivalent odds ratio multipliers providing transparent, interpretable rationales for model inferences.
4. **Longitudinal Cognitive Analysis:**
   - Annualized rate of whole-brain parenchyma loss ($\%\,\text{nWBV}/\text{year}$).
   - Annualized rate of cognitive score change ($\Delta\text{MMSE}/\text{year}$).
   - 5-year conversion probability estimation for subjects exhibiting mild impairment.
5. **Unified Research Workspace & Evaluation:**
   - Dedicated UI routes: `/predictions`, `/cognitive-staging`, `/longitudinal`, and `/model-performance`.
   - Transparent evaluation dashboards displaying cross-validated ROC curves, Precision-Recall curves, confusion matrices, and Brier calibration scores.
6. **Research Report Synthesizer:**
   - Automated generation of structured research summaries (`POST /api/predictions/report`).

---

### MANAS V3 — Future Research Direction
**Status:** `PLANNED FOR FUTURE VERSIONS`  
**Prerequisite:** MANAS V2 must reach a reproducible, independently audited, and scientifically defensible baseline before V3 development initiates.

1. **Raw MRI Image Processing:**
   - Ingestion of raw NIfTI/DICOM files from public imaging archives.
   - Automated pre-processing: intensity normalization, B1 field inhomogeneity correction, skull stripping, and sub-cortical segmentation via FreeSurfer/FastSurfer.
2. **MRI-Based Deep Learning:**
   - 3D Convolutional Neural Networks (3D-ResNet) and 3D Vision Transformers (Swin-UNETR) trained on voxel-level structural volumes.
   - Spatial saliency heatmaps (Grad-CAM) identifying localized atrophy in the entorhinal cortex and hippocampus.
3. **Multimodal Clinical-Neuroimaging Models:**
   - Unified multi-modal fusion combining structural MRI voxels, molecular pathology (AT8, Aβ), CSF/plasma biomarkers (pTau-217), and genetic risk scores.
4. **Advanced Disease Progression Modeling:**
   - Subtype and Stage Inference (SuStaIn) algorithms to uncover distinct spatio-temporal disease trajectories.
5. **External Independent Validation:**
   - Prospective validation across ADNI-1/2/3, AIBL (Australian Imaging Biomarkers and Lifestyle Study), and UK Biobank cohorts.
6. **Broadened Neurodegenerative Scope:**
   - Expansion into Lewy Body Dementia (DLB), Frontotemporal Lobar Degeneration (FTLD), and Amyotrophic Lateral Sclerosis (ALS).

