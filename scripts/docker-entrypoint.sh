#!/usr/bin/env bash
set -e

echo "=== MANAS Backend Starting ==="

# If PostgreSQL is configured, wait until it is ready
if [[ "$DATABASE_URL" == postgresql* ]]; then
    echo "Checking PostgreSQL connection..."
    python -c "
import sys, time, os
from sqlalchemy import create_engine
url = os.environ.get('DATABASE_URL', '')
for i in range(30):
    try:
        engine = create_engine(url, connect_args={'connect_timeout': 3})
        with engine.connect() as conn:
            print('PostgreSQL is ready and accepting connections.')
            sys.exit(0)
    except Exception as e:
        print(f'Waiting for PostgreSQL... ({i+1}/30)')
        time.sleep(2)
print('Error: Could not connect to PostgreSQL within 60s.')
sys.exit(1)
"
fi

# Ensure database tables exist
echo "Ensuring database schema exists..."
python -c "from backend.database.session import create_tables; create_tables(); print('Database tables verified.')"

# Seed canonical atlas regions if empty
python -c "
from backend.database.session import SessionLocal
from backend.models.orm import BrainRegion
from atlas.region_mapper import RegionMapper
from literature.seed_evidence import seed_literature_database
db = SessionLocal()
try:
    count = db.query(BrainRegion).count()
    if count == 0:
        print('Seeding canonical regions...')
        mapper = RegionMapper(db)
        mapper.ensure_allen_aging_regions()
        print('Canonical regions successfully seeded.')
    else:
        print(f'Brain regions already present ({count} regions).')
    seed_literature_database(db)
finally:
    db.close()
"

echo "=== Starting Application ==="
exec "$@"
