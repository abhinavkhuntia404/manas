"""
One-step full database population script for MANAS.
Runs:
  1. Brain Region Ontology Ingestion (Allen Reference Atlas)
  2. OASIS Datasets Ingestion (OASIS-1 and OASIS-2)
  3. Literature Registry & Structured Evidence Claims Seeding
  4. Baseline Statistical Analyses (Whole-brain Volumetry and Cognitive Scores)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime
from backend.database.session import SessionLocal, create_tables
from backend.models.orm import Dataset, DatasetVersion, AnalysisRun, MeasurementType
from atlas.region_mapper import RegionMapper
from ingestion.allen_atlas import AllenAtlasIngester
from ingestion.oasis import OasisIngester
from literature.seed_evidence import seed_literature_database
from analysis.engine import AnalysisEngine

def populate_all():
    print("=== MANAS Database Initialization & Ingestion ===")
    create_tables()
    db = SessionLocal()
    try:
        # 1. Base regions
        print("[1/5] Ensuring Allen Aging canonical regions...")
        mapper = RegionMapper(db)
        mapper.ensure_allen_aging_regions()

        # 2. Complete Allen Reference Atlas
        print("[2/5] Ingesting Allen Reference Atlas ontology...")
        try:
            atlas_ingester = AllenAtlasIngester(db)
            atlas_ingester.run()
        except Exception as e:
            print(f"  Note: Atlas ontology step encountered: {e}")
            db.rollback()

        # 3. OASIS-1 and OASIS-2
        print("[3/5] Ingesting OASIS datasets...")
        # OASIS-1
        ds1 = db.query(Dataset).filter(Dataset.short_name == "oasis_1").first()
        if not ds1:
            ds1 = Dataset(
                name="OASIS-1 Cross-Sectional",
                short_name="oasis_1",
                source_org="Washington University, St. Louis",
                official_url="https://www.oasis-brains.org",
                access_type="OPEN_DIRECT",
                license="CC BY 4.0",
                primary_disease=["Alzheimer's Disease"],
                description="OASIS-1: Cross-Sectional MRI and Clinical Data (436 subjects)."
            )
            db.add(ds1)
            db.commit()
            db.refresh(ds1)

        v1 = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == ds1.dataset_id).first()
        if not v1:
            v1 = DatasetVersion(
                dataset_id=ds1.dataset_id,
                version_tag="OASIS-1-v1.0",
                download_date=datetime.utcnow(),
                is_synthetic=False,
                notes="Ingested from data/raw/oasis/oasis_cross_sectional.xlsx"
            )
            db.add(v1)
            db.commit()
            db.refresh(v1)
        if db.query(Subject).filter(Subject.version_id == v1.version_id).count() == 0:
            OasisIngester(db, v1.version_id, oasis_version="OASIS-1").run()

        # OASIS-2
        ds2 = db.query(Dataset).filter(Dataset.short_name == "oasis_2").first()
        if not ds2:
            ds2 = Dataset(
                name="OASIS-2 Longitudinal",
                short_name="oasis_2",
                source_org="Washington University, St. Louis",
                official_url="https://www.oasis-brains.org",
                access_type="OPEN_DIRECT",
                license="CC BY 4.0",
                primary_disease=["Alzheimer's Disease"],
                description="OASIS-2: Longitudinal MRI and Clinical Data."
            )
            db.add(ds2)
            db.commit()
            db.refresh(ds2)

        v2 = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == ds2.dataset_id).first()
        if not v2:
            v2 = DatasetVersion(
                dataset_id=ds2.dataset_id,
                version_tag="OASIS-2-v1.0",
                download_date=datetime.utcnow(),
                is_synthetic=False,
                notes="Ingested from data/raw/oasis/oasis_longitudinal_demographics.xlsx"
            )
            db.add(v2)
            db.commit()
            db.refresh(v2)
        if db.query(Subject).filter(Subject.version_id == v2.version_id).count() == 0:
            OasisIngester(db, v2.version_id, oasis_version="OASIS-2").run()

        # 4. Literature and Evidence Claims
        print("[4/5] Seeding literature papers and evidence claims...")
        seed_literature_database(db)

        # 5. Baseline Statistical Analyses
        print("[5/5] Checking baseline statistical analysis runs...")
        mtype_wb = db.query(MeasurementType).filter(MeasurementType.name == 'normalized_whole_brain_volume').first()
        if mtype_wb and v1:
            run_id = 'MANAS-AD-2026-00002'
            if not db.query(AnalysisRun).filter(AnalysisRun.analysis_run_id == run_id).first():
                run = AnalysisRun(
                    analysis_run_id=run_id,
                    analysis_type='AD_WHOLE_BRAIN_VOLUMETRY',
                    disease="Alzheimer's Disease",
                    version_id=v1.version_id,
                    measurement_type_id=mtype_wb.type_id,
                    covariates=['age', 'sex'],
                    random_seed=42,
                    status='QUEUED',
                    is_synthetic=False,
                    created_at=datetime.utcnow()
                )
                db.add(run)
                db.commit()
                AnalysisEngine(db).run(run_id)

        print("\n=== Population complete! MANAS database is fully initialized. ===")
    finally:
        db.close()

if __name__ == "__main__":
    populate_all()
