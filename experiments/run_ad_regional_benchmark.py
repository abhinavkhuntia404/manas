"""
MANAS Benchmark Experiment: AD Regional Neuropathology Mapping.
Executes an end-to-end reproducible analysis on real Allen Aging donor data.
Quantifies pTau (AT8 IHC) differences across Hippocampus, Temporal Cortex, Parietal Cortex, and Frontal White Matter.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database.session import SessionLocal, create_tables
from backend.models.orm import Dataset, DatasetVersion, ProcessingRun, BrainRegion, AnalysisRun
from atlas.region_mapper import RegionMapper
from ingestion.allen_aging import AllenAgingIngester
from analysis.engine import AnalysisEngine
from visualization.plots import plot_regional_forest, plot_volcano
from literature.seed_evidence import seed_literature_database


def run_benchmark():
    print("=" * 70)
    print("MANAS — Computational Brain Disease Mapping Benchmark")
    print("Investigating Regional AT8 Phosphorylated Tau in Alzheimer's Disease")
    print("=" * 70)

    # 1. Initialize DB tables
    print("\n[1/5] Initializing Database & Ensuring Tables...")
    create_tables()
    db = SessionLocal()

    try:
        # Seed literature
        seed_literature_database(db)

        # 2. Ensure canonical regions exist
        print("\n[2/5] Registering Canonical Brain Regions (ARA)...")
        mapper = RegionMapper(db)
        mapper.ensure_allen_aging_regions()

        # 3. Check / Ingest Allen Aging real dataset
        print("\n[3/5] Verifying / Ingesting Real Allen Aging Dataset...")
        ds = db.query(Dataset).filter(Dataset.short_name == "allen_aging").first()
        if not ds:
            ds = Dataset(
                name="Allen Aging, Dementia and TBI Study",
                short_name="allen_aging",
                source_org="Allen Institute for Brain Science",
                official_url="https://aging.brain-map.org/download/index",
                access_type="OPEN_DIRECT",
                license="Allen Institute Terms of Use",
                primary_disease=["Alzheimer's Disease"],
                description="Postmortem IHC and protein quantifications in 107 aged donors across 4 brain structures."
            )
            db.add(ds)
            db.commit()
            db.refresh(ds)

        version = db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == ds.dataset_id,
            DatasetVersion.is_synthetic == False
        ).first()

        if not version:
            version = DatasetVersion(
                dataset_id=ds.dataset_id,
                version_tag="allen-aging-v1.0-real",
                download_date=datetime.utcnow(),
                is_synthetic=False,
                notes="Real postmortem donor measurements",
            )
            db.add(version)
            db.commit()
            db.refresh(version)

        proc_run = db.query(ProcessingRun).filter(
            ProcessingRun.version_id == version.version_id,
            ProcessingRun.status == "COMPLETED"
        ).first()

        if not proc_run:
            print("  Ingesting real Allen Aging CSVs from data/raw/allen_aging/...")
            proc_run = ProcessingRun(
                version_id=version.version_id,
                run_type="INGESTION",
                status="QUEUED",
                started_at=datetime.utcnow()
            )
            db.add(proc_run)
            db.commit()
            db.refresh(proc_run)

            ingester = AllenAgingIngester(db, proc_run.run_id, is_synthetic=False)
            ingester.run()
            print("  [OK] Real Allen Aging data ingested successfully.")
        else:
            print(f"  [OK] Found existing ingested dataset (version_id={version.version_id})")

        # 4. Configure and run Statistical Analysis
        print("\n[4/5] Executing Adaptive Statistical Analysis Engine...")
        run_id = f"MANAS-AD-{datetime.utcnow().year}-00001"
        existing_run = db.query(AnalysisRun).filter(AnalysisRun.analysis_run_id == run_id).first()
        if existing_run:
            db.delete(existing_run)
            db.commit()

        from backend.models.orm import MeasurementType
        mtype = db.query(MeasurementType).filter(MeasurementType.name == "ihc_at8_ffpe").first()
        if not mtype:
            raise ValueError("Measurement type 'ihc_at8_ffpe' not found in database.")

        analysis_run = AnalysisRun(
            analysis_run_id=run_id,
            analysis_type="AD_REGIONAL_COMPARISON",
            disease="Alzheimer's Disease",
            version_id=version.version_id,
            measurement_type_id=mtype.type_id,
            covariates=["age", "sex"],
            random_seed=42,
            status="QUEUED",
            is_synthetic=False,
            created_at=datetime.utcnow()
        )
        db.add(analysis_run)
        db.commit()

        engine = AnalysisEngine(db)
        engine.run(run_id)

        # 5. Fetch and report results
        print("\n[5/5] Compiling Findings & Scientific Visualizations...")
        from backend.models.orm import AnalysisResult
        results = (
            db.query(AnalysisResult, BrainRegion)
            .join(BrainRegion, AnalysisResult.region_id == BrainRegion.region_id)
            .filter(AnalysisResult.analysis_run_id == run_id)
            .order_by(AnalysisResult.adjusted_p_value.asc().nullslast())
            .all()
        )

        res_dicts = []
        rows = []
        for res, reg in results:
            d = {
                "region_name": reg.name,
                "abbreviation": reg.abbreviation,
                "n_ad": res.n_disease,
                "n_ctl": res.n_control,
                "mean_ad": round(res.disease_mean, 4) if res.disease_mean is not None else None,
                "mean_ctl": round(res.control_mean, 4) if res.control_mean is not None else None,
                "diff": round(res.mean_difference, 4) if res.mean_difference is not None else None,
                "effect_size": round(res.effect_size, 3) if res.effect_size is not None else None,
                "ci_lower": round(res.effect_size_ci_lower, 3) if res.effect_size_ci_lower is not None else None,
                "ci_upper": round(res.effect_size_ci_upper, 3) if res.effect_size_ci_upper is not None else None,
                "p_value": f"{res.p_value:.3e}" if res.p_value is not None else "N/A",
                "padj": f"{res.adjusted_p_value:.3e}" if res.adjusted_p_value is not None else "N/A",
                "method": res.test_method,
                "status": res.significance_status
            }
            rows.append(d)
            res_dicts.append({
                "region_id": res.region_id,
                "region_name": f"{reg.name} ({reg.abbreviation})",
                "effect_size": res.effect_size,
                "effect_size_ci_lower": res.effect_size_ci_lower,
                "effect_size_ci_upper": res.effect_size_ci_upper,
                "adjusted_p_value": res.adjusted_p_value,
                "significance_status": res.significance_status
            })

        print("\n" + "=" * 105)
        print(f"BENCHMARK RESULTS: Run ID {run_id}")
        print(f"Target: AT8 Phosphorylated Tau (ihc_at8_ffpe) | Seed: 42 | FDR alpha: 0.05")
        print("=" * 105)
        table_df = pd.DataFrame(rows)
        print(table_df.to_string(index=False))
        print("=" * 105)

        # Generate publication plots
        report_dir = Path("./data/reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        forest_path = str(report_dir / "ad_at8_forest_plot.png")
        volcano_path = str(report_dir / "ad_at8_volcano_plot.png")

        plot_regional_forest(res_dicts, forest_path, title="Allen Aging: AT8 pTau Regional Effect Sizes (AD vs Control)")
        plot_volcano(res_dicts, volcano_path, title="Allen Aging: AT8 pTau Regional Pathology Volcano Plot")

        print(f"\n[OK] Generated scientific forest plot:  {forest_path}")
        print(f"[OK] Generated scientific volcano plot: {volcano_path}")
        print("\nBenchmark experiment complete!")

    finally:
        db.close()


if __name__ == "__main__":
    run_benchmark()
