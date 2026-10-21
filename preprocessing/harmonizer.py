"""
Cohort Preprocessing and Harmonization Pipeline — MANAS.
Standardizes clinical variables, harmonizes demographic strata, and applies statistical outlier controls.
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Tuple


class DataHarmonizer:
    @staticmethod
    def filter_quality_measurements(
        df: pd.DataFrame,
        allowed_flags: Tuple[str, ...] = ("PASS", "WARNING")
    ) -> pd.DataFrame:
        """Filter measurements to research-grade quality flags."""
        if "quality_flag" in df.columns:
            return df[df["quality_flag"].isin(allowed_flags)].copy()
        return df.copy()

    @staticmethod
    def winsorize_outliers(
        series: pd.Series,
        lower_percentile: float = 0.01,
        upper_percentile: float = 0.99
    ) -> pd.Series:
        """
        Applies symmetric percentile winsorization to prevent measurement artifacts
        from distorting variance calculations.
        """
        vals = pd.to_numeric(series, errors="coerce")
        lower_bound = vals.quantile(lower_percentile)
        upper_bound = vals.quantile(upper_percentile)
        return vals.clip(lower=lower_bound, upper=upper_bound)

    @staticmethod
    def standardize_covariates(
        df: pd.DataFrame,
        continuous_cols: Optional[List[str]] = None,
        categorical_cols: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Z-scores continuous covariates and encodes categorical indicators (e.g. sex: M=1, F=0).
        """
        out = df.copy()
        if continuous_cols:
            for col in continuous_cols:
                if col in out.columns:
                    vals = pd.to_numeric(out[col], errors="coerce")
                    std = vals.std()
                    if std > 0:
                        out[f"{col}_z"] = (vals - vals.mean()) / std
                    else:
                        out[f"{col}_z"] = 0.0

        if categorical_cols:
            for col in categorical_cols:
                if col in out.columns:
                    if col.lower() == "sex":
                        out["sex_binary"] = out[col].map({"M": 1, "F": 0, "Male": 1, "Female": 0})
        return out
