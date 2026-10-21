"""
Biomarker Feature Engineering — MANAS Computational Pathology.
Calculates hyperphosphorylation ratios, composite pathology burden, and regional vulnerability indices.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any


def compute_tau_phosphorylation_ratio(df: pd.DataFrame, ptau_col: str = "ptau_ng_per_mg", total_tau_col: str = "tau_ng_per_mg") -> pd.Series:
    """
    Calculates pTau / total-Tau phosphorylation ratio.
    Hyperphosphorylation is the key driver of neurofibrillary tangle formation.
    """
    if ptau_col not in df.columns or total_tau_col not in df.columns:
        return pd.Series(np.nan, index=df.index)
    
    total = pd.to_numeric(df[total_tau_col], errors="coerce")
    ptau = pd.to_numeric(df[ptau_col], errors="coerce")
    
    # Avoid division by zero
    ratio = np.where(total > 0, ptau / total, np.nan)
    return pd.Series(ratio, index=df.index, name="ptau_ratio")


def compute_composite_pathology_score(df: pd.DataFrame, at8_col: str = "ihc_at8_ffpe", abeta_col: str = "ihc_a_beta_ffpe") -> pd.Series:
    """
    Calculates standardized Z-score composite pathology burden (AT8 pTau + Amyloid-beta).
    """
    series_list = []
    for col in [at8_col, abeta_col]:
        if col in df.columns:
            vals = pd.to_numeric(df[col], errors="coerce")
            std = vals.std()
            if std > 0:
                z = (vals - vals.mean()) / std
                series_list.append(z)
    
    if not series_list:
        return pd.Series(np.nan, index=df.index, name="composite_pathology_z")
    
    composite = pd.concat(series_list, axis=1).mean(axis=1)
    composite.name = "composite_pathology_z"
    return composite


def map_braak_staging(braak_series: pd.Series) -> pd.DataFrame:
    """
    Maps Braak staging numerical/string ratings (Arabic or Roman numerals) to standardized stage categories:
    - Stage 0: None
    - Stages I-II: Transentorhinal
    - Stages III-IV: Limbic
    - Stages V-VI: Isocortical / Neocortical
    """
    roman_map = {
        "VI": 6, "V": 5, "IV": 4, "III": 3, "II": 2, "I": 1, "0": 0
    }

    def parse_value(raw):
        if pd.isna(raw):
            return np.nan
        s = str(raw).strip().upper()
        # Check Roman numerals
        for r, val in roman_map.items():
            if re.search(r'\b' + r + r'\b', s) or s == r:
                return float(val)
        # Check digits
        m = re.search(r'(\d+)', s)
        if m:
            return float(m.group(1))
        return np.nan

    import re
    numeric = braak_series.apply(parse_value)

    def categorize(val):
        if pd.isna(val):
            return "UNKNOWN"
        val = int(val)
        if val == 0:
            return "STAGE_0_NONE"
        elif val in (1, 2):
            return "STAGE_I_II_TRANSENTORHINAL"
        elif val in (3, 4):
            return "STAGE_III_IV_LIMBIC"
        elif val in (5, 6):
            return "STAGE_V_VI_ISOCORTICAL"
        return "UNKNOWN"

    categories = numeric.apply(categorize)
    return pd.DataFrame({
        "braak_numeric": numeric,
        "braak_anatomical_stage": categories,
    }, index=braak_series.index)
