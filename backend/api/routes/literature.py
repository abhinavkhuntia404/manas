"""
Literature API router.
GET /api/literature         — verified paper registry
GET /api/literature/{id}    — paper detail
GET /api/literature/evidence — evidence claims
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import cast, String
from typing import Optional
from backend.database.session import get_db
from backend.models.orm import LiteraturePaper, EvidenceClaim, ClaimPaper

router = APIRouter()


@router.get("/")
@router.get("/papers")
def list_papers(
    db: Session = Depends(get_db),
    disease: Optional[str] = Query(None),
    verified_only: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    query = db.query(LiteraturePaper)
    if disease:
        query = query.filter(cast(LiteraturePaper.disease, String).ilike(f"%{disease}%"))
    if verified_only:
        query = query.filter(LiteraturePaper.verification_status == "VERIFIED")

    total = query.count()
    papers = query.order_by(LiteraturePaper.year.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "papers": [_paper_summary(p) for p in papers],
    }


@router.get("/evidence")
@router.get("/evidence-claims")
def list_evidence(
    db: Session = Depends(get_db),
    disease: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    query = db.query(EvidenceClaim)
    if disease:
        query = query.filter(EvidenceClaim.disease == disease)
    if status:
        query = query.filter(EvidenceClaim.evidence_status == status)

    claims = query.all()
    result = []
    for c in claims:
        supporting = [
            _paper_summary(cp.paper)
            for cp in c.claim_links if cp.relationship_type == "SUPPORTS"
        ]
        contradicting = [
            _paper_summary(cp.paper)
            for cp in c.claim_links if cp.relationship_type == "CONTRADICTS"
        ]
        result.append({
            "claim_id": c.claim_id,
            "claim_text": c.claim_text,
            "disease": c.disease,
            "region_id": c.region_id,
            "evidence_status": c.evidence_status,
            "manas_result_summary": c.manas_result_summary,
            "supporting_papers": supporting,
            "contradicting_papers": contradicting,
        })
    return result


@router.get("/{paper_id}")
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(LiteraturePaper).filter(LiteraturePaper.paper_id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")
    return _paper_detail(paper)


def _paper_summary(p: LiteraturePaper) -> dict:
    return {
        "paper_id": p.paper_id,
        "title": p.title,
        "authors": p.authors[:3] if p.authors else [],
        "year": p.year,
        "journal": p.journal,
        "doi": p.doi,
        "disease": p.disease,
        "verification_status": p.verification_status,
    }


def _paper_detail(p: LiteraturePaper) -> dict:
    return {
        "paper_id": p.paper_id,
        "title": p.title,
        "authors": p.authors,
        "year": p.year,
        "journal": p.journal,
        "doi": p.doi,
        "pubmed_id": p.pubmed_id,
        "url": p.url,
        "disease": p.disease,
        "brain_regions": p.brain_regions,
        "datasets_used": p.datasets_used,
        "sample_size": p.sample_size,
        "method": p.method,
        "main_finding": p.main_finding,
        "limitations": p.limitations,
        "verification_status": p.verification_status,
        "verified_via": p.verified_via,
    }
