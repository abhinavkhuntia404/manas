"""
Analysis Service — Business logic for orchestrating and querying statistical analysis jobs.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.models.orm import (
    AnalysisRun, AnalysisResult, DatasetVersion,
    MeasurementType, BrainRegion
)
from analysis.engine import AnalysisEngine
from backend.schemas.analysis import AnalysisCreateRequest

logger = logging.getLogger("manas.backend.services.analysis")


class AnalysisService:
    def __init__(self, db: Session):
        self.db = db

    def generate_run_id(self, disease: str) -> str:
        year = datetime.utcnow().year
        prefix = "AD" if "alzheimer" in disease.lower() else "PD"
        count = self.db.query(AnalysisRun).filter(
            AnalysisRun.analysis_run_id.like(f"MANAS-{prefix}-{year}-%")
        ).count()
        return f"MANAS-{prefix}-{year}-{count+1:05d}"

    def create_and_enqueue(self, req: AnalysisCreateRequest) -> AnalysisRun:
        # Verify version
        version = self.db.query(DatasetVersion).filter(
            DatasetVersion.version_id == req.version_id
        ).first()
        if not version:
            raise ValueError(f"Dataset version {req.version_id} not found")

        # Verify measurement type
        mtype = self.db.query(MeasurementType).filter(
            MeasurementType.name == req.measurement_type_name
        ).first()
        if not mtype:
            raise ValueError(f"Measurement type '{req.measurement_type_name}' not found")

        # Check existing active run
        existing = self.db.query(AnalysisRun).filter(
            AnalysisRun.version_id == req.version_id,
            AnalysisRun.disease == req.disease,
            AnalysisRun.analysis_type == req.analysis_type,
            AnalysisRun.measurement_type_id == mtype.type_id,
            AnalysisRun.status.in_(["QUEUED", "RUNNING"])
        ).first()
        if existing:
            return existing

        run_id = self.generate_run_id(req.disease)
        run = AnalysisRun(
            analysis_run_id=run_id,
            analysis_type=req.analysis_type,
            disease=req.disease,
            version_id=req.version_id,
            measurement_type_id=mtype.type_id,
            covariates=req.covariates,
            parameters=req.model_dump(),
            random_seed=req.random_seed,
            status="QUEUED",
            is_synthetic=version.is_synthetic,
            created_at=datetime.utcnow(),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def execute_run(self, run_id: str):
        engine = AnalysisEngine(self.db)
        engine.run(run_id)

    def get_run_details(self, run_id: str) -> Optional[AnalysisRun]:
        return self.db.query(AnalysisRun).filter(
            AnalysisRun.analysis_run_id == run_id
        ).first()

    def get_results_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        rows = (
            self.db.query(AnalysisResult, BrainRegion)
            .join(BrainRegion, AnalysisResult.region_id == BrainRegion.region_id)
            .filter(AnalysisResult.analysis_run_id == run_id)
            .order_by(AnalysisResult.adjusted_p_value.asc().nullslast())
            .all()
        )
        output = []
        for res, reg in rows:
            output.append({
                "result_id": res.result_id,
                "region_id": res.region_id,
                "region_name": reg.name,
                "abbreviation": reg.abbreviation,
                "hemisphere": reg.hemisphere,
                "anatomical_category": reg.anatomical_category,
                "lobe": reg.lobe,
                "n_disease": res.n_disease or 0,
                "n_control": res.n_control or 0,
                "disease_mean": res.disease_mean,
                "disease_median": res.disease_median,
                "disease_sd": res.disease_sd,
                "control_mean": res.control_mean,
                "control_median": res.control_median,
                "control_sd": res.control_sd,
                "mean_difference": res.mean_difference,
                "effect_size": res.effect_size,
                "effect_size_ci_lower": res.effect_size_ci_lower,
                "effect_size_ci_upper": res.effect_size_ci_upper,
                "p_value": res.p_value,
                "adjusted_p_value": res.adjusted_p_value,
                "significance_status": res.significance_status,
                "test_method": res.test_method,
                "test_statistic": res.test_statistic,
                "degrees_of_freedom": res.degrees_of_freedom,
                "notes": res.notes,
            })
        return output
