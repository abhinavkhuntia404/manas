"""
MANAS Scientific Visualization Engine.
Produces publication-grade plots:
1. Forest Plot of Regional Effect Sizes with 95% Bootstrap CIs.
2. Grouped Pathology Box/Violin Plots across brain regions.
3. Volcano Plots (Effect Size vs -log10 Adjusted p-value).
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt


def plot_regional_forest(
    results: List[Dict[str, Any]],
    output_path: str,
    title: str = "Regional Effect Sizes (AD vs Control) — 95% Bootstrap CI"
) -> str:
    """
    Generates a scientific forest plot displaying regional effect sizes and bootstrap CIs.
    """
    if not results:
        return ""

    df = pd.DataFrame(results)
    # Filter valid effect sizes
    df = df.dropna(subset=["effect_size"]).sort_values("effect_size", ascending=True)

    if len(df) == 0:
        return ""

    fig, ax = plt.subplots(figsize=(8, max(4, len(df) * 0.8)), dpi=300)

    y_pos = np.arange(len(df))
    regions = df["region_name"].values if "region_name" in df.columns else df["region_id"].astype(str).values
    effects = df["effect_size"].values
    ci_lowers = df["effect_size_ci_lower"].fillna(df["effect_size"]).values
    ci_uppers = df["effect_size_ci_upper"].fillna(df["effect_size"]).values

    # Colors based on significance
    colors = [
        "#d9534f" if sig == "FDR_SIGNIFICANT" else "#6c757d"
        for sig in df.get("significance_status", ["NOT_TESTED"] * len(df))
    ]

    # Reference line at null effect (0.0)
    ax.axvline(0, color="#222222", linestyle="--", linewidth=1.2, alpha=0.7)

    # Plot confidence intervals
    for i, (eff, low, high, col) in enumerate(zip(effects, ci_lowers, ci_uppers, colors)):
        ax.plot([low, high], [i, i], color=col, linewidth=2.2, solid_capstyle="round")
        ax.scatter([eff], [i], color=col, s=70, zorder=3)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(regions, fontsize=10, fontweight=500)
    ax.set_xlabel("Standardized Effect Size (Cohen's d / Hedges' g)", fontsize=11, labelpad=8)
    ax.set_title(title, fontsize=12, fontweight=600, pad=12)

    # Subtle grid
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_volcano(
    results: List[Dict[str, Any]],
    output_path: str,
    alpha: float = 0.05,
    title: str = "Volcano Plot: Regional Pathology Differences"
) -> str:
    """
    Volcano plot: Effect size (X) vs -log10(Adjusted p-value) (Y).
    """
    if not results:
        return ""

    df = pd.DataFrame(results).dropna(subset=["effect_size", "adjusted_p_value"])
    if len(df) == 0:
        return ""

    df["log_padj"] = -np.log10(np.maximum(df["adjusted_p_value"], 1e-12))
    threshold_y = -np.log10(alpha)

    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)

    # Significance mask
    sig_mask = df["adjusted_p_value"] < alpha

    # Points
    ax.scatter(df.loc[~sig_mask, "effect_size"], df.loc[~sig_mask, "log_padj"],
               color="#888888", alpha=0.7, s=50, label="Not Significant")
    ax.scatter(df.loc[sig_mask, "effect_size"], df.loc[sig_mask, "log_padj"],
               color="#d9534f", alpha=0.9, s=70, label=f"FDR < {alpha}")

    # Threshold line
    ax.axhline(threshold_y, color="#e0a96d", linestyle="--", linewidth=1.2, label=f"α = {alpha}")

    # Annotate region names
    for _, row in df.iterrows():
        name = row.get("region_name", str(row["region_id"]))
        ax.annotate(name, (row["effect_size"], row["log_padj"]),
                    textcoords="offset points", xytext=(5, 5), fontsize=8)

    ax.set_xlabel("Effect Size (Cohen's d)", fontsize=11)
    ax.set_ylabel("-log10(Adjusted p-value)", fontsize=11)
    ax.set_title(title, fontsize=12, fontweight=600)
    ax.legend(frameon=True, fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path)
    plt.close(fig)
    return output_path
