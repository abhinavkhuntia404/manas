# MANAS — मनस्
## Computational Brain Disease Mapping

> Research-grade computational neuroscience platform integrating publicly available
> human brain, molecular, pathological and clinical datasets to investigate
> Alzheimer's disease and Parkinson's disease.

**MANAS is NOT a startup product, AI chatbot, or medical device.**
It is a serious computational research platform.

---

## Quick Start

### Prerequisites
- Docker + Docker Compose
- Python 3.12+ (for standalone backend)
- Node.js 18+ (for standalone frontend)

### 1. Clone and start
```bash
git clone <repo>
cd manas
docker-compose up --build
```

Then open:
- **Frontend**: http://localhost:3000
- **API docs**: http://localhost:8000/api/docs
- **Health check**: http://localhost:8000/api/health

### 2. Ingest data

**Allen Aging (107 real donors — no registration needed):**
```bash
curl -X POST "http://localhost:8000/api/ingestion/allen-aging?is_synthetic=false"
```
Files must be in `data/raw/allen_aging/` — download from:
https://aging.brain-map.org/download/index

The download command (already done in this repo):
```bash
# DonorInformation.csv
curl "https://aging.brain-map.org/api/v2/data/query.csv?criteria=model::ApiTbiDonorDetail,rma::options[num_rows\$eqall]" -o data/raw/allen_aging/DonorInformation.csv

# ProteinAndPathologyQuantifications.csv
curl "https://aging.brain-map.org/api/v2/data/query.csv?criteria=model::ApiTbiDonorMetric,rma::options[num_rows\$eqall]" -o data/raw/allen_aging/ProteinAndPathologyQuantifications.csv
```

**OASIS-1 (436 subjects):**
```bash
# Place oasis_cross_sectional.xlsx in data/raw/oasis/
# Then:
curl -X POST "http://localhost:8000/api/ingestion/oasis?version=OASIS-1"
```

**Allen Atlas (brain region ontology):**
```bash
curl -X POST "http://localhost:8000/api/ingestion/allen-atlas"
```

### 3. Run an analysis

```bash
curl -X POST "http://localhost:8000/api/analyses/" \
  -H "Content-Type: application/json" \
  -d '{
    "version_id": 1,
    "disease": "Alzheimer'\''s Disease",
    "measurement_type_name": "ihc_at8_ffpe",
    "covariates": ["age", "sex"],
    "random_seed": 42
  }'
```

Poll status:
```bash
curl "http://localhost:8000/api/analyses/MANAS-AD-2026-00001"
```

Results:
```bash
curl "http://localhost:8000/api/analyses/MANAS-AD-2026-00001/results"
```

---

## Data Sources

| Dataset | Access | Registration | Downloaded |
|---------|--------|-------------|-----------|
| Allen Aging, Dementia & TBI | Open | ❌ None required | ✅ Yes |
| Allen Human Brain Atlas | Open | ❌ None required | Via API |
| OASIS-1 Cross-Sectional | Open (CC BY 4.0) | ❌ None required | ✅ Yes |
| OASIS-2 Longitudinal | Open (CC BY 4.0) | ❌ None required | ✅ Yes |

---

## Architecture

```
manas/
├── backend/
│   ├── main.py                  # FastAPI application
│   ├── models/orm.py            # 15-table SQLAlchemy schema
│   ├── database/session.py      # DB session factory
│   └── api/routes/              # health, datasets, regions, analyses, literature, ingestion
├── frontend/
│   └── src/app/                 # Next.js 14 App Router — 10 pages
├── analysis/
│   └── engine.py                # Statistical analysis pipeline
├── ingestion/
│   ├── allen_aging.py           # Allen Aging ingester
│   ├── allen_atlas.py           # Brain region ontology ingester
│   └── oasis.py                 # OASIS-1 and OASIS-2 ingester
├── atlas/
│   └── region_mapper.py         # Source region → canonical mapping
├── validation/
│   └── qc_pipeline.py           # PASS/WARNING/FAIL QC checks
├── configs/
│   └── settings.py              # Pydantic env config
├── data/
│   ├── raw/allen_aging/         # Downloaded Allen Aging CSVs
│   ├── raw/oasis/               # Downloaded OASIS XLSXs
│   └── synthetic/generator.py   # Schema-identical synthetic data
└── docker-compose.yml
```

---

## Statistical Pipeline

```
1. Normality test     → Shapiro-Wilk (n ≤ 50) or D'Agostino-Pearson (n > 50)
2. Test selection     → Student's t / Welch's t / Mann-Whitney U
3. Effect size        → Cohen's d (Hedges' g) or rank-biserial r
4. Confidence interval → Bootstrap percentile 95% CI (n=1000)
5. FDR correction     → Benjamini-Hochberg (α = 0.05)
6. Provenance         → All parameters, seed, software versions logged
```

Every result has a permanent `MANAS-AD-YYYY-NNNNN` ID for full reproducibility.

---

## Environment Variables

```env
DATABASE_URL=postgresql://manas:manas@db:5432/manas
ENVIRONMENT=development
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO
FDR_ALPHA=0.05
MIN_GROUP_SIZE=5
BOOTSTRAP_N=1000
DEFAULT_RANDOM_SEED=42
```

---

## Development (without Docker)

**Backend:**
```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Database:**
```bash
docker run -e POSTGRES_USER=manas -e POSTGRES_PASSWORD=manas -e POSTGRES_DB=manas \
  -p 5432:5432 postgres:16
```

---

## Scientific Disclaimer

MANAS is a computational research platform. Its results represent statistical analyses
of publicly available research datasets. They should not be interpreted as medical
diagnosis, clinical advice, treatment recommendations, or proof of biological causation.
All analyses are exploratory. Findings must be independently validated before drawing
scientific conclusions.

---

## Citation

If you use MANAS in your research:
```
MANAS — Computational Brain Disease Mapping Platform (2026).
Open-source research software. https://github.com/<repo>
Data: Allen Institute for Brain Science, OASIS (Washington University).
```

## License

MIT License. Data licenses: see individual datasets.
Allen Institute: Allen Institute Terms of Use.
OASIS: CC BY 4.0.
