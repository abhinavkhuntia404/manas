"""
Analysis API router.
POST /api/analyses          — submit an analysis job
GET  /api/analyses          — list analysis runs
GET  /api/analyses/{id}     — analysis detail + results
GET  /api/analyses/{id}/results — paginated per-region results
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from pydantic import BaseModel
import uuid
from datetime import datetime

from backend.database.session import get_db
from backend.models.orm import (
    AnalysisRun, AnalysisResult, DatasetVersion,
    BrainAtlas, MeasurementType, BrainRegion
)
from analysis.engine import AnalysisEngine
from configs.settings import get_settings

router = APIRouter()
settings = get_settings()

ANALYSIS_COUNTER_KEY = "manas_analysis_counter"


class AnalysisRequest(BaseModel):
    version_id: int
    disease: str = "Alzheimer's Disease"
    analysis_type: str = "AD_REGIONAL_COMPARISON"
    measurement_type_name: str
    covariates: list[str] = ["age", "sex"]
    random_seed: int = 42


def _generate_run_id(disease: str, db: Session) -> str:
    """Generate MANAS-AD-YYYY-NNNNN style run ID."""
    year = datetime.now().year
    prefix = "AD" if "alzheimer" in disease.lower() else "PD"
    count = db.query(AnalysisRun).filter(
        AnalysisRun.analysis_run_id.like(f"MANAS-{prefix}-{year}-%")
    ).count()
    return f"MANAS-{prefix}-{year}-{count+1:05d}"


@router.post("/")
def submit_analysis(
    req: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Submit a new analysis job. Prevents duplicate submissions."""
    # Check for duplicate
    existing = (
        db.query(AnalysisRun)
        .filter(
            AnalysisRun.version_id == req.version_id,
            AnalysisRun.disease == req.disease,
            AnalysisRun.analysis_type == req.analysis_type,
            AnalysisRun.status.in_(["QUEUED", "RUNNING", "COMPLETED"]),
        )
        .first()
    )
    if existing and existing.status in ("QUEUED", "RUNNING"):
        raise HTTPException(
            status_code=409,
            detail=f"Identical analysis already {existing.status}: {existing.analysis_run_id}",
        )

    # Verify version exists
    version = db.query(DatasetVersion).filter(DatasetVersion.version_id == req.version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail=f"Dataset version {req.version_id} not found")

    # Verify measurement type exists
    mtype = (
        db.query(MeasurementType)
        .filter(MeasurementType.name == req.measurement_type_name)
        .first()
    )
    if not mtype:
        raise HTTPException(
            status_code=404,
            detail=f"Measurement type '{req.measurement_type_name}' not found in database",
        )

    run_id = _generate_run_id(req.disease, db)

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
    db.add(run)
    db.commit()
    db.refresh(run)

    background_tasks.add_task(_run_analysis_background, run_id)

    return {
        "analysis_run_id": run_id,
        "status": "QUEUED",
        "message": "Analysis queued. Poll /api/analyses/{id} for status.",
        "is_synthetic": version.is_synthetic,
    }


def _run_analysis_background(run_id: str):
    """Execute the analysis in a background task."""
    from backend.database.session import SessionLocal
    db = SessionLocal()
    try:
        engine = AnalysisEngine(db, settings)
        engine.run(run_id)
    finally:
        db.close()


@router.get("/")
def list_analyses(
    db: Session = Depends(get_db),
    disease: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List analysis runs, newest first."""
    query = db.query(AnalysisRun)
    if disease:
        query = query.filter(AnalysisRun.disease.ilike(f"%{disease}%"))
    if status:
        query = query.filter(AnalysisRun.status == status)

    total = query.count()
    runs = query.order_by(desc(AnalysisRun.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "runs": [
            {
                "analysis_run_id": r.analysis_run_id,
                "analysis_type": r.analysis_type,
                "disease": r.disease,
                "status": r.status,
                "is_synthetic": r.is_synthetic,
                "n_total": r.n_total,
                "n_disease": r.n_disease,
                "n_control": r.n_control,
                "statistical_method": r.statistical_method,
                "correction_method": r.correction_method,
                "started_at": str(r.started_at) if r.started_at else None,
                "completed_at": str(r.completed_at) if r.completed_at else None,
            }
            for r in runs
        ],
    }


@router.get("/{run_id}")
def get_analysis(run_id: str, db: Session = Depends(get_db)):
    """Full analysis detail including reproducibility metadata."""
    run = db.query(AnalysisRun).filter(AnalysisRun.analysis_run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Analysis run {run_id} not found")

    return {
        "analysis_run_id": run.analysis_run_id,
        "analysis_type": run.analysis_type,
        "disease": run.disease,
        "status": run.status,
        "is_synthetic": run.is_synthetic,
        "statistical_method": run.statistical_method,
        "correction_method": run.correction_method,
        "effect_size_measure": run.effect_size_measure,
        "covariates": run.covariates,
        "parameters": run.parameters,
        "random_seed": run.random_seed,
        "n_total": run.n_total,
        "n_disease": run.n_disease,
        "n_control": run.n_control,
        "software_env": run.software_env,
        "code_commit": run.code_commit,
        "ingestion_version": run.ingestion_version,
        "preprocessing_version": run.preprocessing_version,
        "started_at": str(run.started_at) if run.started_at else None,
        "completed_at": str(run.completed_at) if run.completed_at else None,
        "error_message": run.error_message,
        "disclaimer": (
            "These results are statistical associations derived from analysis "
            "of research datasets. They do not constitute medical diagnosis or "
            "proof of biological causation."
        ),
    }


@router.get("/{run_id}/results")
def get_analysis_results(
    run_id: str,
    db: Session = Depends(get_db),
    significant_only: bool = Query(False),
    sort_by: str = Query("effect_size"),
    sort_dir: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
):
    """Paginated per-region results for an analysis run."""
    run = db.query(AnalysisRun).filter(AnalysisRun.analysis_run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Analysis run {run_id} not found")
    if run.status != "COMPLETED":
        return {"message": f"Analysis is {run.status}. Results not yet available.", "results": []}

    query = (
        db.query(AnalysisResult, BrainRegion)
        .join(BrainRegion, AnalysisResult.region_id == BrainRegion.region_id)
        .filter(AnalysisResult.analysis_run_id == run_id)
    )

    if significant_only:
        query = query.filter(AnalysisResult.significance_status == "FDR_SIGNIFICANT")

    # Sorting
    sort_col = getattr(AnalysisResult, sort_by, AnalysisResult.effect_size)
    if sort_dir == "asc":
        query = query.order_by(sort_col.asc().nullslast())
    else:
        query = query.order_by(sort_col.desc().nullslast())

    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "analysis_run_id": run_id,
        "is_synthetic": run.is_synthetic,
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": [
            {
                "region_id": region.region_id,
                "region_name": region.name,
                "hemisphere": region.hemisphere,
                "anatomical_category": region.anatomical_category,
                "n_disease": res.n_disease,
                "n_control": res.n_control,
                "disease_mean": res.disease_mean,
                "control_mean": res.control_mean,
                "mean_difference": res.mean_difference,
                "effect_size": res.effect_size,
                "effect_size_ci_lower": res.effect_size_ci_lower,
                "effect_size_ci_upper": res.effect_size_ci_upper,
                "p_value": res.p_value,
                "adjusted_p_value": res.adjusted_p_value,
                "significance_status": res.significance_status,
                "test_method": res.test_method,
            }
            for res, region in rows
        ],
    }
