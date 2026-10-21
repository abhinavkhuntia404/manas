'use client';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api, type AnalysisResult } from '@/lib/api';

type RunDetail = {
  analysis_run_id: string;
  analysis_type: string;
  disease: string;
  status: string;
  is_synthetic: boolean;
  statistical_method: string | null;
  correction_method: string | null;
  effect_size_measure: string | null;
  covariates: string[] | null;
  parameters: Record<string, unknown>;
  random_seed: number | null;
  n_total: number | null;
  n_disease: number | null;
  n_control: number | null;
  software_env: Record<string, string> | null;
  code_commit: string | null;
  ingestion_version: string | null;
  preprocessing_version: string | null;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
};

function fmt(n: number | null | undefined, d = 3) {
  return n == null ? '--' : Number(n).toFixed(d);
}

function ProvenanceRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="provenance-row">
      <span className="provenance-key">{label}</span>
      <span className="provenance-val">{value}</span>
    </div>
  );
}

function SignificanceBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    FDR_SIGNIFICANT:     { label: 'FDR Significant',   cls: 'badge-sig' },
    NOT_FDR_SIGNIFICANT: { label: 'Not Significant',   cls: 'badge-not-sig' },
    INSUFFICIENT_DATA:   { label: 'Insufficient Data', cls: 'badge-insufficient' },
    NOT_TESTED:          { label: 'Not Tested',         cls: 'badge-insufficient' },
  };
  const { label, cls } = map[status] ?? { label: status, cls: 'badge-insufficient' };
  return <span className={`badge ${cls}`}>{label}</span>;
}

export default function AnalysisRunDetailPage() {
  const params = useParams();
  const runId = (params?.id as string) || '';

  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [loadingDetail, setLoadingDetail] = useState(true);
  const [loadingResults, setLoadingResults] = useState(false);
  const [sortCol, setSortCol] = useState<keyof AnalysisResult>('effect_size');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!runId) return;
    api.analyses.get(runId)
      .then(d => { setDetail(d as RunDetail); setLoadingDetail(false); })
      .catch(e => { setError(String(e.message)); setLoadingDetail(false); });
  }, [runId]);

  useEffect(() => {
    if (!detail || detail.status !== 'COMPLETED') return;
    setLoadingResults(true);
    api.analyses.results(runId, { page_size: 500 })
      .then(d => { setResults(d.results); setLoadingResults(false); })
      .catch(() => setLoadingResults(false));
  }, [detail, runId]);

  const sorted = [...results].sort((a, b) => {
    const va = (a[sortCol] as number) ?? 0;
    const vb = (b[sortCol] as number) ?? 0;
    return sortDir === 'desc' ? vb - va : va - vb;
  });

  const sort = (col: keyof AnalysisResult) => {
    if (sortCol === col) setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setSortCol(col); setSortDir('desc'); }
  };

  if (loadingDetail) return (
    <div className="page-content">
      <div className="card" style={{ textAlign: 'center', padding: 48 }}>
        <div className="spinner" style={{ margin: '0 auto 16px' }} />
        <p style={{ color: 'var(--color-text-muted)' }}>Loading analysis run...</p>
      </div>
    </div>
  );

  if (error || !detail) return (
    <div className="page-content">
      <a href="/analysis-runs" style={{ fontSize: '0.82rem', color: 'var(--color-accent)', display: 'block', marginBottom: 16 }}>
        &larr; back to Analysis Runs
      </a>
      <div className="empty-state">
        <div className="empty-state-title">Run not found</div>
        <p style={{ fontSize: '0.82rem', marginTop: 4, color: 'var(--color-fail)' }}>{error}</p>
      </div>
    </div>
  );

  const statusCls = detail.status === 'COMPLETED' ? 'badge-pass'
    : detail.status === 'FAILED' ? 'badge-fail' : 'badge-warn';
  const sigCount = results.filter(r => r.significance_status === 'FDR_SIGNIFICANT').length;

  return (
    <div className="page-content">
      <a href="/analysis-runs" style={{ fontSize: '0.82rem', color: 'var(--color-accent)', display: 'block', marginBottom: 16 }}>
        &larr; back to Analysis Runs
      </a>

      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
          <h1 className="page-title" style={{ fontFamily: 'var(--font-mono)', fontSize: '1.3rem' }}>
            {detail.analysis_run_id}
          </h1>
          <span className={`badge ${statusCls}`}>{detail.status}</span>
          {detail.is_synthetic && (
            <span className="badge" style={{ background: 'var(--color-synthetic-bg)', color: 'var(--color-synthetic)' }}>
              SYNTHETIC
            </span>
          )}
        </div>
        <p className="page-subtitle">{detail.disease} &middot; {detail.analysis_type.replace(/_/g, ' ')}</p>
      </div>

      {detail.is_synthetic && (
        <div className="synthetic-banner">SYNTHETIC DATA — These are not real scientific results.</div>
      )}

      {detail.status === 'FAILED' && detail.error_message && (
        <div className="card" style={{ borderColor: 'var(--color-fail)', borderLeftWidth: 3, marginBottom: 24 }}>
          <div className="section-label" style={{ color: 'var(--color-fail)', marginBottom: 6 }}>Error</div>
          <pre style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--color-fail)', whiteSpace: 'pre-wrap' }}>
            {detail.error_message}
          </pre>
        </div>
      )}

      {detail.status === 'COMPLETED' && (
        <div className="stat-grid" style={{ marginBottom: 24 }}>
          {[
            { val: detail.n_total ?? '--',   label: 'Total subjects' },
            { val: detail.n_disease ?? '--', label: 'Disease group' },
            { val: detail.n_control ?? '--', label: 'Control group' },
            { val: sigCount,                  label: 'FDR-significant regions' },
            { val: results.length,            label: 'Regions tested' },
            { val: detail.random_seed ?? '--', label: 'Random seed' },
          ].map(({ val, label }) => (
            <div key={label} className="stat-box">
              <div className="stat-value">{String(val)}</div>
              <div className="stat-label">{label}</div>
            </div>
          ))}
        </div>
      )}

      <div className="grid-2" style={{ gap: 24, marginBottom: 24 }}>
        <div className="card">
          <div className="card-header"><div className="card-title">Run Identification</div></div>
          <div className="provenance">
            <ProvenanceRow label="Run ID"        value={detail.analysis_run_id} />
            <ProvenanceRow label="Disease"       value={detail.disease} />
            <ProvenanceRow label="Analysis type" value={detail.analysis_type} />
            <ProvenanceRow label="Status"        value={detail.status} />
            <ProvenanceRow label="Data type"     value={detail.is_synthetic ? 'SYNTHETIC' : 'REAL DATA'} />
            <ProvenanceRow label="Started"       value={detail.started_at ?? '--'} />
            <ProvenanceRow label="Completed"     value={detail.completed_at ?? '--'} />
          </div>
        </div>
        <div className="card">
          <div className="card-header"><div className="card-title">Statistical Specification</div></div>
          <div className="provenance">
            <ProvenanceRow label="Statistical method"  value={detail.statistical_method ?? '--'} />
            <ProvenanceRow label="Correction"          value={detail.correction_method ?? '--'} />
            <ProvenanceRow label="Effect size measure" value={detail.effect_size_measure ?? '--'} />
            <ProvenanceRow label="Covariates"          value={detail.covariates?.join(', ') ?? '--'} />
            <ProvenanceRow label="Random seed"         value={String(detail.random_seed ?? '--')} />
          </div>
        </div>
      </div>

      <div className="grid-2" style={{ gap: 24, marginBottom: 24 }}>
        <div className="card">
          <div className="card-header"><div className="card-title">Data Provenance</div></div>
          <div className="provenance">
            <ProvenanceRow label="Ingestion version"     value={detail.ingestion_version ?? '--'} />
            <ProvenanceRow label="Preprocessing version" value={detail.preprocessing_version ?? '--'} />
            <ProvenanceRow label="Code commit"           value={detail.code_commit ?? '--'} />
          </div>
        </div>
        <div className="card">
          <div className="card-header"><div className="card-title">Software Environment</div></div>
          <div className="provenance">
            {detail.software_env
              ? Object.entries(detail.software_env).map(([k, v]) => <ProvenanceRow key={k} label={k} value={v} />)
              : <p style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>Not recorded</p>
            }
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header"><div className="card-title">Full Parameters (JSON)</div></div>
        <pre style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', background: 'var(--color-surface-2)',
          border: '1px solid var(--color-border)', borderRadius: 4, padding: 12, overflow: 'auto',
          maxHeight: 220, color: 'var(--color-text)' }}>
          {JSON.stringify(detail.parameters, null, 2)}
        </pre>
      </div>

      {detail.status === 'COMPLETED' && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h2 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Per-Region Results</h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
              {loadingResults ? 'Loading...' : `${results.length} regions`}
            </span>
          </div>
          {loadingResults ? (
            <div className="card" style={{ textAlign: 'center', padding: 32 }}>
              <div className="spinner" style={{ margin: '0 auto' }} />
            </div>
          ) : results.length === 0 ? (
            <div className="empty-state"><div className="empty-state-title">No results stored</div></div>
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead><tr>
                  <th>Region</th><th>Hemisphere</th>
                  <th onClick={() => sort('n_disease')} style={{ cursor: 'pointer' }}>N (Dis.)</th>
                  <th onClick={() => sort('n_control')} style={{ cursor: 'pointer' }}>N (Ctrl)</th>
                  <th onClick={() => sort('disease_mean')} style={{ cursor: 'pointer' }}>Dis. Mean</th>
                  <th onClick={() => sort('control_mean')} style={{ cursor: 'pointer' }}>Ctrl Mean</th>
                  <th onClick={() => sort('effect_size')} style={{ cursor: 'pointer' }}>
                    Effect {sortCol === 'effect_size' ? (sortDir === 'desc' ? ' \u2193' : ' \u2191') : ''}
                  </th>
                  <th>95% CI</th>
                  <th onClick={() => sort('p_value')} style={{ cursor: 'pointer' }}>p</th>
                  <th onClick={() => sort('adjusted_p_value')} style={{ cursor: 'pointer' }}>adj.p</th>
                  <th>Significance</th><th>Test</th>
                </tr></thead>
                <tbody>
                  {sorted.map(r => (
                    <tr key={r.region_id} onClick={() => window.location.href = `/brain-regions/${r.region_id}`}>
                      <td style={{ fontWeight: 500 }}>{r.region_name}</td>
                      <td style={{ color: 'var(--color-text-muted)', fontSize: '0.78rem' }}>{r.hemisphere}</td>
                      <td className="mono">{r.n_disease}</td>
                      <td className="mono">{r.n_control}</td>
                      <td className="mono">{fmt(r.disease_mean)}</td>
                      <td className="mono">{fmt(r.control_mean)}</td>
                      <td className="mono" style={{ fontWeight: 600, color: Math.abs(r.effect_size) > 0.5 ? 'var(--color-sig)' : undefined }}>
                        {fmt(r.effect_size)}
                      </td>
                      <td className="mono" style={{ fontSize: '0.75rem' }}>
                        [{fmt(r.effect_size_ci_lower, 2)}, {fmt(r.effect_size_ci_upper, 2)}]
                      </td>
                      <td className="mono">{fmt(r.p_value, 4)}</td>
                      <td className="mono">{fmt(r.adjusted_p_value, 4)}</td>
                      <td><SignificanceBadge status={r.significance_status} /></td>
                      <td style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>{r.test_method}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <div className="card" style={{ borderLeft: '3px solid var(--color-accent)' }}>
        <div className="section-label" style={{ marginBottom: 8 }}>Reproducibility</div>
        <p style={{ fontSize: '0.82rem', color: 'var(--color-text-2)', lineHeight: 1.7 }}>
          To reproduce: use dataset version ID {String(detail.parameters?.version_id ?? '--')},
          random seed {detail.random_seed}, submit via POST /api/analyses/ with the parameters JSON above.
        </p>
        <div style={{ marginTop: 12 }}>
          <a href={`/reproducibility?run=${detail.analysis_run_id}`} style={{ fontSize: '0.82rem', color: 'var(--color-accent)' }}>
            Open in Reproducibility Viewer &rarr;
          </a>
        </div>
      </div>
    </div>
  );
}
