"""
Unit tests for MANAS Quality Control Pipeline.
Verifies that dirty or invalid clinical/measurement records trigger WARNING/FAIL flags
and clean records trigger PASS.
"""

import pytest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.orm import Base, ProcessingRun, Dataset, DatasetVersion, QCResult
from validation.qc_pipeline import QCPipeline


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    ds = Dataset(name="Test Dataset", short_name="test_ds")
    db.add(ds)
    db.flush()

    ver = DatasetVersion(dataset_id=ds.dataset_id, version_tag="v1.0")
    db.add(ver)
    db.flush()

    run = ProcessingRun(version_id=ver.version_id, run_type="QC", status="RUNNING")
    db.add(run)
    db.commit()

    yield db, run.run_id
    db.close()


def test_qc_clean_donors(test_db):
    db, run_id = test_db
    qc = QCPipeline(db, run_id)

    clean_df = pd.DataFrame({
        "donor_id": [1, 2, 3],
        "age": [75, 82, 68],
        "sex": ["M", "F", "M"],
        "dsm_iv_clinical_diagnosis": ["Alzheimer's Disease Type", "No Dementia", "No Dementia"],
        "act_demented": ["Dementia", "No Dementia", "No Dementia"],
        "braak": [5, 1, 2],
        "cerad": [3, 0, 0],
        "nincds_arda_diagnosis": ["Probable AD", "Control", "Control"],
    })

    qc.validate_donors(clean_df)
    results = db.query(QCResult).filter(QCResult.processing_run_id == run_id).all()
    # All checks should pass
    fails = [r for r in results if r.status == "FAIL"]
    assert len(fails) == 0


def test_qc_duplicate_donors(test_db):
    db, run_id = test_db
    qc = QCPipeline(db, run_id)

    duplicate_df = pd.DataFrame({
        "donor_id": [1, 1, 2],  # Duplicate donor_id = 1
        "age": [75, 75, 82],
        "sex": ["M", "M", "F"],
        "dsm_iv_clinical_diagnosis": ["Alzheimer's Disease Type", "Alzheimer's Disease Type", "No Dementia"],
        "act_demented": ["Dementia", "Dementia", "No Dementia"],
        "braak": [5, 5, 1],
        "cerad": [3, 3, 0],
        "nincds_arda_diagnosis": ["Probable AD", "Probable AD", "Control"],
    })

    qc.validate_donors(duplicate_df)
    dupe_check = db.query(QCResult).filter(
        QCResult.processing_run_id == run_id,
        QCResult.check_name == "duplicate_donors"
    ).first()

    assert dupe_check is not None
    assert dupe_check.status == "FAIL"
    assert dupe_check.affected_count == 1
