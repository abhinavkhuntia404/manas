"""
Brain Regions API router.
GET /api/regions           — paginated region list
GET /api/regions/{id}      — region detail with latest analysis result
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from backend.database.session import get_db
from backend.models.orm import BrainRegion, BrainAtlas, AnalysisResult, AnalysisRun

router = APIRouter()


@router.get("/")
def list_regions(
    db: Session = Depends(get_db),
    atlas_id: Optional[int] = Query(None),
    hemisphere: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
):
    """List canonical brain regions with optional filtering."""
    query = db.query(BrainRegion)
    if atlas_id:
        query = query.filter(BrainRegion.atlas_id == atlas_id)
    if hemisphere:
        query = query.filter(BrainRegion.hemisphere == hemisphere)
    if category:
        query = query.filter(BrainRegion.anatomical_category == category)
    if search:
        query = query.filter(BrainRegion.name.ilike(f"%{search}%"))

    total = query.count()
    regions = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "regions": [
            {
                "region_id": r.region_id,
                "name": r.name,
                "abbreviation": r.abbreviation,
                "hemisphere": r.hemisphere,
                "anatomical_category": r.anatomical_category,
                "lobe": r.lobe,
                "atlas_id": r.atlas_id,
                "parent_region_id": r.parent_region_id,
                "is_leaf": r.is_leaf,
            }
            for r in regions
        ],
    }


@router.get("/{region_id}")
def get_region(region_id: int, db: Session = Depends(get_db)):
    """Region detail including latest analysis results for all diseases."""
    region = db.query(BrainRegion).filter(BrainRegion.region_id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail=f"Region {region_id} not found")

    atlas = db.query(BrainAtlas).filter(BrainAtlas.atlas_id == region.atlas_id).first()

    # Get latest completed analysis results for this region
    analysis_results = (
        db.query(AnalysisResult, AnalysisRun)
        .join(AnalysisRun, AnalysisResult.analysis_run_id == AnalysisRun.analysis_run_id)
        .filter(
            AnalysisResult.region_id == region_id,
            AnalysisRun.status == "COMPLETED",
        )
        .order_by(AnalysisRun.completed_at.desc())
        .limit(10)
        .all()
    )

    results_data = [
        {
            "analysis_run_id": run.analysis_run_id,
            "disease": run.disease,
            "is_synthetic": run.is_synthetic,
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
        for res, run in analysis_results
    ]

    parent = None
    if region.parent_region_id:
        pr = db.query(BrainRegion).filter(BrainRegion.region_id == region.parent_region_id).first()
        parent = {"region_id": pr.region_id, "name": pr.name} if pr else None

    return {
        "region_id": region.region_id,
        "name": region.name,
        "abbreviation": region.abbreviation,
        "hemisphere": region.hemisphere,
        "anatomical_category": region.anatomical_category,
        "lobe": region.lobe,
        "mni_x": region.mni_x,
        "mni_y": region.mni_y,
        "mni_z": region.mni_z,
        "is_leaf": region.is_leaf,
        "depth": region.depth,
        "atlas": {
            "atlas_id": atlas.atlas_id,
            "name": atlas.name,
            "version": atlas.version,
        } if atlas else None,
        "parent": parent,
        "analysis_results": results_data,
    }
