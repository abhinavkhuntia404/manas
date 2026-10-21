"""
Datasets API router.
GET /api/datasets         — list all datasets with version info
GET /api/datasets/{id}    — dataset detail with QC status
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database.session import get_db
from backend.models.orm import Dataset, DatasetVersion, ProcessingRun

router = APIRouter()


@router.get("/")
def list_datasets(
    db: Session = Depends(get_db),
    access_type: Optional[str] = Query(None),
):
    """List all registered datasets with latest version info."""
    query = db.query(Dataset)
    if access_type:
        query = query.filter(Dataset.access_type == access_type)
    datasets = query.all()

    result = []
    for ds in datasets:
        latest = (
            db.query(DatasetVersion)
            .filter(DatasetVersion.dataset_id == ds.dataset_id)
            .order_by(DatasetVersion.created_at.desc())
            .first()
        )
        result.append({
            "dataset_id": ds.dataset_id,
            "name": ds.name,
            "short_name": ds.short_name,
            "source_org": ds.source_org,
            "official_url": ds.official_url,
            "access_type": ds.access_type,
            "license": ds.license,
            "primary_disease": ds.primary_disease,
            "description": ds.description,
            "latest_version": {
                "version_id": latest.version_id,
                "version_tag": latest.version_tag,
                "download_date": latest.download_date,
                "is_synthetic": latest.is_synthetic,
            } if latest else None,
        })
    return result


@router.get("/{dataset_id}")
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Dataset detail including all versions and latest QC summary."""
    ds = db.query(Dataset).filter(Dataset.dataset_id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

    versions = (
        db.query(DatasetVersion)
        .filter(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.created_at.desc())
        .all()
    )

    versions_data = []
    for v in versions:
        # Get latest processing run for this version
        latest_run = (
            db.query(ProcessingRun)
            .filter(ProcessingRun.version_id == v.version_id)
            .order_by(ProcessingRun.created_at.desc())
            .first()
        )
        versions_data.append({
            "version_id": v.version_id,
            "version_tag": v.version_tag,
            "download_date": str(v.download_date) if v.download_date else None,
            "checksum": v.checksum,
            "is_synthetic": v.is_synthetic,
            "notes": v.notes,
            "processing_status": latest_run.status if latest_run else "NOT_PROCESSED",
            "records_processed": latest_run.records_processed if latest_run else None,
            "records_rejected": latest_run.records_rejected if latest_run else None,
        })

    return {
        "dataset_id": ds.dataset_id,
        "name": ds.name,
        "short_name": ds.short_name,
        "source_org": ds.source_org,
        "official_url": ds.official_url,
        "access_type": ds.access_type,
        "license": ds.license,
        "primary_disease": ds.primary_disease,
        "description": ds.description,
        "versions": versions_data,
    }
