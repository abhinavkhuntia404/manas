"""
Integration test for MANAS End-to-End Analysis Pipeline.
Exercises full lifecycle: Schema initialization -> Region mapping -> Data ingestion -> Statistical Engine -> Provenance.
"""

import pytest
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.orm import (
    Base, Dataset, DatasetVersion, Subject,
    MeasurementType, Measurement, BrainRegion,
    AnalysisRun, AnalysisResult
)
from atlas.region_mapper import RegionMapper
from analysis.engine import AnalysisEngine


@pytest.fixture
def integrated_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 1. Regions
    mapper = RegionMapper(db)
    mapper.ensure_allen_aging_regions()

    # 2. Dataset & Version
    ds = Dataset(name="Allen Aging Integration Test", short_name="allen_aging_test")
    db.add(ds)
    db.flush()

    ver = DatasetVersion(dataset_id=ds.dataset_id, version_tag="v1.0-test", is_synthetic=False)
    db.add(ver)
    db.flush()

    # 3. Measurement Type
    mtype = MeasurementType(
        name="ihc_at8_ffpe",
        category="PATHOLOGY",
        unit="area_fraction",
        description="AT8 phosphorylated tau immunohistochemistry"
    )
    db.add(mtype)
    db.flush()

    # 4. Subjects: 10 AD and 10 Controls
    np.random.seed(42)
    regions = db.query(BrainRegion).all()

    for i in range(1, 21):
        status = "AD" if i <= 10 else "CONTROL"
        sub = Subject(
            version_id=ver.version_id,
            source_subject_id=f"donor_{i}",
            disease_status=status,
            age_at_entry=75 + np.random.randint(-5, 10),
            sex="M" if i % 2 == 0 else "F",
            is_synthetic=False
        )
        db.add(sub)
        db.flush()

        # Generate measurements for each region
        for reg in regions:
            # If AD and Hippocampus/TCx, elevated pTau
            base_val = 0.5 if status == "CONTROL" else (3.5 if reg.abbreviation in ("HIP", "TCx") else 1.0)
            val = max(0.01, base_val + np.random.normal(0, 0.3))

            m = Measurement(
                version_id=ver.version_id,
                subject_id=sub.subject_id,
                region_id=reg.region_id,
                type_id=mtype.type_id,
                value=float(val),
                quality_flag="PASS",
                is_synthetic=False
            )
            db.add(m)

    db.commit()
    yield db, ver.version_id, mtype.type_id
    db.close()


def test_end_to_end_analysis_execution(integrated_db):
    db, version_id, mtype_id = integrated_db

    run_id = "MANAS-AD-TEST-00001"
    run = AnalysisRun(
        analysis_run_id=run_id,
        analysis_type="AD_REGIONAL_COMPARISON",
        disease="Alzheimer's Disease",
        version_id=version_id,
        measurement_type_id=mtype_id,
        covariates=["age", "sex"],
        random_seed=42,
        status="QUEUED",
        is_synthetic=False,
        created_at=datetime.utcnow()
    )
    db.add(run)
    db.commit()

    # Execute engine
    engine = AnalysisEngine(db)
    engine.run(run_id)

    # Validate run state
    completed_run = db.query(AnalysisRun).filter(AnalysisRun.analysis_run_id == run_id).first()
    assert completed_run.status == "COMPLETED"
    assert completed_run.n_total == 20
    assert completed_run.n_disease == 10
    assert completed_run.n_control == 10
    assert completed_run.software_env is not None

    # Validate results
    results = db.query(AnalysisResult).filter(AnalysisResult.analysis_run_id == run_id).all()
    assert len(results) == 4

    for res in results:
        assert res.disease_mean is not None
        assert res.control_mean is not None
        assert res.effect_size is not None
        assert res.adjusted_p_value is not None
        assert res.effect_size_ci_lower is not None
        assert res.effect_size_ci_upper is not None
        assert res.effect_size_ci_lower <= res.effect_size_ci_upper

    # Hippocampus should be significant with high effect size
    hip_region = db.query(BrainRegion).filter(BrainRegion.abbreviation == "HIP").first()
    hip_res = db.query(AnalysisResult).filter(
        AnalysisResult.analysis_run_id == run_id,
        AnalysisResult.region_id == hip_region.region_id
    ).first()

    assert hip_res is not None
    assert hip_res.effect_size > 2.0
    assert hip_res.adjusted_p_value < 0.05
    assert hip_res.significance_status == "FDR_SIGNIFICANT"
