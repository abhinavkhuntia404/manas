"""
QC Pipeline — validates ingested data against research-grade quality criteria.
Produces PASS / WARNING / FAIL records for every check.
Never silently removes observations.
"""

import logging
import pandas as pd
from sqlalchemy.orm import Session
from backend.models.orm import QCResult

logger = logging.getLogger("manas.validation.qc")

# Allen Aging real column names (from actual downloaded CSV)
REQUIRED_DONOR_COLS = [
    "donor_id", "age", "sex", "dsm_iv_clinical_diagnosis",
    "act_demented", "braak", "cerad", "nincds_arda_diagnosis",
]

REQUIRED_METRIC_COLS = [
    "donor_id", "structure_acronym",
    "ihc_at8_ffpe",  # pTau (Alzheimer's key marker)
    "ihc_a_beta_ffpe",  # Amyloid-β
    "tau_ng_per_mg",
    "ptau_ng_per_mg",
    "ab42_pg_per_mg",
]

VALID_STRUCTURE_ACRONYMS = {"FWM", "HIP", "PCx", "TCx"}

VALID_DISEASE_VALUES = {
    "Alzheimer's Disease Type",
    "No Dementia",
    "Multiple Etiologies",
    "Other Medical",
    "Other or Unknown Cause",
    "Vascular",
}


class QCPipeline:
    def __init__(self, db: Session, processing_run_id: int):
        self.db = db
        self.run_id = processing_run_id

    # ------------------------------------------------------------------
    # Donor validation
    # ------------------------------------------------------------------

    def validate_donors(self, df: pd.DataFrame) -> list[dict]:
        """Validate donor data without crashing on incomplete input schemas."""
        results = []
        missing_cols = [c for c in REQUIRED_DONOR_COLS if c not in df.columns]
        if missing_cols:
            self._record("FAIL", "DATASET", None, "required_columns",
                         f"Missing required donor columns: {missing_cols}", len(missing_cols))
        else:
            self._record("PASS", "DATASET", None, "required_columns",
                         "All required donor columns present", 0)

        # Each check is gated on the columns it actually needs. A failed
        # schema check should produce a QC report, not a secondary KeyError.
        if "donor_id" in df.columns:
            dupes = int(df.duplicated(subset=["donor_id"]).sum())
            self._record("FAIL" if dupes else "PASS", "SUBJECT", None,
                         "duplicate_donors",
                         f"{dupes} duplicate donor_id values found" if dupes else "No duplicate donor IDs", dupes)

        dx_col = "dsm_iv_clinical_diagnosis"
        if dx_col in df.columns:
            dx = df[dx_col]
            missing_dx = int((dx.isna() | dx.astype(str).str.strip().eq("")).sum())
            self._record("WARNING" if missing_dx else "PASS", "SUBJECT", None,
                         "missing_diagnosis",
                         f"{missing_dx} donors missing {dx_col}" if missing_dx else "All donors have a clinical diagnosis", missing_dx)
            invalid_dx = int((~dx.dropna().isin(VALID_DISEASE_VALUES)).sum())
            self._record("WARNING" if invalid_dx else "PASS", "SUBJECT", None,
                         "invalid_diagnosis_labels",
                         f"{invalid_dx} donors have non-standard diagnosis labels" if invalid_dx else "All diagnosis labels are from controlled vocabulary", invalid_dx)

        if "age" in df.columns:
            unparseable_age = int(pd.to_numeric(df["age"].astype(str).str.extract(r"(\d+(?:\.\d+)?)")[0], errors="coerce").isna().sum())
            self._record("WARNING" if unparseable_age else "PASS", "SUBJECT", None,
                         "age_format",
                         f"{unparseable_age} age values could not be parsed" if unparseable_age else "All donor age values are parseable", unparseable_age)

        if "sex" in df.columns:
            invalid_sex = int((~df["sex"].astype(str).str.upper().isin(["M", "F", "MALE", "FEMALE"])).sum())
            self._record("WARNING" if invalid_sex else "PASS", "SUBJECT", None,
                         "sex_values",
                         f"{invalid_sex} donors have non-standard sex values" if invalid_sex else "All sex values are M or F", invalid_sex)

        if "braak" in df.columns:
            braak_vals = pd.to_numeric(df["braak"], errors="coerce")
            out_of_range = int(((braak_vals < 0) | (braak_vals > 6)).sum())
            self._record("WARNING" if out_of_range else "PASS", "SUBJECT", None,
                         "braak_range",
                         f"{out_of_range} Braak scores outside 0-6 range" if out_of_range else f"All Braak scores in valid range 0-6 (n={braak_vals.notna().sum()})", out_of_range)

        return results

    # ------------------------------------------------------------------
    # Metrics validation
    # ------------------------------------------------------------------

    def validate_metrics(self, df: pd.DataFrame) -> list[dict]:
        results = []

        # Check 1: Required columns
        missing_cols = [c for c in REQUIRED_METRIC_COLS if c not in df.columns]
        if missing_cols:
            self._record("WARNING", "DATASET", None, "required_metric_columns",
                         f"Some expected metric columns missing: {missing_cols}", len(missing_cols))
        else:
            self._record("PASS", "DATASET", None, "required_metric_columns",
                         "All required metric columns present", 0)

        # Check 2: Valid structure acronyms
        if "structure_acronym" in df.columns:
            unknown_regions = df[~df["structure_acronym"].isin(VALID_STRUCTURE_ACRONYMS)]["structure_acronym"].unique()
            if len(unknown_regions) > 0:
                self._record("WARNING", "REGION", None, "unknown_regions",
                             f"Unknown structure_acronym values: {list(unknown_regions)}", len(unknown_regions))
            else:
                self._record("PASS", "REGION", None, "unknown_regions",
                             f"All structure_acronym values recognised: {VALID_STRUCTURE_ACRONYMS}", 0)

        # Check 3: Missing data per key measurement
        for col in ["ihc_at8_ffpe", "ihc_a_beta_ffpe", "tau_ng_per_mg",
                    "ptau_ng_per_mg", "ab42_pg_per_mg"]:
            if col not in df.columns:
                continue
            numeric = pd.to_numeric(df[col], errors="coerce")
            n_missing = numeric.isna().sum()
            pct = round(100 * n_missing / len(df), 1)
            status = "FAIL" if pct > 50 else "WARNING" if pct > 20 else "PASS"
            self._record(status, "MEASUREMENT", None, f"missing_{col}",
                         f"{col}: {n_missing}/{len(df)} missing ({pct}%)", n_missing)

        # Check 4: Negative values in measurements that should be non-negative
        non_negative_cols = ["ihc_at8_ffpe", "ihc_a_beta_ffpe", "ihc_a_syn",
                              "tau_ng_per_mg", "ptau_ng_per_mg", "ab42_pg_per_mg"]
        for col in non_negative_cols:
            if col not in df.columns:
                continue
            numeric = pd.to_numeric(df[col], errors="coerce")
            n_neg = (numeric < 0).sum()
            if n_neg > 0:
                self._record("WARNING", "MEASUREMENT", None, f"negative_{col}",
                             f"{col}: {n_neg} negative values (flagged for review)", n_neg)

        # Check 5: Region × donor completeness (expect 4 rows per donor)
        if "donor_id" in df.columns and "structure_acronym" in df.columns:
            donor_region_counts = df.groupby("donor_id")["structure_acronym"].count()
            incomplete = (donor_region_counts < 4).sum()
            if incomplete > 0:
                self._record("WARNING", "MEASUREMENT", None, "incomplete_donor_regions",
                             f"{incomplete} donors have fewer than 4 brain region measurements", incomplete)
            else:
                self._record("PASS", "MEASUREMENT", None, "incomplete_donor_regions",
                             "All donors have measurements for all 4 brain regions", 0)

        return results

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _record(
        self,
        status: str,
        entity_type: str,
        entity_id: int | None,
        check_name: str,
        message: str,
        affected_count: int = 0,
    ):
        qc = QCResult(
            processing_run_id=self.run_id,
            entity_type=entity_type,
            entity_id=entity_id,
            check_name=check_name,
            status=status,
            message=message,
            affected_count=int(affected_count) if affected_count is not None else 0,
        )
        self.db.add(qc)
        self.db.flush()
        level = logging.ERROR if status == "FAIL" else logging.WARNING if status == "WARNING" else logging.INFO
        logger.log(level, f"QC [{status}] {check_name}: {message}")
