"""
OASIS Ingester — OASIS-1 (Cross-Sectional) and OASIS-2 (Longitudinal).

OASIS-1: oasis_cross_sectional.xlsx — 436 subjects, CDR, MMSE, nWBV, eTIV
OASIS-2: oasis_longitudinal_demographics.xlsx — 373 visit rows, longitudinal

Key clinical measurements available (no MRI images needed):
  CDR  — Clinical Dementia Rating (0=none, 0.5=very mild, 1=mild, 2=moderate)
  MMSE — Mini-Mental State Examination (0–30, lower = worse)
  nWBV — Normalized Whole Brain Volume (MRI-derived, provided as scalar)
  eTIV — Estimated Total Intracranial Volume

Disease classification:
  CDR == 0    → CONTROL
  CDR == 0.5  → MCI (mild cognitive impairment)
  CDR >= 1    → AD (Alzheimer's / dementia)
  Group == 'Nondemented' → CONTROL
  Group == 'Demented'    → AD
  Group == 'Converted'   → CONVERTED (started control, became demented)

IMPORTANT: nWBV is a whole-brain measurement, not a regional measurement.
It maps to a synthetic "Whole Brain" region in the canonical atlas.
This is documented and scientifically valid.
"""

import logging
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from backend.models.orm import (
    BrainAtlas, BrainRegion, Dataset, DatasetVersion,
    Measurement, MeasurementType, ProcessingRun,
    QCResult, RegionMapping, Subject
)

logger = logging.getLogger("manas.ingestion.oasis")

OASIS_CROSS_PATH = Path("data/raw/oasis/oasis_cross_sectional.xlsx")
OASIS_LONG_PATH  = Path("data/raw/oasis/oasis_longitudinal_demographics.xlsx")

INGESTION_VERSION = "oasis_ingester_v1.0"

# CDR → disease_status mapping
def cdr_to_disease(cdr_val) -> str:
    try:
        cdr = float(cdr_val)
        if cdr == 0:
            return "CONTROL"
        elif cdr == 0.5:
            return "MCI"
        else:
            return "AD"
    except (TypeError, ValueError):
        return "UNKNOWN"

# Group field → disease_status (OASIS-2)
GROUP_MAP = {
    "Nondemented": "CONTROL",
    "Demented": "AD",
    "Converted": "CONVERTED",
}

# Measurement columns and their metadata
OASIS_MEASUREMENTS = {
    "MMSE": {
        "name": "mmse_score",
        "category": "CLINICAL",
        "unit": "score (0-30)",
        "description": "Mini-Mental State Examination score. Range 0–30; lower = more impaired.",
        "source_assay": "neuropsychological_test",
    },
    "CDR": {
        "name": "cdr_score",
        "category": "CLINICAL",
        "unit": "score (0-3)",
        "description": "Clinical Dementia Rating. 0=none, 0.5=questionable, 1=mild, 2=moderate, 3=severe.",
        "source_assay": "clinical_assessment",
    },
    "nWBV": {
        "name": "normalized_whole_brain_volume",
        "category": "NEUROIMAGING_DERIVED",
        "unit": "proportion",
        "description": "Normalized Whole Brain Volume (nWBV). Ratio of brain volume to intracranial volume. MRI-derived scalar.",
        "source_assay": "mri_volumetry",
    },
    "eTIV": {
        "name": "estimated_total_intracranial_volume",
        "category": "NEUROIMAGING_DERIVED",
        "unit": "mm³",
        "description": "Estimated Total Intracranial Volume (eTIV). MRI-derived.",
        "source_assay": "mri_volumetry",
    },
    "ASF": {
        "name": "atlas_scaling_factor",
        "category": "NEUROIMAGING_DERIVED",
        "unit": "unitless",
        "description": "Atlas Scaling Factor — normalization factor for volume comparison.",
        "source_assay": "mri_volumetry",
    },
}


class OasisIngester:
    """
    Ingests OASIS-1 (cross-sectional) and OASIS-2 (longitudinal) clinical data.

    NOTE: These files contain only aggregate/derived clinical measurements,
    not raw MRI images. The nWBV value is a pre-computed scalar from MRI.
    This ingester does NOT require MRI processing.
    """

    def __init__(self, db: Session, version_id: int, oasis_version: str = "OASIS-1"):
        self.db = db
        self.version_id = version_id
        self.oasis_version = oasis_version
        self.records_processed = 0
        self.records_rejected = 0
        self.warnings = []
        self._whole_brain_region_id = None

    def run(self):
        """Run OASIS ingestion."""
        logger.info(f"Starting {self.oasis_version} ingestion")

        # Ensure whole-brain region exists
        self._whole_brain_region_id = self._get_or_create_whole_brain_region()

        # Ensure measurement types
        mtype_map = self._ensure_measurement_types()

        if self.oasis_version == "OASIS-1":
            df = self._load_cross_sectional()
            self._ingest_cross_sectional(df, mtype_map)
        elif self.oasis_version == "OASIS-2":
            df = self._load_longitudinal()
            self._ingest_longitudinal(df, mtype_map)

        self.db.commit()
        logger.info(
            f"{self.oasis_version} ingestion complete. "
            f"Processed: {self.records_processed}, Rejected: {self.records_rejected}"
        )

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_cross_sectional(self) -> pd.DataFrame:
        df = pd.read_excel(OASIS_CROSS_PATH)
        logger.info(f"OASIS-1: loaded {len(df)} rows, {len(df.columns)} columns")
        return df

    def _load_longitudinal(self) -> pd.DataFrame:
        df = pd.read_excel(OASIS_LONG_PATH)
        # Fix Excel formula artifact in Visit column: '=RIGHT(B2,1)' → extract digit
        if "Visit" in df.columns:
            df["Visit"] = df["Visit"].apply(
                lambda v: re.search(r'\d+', str(v)).group() if isinstance(v, str) and '=' in v
                else v
            )
        logger.info(f"OASIS-2: loaded {len(df)} rows, {len(df.columns)} columns")
        return df

    # ------------------------------------------------------------------
    # Cross-sectional ingestion
    # ------------------------------------------------------------------

    def _ingest_cross_sectional(self, df: pd.DataFrame, mtype_map: dict):
        """
        OASIS-1: one row per subject.
        Maps CDR → disease_status.
        """
        for _, row in df.iterrows():
            subject_id_src = str(row.get("ID", "")).strip()
            if not subject_id_src:
                self.records_rejected += 1
                continue

            cdr = row.get("CDR")
            disease_status = cdr_to_disease(cdr)

            sex_raw = str(row.get("M/F", "Unknown")).strip()
            sex = "M" if sex_raw == "M" else "F" if sex_raw == "F" else "Unknown"

            try:
                age = float(row.get("Age", None))
            except (TypeError, ValueError):
                age = None

            # Create subject
            existing = self.db.query(Subject).filter(
                Subject.version_id == self.version_id,
                Subject.source_subject_id == subject_id_src,
            ).first()

            if existing:
                subj_id = existing.subject_id
            else:
                subj = Subject(
                    version_id=self.version_id,
                    source_subject_id=subject_id_src,
                    disease_status=disease_status,
                    disease_confirmed=disease_status in ("AD", "CONTROL"),
                    age_at_entry=age,
                    sex=sex,
                    education_years=float(row.get("Educ", None) or 0) or None,
                    is_synthetic=False,
                )
                self.db.add(subj)
                self.db.flush()
                subj_id = subj.subject_id
                self.records_processed += 1

            # Ingest measurements
            for col, type_id in mtype_map.items():
                val = row.get(col)
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    quality_flag = "MISSING"
                    value = None
                elif str(val).strip() in ("N/A", ""):
                    quality_flag = "NOT_MEASURED"
                    value = None
                else:
                    try:
                        value = float(val)
                        quality_flag = "PASS"
                    except (ValueError, TypeError):
                        quality_flag = "FAILED_MEASUREMENT"
                        value = None

                m = Measurement(
                    version_id=self.version_id,
                    subject_id=subj_id,
                    region_id=self._whole_brain_region_id,
                    type_id=type_id,
                    value=value,
                    unit=OASIS_MEASUREMENTS.get(col, {}).get("unit"),
                    timepoint="baseline",
                    source_variable=col,
                    quality_flag=quality_flag,
                    is_synthetic=False,
                )
                self.db.add(m)

        self.db.commit()

    # ------------------------------------------------------------------
    # Longitudinal ingestion
    # ------------------------------------------------------------------

    def _ingest_longitudinal(self, df: pd.DataFrame, mtype_map: dict):
        """
        OASIS-2: multiple rows per subject (visits).
        Subject-level split for ML: CRITICAL — all visits of a subject
        stay together. The visit identifier is stored as timepoint.
        """
        subject_registry: dict[str, int] = {}

        for _, row in df.iterrows():
            src_id = str(row.get("Subject ID", "")).strip()
            mri_id = str(row.get("MRI ID", "")).strip()
            if not src_id:
                self.records_rejected += 1
                continue

            group = str(row.get("Group", "")).strip()
            disease_status = GROUP_MAP.get(group, "UNKNOWN")

            sex_raw = str(row.get("M/F", "Unknown")).strip()
            sex = "M" if sex_raw == "M" else "F" if sex_raw == "F" else "Unknown"

            visit_str = str(row.get("Visit", "1")).strip()
            timepoint = f"visit_{visit_str}"

            try:
                age = float(row.get("Age", None))
            except (TypeError, ValueError):
                age = None

            # Subject (one record per subject, not per visit)
            if src_id not in subject_registry:
                existing = self.db.query(Subject).filter(
                    Subject.version_id == self.version_id,
                    Subject.source_subject_id == src_id,
                ).first()
                if existing:
                    subject_registry[src_id] = existing.subject_id
                else:
                    subj = Subject(
                        version_id=self.version_id,
                        source_subject_id=src_id,
                        disease_status=disease_status,
                        disease_confirmed=True,
                        age_at_entry=age,
                        sex=sex,
                        education_years=float(row.get("EDUC", None) or 0) or None,
                        is_synthetic=False,
                    )
                    self.db.add(subj)
                    self.db.flush()
                    subject_registry[src_id] = subj.subject_id
                    self.records_processed += 1

            subj_id = subject_registry[src_id]

            # Measurements for this visit
            for col, type_id in mtype_map.items():
                val = row.get(col)
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    quality_flag = "MISSING"
                    value = None
                else:
                    try:
                        value = float(val)
                        quality_flag = "PASS"
                    except (TypeError, ValueError):
                        quality_flag = "FAILED_MEASUREMENT"
                        value = None

                m = Measurement(
                    version_id=self.version_id,
                    subject_id=subj_id,
                    region_id=self._whole_brain_region_id,
                    type_id=type_id,
                    value=value,
                    unit=OASIS_MEASUREMENTS.get(col, {}).get("unit"),
                    timepoint=timepoint,
                    source_variable=col,
                    quality_flag=quality_flag,
                    is_synthetic=False,
                )
                self.db.add(m)

        self.db.commit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_or_create_whole_brain_region(self) -> int:
        """
        OASIS measurements are whole-brain scalars.
        Map to a canonical 'Whole Brain' region.
        """
        atlas = self.db.query(BrainAtlas).filter(
            BrainAtlas.short_name == "ARA_HUMAN"
        ).first()
        if not atlas:
            atlas = BrainAtlas(
                name="Allen Human Reference Atlas",
                short_name="ARA_HUMAN",
                version="2013-human-v1",
                species="Homo sapiens",
            )
            self.db.add(atlas)
            self.db.commit()
            self.db.refresh(atlas)

        region = self.db.query(BrainRegion).filter(
            BrainRegion.atlas_id == atlas.atlas_id,
            BrainRegion.abbreviation == "WB",
        ).first()

        if not region:
            region = BrainRegion(
                atlas_id=atlas.atlas_id,
                name="Whole Brain",
                abbreviation="WB",
                hemisphere="bilateral",
                anatomical_category="whole_brain",
                depth=0,
                is_leaf=True,
            )
            self.db.add(region)
            self.db.flush()

            # Record the mapping
            m = RegionMapping(
                source_name="whole_brain",
                source_dataset="oasis",
                canonical_region_id=region.region_id,
                mapping_method="manual",
                confidence="HIGH",
                reviewer="MANAS-system",
                notes="OASIS nWBV/eTIV/ASF are whole-brain scalar measurements mapped to Whole Brain region.",
            )
            self.db.add(m)
            self.db.commit()

        return region.region_id

    def _ensure_measurement_types(self) -> dict[str, int]:
        """Register OASIS measurement columns as MeasurementType records."""
        mtype_map = {}
        # OASIS uses 'M/F' for sex which is metadata, not a measurement
        measurement_cols = ["MMSE", "CDR", "nWBV", "eTIV", "ASF"]

        for col in measurement_cols:
            meta = OASIS_MEASUREMENTS.get(col, {})
            canonical_name = meta.get("name", col.lower())

            existing = self.db.query(MeasurementType).filter(
                MeasurementType.name == canonical_name
            ).first()
            if existing:
                mtype_map[col] = existing.type_id
                continue

            mtype = MeasurementType(
                name=canonical_name,
                category=meta.get("category", "CLINICAL"),
                unit=meta.get("unit"),
                description=meta.get("description", ""),
                source_assay=meta.get("source_assay"),
            )
            self.db.add(mtype)
            self.db.flush()
            mtype_map[col] = mtype.type_id

        self.db.commit()
        return mtype_map
