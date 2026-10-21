"""
SQLAlchemy ORM Models — MANAS Data Schema
All tables follow the canonical V1 schema.
is_synthetic=True on any record prevents it from appearing in
scientific result pages without an explicit DEMO DATA banner.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer,
    String, Text, BigInteger, UniqueConstraint, CheckConstraint,
    Index, JSON
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# ATLAS & REGIONS
# ---------------------------------------------------------------------------

class BrainAtlas(Base):
    __tablename__ = "brain_atlases"

    atlas_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False)
    short_name = Column(String(64), nullable=False, unique=True)
    version = Column(String(64), nullable=False)
    species = Column(String(128), default="Homo sapiens")
    source_url = Column(Text)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    regions = relationship("BrainRegion", back_populates="atlas")


class BrainRegion(Base):
    __tablename__ = "brain_regions"

    region_id = Column(Integer, primary_key=True, autoincrement=True)
    atlas_id = Column(Integer, ForeignKey("brain_atlases.atlas_id"), nullable=False)
    source_region_id = Column(String(128))        # Atlas-internal ID
    name = Column(String(256), nullable=False)
    abbreviation = Column(String(64))
    hemisphere = Column(String(16),
        CheckConstraint("hemisphere IN ('left','right','bilateral','unknown')"))
    parent_region_id = Column(Integer, ForeignKey("brain_regions.region_id"))
    anatomical_category = Column(String(128))     # limbic, cortical, subcortical, ...
    lobe = Column(String(128))
    mni_x = Column(Float)
    mni_y = Column(Float)
    mni_z = Column(Float)
    depth = Column(Integer)                        # Hierarchy depth
    is_leaf = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    atlas = relationship("BrainAtlas", back_populates="regions")
    parent = relationship("BrainRegion", remote_side="BrainRegion.region_id")
    children = relationship("BrainRegion", back_populates="parent")
    mappings = relationship("RegionMapping", back_populates="canonical_region")
    measurements = relationship("Measurement", back_populates="region")
    analysis_results = relationship("AnalysisResult", back_populates="region")

    __table_args__ = (
        Index("idx_regions_atlas", "atlas_id"),
        Index("idx_regions_name", "name"),
    )


class RegionMapping(Base):
    """Maps raw source strings → canonical brain regions."""
    __tablename__ = "region_mappings"

    mapping_id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(Text, nullable=False)
    source_dataset = Column(String(128))
    canonical_region_id = Column(Integer, ForeignKey("brain_regions.region_id"))
    mapping_method = Column(String(64))           # exact, substring, manual, ambiguous
    confidence = Column(String(32),
        CheckConstraint("confidence IN ('HIGH','MEDIUM','LOW','MANUAL_REQUIRED')"))
    reviewer = Column(String(128))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    canonical_region = relationship("BrainRegion", back_populates="mappings")

    __table_args__ = (
        UniqueConstraint("source_name", "source_dataset", name="uq_region_mapping"),
    )


# ---------------------------------------------------------------------------
# DATASET REGISTRY & PROVENANCE
# ---------------------------------------------------------------------------

class Dataset(Base):
    __tablename__ = "datasets"

    dataset_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    short_name = Column(String(64), nullable=False, unique=True)
    source_org = Column(String(256))
    official_url = Column(Text)
    access_type = Column(String(32),
        CheckConstraint("access_type IN ('OPEN_DIRECT','OPEN_WITH_TERMS',"
                        "'REGISTRATION_REQUIRED','APPLICATION_REQUIRED',"
                        "'RESTRICTED','UNKNOWN')"))
    license = Column(Text)
    primary_disease = Column(JSON, default=list)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    versions = relationship("DatasetVersion", back_populates="dataset")


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    version_id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("datasets.dataset_id"), nullable=False)
    version_tag = Column(String(128), nullable=False)
    download_date = Column(DateTime(timezone=True))
    download_url = Column(Text)
    checksum = Column(String(256))
    is_synthetic = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    dataset = relationship("Dataset", back_populates="versions")
    files = relationship("DatasetFile", back_populates="version")
    processing_runs = relationship("ProcessingRun", back_populates="version")
    subjects = relationship("Subject", back_populates="version")
    measurements = relationship("Measurement", back_populates="version")
    analysis_runs = relationship("AnalysisRun", back_populates="version")

    __table_args__ = (
        UniqueConstraint("dataset_id", "version_tag", name="uq_dataset_version"),
    )


class DatasetFile(Base):
    __tablename__ = "dataset_files"

    file_id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey("dataset_versions.version_id"), nullable=False)
    filename = Column(Text, nullable=False)
    file_path = Column(Text)
    checksum = Column(String(256))
    file_size_bytes = Column(BigInteger)
    file_type = Column(String(64))
    description = Column(Text)

    version = relationship("DatasetVersion", back_populates="files")


class ProcessingRun(Base):
    __tablename__ = "processing_runs"

    run_id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey("dataset_versions.version_id"), nullable=False)
    run_type = Column(String(64))                 # INGESTION, VALIDATION, QC, PREPROCESSING
    status = Column(String(32),
        CheckConstraint("status IN ('QUEUED','RUNNING','COMPLETED','FAILED','CANCELLED')"))
    records_processed = Column(Integer)
    records_rejected = Column(Integer)
    warnings = Column(JSON)
    errors = Column(JSON)
    log_path = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    ingestion_version = Column(String(64))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    version = relationship("DatasetVersion", back_populates="processing_runs")
    qc_results = relationship("QCResult", back_populates="processing_run")


# ---------------------------------------------------------------------------
# SUBJECTS & CLINICAL
# ---------------------------------------------------------------------------

class Subject(Base):
    __tablename__ = "subjects"

    subject_id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey("dataset_versions.version_id"), nullable=False)
    source_subject_id = Column(String(256), nullable=False)
    disease_status = Column(String(64), nullable=False)  # AD, CONTROL, MCI, UNKNOWN
    disease_confirmed = Column(Boolean)
    age_at_entry = Column(Float)
    sex = Column(String(16), CheckConstraint("sex IN ('M','F','Unknown')"))
    education_years = Column(Float)
    apoe4_carrier = Column(Boolean)
    postmortem_interval_hours = Column(Float)
    brain_weight_grams = Column(Float)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    version = relationship("DatasetVersion", back_populates="subjects")
    measurements = relationship("Measurement", back_populates="subject")
    clinical_variables = relationship("ClinicalVariable", back_populates="subject")

    __table_args__ = (
        UniqueConstraint("version_id", "source_subject_id", name="uq_subject_in_version"),
        Index("idx_subjects_disease", "disease_status"),
        Index("idx_subjects_version", "version_id"),
    )


class ClinicalVariable(Base):
    __tablename__ = "clinical_variables"

    var_id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("subjects.subject_id"), nullable=False)
    variable_name = Column(String(256), nullable=False)
    variable_value = Column(Text)
    numeric_value = Column(Float)
    unit = Column(String(64))
    timepoint = Column(String(64))
    source_variable = Column(String(256))
    notes = Column(Text)

    subject = relationship("Subject", back_populates="clinical_variables")


# ---------------------------------------------------------------------------
# MEASUREMENTS
# ---------------------------------------------------------------------------

class MeasurementType(Base):
    __tablename__ = "measurement_types"

    type_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False, unique=True)
    category = Column(String(64))        # PATHOLOGY, GENE_EXPRESSION, CLINICAL
    unit = Column(String(64))
    description = Column(Text)
    source_assay = Column(String(256))

    measurements = relationship("Measurement", back_populates="measurement_type")


class Measurement(Base):
    __tablename__ = "measurements"

    measurement_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey("dataset_versions.version_id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.subject_id"), nullable=False)
    region_id = Column(Integer, ForeignKey("brain_regions.region_id"), nullable=False)
    type_id = Column(Integer, ForeignKey("measurement_types.type_id"), nullable=False)
    value = Column(Float)
    unit = Column(String(64))
    timepoint = Column(String(64))
    source_variable = Column(String(256))
    quality_flag = Column(String(32),
        CheckConstraint("quality_flag IN ('PASS','WARNING','FAIL',"
                        "'MISSING','NOT_MEASURED','NOT_APPLICABLE',"
                        "'FAILED_MEASUREMENT','UNAVAILABLE','EXCLUDED')"))
    exclusion_reason = Column(Text)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    version = relationship("DatasetVersion", back_populates="measurements")
    subject = relationship("Subject", back_populates="measurements")
    region = relationship("BrainRegion", back_populates="measurements")
    measurement_type = relationship("MeasurementType", back_populates="measurements")

    __table_args__ = (
        Index("idx_measurements_subject", "subject_id"),
        Index("idx_measurements_region", "region_id"),
        Index("idx_measurements_type", "type_id"),
        Index("idx_measurements_version", "version_id"),
        Index("idx_measurements_quality", "quality_flag"),
    )


# ---------------------------------------------------------------------------
# QC RESULTS
# ---------------------------------------------------------------------------

class QCResult(Base):
    __tablename__ = "qc_results"

    qc_id = Column(Integer, primary_key=True, autoincrement=True)
    processing_run_id = Column(Integer, ForeignKey("processing_runs.run_id"), nullable=False)
    entity_type = Column(String(64))     # SUBJECT, MEASUREMENT, REGION, DATASET
    entity_id = Column(Integer)
    check_name = Column(String(256), nullable=False)
    status = Column(String(16), CheckConstraint("status IN ('PASS','WARNING','FAIL')"))
    message = Column(Text)
    affected_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    processing_run = relationship("ProcessingRun", back_populates="qc_results")


# ---------------------------------------------------------------------------
# ANALYSIS RUNS & RESULTS
# ---------------------------------------------------------------------------

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    analysis_run_id = Column(String(32), primary_key=True)   # MANAS-AD-2026-00001
    analysis_type = Column(String(128), nullable=False)
    disease = Column(String(128), nullable=False)
    version_id = Column(Integer, ForeignKey("dataset_versions.version_id"), nullable=False)
    atlas_id = Column(Integer, ForeignKey("brain_atlases.atlas_id"))
    measurement_type_id = Column(Integer, ForeignKey("measurement_types.type_id"))
    statistical_method = Column(String(128))
    correction_method = Column(String(64))
    effect_size_measure = Column(String(64))
    covariates = Column(JSON, default=list)
    parameters = Column(JSON)
    random_seed = Column(Integer)
    status = Column(String(32),
        CheckConstraint("status IN ('QUEUED','RUNNING','COMPLETED','FAILED','CANCELLED')"))
    n_total = Column(Integer)
    n_disease = Column(Integer)
    n_control = Column(Integer)
    software_env = Column(JSON)
    code_commit = Column(String(64))
    ingestion_version = Column(String(64))
    preprocessing_version = Column(String(64))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    is_synthetic = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    version = relationship("DatasetVersion", back_populates="analysis_runs")
    results = relationship("AnalysisResult", back_populates="analysis_run")

    __table_args__ = (
        Index("idx_analysis_runs_status", "status"),
        Index("idx_analysis_runs_disease", "disease"),
    )


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    result_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    analysis_run_id = Column(String(32), ForeignKey("analysis_runs.analysis_run_id"), nullable=False)
    region_id = Column(Integer, ForeignKey("brain_regions.region_id"), nullable=False)
    n_disease = Column(Integer)
    n_control = Column(Integer)
    disease_mean = Column(Float)
    disease_median = Column(Float)
    disease_sd = Column(Float)
    control_mean = Column(Float)
    control_median = Column(Float)
    control_sd = Column(Float)
    mean_difference = Column(Float)
    effect_size = Column(Float)
    effect_size_ci_lower = Column(Float)
    effect_size_ci_upper = Column(Float)
    p_value = Column(Float)
    adjusted_p_value = Column(Float)
    significance_status = Column(String(32))  # FDR_SIGNIFICANT, NOT_SIGNIFICANT, INSUFFICIENT_DATA, NOT_TESTED
    test_statistic = Column(Float)
    degrees_of_freedom = Column(Float)
    test_method = Column(String(64))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    analysis_run = relationship("AnalysisRun", back_populates="results")
    region = relationship("BrainRegion", back_populates="analysis_results")

    __table_args__ = (
        Index("idx_results_run", "analysis_run_id"),
        Index("idx_results_region", "region_id"),
        Index("idx_results_padj", "adjusted_p_value"),
    )


# ---------------------------------------------------------------------------
# LITERATURE REGISTRY
# ---------------------------------------------------------------------------

class LiteraturePaper(Base):
    __tablename__ = "literature_papers"

    paper_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    authors = Column(JSON, default=list)
    year = Column(Integer)
    journal = Column(String(512))
    doi = Column(String(256), unique=True)
    pubmed_id = Column(String(64))
    url = Column(Text)
    disease = Column(JSON, default=list)
    brain_regions = Column(JSON, default=list)
    datasets_used = Column(JSON, default=list)
    sample_size = Column(Integer)
    method = Column(Text)
    main_finding = Column(Text)
    limitations = Column(Text)
    verification_status = Column(String(32),
        CheckConstraint("verification_status IN ('VERIFIED','UNVERIFIED','RETRACTED')"),
        default="UNVERIFIED")
    verified_via = Column(String(256))
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    claim_links = relationship("ClaimPaper", back_populates="paper")


class EvidenceClaim(Base):
    __tablename__ = "evidence_claims"

    claim_id = Column(Integer, primary_key=True, autoincrement=True)
    claim_text = Column(Text, nullable=False)
    disease = Column(String(128))
    region_id = Column(Integer, ForeignKey("brain_regions.region_id"))
    evidence_status = Column(String(32),
        CheckConstraint("evidence_status IN ('ESTABLISHED','SUPPORTED','UNCERTAIN','CONTRADICTED','UNTESTED')"))
    manas_result_summary = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    region = relationship("BrainRegion")
    claim_links = relationship("ClaimPaper", back_populates="claim")


class ClaimPaper(Base):
    __tablename__ = "claim_papers"

    claim_id = Column(Integer, ForeignKey("evidence_claims.claim_id"), primary_key=True)
    paper_id = Column(Integer, ForeignKey("literature_papers.paper_id"), primary_key=True)
    relationship_type = Column(String(32),
        CheckConstraint("relationship_type IN ('SUPPORTS','CONTRADICTS','NEUTRAL')"))

    claim = relationship("EvidenceClaim", back_populates="claim_links")
    paper = relationship("LiteraturePaper", back_populates="claim_links")
