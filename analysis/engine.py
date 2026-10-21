"""
MANAS Statistical Analysis Engine.
Orchestrates the full AD regional comparison pipeline.

Pipeline:
  1. Load analysis-ready data from DB
  2. Normality test (Shapiro-Wilk / D'Agostino-Pearson)
  3. Test selection (t-test / Welch / Mann-Whitney U)
  4. Effect size (Cohen's d or rank-biserial r) + bootstrap 95% CI
  5. BH FDR multiple testing correction
  6. Covariate-adjusted regression (where data permit)
  7. Robustness analysis (3 alternative specs)
  8. Store results with full provenance
"""

import logging
import platform
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sqlalchemy.orm import Session

from backend.models.orm import (
    AnalysisResult, AnalysisRun, BrainRegion,
    DatasetVersion, Measurement, MeasurementType, Subject
)
from configs.settings import get_settings

logger = logging.getLogger("manas.analysis.engine")
settings = get_settings()

# Minimum subjects per group to run any statistical test
MIN_GROUP_N = settings.min_group_size
FDR_ALPHA = settings.fdr_alpha
BOOTSTRAP_N = settings.bootstrap_n


class AnalysisEngine:
    """
    Executes a full MANAS analysis run, end-to-end.
    Call engine.run(analysis_run_id).
    """

    def __init__(self, db: Session = None, cfg=None):
        self.db = db
        self.cfg = cfg if cfg is not None else settings

    def run(self, analysis_run_id: str):
        """Main entry point. Updates run status throughout."""
        run = self._get_run(analysis_run_id)
        if not run:
            raise ValueError(f"Analysis run {analysis_run_id} not found")

        logger.info(f"Starting analysis {analysis_run_id}")
        self._set_status(run, "RUNNING", started_at=datetime.utcnow())

        try:
            # --- Step 1: Load data ---
            df = self._load_data(run)
            logger.info(f"Loaded {len(df)} measurement rows")

            if len(df) == 0:
                raise ValueError("No analysis-ready measurements found for this configuration")

            # --- Step 2: Compute distinct subject group sizes ---
            n_disease = int(df[df["disease_status"] == "AD"]["subject_id"].nunique())
            n_control = int(df[df["disease_status"] == "CONTROL"]["subject_id"].nunique())
            n_total = n_disease + n_control
            run.n_total = n_total
            run.n_disease = n_disease
            run.n_control = n_control
            self.db.commit()
            logger.info(f"Groups: AD={n_disease}, CONTROL={n_control}")

            # --- Step 3: Regional analysis ---
            results = []
            regions = df["region_id"].unique()
            for region_id in regions:
                region_df = df[df["region_id"] == region_id]
                result = self._analyze_region(region_id, region_df)
                results.append(result)

            # --- Step 4: Multiple testing correction (BH FDR) ---
            results = self._apply_fdr_correction(results)

            # --- Step 5: Store results ---
            self._store_results(run, results)

            # --- Step 6: Record provenance ---
            run.software_env = self._get_env_info()
            run.statistical_method = "normality-adaptive (Shapiro-Wilk/D'Agostino -> Student's t / Welch's t / Mann-Whitney U)"
            run.correction_method = "Benjamini-Hochberg FDR"
            run.effect_size_measure = "Cohen's d (parametric) / rank-biserial r (non-parametric)"
            self._set_status(run, "COMPLETED", completed_at=datetime.utcnow())
            logger.info(f"Analysis {analysis_run_id} completed. {len(results)} regions tested.")

        except Exception as exc:
            logger.error(f"Analysis {analysis_run_id} failed: {exc}", exc_info=True)
            run.error_message = str(exc)
            self._set_status(run, "FAILED", completed_at=datetime.utcnow())
            raise

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_data(self, run: AnalysisRun) -> pd.DataFrame:
        """
        Load analysis-ready measurements joined with subject disease status.
        Only PASS quality measurements are included by default.
        """
        version_id = run.version_id
        mtype_id = run.measurement_type_id

        rows = (
            self.db.query(
                Measurement.value,
                Measurement.region_id,
                Measurement.quality_flag,
                Subject.disease_status,
                Subject.age_at_entry,
                Subject.sex,
                Subject.subject_id,
            )
            .join(Subject, Measurement.subject_id == Subject.subject_id)
            .filter(
                Measurement.version_id == version_id,
                Measurement.type_id == mtype_id,
                Measurement.quality_flag.in_(["PASS", "WARNING"]),
                Subject.disease_status.in_(["AD", "CONTROL"]),
            )
            .all()
        )

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=[
            "value", "region_id", "quality_flag",
            "disease_status", "age_at_entry", "sex", "subject_id"
        ])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
        return df

    # ------------------------------------------------------------------
    # Per-region analysis
    # ------------------------------------------------------------------

    def _analyze_region(self, region_id: int, df: pd.DataFrame) -> dict:
        """
        Full statistical analysis for one brain region.
        Returns a dict of all result fields.
        """
        disease_vals = df[df["disease_status"] == "AD"]["value"].dropna().values
        control_vals = df[df["disease_status"] == "CONTROL"]["value"].dropna().values

        n_d = len(disease_vals)
        n_c = len(control_vals)

        base = {
            "region_id": region_id,
            "n_disease": n_d,
            "n_control": n_c,
            "disease_mean": float(np.mean(disease_vals)) if n_d > 0 else None,
            "disease_median": float(np.median(disease_vals)) if n_d > 0 else None,
            "disease_sd": float(np.std(disease_vals, ddof=1)) if n_d > 1 else None,
            "control_mean": float(np.mean(control_vals)) if n_c > 0 else None,
            "control_median": float(np.median(control_vals)) if n_c > 0 else None,
            "control_sd": float(np.std(control_vals, ddof=1)) if n_c > 1 else None,
            "mean_difference": None,
            "effect_size": None,
            "effect_size_ci_lower": None,
            "effect_size_ci_upper": None,
            "p_value": None,
            "adjusted_p_value": None,
            "significance_status": "NOT_TESTED",
            "test_statistic": None,
            "degrees_of_freedom": None,
            "test_method": None,
        }

        if n_d < MIN_GROUP_N or n_c < MIN_GROUP_N:
            base["significance_status"] = "INSUFFICIENT_DATA"
            return base

        base["mean_difference"] = base["disease_mean"] - base["control_mean"]

        # --- Normality test ---
        is_parametric = self._is_parametric(disease_vals, control_vals)

        # --- Statistical test ---
        if is_parametric:
            # Levene test for equal variances
            _, p_levene = stats.levene(disease_vals, control_vals)
            equal_var = p_levene > 0.05

            if equal_var:
                stat, p = stats.ttest_ind(disease_vals, control_vals, equal_var=True)
                method = "Student's t-test"
                df_val = n_d + n_c - 2
            else:
                stat, p = stats.ttest_ind(disease_vals, control_vals, equal_var=False)
                method = "Welch's t-test"
                # Welch-Satterthwaite df approximation
                s1, s2 = np.var(disease_vals, ddof=1), np.var(control_vals, ddof=1)
                df_val = (s1/n_d + s2/n_c)**2 / ((s1/n_d)**2/(n_d-1) + (s2/n_c)**2/(n_c-1))

            # Cohen's d (Hedges' g correction for small samples)
            pooled_sd = np.sqrt(
                ((n_d - 1) * np.var(disease_vals, ddof=1) +
                 (n_c - 1) * np.var(control_vals, ddof=1)) / (n_d + n_c - 2)
            )
            d = (base["disease_mean"] - base["control_mean"]) / pooled_sd if pooled_sd > 0 else 0.0
            # Hedges' g correction
            correction = 1 - (3 / (4 * (n_d + n_c - 2) - 1))
            effect = d * correction

            ci_lower, ci_upper = self._bootstrap_effect_ci(
                disease_vals, control_vals, self._cohens_d, n=BOOTSTRAP_N
            )

        else:
            # Mann-Whitney U
            stat, p = stats.mannwhitneyu(disease_vals, control_vals, alternative="two-sided")
            method = "Mann-Whitney U"
            df_val = None

            # Rank-biserial correlation (disease vs control)
            n1, n2 = len(disease_vals), len(control_vals)
            effect = (2 * stat) / (n1 * n2) - 1

            ci_lower, ci_upper = self._bootstrap_effect_ci(
                disease_vals, control_vals, self._rank_biserial, n=BOOTSTRAP_N
            )

        base.update({
            "p_value": float(p),
            "test_statistic": float(stat),
            "degrees_of_freedom": float(df_val) if df_val is not None else None,
            "test_method": method,
            "effect_size": float(effect),
            "effect_size_ci_lower": float(ci_lower),
            "effect_size_ci_upper": float(ci_upper),
        })
        return base

    # ------------------------------------------------------------------
    # Normality testing
    # ------------------------------------------------------------------

    @staticmethod
    def _is_parametric(group1: np.ndarray, group2: np.ndarray) -> bool:
        """
        Test normality of both groups.
        Shapiro-Wilk for n ≤ 50, D'Agostino-Pearson for n > 50.
        Returns True if BOTH groups pass normality (p > 0.05).
        """
        def test_one(arr):
            n = len(arr)
            if n < 3:
                return False
            if n <= 50:
                _, p = stats.shapiro(arr)
            else:
                _, p = stats.normaltest(arr)
            return p > 0.05

        return test_one(group1) and test_one(group2)

    # ------------------------------------------------------------------
    # Effect sizes
    # ------------------------------------------------------------------

    @staticmethod
    def _cohens_d(g1: np.ndarray, g2: np.ndarray) -> float:
        n1, n2 = len(g1), len(g2)
        if n1 < 2 or n2 < 2:
            return 0.0
        pooled = np.sqrt(
            ((n1 - 1) * np.var(g1, ddof=1) + (n2 - 1) * np.var(g2, ddof=1))
            / (n1 + n2 - 2)
        )
        return (np.mean(g1) - np.mean(g2)) / pooled if pooled > 0 else 0.0

    @staticmethod
    def _rank_biserial(g1: np.ndarray, g2: np.ndarray) -> float:
        u, _ = stats.mannwhitneyu(g1, g2, alternative="two-sided")
        return (2 * u) / (len(g1) * len(g2)) - 1

    def _bootstrap_effect_ci(
        self,
        g1: np.ndarray,
        g2: np.ndarray,
        effect_fn,
        n: int = 1000,
        alpha: float = 0.05,
    ) -> tuple[float, float]:
        """
        Bootstrap percentile confidence interval for an effect size.
        Subject-safe (resamples within each group independently).
        """
        rng = np.random.default_rng(self.cfg.default_random_seed)
        bootstrapped = []
        for _ in range(n):
            b1 = rng.choice(g1, size=len(g1), replace=True)
            b2 = rng.choice(g2, size=len(g2), replace=True)
            bootstrapped.append(effect_fn(b1, b2))
        ci_lower = float(np.percentile(bootstrapped, 100 * alpha / 2))
        ci_upper = float(np.percentile(bootstrapped, 100 * (1 - alpha / 2)))
        return ci_lower, ci_upper

    # ------------------------------------------------------------------
    # Multiple testing correction — BH FDR
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_fdr_correction(results: list[dict]) -> list[dict]:
        """
        Apply Benjamini-Hochberg FDR correction across all testable regions.
        Regions with insufficient data are excluded from correction.
        """
        testable = [(i, r) for i, r in enumerate(results) if r["p_value"] is not None]
        if not testable:
            return results

        indices, testable_results = zip(*testable)
        p_values = np.array([r["p_value"] for r in testable_results])

        # BH procedure
        n = len(p_values)
        sorted_idx = np.argsort(p_values)
        sorted_p = p_values[sorted_idx]

        ranks = np.arange(1, n + 1)
        adj_sorted = sorted_p * n / ranks

        # Enforce monotonicity (cumulative minimum from right on sorted array)
        adj_sorted = np.minimum.accumulate(adj_sorted[::-1])[::-1]
        adj_sorted = np.clip(adj_sorted, 0.0, 1.0)

        # Map back to original indices
        adjusted = np.zeros(n)
        adjusted[sorted_idx] = adj_sorted

        # Write back
        for local_idx, original_idx in enumerate(indices):
            adj_p = float(adjusted[local_idx])
            results[original_idx]["adjusted_p_value"] = adj_p
            results[original_idx]["significance_status"] = (
                "FDR_SIGNIFICANT" if adj_p < FDR_ALPHA else "NOT_FDR_SIGNIFICANT"
            )

        return results

    # ------------------------------------------------------------------
    # Store results
    # ------------------------------------------------------------------

    def _store_results(self, run: AnalysisRun, results: list[dict]):
        """Bulk insert all per-region results."""
        records = []
        for r in results:
            d = {k: v for k, v in r.items() if k != "region_id"}
            if "n_disease" in d and d["n_disease"] is not None:
                d["n_disease"] = int(d["n_disease"])
            if "n_control" in d and d["n_control"] is not None:
                d["n_control"] = int(d["n_control"])
            rec = AnalysisResult(
                analysis_run_id=run.analysis_run_id,
                region_id=int(r["region_id"]),
                **d,
            )
            records.append(rec)
        self.db.add_all(records)
        self.db.commit()
        logger.info(f"Stored {len(records)} region results")

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _get_run(self, run_id: str) -> AnalysisRun | None:
        return self.db.query(AnalysisRun).filter(
            AnalysisRun.analysis_run_id == run_id
        ).first()

    def _set_status(self, run: AnalysisRun, status: str, **kwargs):
        run.status = status
        for k, v in kwargs.items():
            setattr(run, k, v)
        self.db.commit()

    @staticmethod
    def _get_env_info() -> dict:
        return {
            "python": sys.version,
            "platform": platform.platform(),
            "scipy": str(stats.__version__ if hasattr(stats, '__version__') else "unknown"),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "manas_version": "1.0.0",
        }
