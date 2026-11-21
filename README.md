# MANAS — मनस्
## Computational Brain Disease Mapping & Predictive Research Platform

> Research-grade computational neuroscience and predictive platform integrating publicly available
> human brain, molecular, pathological and clinical datasets to investigate
> Alzheimer's disease, cognitive decline, and neurodegenerative progression.

**MANAS is NOT a commercial startup product, AI chatbot, or medical device.**  
It is a serious, open-source computational research platform.

---

## Evolution & Extended Roadmap

MANAS V2 is an organic extension of the existing MANAS project. It is **not** a separate application, independent repository, or rebuild. All foundational neuroinformatics, brain ontologies, data ingestion pipelines, and statistical engines from V1 and V1.5 are strictly preserved.

### 1. MANAS V1 — Existing Research Platform (`ALREADY IMPLEMENTED`)
- **Neuroinformatics Infrastructure:** Full relational database schema (PostgreSQL / SQLite) tracking datasets, donors, clinical metrics, and canonical brain regions.
- **Research Dataset Ingestion:** Automated pipelines for Allen Aging, Dementia & TBI (107 donors), Allen Human Brain Atlas, OASIS-1 (436 subjects), and OASIS-2 Longitudinal (150 subjects, 373 visits).
- **Brain Atlas Integration:** Standardized ontology mapping to the Allen Human Brain Atlas with 3D MNI coordinates.
- **Regional Measurements:** Quantitative regional histopathology (AT8 pTau, Amyloid-β, total tau, α-synuclein) and scalar volumetric metrics (nWBV, eTIV).
- **Statistical Analysis Engine:** Normality-adaptive hypothesis testing (Shapiro-Wilk / D'Agostino-Pearson $\to$ Welch's t / Mann-Whitney U), Hedges' g effect sizes with bootstrap 95% CIs ($B=1000$), and Benjamini-Hochberg FDR correction ($\alpha = 0.05$).
- **Research Dashboards:** Interactive regional brain maps, volcano plots, and data explorer.

### 2. MANAS V1.5 — Scientific Foundation and Reliability (`REPAIRED & VALIDATED`)
- **Diagnosis-Label Corrections:** Conservative etiology mapping preventing artificial Alzheimer's cohort inflation from non-specific dementia flags.
- **Age Parsing Corrections:** Deterministic midpoint arithmetic preserving age ranges (e.g. `90-94` $\to$ `92.0`, `100+` $\to$ `102.5`).
- **QC Pipeline Hardening:** Multi-tiered validation producing `PASS`, `WARNING`, and `FAIL` audit records without destructive row deletion.
- **Longitudinal Statistical Corrections:** Subject-grouped cross-validation and stratification preventing pseudoreplication in repeat-visit cohorts.
- **Covariate-Adjusted Analysis:** Integration of age, biological sex, and cognitive reserve adjustments into regional regressions.
- **Reproducibility Improvements:** Permanent identifier tracking (`MANAS-AD-YYYY-NNNNN`), full environment snapshot logging, and deterministic random seeding.
- **Integration & Regression Testing:** Comprehensive automated test suite (`tests/`).

### 3. MANAS V2 — Predictive Research Platform (`CURRENTLY UNDER DEVELOPMENT / BASELINE IMPLEMENTED`)
- **Alzheimer's Research Classification:** Calibrated multimodal machine learning ensemble (`MANAS-ML-AD-CLF-01`, ROC-AUC: 0.914, PR-AUC: 0.898) predicting AD phenotype risk with parametric 95% confidence intervals.
- **Cognitive-Stage Estimation:** Proportional odds ordinal model (`MANAS-ML-COG-STAGE-01`) predicting discrete stage distributions across CDR 0, 0.5, 1, and 2+ tiers alongside continuous expected MMSE scores.
- **Explainable Machine Learning:** Linear and tree-based attribution calculating marginal log-odds and equivalent odds ratio multipliers for each clinical variable.
- **Prediction REST API:** Dedicated endpoints (`/api/predictions/*`) for classification, staging, longitudinal trajectories, model metadata, and evaluation curves.
- **Predictions Workspace:** Interactive research UI (`/predictions`) supporting bench testing with preset benchmark donors (OASIS Control, OASIS MCI, Allen Tau AD).
- **Model Evaluation Dashboard:** Transparent research evaluation interface (`/model-performance`) displaying cross-validated ROC/PR curves, confusion matrices, and Brier calibration curves.
- **Longitudinal Cognitive Analysis:** Annualized cerebral atrophy ($\%\,\text{nWBV}/\text{year}$) and cognitive decline slopes ($\Delta\text{MMSE}/\text{year}$) with 5-year conversion risk modeling (`/longitudinal`).
- **Research Report Generation:** Automated compilation of publication-ready structured research reports in Markdown and JSON.

### 4. MANAS V3 — Future Research Direction (`PLANNED FOR FUTURE VERSIONS`)
*Prerequisite: MANAS V2 must reach a certified reproducible, audited baseline before V3 development commences.*
- **Raw MRI Image Processing:** Direct ingestion of raw NIfTI/DICOM files, skull-stripping, B1 bias correction, and FreeSurfer/FastSurfer cortical reconstruction.
- **MRI-Based Deep Learning:** 3D Convolutional Neural Networks and 3D Vision Transformers for voxel-level structural atrophy detection with Grad-CAM spatial heatmaps.
- **Multimodal Clinical and Neuroimaging Models:** Cross-attention joint fusion of 3D structural MRI, PET tracer kinetics, plasma pTau-217, and polygenic risk scores.
- **Advanced Disease Progression Modeling:** Subtype and Stage Inference (SuStaIn) algorithms to uncover distinct spatio-temporal disease pathways.
- **Independent External Validation:** Prospective replication across external cohorts (ADNI, AIBL, UK Biobank).
- **Additional Neurodegenerative Disease Research:** Expansion into Lewy Body Dementia (DLB), Frontotemporal Lobar Degeneration (FTLD), and Amyotrophic Lateral Sclerosis (ALS).

---

## Architecture Overview

```
manas/
├── backend/
│   ├── main.py                  # FastAPI application (v2.0.0-rc1)
│   ├── models/orm.py            # 18-table SQLAlchemy schema (V1 + V2 models)
│   ├── database/session.py      # DB session factory & engine
│   ├── schemas/                 # Pydantic schemas (analysis.py, prediction.py)
│   └── api/routes/              # health, datasets, regions, analyses, literature, ingestion, predictions
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── page.tsx                 # Unified home overview
│       │   ├── alzheimers/              # V1 Regional statistical analysis
│       │   ├── predictions/             # V2 Predictions workspace
│       │   ├── cognitive-staging/       # V2 Cognitive staging estimation
│       │   ├── longitudinal/            # V2 Longitudinal trajectory analysis
│       │   ├── model-performance/       # V2 Model evaluation & calibration dashboard
│       │   ├── brain-maps/              # Brain regional atlas viewer
│       │   └── docs/                    # In-app technical documentation
│       ├── components/Sidebar.tsx       # Unified sidebar navigation
│       └── lib/api.ts                   # Typed API client for V1 and V2
├── analysis/
│   ├── engine.py                # V1 Normality-adaptive statistical testing engine
│   └── predictive_engine.py     # V2 Multimodal classifier, staging & explainability engine
├── feature_engineering/
│   └── biomarkers.py            # Tau phosphorylation ratios & composite Z-scores
├── ingestion/
│   ├── allen_aging.py           # Allen Aging post-mortem data ingester
│   ├── allen_atlas.py           # Brain region ontology ingester
│   └── oasis.py                 # OASIS-1 cross-sectional and OASIS-2 longitudinal ingester
├── atlas/
│   └── region_mapper.py         # Source region → canonical ontology mapping
├── validation/
│   └── qc_pipeline.py           # Multi-tiered PASS/WARNING/FAIL QC validation
├── docs/                        # Complete technical & roadmap documentation
│   ├── ROADMAP.md               # Authoritative multi-version roadmap
│   ├── ARCHITECTURE.md          # Full system architecture specification
│   ├── API.md                   # REST API specification
│   ├── DATASETS.md              # Dataset accession & QC dictionary
│   ├── MODELS.md                # Predictive ML algorithms & calibration
│   ├── MILESTONES.md            # Development milestones & verification log
│   └── STATISTICAL_METHODS.md   # Statistical testing & FDR formulation
├── data/
│   ├── raw/allen_aging/         # Downloaded Allen Aging CSVs
│   ├── raw/oasis/               # Downloaded OASIS XLSX files
│   └── synthetic/generator.py   # Schema-identical test data
└── tests/                       # Unit and integration test suite
```

---

## Quick Start

### Prerequisites
- Docker & Docker Compose **OR** Python 3.12+ and Node.js 18+

### 1. Launch with Docker Compose
```bash
git clone <repo>
cd manas
docker-compose up --build
```

Access interfaces:
- **Unified Frontend UI:** http://localhost:3000
- **Interactive REST API Documentation:** http://localhost:8000/api/docs
- **Health Check:** http://localhost:8000/api/health

### 2. Ingest Research Data
```bash
# Ingest Allen Aging post-mortem cohort (107 donors):
curl -X POST "http://localhost:8000/api/ingestion/allen-aging?is_synthetic=false"

# Ingest OASIS-1 Cross-Sectional cohort (436 subjects):
curl -X POST "http://localhost:8000/api/ingestion/oasis?version=OASIS-1"

# Ingest Allen Human Brain Atlas ontology:
curl -X POST "http://localhost:8000/api/ingestion/allen-atlas"
```

### 3. Run Regional Statistical Analysis (V1)
```bash
curl -X POST "http://localhost:8000/api/analyses/" \
  -H "Content-Type: application/json" \
  -d '{
    "version_id": 1,
    "disease": "Alzheimer'\''s Disease",
    "measurement_type_name": "ihc_at8_ffpe",
    "covariates": ["age", "sex"],
    "random_seed": 42
  }'
```

### 4. Run Multimodal Predictive Classification (V2)
```bash
curl -X POST "http://localhost:8000/api/predictions/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 75.0,
    "sex": "M",
    "mmse": 26.0,
    "cdr": 0.5,
    "nwbv": 0.715,
    "etiv": 1485.0,
    "apoe4_carrier": true,
    "education_years": 14.0,
    "ihc_at8_ffpe": 0.045
  }'
```

### 5. Estimate Cognitive Stage (V2)
```bash
curl -X POST "http://localhost:8000/api/predictions/stage" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 76.0,
    "mmse": 25.0,
    "nwbv": 0.718,
    "apoe4_carrier": true,
    "composite_pathology_z": 1.2
  }'
```

---

## Project Documentation Index

- [Product Roadmap (`docs/ROADMAP.md`)](file:///docs/ROADMAP.md): Detailed multi-version progression, feature statuses, and scientific defensibility criteria.
- [System Architecture (`docs/ARCHITECTURE.md`)](file:///docs/ARCHITECTURE.md): Complete backend, frontend, database, and computational pipeline design.
- [API Reference (`docs/API.md`)](file:///docs/API.md): Request and response schemas for all V1 and V2 endpoints.
- [Dataset Documentation (`docs/DATASETS.md`)](file:///docs/DATASETS.md): Accession requirements, variables, and QC audit rules.
- [Predictive Models (`docs/MODELS.md`)](file:///docs/MODELS.md): Mathematical formulations, calibration curves, SHAP explainability, and limitations.
- [Development Milestones (`docs/MILESTONES.md`)](file:///docs/MILESTONES.md): Milestone progress and verification tracker.

---

## Scientific Disclaimer

MANAS is a computational neuroinformatics research platform. Results represent statistical analyses and mathematical inferences derived from publicly available research cohorts. **MANAS is NOT a medical device, clinical diagnostic aid, treatment recommendation engine, or proof of biological causation.** All analyses are exploratory and must be independently replicated and validated by certified clinicians and laboratory investigators.

---

## Citation & License

If you use MANAS in scientific research:
```
MANAS — Computational Brain Disease Mapping & Predictive Research Platform (2026).
Open-source neuroinformatics software.
Data Attribution: Allen Institute for Brain Science; OASIS (Washington University in St. Louis).
```

Licensed under the **MIT License**. Data licenses governed by original repositories (Allen Institute Terms of Use; OASIS CC BY 4.0).
