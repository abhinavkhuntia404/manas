-- MANAS Database Initialization Script (PostgreSQL)
-- मनस् — Computational Brain Disease Mapping Platform

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Atlases
CREATE TABLE IF NOT EXISTS brain_atlases (
    atlas_id SERIAL PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    short_name VARCHAR(64) NOT NULL UNIQUE,
    version VARCHAR(64) NOT NULL,
    species VARCHAR(128) DEFAULT 'Homo sapiens',
    source_url TEXT,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Regions
CREATE TABLE IF NOT EXISTS brain_regions (
    region_id SERIAL PRIMARY KEY,
    atlas_id INTEGER NOT NULL REFERENCES brain_atlases(atlas_id),
    source_region_id VARCHAR(128),
    name VARCHAR(256) NOT NULL,
    abbreviation VARCHAR(64),
    hemisphere VARCHAR(16) CHECK (hemisphere IN ('left','right','bilateral','unknown')),
    parent_region_id INTEGER REFERENCES brain_regions(region_id),
    anatomical_category VARCHAR(128),
    lobe VARCHAR(128),
    mni_x FLOAT,
    mni_y FLOAT,
    mni_z FLOAT,
    depth INTEGER,
    is_leaf BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_regions_atlas ON brain_regions(atlas_id);
CREATE INDEX IF NOT EXISTS idx_regions_name ON brain_regions(name);

-- Region Mappings
CREATE TABLE IF NOT EXISTS region_mappings (
    mapping_id SERIAL PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_dataset VARCHAR(128),
    canonical_region_id INTEGER REFERENCES brain_regions(region_id),
    mapping_method VARCHAR(64),
    confidence VARCHAR(32) CHECK (confidence IN ('HIGH','MEDIUM','LOW','MANUAL_REQUIRED')),
    reviewer VARCHAR(128),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_region_mapping UNIQUE (source_name, source_dataset)
);

-- Datasets
CREATE TABLE IF NOT EXISTS datasets (
    dataset_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    short_name VARCHAR(64) NOT NULL UNIQUE,
    source_org VARCHAR(256),
    official_url TEXT,
    access_type VARCHAR(32) CHECK (access_type IN ('OPEN_DIRECT','OPEN_WITH_TERMS','REGISTRATION_REQUIRED','APPLICATION_REQUIRED','RESTRICTED','UNKNOWN')),
    license TEXT,
    primary_disease JSONB,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Dataset Versions
CREATE TABLE IF NOT EXISTS dataset_versions (
    version_id SERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL REFERENCES datasets(dataset_id),
    version_tag VARCHAR(128) NOT NULL,
    download_date TIMESTAMPTZ,
    download_url TEXT,
    checksum VARCHAR(256),
    is_synthetic BOOLEAN DEFAULT FALSE NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_dataset_version UNIQUE (dataset_id, version_tag)
);

-- Processing Runs
CREATE TABLE IF NOT EXISTS processing_runs (
    run_id SERIAL PRIMARY KEY,
    version_id INTEGER NOT NULL REFERENCES dataset_versions(version_id),
    run_type VARCHAR(64),
    status VARCHAR(32) CHECK (status IN ('QUEUED','RUNNING','COMPLETED','FAILED','CANCELLED')),
    records_processed INTEGER,
    records_rejected INTEGER,
    warnings JSONB,
    errors JSONB,
    log_path TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    ingestion_version VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Subjects
CREATE TABLE IF NOT EXISTS subjects (
    subject_id SERIAL PRIMARY KEY,
    version_id INTEGER NOT NULL REFERENCES dataset_versions(version_id),
    source_subject_id VARCHAR(256) NOT NULL,
    disease_status VARCHAR(64) NOT NULL,
    disease_confirmed BOOLEAN,
    age_at_entry FLOAT,
    sex VARCHAR(16) CHECK (sex IN ('M','F','Unknown')),
    education_years FLOAT,
    apoe4_carrier BOOLEAN,
    postmortem_interval_hours FLOAT,
    brain_weight_grams FLOAT,
    is_synthetic BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_subject_in_version UNIQUE (version_id, source_subject_id)
);

CREATE INDEX IF NOT EXISTS idx_subjects_disease ON subjects(disease_status);
CREATE INDEX IF NOT EXISTS idx_subjects_version ON subjects(version_id);

-- Measurement Types
CREATE TABLE IF NOT EXISTS measurement_types (
    type_id SERIAL PRIMARY KEY,
    name VARCHAR(256) NOT NULL UNIQUE,
    category VARCHAR(64),
    unit VARCHAR(64),
    description TEXT,
    source_assay VARCHAR(256)
);

-- Measurements
CREATE TABLE IF NOT EXISTS measurements (
    measurement_id BIGSERIAL PRIMARY KEY,
    version_id INTEGER NOT NULL REFERENCES dataset_versions(version_id),
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id),
    region_id INTEGER NOT NULL REFERENCES brain_regions(region_id),
    type_id INTEGER NOT NULL REFERENCES measurement_types(type_id),
    value FLOAT,
    unit VARCHAR(64),
    timepoint VARCHAR(64),
    source_variable VARCHAR(256),
    quality_flag VARCHAR(32) CHECK (quality_flag IN ('PASS','WARNING','FAIL','MISSING','NOT_MEASURED','NOT_APPLICABLE','FAILED_MEASUREMENT','UNAVAILABLE','EXCLUDED')),
    exclusion_reason TEXT,
    is_synthetic BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_measurements_subject ON measurements(subject_id);
CREATE INDEX IF NOT EXISTS idx_measurements_region ON measurements(region_id);
CREATE INDEX IF NOT EXISTS idx_measurements_type ON measurements(type_id);
CREATE INDEX IF NOT EXISTS idx_measurements_version ON measurements(version_id);
CREATE INDEX IF NOT EXISTS idx_measurements_quality ON measurements(quality_flag);

-- QC Results
CREATE TABLE IF NOT EXISTS qc_results (
    qc_id SERIAL PRIMARY KEY,
    processing_run_id INTEGER NOT NULL REFERENCES processing_runs(run_id),
    entity_type VARCHAR(64),
    entity_id INTEGER,
    check_name VARCHAR(256) NOT NULL,
    status VARCHAR(16) CHECK (status IN ('PASS','WARNING','FAIL')),
    message TEXT,
    affected_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Analysis Runs
CREATE TABLE IF NOT EXISTS analysis_runs (
    analysis_run_id VARCHAR(32) PRIMARY KEY,
    analysis_type VARCHAR(128) NOT NULL,
    disease VARCHAR(128) NOT NULL,
    version_id INTEGER NOT NULL REFERENCES dataset_versions(version_id),
    atlas_id INTEGER REFERENCES brain_atlases(atlas_id),
    measurement_type_id INTEGER REFERENCES measurement_types(type_id),
    statistical_method VARCHAR(128),
    correction_method VARCHAR(64),
    effect_size_measure VARCHAR(64),
    covariates JSONB,
    parameters JSONB,
    random_seed INTEGER,
    status VARCHAR(32) CHECK (status IN ('QUEUED','RUNNING','COMPLETED','FAILED','CANCELLED')),
    n_total INTEGER,
    n_disease INTEGER,
    n_control INTEGER,
    software_env JSONB,
    code_commit VARCHAR(64),
    ingestion_version VARCHAR(64),
    preprocessing_version VARCHAR(64),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    is_synthetic BOOLEAN DEFAULT FALSE NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_analysis_runs_status ON analysis_runs(status);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_disease ON analysis_runs(disease);

-- Analysis Results
CREATE TABLE IF NOT EXISTS analysis_results (
    result_id BIGSERIAL PRIMARY KEY,
    analysis_run_id VARCHAR(32) NOT NULL REFERENCES analysis_runs(analysis_run_id),
    region_id INTEGER NOT NULL REFERENCES brain_regions(region_id),
    n_disease INTEGER,
    n_control INTEGER,
    disease_mean FLOAT,
    disease_median FLOAT,
    disease_sd FLOAT,
    control_mean FLOAT,
    control_median FLOAT,
    control_sd FLOAT,
    mean_difference FLOAT,
    effect_size FLOAT,
    effect_size_ci_lower FLOAT,
    effect_size_ci_upper FLOAT,
    p_value FLOAT,
    adjusted_p_value FLOAT,
    significance_status VARCHAR(32),
    test_statistic FLOAT,
    degrees_of_freedom FLOAT,
    test_method VARCHAR(64),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_results_run ON analysis_results(analysis_run_id);
CREATE INDEX IF NOT EXISTS idx_results_region ON analysis_results(region_id);
CREATE INDEX IF NOT EXISTS idx_results_padj ON analysis_results(adjusted_p_value);
