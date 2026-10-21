"""
Allen Aging, Dementia & TBI Study — Data Ingester.

Downloads or reads from local cache:
  - DonorInformation.csv       → subjects table
  - ProteinAndPathologyQuantifications.csv → measurements table

Access: OPEN_DIRECT — no registration required.
Source: https://aging.brain-map.org/download/index

IMPORTANT: Raw files are never modified.
All transformations produce new records in the database.
"""

import csv
import hashlib
import io
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from sqlalchemy.orm import Session

from backend.models.orm import (
    BrainAtlas, BrainRegion, DatasetVersion, MeasurementType,
    Measurement, ProcessingRun, QCResult, RegionMapping, Subject
)
from validation.qc_pipeline import QCPipeline
from atlas.region_mapper import RegionMapper

logger = logging.getLogger("manas.ingestion.allen_aging")

# Direct download URLs — no auth required
DONOR_INFO_URL = (
    "https://aging.brain-map.org/api/v2/data/query.csv"
    "?criteria=model::ApiTbiDonorDetail,rma::options[num_rows$eqall]"
)
PROTEIN_PATHOLOGY_URL = (
    "https://aging.brain-map.org/api/v2/data/query.csv"
    "?criteria=model::ApiTbiDonorMetric,rma::options[num_rows$eqall]"
)

def map_allen_diagnosis(raw_dx: str, act_demented: str = "") -> str:
    s = str(raw_dx).strip().lower()
    act = str(act_demented).strip().lower()
    if "alzheimer" in s:
        return "AD"
    if "no dementia" in s or "reference" in s:
        return "CONTROL"
    if act == "no dementia":
        return "CONTROL"
    if act == "dementia" or "dementia" in s:
        return "AD"
    if "multiple" in s or "vascular" in s or "other" in s:
        return "OTHER"
    return "UNKNOWN"

DIAGNOSIS_MAP = {
    "alzheimer's disease type": "AD",
    "no dementia": "CONTROL",
    "reference": "CONTROL",
    "dementia": "AD",
}

INGESTION_VERSION = "allen_aging_ingester_v1.0"


class AllenAgingIngester:
    """
    Ingests the Allen Aging, Dementia & TBI Study into MANAS.

    If is_synthetic=True: loads schema-identical synthetic data from
    data/synthetic/allen_aging_synthetic.csv (for development/testing).
    If is_synthetic=False: downloads or reads from data/raw/allen_aging/.

    Raw data is NEVER modified or deleted.
    """

    def __init__(self, db: Session, processing_run_id: int, is_synthetic: bool = True):
        self.db = db
        self.processing_run_id = processing_run_id
        self.is_synthetic = is_synthetic
        self.proc_run = db.query(ProcessingRun).filter(
            ProcessingRun.run_id == processing_run_id
        ).first()
        self.warnings = []
        self.errors = []
        self.records_processed = 0
        self.records_rejected = 0

        self.raw_dir = Path("data/raw/allen_aging")
        self.synthetic_dir = Path("data/synthetic")

    def run(self):
        """Execute full ingestion pipeline."""
        self._update_run_status("RUNNING", started_at=datetime.utcnow())
        try:
            # Step 1: Load data
            donors_df, metrics_df = self._load_data()
            logger.info(f"Loaded {len(donors_df)} donors, {len(metrics_df)} metric rows")

            # Step 2: Validate structure
            qc = QCPipeline(self.db, self.processing_run_id)
            qc.validate_donors(donors_df)
            qc.validate_metrics(metrics_df)

            # Step 3: Ingest donors → subjects table
            subject_map = self._ingest_donors(donors_df)
            logger.info(f"Ingested {len(subject_map)} subjects")

            # Step 4: Ensure measurement types
            mtype_map = self._ensure_measurement_types(metrics_df)

            # Step 5: Load region mapper
            mapper = RegionMapper(self.db)

            # Step 6: Ingest measurements
            self._ingest_measurements(metrics_df, subject_map, mtype_map, mapper)

            # Step 7: Record outcome
            self._update_run_status(
                "COMPLETED",
                completed_at=datetime.utcnow(),
                records_processed=self.records_processed,
                records_rejected=self.records_rejected,
                warnings=self.warnings,
                errors=self.errors,
            )
            logger.info(
                f"Ingestion complete. Processed: {self.records_processed}, "
                f"Rejected: {self.records_rejected}"
            )

        except Exception as exc:
            logger.error(f"Ingestion failed: {exc}", exc_info=True)
            self._update_run_status(
                "FAILED",
                completed_at=datetime.utcnow(),
                errors=[{"error": str(exc)}],
            )
            raise

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        if self.is_synthetic:
            return self._load_synthetic()
        return self._load_real()

    def _load_real(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        donor_path = self.raw_dir / "DonorInformation.csv"
        metric_path = self.raw_dir / "ProteinAndPathologyQuantifications.csv"

        if not donor_path.exists():
            raise FileNotFoundError(
                f"DonorInformation.csv not found at {donor_path}. "
                "Run: POST /api/ingestion/allen-aging or download manually from "
                "https://aging.brain-map.org/download/index"
            )
        if not metric_path.exists():
            raise FileNotFoundError(
                f"ProteinAndPathologyQuantifications.csv not found at {metric_path}."
            )

        donors = pd.read_csv(donor_path, low_memory=False)
        metrics = pd.read_csv(metric_path, low_memory=False)
        logger.info(f"Loaded real data: {len(donors)} donors, {len(metrics)} metric rows")
        return donors, metrics

    def _load_synthetic(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        from data.synthetic.generator import generate_allen_aging_synthetic
        donors, metrics = generate_allen_aging_synthetic(n_subjects=107)
        logger.info(f"Loaded SYNTHETIC data: {len(donors)} donors, {len(metrics)} metric rows")
        return donors, metrics

    # ------------------------------------------------------------------
    # Donor ingestion
    # ------------------------------------------------------------------

    def _ingest_donors(self, df: pd.DataFrame) -> dict[str, int]:
        """
        Map donor rows to Subject records.
        Returns {source_subject_id: subject_id} mapping.
        """
        version_id = self.proc_run.version_id
        subject_map = {}

        for _, row in df.iterrows():
            src_id = str(row.get("donor_id", row.get("Donor ID", "UNKNOWN")))
            if src_id == "UNKNOWN":
                self._reject("No donor ID", row)
                continue

            # Disease status mapping
            raw_dx = str(row.get("dsm_iv_clinical_diagnosis", ""))
            act_dx = str(row.get("act_demented", row.get("Act_Demented", "")))
            disease_status = map_allen_diagnosis(raw_dx, act_dx)
            if disease_status == "UNKNOWN":
                self._warn(f"Unrecognized diagnosis '{raw_dx}' / '{act_dx}' for donor {src_id} -> UNKNOWN")

            # Sex
            raw_sex = str(row.get("sex", row.get("Sex", "Unknown"))).strip()
            sex = "M" if raw_sex.upper() in ("M", "MALE") else "F" if raw_sex.upper() in ("F", "FEMALE") else "Unknown"

            # Age
            try:
                age = float(str(row.get("age_at_first_tbi", row.get("Age", ""))).replace("+", "").strip())
            except (ValueError, TypeError):
                age = None
                self._warn(f"Age could not be parsed for donor {src_id}")

            # Check for existing
            existing = (
                self.db.query(Subject)
                .filter(
                    Subject.version_id == version_id,
                    Subject.source_subject_id == src_id,
                )
                .first()
            )
            if existing:
                subject_map[src_id] = existing.subject_id
                continue

            subject = Subject(
                version_id=version_id,
                source_subject_id=src_id,
                disease_status=disease_status,
                disease_confirmed=disease_status in ("AD", "CONTROL"),
                age_at_entry=age,
                sex=sex,
                is_synthetic=self.is_synthetic,
            )
            self.db.add(subject)
            self.db.flush()
            subject_map[src_id] = subject.subject_id
            self.records_processed += 1

        self.db.commit()
        return subject_map

    # ------------------------------------------------------------------
    # Measurement type registry
    # ------------------------------------------------------------------

    def _ensure_measurement_types(self, df: pd.DataFrame) -> dict[str, int]:
        """
        Register all measurement columns as MeasurementType records.
        Returns {column_name: type_id}.
        """
        # Columns that are NOT measurements
        skip_cols = {
            "donor_id", "donor_name", "structure_id", "structure_acronym",
            "structure_name", "hemisphere", "structure_color",
        }
        mtype_map = {}

        for col in df.columns:
            if col in skip_cols:
                continue
            existing = (
                self.db.query(MeasurementType)
                .filter(MeasurementType.name == col)
                .first()
            )
            if existing:
                mtype_map[col] = existing.type_id
                continue

            category = self._infer_measurement_category(col)
            mtype = MeasurementType(
                name=col,
                category=category,
                unit=self._infer_unit(col),
                description=f"Allen Aging TBI Study: {col}",
                source_assay=self._infer_assay(col),
            )
            self.db.add(mtype)
            self.db.flush()
            mtype_map[col] = mtype.type_id

        self.db.commit()
        return mtype_map

    # ------------------------------------------------------------------
    # Measurement ingestion
    # ------------------------------------------------------------------

    def _ingest_measurements(
        self,
        df: pd.DataFrame,
        subject_map: dict[str, int],
        mtype_map: dict[str, int],
        mapper: "RegionMapper",
    ):
        """
        For each (donor × region × measurement_type), insert a Measurement.
        Missing/invalid values are flagged, never silently dropped.
        """
        version_id = self.proc_run.version_id
        skip_cols = {
            "donor_id", "donor_name", "structure_id", "structure_acronym",
            "structure_name", "hemisphere", "structure_color",
        }
        batch = []
        BATCH_SIZE = 500

        for _, row in df.iterrows():
            src_id = str(row.get("donor_id", "UNKNOWN"))
            subject_id = subject_map.get(src_id)
            if not subject_id:
                self._reject(f"No subject record for donor {src_id}", row)
                continue

            # Region mapping
            region_name = str(row.get("structure_name", row.get("structure_acronym", "")))
            hemisphere = str(row.get("hemisphere", "bilateral")).lower()
            region_id = mapper.map(
                region_name,
                source_dataset="allen_aging",
                hemisphere=hemisphere,
            )
            if not region_id:
                self._warn(f"Region '{region_name}' could not be mapped — skipping measurements for this row")
                self.records_rejected += 1
                continue

            for col, type_id in mtype_map.items():
                if col in skip_cols:
                    continue
                raw_val = row.get(col)

                # Determine quality flag
                if raw_val is None or (isinstance(raw_val, float) and pd.isna(raw_val)):
                    quality_flag = "MISSING"
                    value = None
                elif str(raw_val).strip() in ("", "N/A", "n/a", "NA", "na"):
                    quality_flag = "NOT_MEASURED"
                    value = None
                else:
                    try:
                        value = float(raw_val)
                        quality_flag = "PASS"
                    except (ValueError, TypeError):
                        quality_flag = "FAILED_MEASUREMENT"
                        value = None
                        self._warn(f"Non-numeric value '{raw_val}' in column '{col}' for donor {src_id}")

                batch.append(
                    Measurement(
                        version_id=version_id,
                        subject_id=subject_id,
                        region_id=region_id,
                        type_id=type_id,
                        value=value,
                        unit=None,
                        source_variable=col,
                        quality_flag=quality_flag,
                        is_synthetic=self.is_synthetic,
                    )
                )
                self.records_processed += 1

            if len(batch) >= BATCH_SIZE:
                self.db.bulk_save_objects(batch)
                self.db.commit()
                batch = []

        if batch:
            self.db.bulk_save_objects(batch)
            self.db.commit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _update_run_status(self, status: str, **kwargs):
        for k, v in kwargs.items():
            setattr(self.proc_run, k, v)
        self.proc_run.status = status
        self.proc_run.ingestion_version = INGESTION_VERSION
        self.db.commit()

    def _warn(self, msg: str):
        logger.warning(msg)
        self.warnings.append({"message": msg, "timestamp": datetime.utcnow().isoformat()})

    def _reject(self, reason: str, row):
        logger.warning(f"REJECTED: {reason}")
        self.errors.append({"reason": reason, "timestamp": datetime.utcnow().isoformat()})
        self.records_rejected += 1

    @staticmethod
    def _infer_measurement_category(col: str) -> str:
        col_lower = col.lower()
        if any(k in col_lower for k in ["tau", "amyloid", "abeta", "ab42", "ptau",
                                          "ihc", "immunohisto", "nfts", "plaques"]):
            return "PATHOLOGY"
        if any(k in col_lower for k in ["fpkm", "tpm", "rnaseq", "rna", "expression"]):
            return "GENE_EXPRESSION"
        if any(k in col_lower for k in ["isoprostane", "luminex", "protein"]):
            return "PROTEIN_QUANTIFICATION"
        return "OTHER"

    @staticmethod
    def _infer_unit(col: str) -> Optional[str]:
        col_lower = col.lower()
        if "fpkm" in col_lower:
            return "FPKM"
        if "tpm" in col_lower:
            return "TPM"
        if "isoprostane" in col_lower:
            return "pg/g tissue"
        return None

    @staticmethod
    def _infer_assay(col: str) -> Optional[str]:
        col_lower = col.lower()
        if any(k in col_lower for k in ["ihc", "nfts", "plaques", "neuritic"]):
            return "immunohistochemistry"
        if any(k in col_lower for k in ["luminex"]):
            return "luminex_multiplex"
        if "isoprostane" in col_lower:
            return "isoprostane_elisa"
        if any(k in col_lower for k in ["fpkm", "tpm"]):
            return "rna_seq"
        return None
