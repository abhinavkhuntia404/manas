"""
Synthetic data generator for Allen Aging schema.
Produces schema-identical data with is_synthetic = True clearly set.
Used for development and testing when real data is unavailable.
"""

import numpy as np
import pandas as pd
from typing import Tuple

REGIONS = ['FWM', 'HIP', 'PCx', 'TCx']

DIAGNOSIS_CHOICES = [
    "Alzheimer's Disease Type",
    "No Dementia",
    "No Dementia",   # weight toward control
    "Vascular",
    "Multiple Etiologies",
]

METRIC_COLUMNS = [
    'ihc_a_syn', 'ihc_tau2_ffpe', 'ihc_at8_ffpe', 'ihc_at8',
    'ihc_ptdp_43_ffpe', 'ihc_a_beta_ffpe', 'ihc_a_beta',
    'ihc_iba1_ffpe', 'ihc_gfap_ffpe',
    'ptau_ng_per_mg', 'vegf_pg_per_mg', 'ab42_over_ab40_ratio',
    'tnf_a_pg_per_mg', 'tau_ng_per_mg', 'il_10_pg_per_mg',
    'isoprostane_pg_per_mg', 'il_6_pg_per_mg', 'il_1b_pg_per_mg',
    'ptau_over_tau_ratio', 'il_4_pg_per_mg', 'rantes_pg_per_mg',
    'ab40_pg_per_mg', 'a_syn_pg_per_mg', 'ifn_g_pg_per_mg',
    'mcp_1_pg_per_mg', 'bdnf_pg_per_mg', 'mip_1a_pg_per_mg',
    'il_7_pg_per_mg', 'ab42_pg_per_mg',
]

# Effect sizes for synthetic AD vs Control (Cohen's d)
# Positive = higher in AD, Negative = lower in AD
SYNTHETIC_EFFECTS = {
    'ihc_at8_ffpe':   0.8,   # pTau — elevated in AD
    'ihc_a_beta_ffpe': 0.7,  # Aβ — elevated in AD
    'tau_ng_per_mg':  0.6,
    'ptau_ng_per_mg': 0.9,
    'ab42_pg_per_mg': 0.7,
    'ihc_a_syn':      0.3,
    'bdnf_pg_per_mg': -0.5,  # BDNF — reduced in AD
}


def generate_allen_aging_synthetic(
    n_subjects: int = 107,
    seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate schema-identical synthetic Allen Aging data.
    Returns (donors_df, metrics_df) with same column names as real data.
    """
    rng = np.random.default_rng(seed)

    n_ad = n_subjects // 2
    n_ctrl = n_subjects - n_ad

    # --- Donors ---
    donor_ids = [f"SYN_{i:05d}" for i in range(n_subjects)]
    diagnoses = (
        ["Alzheimer's Disease Type"] * n_ad +
        ["No Dementia"] * n_ctrl
    )
    ages = list(rng.integers(65, 98, size=n_ad)) + list(rng.integers(65, 98, size=n_ctrl))
    sexes = rng.choice(['M', 'F'], size=n_subjects).tolist()
    braak = (
        list(rng.integers(4, 7, size=n_ad)) +     # AD: higher Braak
        list(rng.integers(0, 3, size=n_ctrl))       # Ctrl: lower Braak
    )
    cerad = (
        list(rng.integers(2, 4, size=n_ad)) +
        list(rng.integers(0, 2, size=n_ctrl))
    )

    donors_df = pd.DataFrame({
        'donor_id': donor_ids,
        'name': [f"SYNTHETIC-{i:03d}" for i in range(n_subjects)],
        'age': ages,
        'sex': sexes,
        'apo_e4_allele': rng.choice(['Y', 'N'], size=n_subjects).tolist(),
        'education_years': rng.integers(8, 20, size=n_subjects).tolist(),
        'age_at_first_tbi': [0] * n_subjects,
        'longest_loc_duration': ['Unknown or N/A'] * n_subjects,
        'cerad': cerad,
        'num_tbi_w_loc': [0] * n_subjects,
        'dsm_iv_clinical_diagnosis': diagnoses,
        'control_set': rng.integers(1, 35, size=n_subjects).tolist(),
        'nincds_arda_diagnosis': [
            "Probable Alzheimer'S Disease" if d == "Alzheimer's Disease Type" else "No Dementia"
            for d in diagnoses
        ],
        'ever_tbi_w_loc': ['N'] * n_subjects,
        'race': ['White'] * n_subjects,
        'hispanic': ['Not Hispanic'] * n_subjects,
        'act_demented': ['Dementia' if d == "Alzheimer's Disease Type" else 'No Dementia' for d in diagnoses],
        'braak': braak,
        'nia_reagan': cerad,
    })

    # --- Metrics ---
    rows = []
    for i, donor_id in enumerate(donor_ids):
        is_ad = diagnoses[i] == "Alzheimer's Disease Type"
        for region in REGIONS:
            row = {
                'donor_id': donor_id,
                'donor_name': f"SYNTHETIC-{i:03d}",
                'structure_id': hash(region) % 100000,
                'structure_acronym': region,
            }
            for col in METRIC_COLUMNS:
                base_mean = abs(rng.normal(0.01, 0.005))
                effect = SYNTHETIC_EFFECTS.get(col, 0.0)
                if is_ad:
                    val = rng.normal(base_mean * (1 + effect * 0.3), base_mean * 0.2)
                else:
                    val = rng.normal(base_mean, base_mean * 0.2)
                # Inject some missing values (~5%)
                if rng.random() < 0.05:
                    row[col] = None
                else:
                    row[col] = max(0.0, float(val))
            rows.append(row)

    metrics_df = pd.DataFrame(rows)
    return donors_df, metrics_df
