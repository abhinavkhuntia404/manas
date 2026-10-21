"""
Unit tests for RegionMapper.
Verifies canonical mapping of Allen Aging structure acronyms (HIP, FWM, PCx, TCx) to BrainRegion records.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.orm import Base, BrainAtlas, BrainRegion
from atlas.region_mapper import RegionMapper


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    yield db
    db.close()


def test_ensure_allen_aging_regions(test_db):
    mapper = RegionMapper(test_db)
    mapper.ensure_allen_aging_regions()

    # Verify all 4 regions created
    regions = test_db.query(BrainRegion).all()
    acronyms = {r.abbreviation for r in regions}
    assert acronyms == {"HIP", "FWM", "PCx", "TCx"}

    hip = test_db.query(BrainRegion).filter(BrainRegion.abbreviation == "HIP").first()
    assert hip is not None
    assert hip.name == "Hippocampus"
    assert hip.anatomical_category == "limbic"


def test_map_region_lookup(test_db):
    mapper = RegionMapper(test_db)
    mapper.ensure_allen_aging_regions()

    region_id = mapper.map_region("HIP")
    assert region_id is not None

    # Idempotent: same region returns same ID
    assert mapper.map_region("HIP") == region_id

    # Unknown region returns None
    assert mapper.map_region("NON_EXISTENT_LOBE") is None
