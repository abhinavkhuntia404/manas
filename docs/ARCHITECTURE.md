# MANAS System Architecture & Technical Specification

> **Platform:** MANAS (मनस्) — Computational Brain Disease Mapping & Predictive Research Platform  
> **Version:** 2.0.0-rc1 (Integrated Research & Predictive Platform)  
> **Core Tenet:** A unified, single-application architecture where predictive machine learning (V2) extends the neuroinformatics and statistical foundation (V1).

---

## 1. Architectural Overview

MANAS is structured into six modular, vertically integrated layers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        NEXT.JS 14 FRONTEND                             │
│  Research Dashboards │ Predictive Workspace │ Staging │ Evaluation UI  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / JSON REST API
┌───────────────────────────────────▼────────────────────────────────────┐
│                         FASTAPI BACKEND                                │
│  Rate Limiting │ CORS │ Pydantic Validation │ Dependency Injection     │
├───────────────────────────────────┬────────────────────────────────────┤
│   STATISTICAL ENGINE (V1/V1.5)    │    PREDICTIVE ENGINE (V2)          │
│   - Normality Tests               │    - Multimodal AD Classifier      │
│   - Welch / Mann-Whitney          │    - Ordinal Cognitive Staging     │
│   - Effect Size & Bootstrap CI    │    - SHAP Feature Attribution      │
│   - Benjamini-Hochberg FDR        │    - Longitudinal Trajectories     │
│   - Covariate Adjustments         │    - Report Generation             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ SQLAlchemy 2.0 ORM
┌───────────────────────────────────▼────────────────────────────────────┐
│                    RELATIONAL DATABASE (POSTGRESQL / SQLITE)           │
│  Atlases │ Regions │ Datasets │ Subjects │ Measurements │ QC │ Inferences │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Ingestion & QC Pipelines
┌───────────────────────────────────▼────────────────────────────────────┐
│                       DATA INGESTION & HARMONIZATION                   │
│  Allen Aging Ingester │ Allen Atlas Ingester │ OASIS Ingester │ QC     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer-by-Layer Architectural Details

### 2.1. Presentation Layer (Frontend)
- **Framework:** Next.js 14 with React Server and Client Components (App Router).
- **Design System:** Scientific instrument aesthetic; neutral slate backgrounds (`#f8f9fb`), card-based surfaces (`#ffffff`), border hierarchy (`#dde1e9`), research blue primary accent (`#1a56db`), and JetBrains Mono for all numeric and statistical metrics.
- **Navigation Structure:** Managed in `frontend/src/components/Sidebar.tsx`:
  - **Diseases & Research:** Overview (`/`), Alzheimer's (`/alzheimers`), Vascular (`/vascular`), Lewy Body (`/lewy-body`), Brain Maps (`/brain-maps`), Brain Regions (`/brain-regions`).
  - **Data:** Datasets (`/datasets`), Data Explorer (`/data-explorer`).
  - **Analysis (V1):** Analysis Runs (`/analysis-runs`), Reproducibility (`/reproducibility`), Research Evidence (`/evidence`).
  - **Predictive Research (V2):** Predictions Workspace (`/predictions`), Cognitive Staging (`/cognitive-staging`), Longitudinal Research (`/longitudinal`), Model Performance (`/model-performance`).
  - **System:** Documentation (`/docs`).
- **Client Networking:** Typed fetch client (`frontend/src/lib/api.ts`) connecting to `API_BASE` (`NEXT_PUBLIC_API_URL`).

### 2.2. Application & API Layer (Backend)
- **Framework:** FastAPI with asynchronous ASGI execution and Lifespan event handlers.
- **Routing Structure:**
  - `health.py`: System health and relational database connectivity probe (`/api/health`).
  - `datasets.py`: Accession registry, download metadata, versions (`/api/datasets`).
  - `regions.py`: Brain ontology search, hierarchical depth, MNI coordinates (`/api/regions`).
  - `analyses.py`: Submission and results polling for statistical regional analyses (`/api/analyses`).
  - `literature.py`: Peer-reviewed evidence registry and DOI links (`/api/literature`).
  - `ingestion.py`: Triggering data ingest and monitoring background processing runs (`/api/ingestion`).
  - `predictions.py` (V2): Multi-modal classification, cognitive staging, longitudinal progression, model evaluation metrics, and research report synthesis (`/api/predictions`).
- **Security & Quality of Service:** SlowAPI rate limiting per IP address, strict CORS domain allowlisting, and global exception handlers with debug shielding.

### 2.3. Computational Engines

#### A. Statistical Analysis Engine (`analysis/engine.py`)
- Executes hypothesis testing comparing disease vs control cohorts per brain region.
- Steps:
  1. Filters measurements with `PASS` or `WARNING` quality flags.
  2. Evaluates distribution normality via Shapiro-Wilk ($n \le 50$) or D'Agostino-Pearson ($n > 50$).
  3. Dispatches Student's t, Welch's t, or Mann-Whitney U test based on variance equality (Levene test) and normality.
  4. Computes Hedges' g or rank-biserial correlation $r$ with 1000-iteration bootstrap percentile 95% confidence intervals.
  5. Enforces monotonic Benjamini-Hochberg False Discovery Rate (FDR, $\alpha = 0.05$) correction.
  6. Records complete software environment, Python library versions, random seed, and Git commit hash.

#### B. Predictive Modeling Engine (`analysis/predictive_engine.py`)
- Validated algorithms for V2 predictive neuroinformatics:
  1. **AD Classification:** Calibrated regularized logistic ensemble combining cognitive scores (MMSE), brain volumetrics (nWBV), demographic covariates (age, sex, education), genetics (APOE ε4), and quantitative histopathology (AT8 pTau).
  2. **Cognitive Staging:** Proportional odds ordinal model estimating probabilities for CDR 0, 0.5, 1, and 2+, with continuous expected MMSE scores and Braak staging anatomical correlates.
  3. **Explainable AI (SHAP Attribution):** Calculates directional marginal log-odds and equivalent odds ratios for each predictor variable.
  4. **Longitudinal Trajectory Modeling:** Computes annualized whole-brain atrophy rates ($\%\,\text{nWBV}/\text{year}$) and MMSE decline slopes from sequential visits, projecting 5-year trajectories with expanding confidence bands.
  5. **Report Synthesizer:** Compiles publication-ready scientific research reports in Markdown.

---

## 3. Unified Database Schema

The database schema spans 18 normalized tables:

```
[ brain_atlases ] ──< [ brain_regions ] ──< [ region_mappings ]
                             │
                             ├──< [ measurements ] >── [ measurement_types ]
                             │            │
[ datasets ] ──< [ dataset_versions ] ────┤
                        │                 │
                        ├──< [ subjects ] ┘
                        │        │
                        │        ├──< [ clinical_variables ]
                        │        └──< [ longitudinal_trajectories ] (V2)
                        │
                        ├──< [ processing_runs ] ──< [ qc_results ]
                        │
                        └──< [ analysis_runs ] ──< [ analysis_results ]

[ literature_papers ] ──< [ claim_papers ] >── [ evidence_claims ]

[ prediction_models ] (V2) ──< [ prediction_inferences ] (V2)
```

### Table Definitions:
1. `brain_atlases`: Reference brain coordinate ontologies.
2. `brain_regions`: Canonical anatomical structures (MNI coordinates, lobes, categories).
3. `region_mappings`: Source dataset nomenclature to canonical region mappings.
4. `datasets`: Open research accession registry (Allen, OASIS).
5. `dataset_versions`: Version tags, checksums, download dates, `is_synthetic` flags.
6. `dataset_files`: Raw downloaded archives and tabular files.
7. `processing_runs`: Ingestion, validation, and QC job tracking.
8. `subjects`: Donor demographic, genetic (APOE), and clinical etiology profiles.
9. `clinical_variables`: Longitudinal and cross-sectional clinical ratings (MMSE, CDR).
10. `measurement_types`: Quantitative assay registry (IHC, Luminex, MRI scalars).
11. `measurements`: Regional quantified values with quality flags (`PASS`, `WARNING`, `FAIL`).
12. `qc_results`: Detailed audit records of data validation checks.
13. `analysis_runs`: Statistical run provenance (`MANAS-AD-YYYY-NNNNN`), parameters, environment.
14. `analysis_results`: Regional effect sizes, p-values, adjusted p-values, test statistics.
15. `literature_papers`: Verified publication metadata and DOIs.
16. `evidence_claims`: Structured scientific hypotheses mapped to brain regions.
17. `claim_papers`: Evidence-to-literature relationship links.
18. `prediction_models` (V2): Registry of trained predictive algorithms, versions, and validation metrics.
19. `prediction_inferences` (V2): Permanent record of predictive queries, probabilities, and SHAP weights.
20. `longitudinal_trajectories` (V2): Multi-visit subject atrophy rates and decline slopes.

---

## 4. Scientific Provenance & Data Isolation

To prevent demo data from contaminating empirical research:
- Every table carrying subject or measurement data includes an `is_synthetic: Boolean` column.
- Records flagged with `is_synthetic = True` trigger an unambiguous warning banner in the user interface.
- Real scientific data ingestion requires executing official ingestion scripts against authentic files downloaded directly from the Allen Institute or OASIS repositories.
- Statistical analysis runs and predictive inferences generate permanent, deterministic IDs (e.g. `MANAS-AD-2026-00001`, `MANAS-PRED-2026-A1B2C3D4`) storing complete environment and parameter snapshots.

