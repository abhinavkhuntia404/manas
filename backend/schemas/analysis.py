"""
Pydantic Schemas for MANAS Analysis API.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class AnalysisCreateRequest(BaseModel):
    version_id: int = Field(..., description="ID of the dataset version to analyze")
    disease: str = Field("Alzheimer's Disease", description="Target disease phenotype")
    analysis_type: str = Field("AD_REGIONAL_COMPARISON", description="Analysis workflow identifier")
    measurement_type_name: str = Field(..., description="Canonical name of measurement type (e.g. ihc_at8_ffpe)")
    covariates: List[str] = Field(default_factory=lambda: ["age", "sex"], description="Covariates to adjust for")
    random_seed: int = Field(42, description="Random seed for bootstrap reproducibility")


class RegionResultItem(BaseModel):
    region_id: int
    region_name: str
    abbreviation: Optional[str] = None
    hemisphere: Optional[str] = None
    anatomical_category: Optional[str] = None
    lobe: Optional[str] = None
    n_disease: int
    n_control: int
    disease_mean: Optional[float] = None
    disease_median: Optional[float] = None
    disease_sd: Optional[float] = None
    control_mean: Optional[float] = None
    control_median: Optional[float] = None
    control_sd: Optional[float] = None
    mean_difference: Optional[float] = None
    effect_size: Optional[float] = None
    effect_size_ci_lower: Optional[float] = None
    effect_size_ci_upper: Optional[float] = None
    p_value: Optional[float] = None
    adjusted_p_value: Optional[float] = None
    significance_status: str
    test_method: Optional[str] = None
    test_statistic: Optional[float] = None
    degrees_of_freedom: Optional[float] = None
    notes: Optional[str] = None


class AnalysisDetailResponse(BaseModel):
    analysis_run_id: str
    analysis_type: str
    disease: str
    version_id: int
    measurement_type_id: Optional[int] = None
    measurement_type_name: Optional[str] = None
    status: str
    statistical_method: Optional[str] = None
    correction_method: Optional[str] = None
    effect_size_measure: Optional[str] = None
    covariates: List[str] = Field(default_factory=list)
    random_seed: Optional[int] = None
    n_total: Optional[int] = None
    n_disease: Optional[int] = None
    n_control: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    software_env: Optional[Dict[str, Any]] = None
    is_synthetic: bool = False
    error_message: Optional[str] = None
    results: List[RegionResultItem] = Field(default_factory=list)
