# MANAS Dataset Registry & Data Ingestion Specification

> **Platform:** MANAS (मनस्) — Computational Brain Disease Mapping  
> **Policy:** All data utilized in MANAS originates from open, publicly accessible, ethics-approved human research repositories.

---

## 1. Summary of Registered Datasets

| Dataset | Organization | Access Type | Registration | Sample Size | Primary Modalities |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Allen Aging, Dementia and TBI** | Allen Institute for Brain Science | `OPEN_DIRECT` | None | 107 donors | Post-mortem IHC, Luminex pathology, RNA-seq |
| **Allen Human Brain Atlas** | Allen Institute for Brain Science | `OPEN_DIRECT` | None | 6 brains | Hierarchical anatomical brain ontology |
| **OASIS-1 Cross-Sectional** | Washington University in St. Louis | `OPEN_DIRECT` | None (CC BY 4.0) | 436 subjects | Structural MRI volumetrics (nWBV, eTIV), CDR, MMSE |
| **OASIS-2 Longitudinal** | Washington University in St. Louis | `OPEN_DIRECT` | None (CC BY 4.0) | 150 subjects (373 visits) | Multi-timepoint longitudinal MRI volumetrics, MMSE, CDR |

---

## 2. Dataset Detailed Profiles

### 2.1. Allen Aging, Dementia and TBI Study
- **Accession:** Open direct API access.
- **Source URL:** https://aging.brain-map.org/download/index
- **Files Utilized:**
  - `DonorInformation.csv` (107 rows, donor clinical and demographic profile)
  - `ProteinAndPathologyQuantifications.csv` (3,770 quantified tissue measurements)
- **Sample Characteristics:**
  - 107 post-mortem human donors from the Seattle Adult Changes in Thought (ACT) study.
  - Age range: 77 to 100+ years.
  - Brain Regions Sampled (4 canonical regions):
    - `HIP`: Hippocampus (limbic / allocortex)
    - `TCx`: Temporal Cortex (superior and middle temporal gyri)
    - `PCx`: Parietal Cortex (inferior parietal lobule)
    - `FWM`: Forebrain White Matter
- **Quantified Pathological Biomarkers:**
  - `ihc_at8_ffpe`: Phosphorylated tau (AT8 monoclonal antibody) area fraction.
  - `ihc_a_beta_ffpe`: Amyloid-β area fraction.
  - `tau_ng_per_mg`: Total tau protein quantified by Luminex immunoassay.
  - `ptau_ng_per_mg`: Phosphorylated tau at Thr181.
  - `ab42_pg_per_mg`: Amyloid-β 42 peptide concentration.
  - `ihc_a_syn`: α-synuclein area fraction (Lewy pathology).
- **V1.5 Diagnostic Ingestion Rules:**
  - Strict etiology mapping based on `dsm_iv_clinical_diagnosis`.
  - Only donors classified explicitly as `"Alzheimer's Disease Type"` receive `disease_status = 'AD'`.
  - Non-demented ACT donors receive `disease_status = 'CONTROL'`.
  - Generic dementia without clear AD etiology is classified as `OTHER` or `UNKNOWN` to prevent diagnostic inflation.
  - Age ranges (`"90-94"`, `"100+"`) are converted to midpoints (`92.0`, `102.5`) with precision flags.

---

### 2.2. Allen Human Brain Atlas
- **Source:** Allen Institute REST API (`http://api.brain-map.org/api/v2/data/Structure/`).
- **Function:** Serves as the canonical coordinate reference system for brain structures in MANAS.
- **Hierarchical Depth:** Roots from `"Brain"` down to sub-cortical nuclei and cortical gyri.
- **Coordinate System:** Montreal Neurological Institute (MNI) spatial coordinates $(x, y, z)$.

---

### 2.3. OASIS-1: Cross-Sectional MRI & Clinical Cohort
- **Accession:** Open Access under Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Files Utilized:** `oasis_cross_sectional.xlsx`
- **Sample Characteristics:**
  - 436 subjects aged 18 to 96 years.
  - Includes young, middle-aged, non-demented older adults, and older adults with mild-to-moderate Alzheimer's disease.
- **Key Scalar Metrics:**
  - `CDR`: Clinical Dementia Rating (0 = normal, 0.5 = very mild / questionable, 1 = mild, 2 = moderate).
  - `MMSE`: Mini-Mental State Examination score (range 0–30).
  - `nWBV`: Normalized Whole Brain Volume. Expressed as the proportion of total intracranial volume occupied by brain tissue.
  - `eTIV`: Estimated Total Intracranial Volume in mm³.
  - `Educ`: Formal education in years (cognitive reserve covariate).
  - `SES`: Socioeconomic status (1 to 5 scale).

---

### 2.4. OASIS-2: Longitudinal MRI & Cognitive Decline Cohort
- **Accession:** Open Access under CC BY 4.0.
- **Files Utilized:** `oasis_longitudinal_demographics.xlsx`
- **Sample Characteristics:**
  - 150 older adults aged 60 to 96 years scanned across 373 distinct imaging sessions.
  - Follow-up intervals range from 180 to 2,600 days.
  - 72 subjects remained non-demented across all visits.
  - 64 subjects were demented at initial visit and remained demented.
  - 14 subjects were characterized as **Converters** (entered non-demented and converted to very mild/mild dementia at subsequent visits).
- **Analytical Utility in MANAS V2:**
  - Calibrates longitudinal brain atrophy estimation ($\%\,\text{nWBV}/\text{year}$).
  - Serves as the ground truth validation set for the 5-year conversion risk model.

---

## 3. Quality Control (QC) Pipeline Rules

The MANAS Quality Control Pipeline (`validation/qc_pipeline.py`) validates every record prior to committing to the database:

1. **Schema Check:** Verifies existence of all mandatory columns.
2. **Duplicate Check:** Rejects duplicate donor or subject accession keys (`status = FAIL`).
3. **Plausibility Ranges:**
   - Age: $40 \le \text{age} \le 115$ (Values $< 40$ in dementia cohorts trigger `WARNING`).
   - MMSE: $0 \le \text{MMSE} \le 30$ (Values outside trigger `FAIL`).
   - CDR: $\text{CDR} \in \{0.0, 0.5, 1.0, 2.0, 3.0\}$.
   - nWBV: $0.50 \le \text{nWBV} \le 0.90$.
   - Braak Stage: $0 \le \text{Braak} \le 6$.
4. **Biological Plausibility:** Identifies extreme outliers (> 4 standard deviations from mean) and assigns a `quality_flag = 'WARNING'`. Observations with warnings are reported transparently in QC tables and can be toggled by the investigator.

