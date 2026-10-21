"""
Ingestion trigger API router.
POST /api/ingestion/allen-aging  — trigger Allen Aging ingestion
POST /api/ingestion/allen-atlas  — trigger Allen Atlas ingestion
POST /api/ingestion/oasis        — trigger OASIS ingestion
GET  /api/ingestion/status/{run_id} — check processing run status
"""

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from backend.database.session import get_db
from backend.models.orm import Dataset, DatasetVersion, ProcessingRun

router = APIRouter()


@router.post("/allen-aging")
def trigger_allen_aging_ingestion(
    background_tasks: BackgroundTasks,
    is_synthetic: bool = True,
    db: Session = Depends(get_db),
):
    """
    Trigger ingestion of Allen Aging, Dementia & TBI Study data.
    is_synthetic=True uses the schema-identical synthetic demo dataset.
    is_synthetic=False requires real downloaded files in data/raw/allen_aging/.
    """
    # Find or create dataset record
    ds = db.query(Dataset).filter(Dataset.short_name == "allen_aging").first()
    if not ds:
        ds = Dataset(
            name="Allen Aging, Dementia and TBI Study",
            short_name="allen_aging",
            source_org="Allen Institute for Brain Science",
            official_url="https://aging.brain-map.org/download/index",
            access_type="OPEN_DIRECT",
            license="Allen Institute Terms of Use",
            primary_disease=["Alzheimer's Disease", "TBI"],
            description=(
                "De-identified clinical, protein quantification, and "
                "immunohistochemistry pathology data from 107 donors "
                "(55 dementia/AD, 52 reference controls)."
            ),
        )
        db.add(ds)
        db.commit()
        db.refresh(ds)

    tag = f"synthetic-{datetime.now().strftime('%Y%m%d')}" if is_synthetic else f"real-{datetime.now().strftime('%Y%m%d')}"
    version = DatasetVersion(
        dataset_id=ds.dataset_id,
        version_tag=tag,
        download_date=datetime.utcnow(),
        download_url="https://aging.brain-map.org/api/v2/data/query.csv?criteria=model::ApiTbiDonorDetail,rma::options[num_rows$eqall]",
        is_synthetic=is_synthetic,
        notes="Synthetic schema-identical demo data" if is_synthetic else "Real downloaded data",
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    proc_run = ProcessingRun(
        version_id=version.version_id,
        run_type="INGESTION",
        status="QUEUED",
        created_at=datetime.utcnow(),
    )
    db.add(proc_run)
    db.commit()
    db.refresh(proc_run)

    background_tasks.add_task(_ingest_allen_aging_background, proc_run.run_id, is_synthetic)

    return {
        "message": "Allen Aging ingestion queued",
        "processing_run_id": proc_run.run_id,
        "version_id": version.version_id,
        "version_tag": tag,
        "is_synthetic": is_synthetic,
        "note": (
            "Using SYNTHETIC demo data — not real scientific results."
            if is_synthetic
            else "Using REAL Allen Aging data. Ensure files are in data/raw/allen_aging/."
        ),
    }


@router.post("/allen-atlas")
def trigger_allen_atlas_ingestion(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger ingestion of Allen Human Brain Atlas region ontology."""
    background_tasks.add_task(_ingest_allen_atlas_background)
    return {
        "message": "Allen Human Brain Atlas atlas ingestion queued.",
        "note": "This populates the canonical brain_regions table.",
    }


@router.get("/status/{run_id}")
def get_processing_status(run_id: int, db: Session = Depends(get_db)):
    run = db.query(ProcessingRun).filter(ProcessingRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Processing run {run_id} not found")
    return {
        "run_id": run.run_id,
        "run_type": run.run_type,
        "status": run.status,
        "records_processed": run.records_processed,
        "records_rejected": run.records_rejected,
        "warnings": run.warnings,
        "errors": run.errors,
        "started_at": str(run.started_at) if run.started_at else None,
        "completed_at": str(run.completed_at) if run.completed_at else None,
    }


def _ingest_allen_aging_background(run_id: int, is_synthetic: bool):
    """Background task: run Allen Aging ingestion."""
    from backend.database.session import SessionLocal
    from ingestion.allen_aging import AllenAgingIngester
    db = SessionLocal()
    try:
        ingester = AllenAgingIngester(db, run_id, is_synthetic=is_synthetic)
        ingester.run()
    finally:
        db.close()


@router.post("/oasis")
def trigger_oasis_ingestion(
    background_tasks: BackgroundTasks,
    version: str = "OASIS-1",
    db: Session = Depends(get_db),
):
    """Trigger OASIS-1 or OASIS-2 ingestion from data/raw/oasis/."""
    ds = db.query(Dataset).filter(Dataset.short_name == version.lower().replace("-", "_")).first()
    if not ds:
        short = version.lower().replace("-", "_")
        ds = Dataset(
            name=f"OASIS {version}",
            short_name=short,
            source_org="Washington University, St. Louis",
            official_url="https://www.oasis-brains.org",
            access_type="OPEN_DIRECT",
            license="CC BY 4.0",
            primary_disease=["Alzheimer's Disease"],
            description=f"OASIS {version} brain MRI and clinical data.",
        )
        db.add(ds)
        db.commit()
        db.refresh(ds)

    tag = f"{version}-{datetime.now().strftime('%Y%m%d')}"
    v = DatasetVersion(
        dataset_id=ds.dataset_id,
        version_tag=tag,
        download_date=datetime.utcnow(),
        is_synthetic=False,
        notes=f"Ingested from data/raw/oasis/",
    )
    db.add(v)
    db.commit()
    db.refresh(v)

    background_tasks.add_task(_ingest_oasis_background, v.version_id, version)
    return {"message": f"{version} ingestion queued", "version_id": v.version_id, "version_tag": tag}


def _ingest_oasis_background(version_id: int, oasis_version: str):
    """Background task: run OASIS ingestion."""
    from backend.database.session import SessionLocal
    from ingestion.oasis import OasisIngester
    db = SessionLocal()
    try:
        ingester = OasisIngester(db, version_id, oasis_version=oasis_version)
        ingester.run()
    finally:
        db.close()


def _ingest_allen_atlas_background():
    """Background task: run Allen Atlas ontology ingestion."""
    from backend.database.session import SessionLocal
    from ingestion.allen_atlas import AllenAtlasIngester
    db = SessionLocal()
    try:
        ingester = AllenAtlasIngester(db)
        ingester.run()
    finally:
        db.close()
