/**
 * MANAS API client — typed fetch wrappers for all backend endpoints.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8005';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.detail ?? err.message ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ── Types ────────────────────────────────────────────────────
export interface Dataset {
  dataset_id: number;
  name: string;
  short_name: string;
  source_org: string;
  official_url: string;
  access_type: 'OPEN_DIRECT' | 'OPEN_WITH_TERMS' | 'REGISTRATION_REQUIRED' | 'APPLICATION_REQUIRED' | 'RESTRICTED' | 'UNKNOWN';
  license: string;
  primary_disease: string[];
  description: string;
  latest_version?: {
    version_id: number;
    version_tag: string;
    download_date: string;
    is_synthetic: boolean;
  };
}

export interface BrainRegion {
  region_id: number;
  name: string;
  abbreviation: string;
  hemisphere: string;
  anatomical_category: string;
  lobe: string;
  atlas_id: number;
  parent_region_id: number | null;
  is_leaf: boolean;
}

export interface BrainRegionDetail extends BrainRegion {
  mni_x: number | null;
  mni_y: number | null;
  mni_z: number | null;
  depth: number;
  atlas: { atlas_id: number; name: string; version: string } | null;
  parent: { region_id: number; name: string } | null;
  analysis_results: AnalysisResult[];
}

export interface AnalysisRun {
  analysis_run_id: string;
  analysis_type: string;
  disease: string;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  is_synthetic: boolean;
  n_total: number | null;
  n_disease: number | null;
  n_control: number | null;
  statistical_method: string | null;
  correction_method: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface AnalysisResult {
  region_id: number;
  region_name: string;
  hemisphere: string;
  anatomical_category: string;
  n_disease: number;
  n_control: number;
  disease_mean: number;
  control_mean: number;
  mean_difference: number;
  effect_size: number;
  effect_size_ci_lower: number;
  effect_size_ci_upper: number;
  p_value: number;
  adjusted_p_value: number;
  significance_status: 'FDR_SIGNIFICANT' | 'NOT_FDR_SIGNIFICANT' | 'INSUFFICIENT_DATA' | 'NOT_TESTED';
  test_method: string;
}

export interface LiteraturePaper {
  paper_id: number;
  title: string;
  authors: string[];
  year: number;
  journal: string;
  doi: string;
  disease: string[];
  verification_status: 'VERIFIED' | 'UNVERIFIED' | 'RETRACTED';
}

export interface EvidenceClaim {
  claim_id: number;
  claim_text: string;
  disease: string;
  region_id: number | null;
  evidence_status: 'ESTABLISHED' | 'SUPPORTED' | 'UNCERTAIN' | 'CONTRADICTED' | 'UNTESTED';
  manas_result_summary: string | null;
  supporting_papers: LiteraturePaper[];
  contradicting_papers: LiteraturePaper[];
}

// ── V2 Predictive Platform Types ──────────────────────────────
export interface FeatureAttributionItem {
  feature: string;
  feature_label: string;
  value: number | null;
  importance: number;
  contribution: number;
  effect: 'INCREASES_RISK' | 'DECREASES_RISK' | 'NEUTRAL';
  odds_ratio: number | null;
}

export interface ClassificationRequest {
  age?: number | null;
  sex?: string;
  mmse?: number | null;
  cdr?: number | null;
  nwbv?: number | null;
  etiv?: number | null;
  apoe4_carrier?: boolean | null;
  education_years?: number | null;
  ihc_at8_ffpe?: number | null;
  ihc_a_beta_ffpe?: number | null;
  ptau_ratio?: number | null;
  model_id?: string;
}

export interface ClassificationResponse {
  inference_id: string;
  model_id: string;
  predicted_class: 'AD' | 'CONTROL' | 'MCI';
  predicted_class_label: string;
  probability: number;
  confidence_interval_low: number;
  confidence_interval_high: number;
  risk_tier: 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH';
  risk_summary: string;
  feature_attributions: FeatureAttributionItem[];
  model_version: string;
  model_accuracy: number;
  model_roc_auc: number;
  disclaimer: string;
}

export interface CognitiveStagingRequest {
  age?: number | null;
  sex?: string;
  mmse?: number | null;
  nwbv?: number | null;
  etiv?: number | null;
  apoe4_carrier?: boolean | null;
  composite_pathology_z?: number | null;
  braak_stage?: string | null;
}

export interface StageProbability {
  stage: string;
  stage_name: string;
  probability: number;
  clinical_description: string;
}

export interface CognitiveStagingResponse {
  inference_id: string;
  primary_stage: string;
  primary_stage_label: string;
  stage_probabilities: StageProbability[];
  estimated_mmse: number;
  estimated_mmse_range: [number, number];
  braak_anatomical_correlation: string;
  progression_velocity: string;
  recommended_monitoring_interval: string;
}

export interface VisitPoint {
  visit_id: number;
  time_days: number;
  age: number;
  mmse?: number | null;
  cdr?: number | null;
  nwbv?: number | null;
  etiv?: number | null;
}

export interface LongitudinalRequest {
  subject_id?: string;
  visits: VisitPoint[];
}

export interface FittedTrajectoryPoint {
  year: number;
  predicted_nwbv: number;
  predicted_mmse: number;
  ci_lower: number;
  ci_upper: number;
}

export interface LongitudinalResponse {
  subject_id: string;
  visits_count: number;
  total_followup_years: number;
  annualized_brain_atrophy_pct: number;
  annualized_mmse_change: number;
  trajectory_type: 'STABLE_NORMAL' | 'TYPICAL_AGING' | 'ACCELERATED_ATROPHY' | 'RAPID_COGNITIVE_DECLINE';
  trajectory_description: string;
  conversion_risk_5year: number;
  fitted_trajectory: FittedTrajectoryPoint[];
  clinical_interpretation: string;
}

export interface ModelMetadata {
  model_id: string;
  name: string;
  version: string;
  target_variable: string;
  algorithm: string;
  training_dataset: string;
  n_train: number;
  n_features: number;
  features: string[];
  metrics: {
    roc_auc: number;
    pr_auc: number;
    accuracy: number;
    f1: number;
    sensitivity: number;
    specificity: number;
    brier_score: number;
  };
  cv_method: string;
  is_active: boolean;
  created_at: string;
}

export interface ModelEvaluation {
  model_id: string;
  name: string;
  algorithm: string;
  target_variable: string;
  roc_curve: { fpr: number[]; tpr: number[]; thresholds: number[] };
  pr_curve: { recall: number[]; precision: number[] };
  confusion_matrix: {
    matrix: Array<{ label: string; pred_control: number; pred_ad: number }>;
    total_tested: number;
    threshold: number;
  };
  calibration_curve: { prob_pred: number[]; prob_true: number[] };
  feature_importances: Array<{ feature: string; importance: number; category: string; direction: string }>;
  metrics: Record<string, number>;
}

export interface ResearchReportRequest {
  subject_identifier: string;
  clinical_inputs: Record<string, unknown>;
  classification?: Record<string, unknown> | null;
  cognitive_staging?: Record<string, unknown> | null;
  longitudinal?: Record<string, unknown> | null;
  investigator_notes?: string | null;
}

export interface ResearchReportResponse {
  report_id: string;
  generated_at: string;
  subject_identifier: string;
  title: string;
  executive_summary: string;
  content_markdown: string;
  risk_profile: {
    probability?: number;
    risk_tier?: string;
    predicted_stage?: string;
  };
  disclaimer: string;
}

// ── API functions ─────────────────────────────────────────────

export const api = {
  health: () => apiFetch<{ status: string; version: string; database: string }>('/api/health'),

  datasets: {
    list: () => apiFetch<Dataset[]>('/api/datasets/'),
    get: (id: number) => apiFetch<Dataset>(`/api/datasets/${id}`),
  },

  regions: {
    list: (params?: { page?: number; page_size?: number; search?: string; hemisphere?: string }) => {
      const q = new URLSearchParams(params as Record<string, string>);
      return apiFetch<{ total: number; regions: BrainRegion[] }>(`/api/regions/?${q}`);
    },
    get: (id: number) => apiFetch<BrainRegionDetail>(`/api/regions/${id}`),
  },

  analyses: {
    list: (params?: { disease?: string; status?: string; page?: number }) => {
      const q = new URLSearchParams(params as Record<string, string>);
      return apiFetch<{ total: number; runs: AnalysisRun[] }>(`/api/analyses/?${q}`);
    },
    get: (id: string) => apiFetch<AnalysisRun & { parameters: Record<string, unknown>; software_env: Record<string, string> }>(`/api/analyses/${id}`),
    results: (id: string, params?: { significant_only?: boolean; page?: number; page_size?: number }) => {
      const q = new URLSearchParams(params as Record<string, string>);
      return apiFetch<{ analysis_run_id: string; is_synthetic: boolean; total: number; results: AnalysisResult[] }>(`/api/analyses/${id}/results?${q}`);
    },
    submit: (payload: {
      version_id: number;
      disease: string;
      measurement_type_name: string;
      covariates: string[];
      random_seed: number;
    }) => apiFetch<{ analysis_run_id: string; status: string; is_synthetic: boolean }>('/api/analyses/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  },

  predictions: {
    models: () => apiFetch<ModelMetadata[]>('/api/predictions/models'),
    evaluation: (modelId: string) => apiFetch<ModelEvaluation>(`/api/predictions/models/${modelId}/evaluation`),
    classify: (payload: ClassificationRequest) =>
      apiFetch<ClassificationResponse>('/api/predictions/classify', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    stage: (payload: CognitiveStagingRequest) =>
      apiFetch<CognitiveStagingResponse>('/api/predictions/stage', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    longitudinal: (payload: LongitudinalRequest) =>
      apiFetch<LongitudinalResponse>('/api/predictions/longitudinal', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    generateReport: (payload: ResearchReportRequest) =>
      apiFetch<ResearchReportResponse>('/api/predictions/report', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },

  literature: {
    list: (params?: { disease?: string; verified_only?: boolean }) => {
      const q = new URLSearchParams(params as Record<string, string>);
      return apiFetch<{ total: number; papers: LiteraturePaper[] }>(`/api/literature/?${q}`);
    },
    evidence: (params?: { disease?: string }) => {
      const q = new URLSearchParams(params as Record<string, string>);
      return apiFetch<EvidenceClaim[]>(`/api/literature/evidence?${q}`);
    },
  },

  ingestion: {
    triggerAllenAging: (is_synthetic = false) =>
      apiFetch<{ message: string; processing_run_id: number; version_id: number; is_synthetic: boolean }>(
        `/api/ingestion/allen-aging?is_synthetic=${is_synthetic}`,
        { method: 'POST' }
      ),
    triggerAllenAtlas: () =>
      apiFetch<{ message: string }>('/api/ingestion/allen-atlas', { method: 'POST' }),
    status: (run_id: number) =>
      apiFetch<{ run_id: number; status: string; records_processed: number; records_rejected: number }>(
        `/api/ingestion/status/${run_id}`
      ),
  },
};
