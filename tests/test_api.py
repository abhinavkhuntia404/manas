"""
API integration tests for MANAS FastAPI application.
Verifies health, datasets, brain regions, and literature endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database.session import create_tables, SessionLocal
from atlas.region_mapper import RegionMapper
from literature.seed_evidence import seed_literature_database


@pytest.fixture(scope="module")
def client():
    # Setup test DB tables
    create_tables()
    db = SessionLocal()
    mapper = RegionMapper(db)
    mapper.ensure_allen_aging_regions()
    seed_literature_database(db)
    db.close()

    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_regions_endpoint(client):
    response = client.get("/api/regions/")
    assert response.status_code == 200
    data = response.json()
    assert "regions" in data
    regions = data["regions"]
    assert len(regions) >= 4
    acronyms = {r["abbreviation"] for r in regions}
    assert "HIP" in acronyms


def test_literature_endpoint(client):
    response = client.get("/api/literature/")
    assert response.status_code == 200
    data = response.json()
    assert "papers" in data
    papers = data["papers"]
    assert len(papers) >= 1

    # Test filtering by disease
    filtered_resp = client.get("/api/literature/?disease=Alzheimer")
    assert filtered_resp.status_code == 200
    filtered_data = filtered_resp.json()
    assert len(filtered_data["papers"]) >= 1


def test_analyses_list_endpoint(client):
    response = client.get("/api/analyses/")
    assert response.status_code == 200
    data = response.json()
    assert "runs" in data
    assert "total" in data
