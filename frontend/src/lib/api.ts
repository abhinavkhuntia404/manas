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
