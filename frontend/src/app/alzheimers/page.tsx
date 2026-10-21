'use client';
import { useEffect, useState, useCallback } from 'react';
import { api, type AnalysisRun, type AnalysisResult } from '@/lib/api';

function fmt(n: number | null | undefined, digits = 3): string {
  if (n == null) return '—';
  return Number(n).toFixed(digits);
}

function SignificanceBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    FDR_SIGNIFICANT:  { label: 'FDR Significant',    cls: 'badge-sig' },
    NOT_FDR_SIGNIFICANT: { label: 'Not Significant', cls: 'badge-not-sig' },
    INSUFFICIENT_DATA: { label: 'Insufficient Data', cls: 'badge-insufficient' },
    NOT_TESTED:        { label: 'Not Tested',         cls: 'badge-insufficient' },
  };
  const { label, cls } = map[status] ?? { label: status, cls: 'badge-insufficient' };
  return <span className={`badge ${cls}`}>{label}</span>;
}

export default function AlzheimersPage() {
  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [runDetail, setRunDetail] = useState<(AnalysisRun & { parameters: Record<string, unknown>; software_env: Record<string, string> }) | null>(null);
  const [loading, setLoading] = useState(true);
  const [sortCol, setSortCol] = useState<keyof AnalysisResult>('effect_size');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    api.analyses.list({ disease: "Alzheimer" }).then(data => {
      setRuns(data.runs);
      const completed = data.runs.find(r => r.status === 'COMPLETED');
      if (completed) setSelectedRun(completed.analysis_run_id);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedRun) return;
    Promise.all([
      api.analyses.results(selectedRun, { page_size: 500 }),
      api.analyses.get(selectedRun),
    ]).then(([r, detail]) => {
      setResults(r.results);
      setRunDetail(detail);
    }).catch(() => {});
  }, [selectedRun]);

  const sorted = [...results].sort((a, b) => {
    const va = a[sortCol] as number ?? 0;
    const vb = b[sortCol] as number ?? 0;
    return sortDir === 'desc' ? vb - va : va - vb;
  });

  const sort = (col: keyof AnalysisResult) => {
    if (sortCol === col) setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setSortCol(col); setSortDir('desc'); }
  };

  const isSynthetic = runDetail?.is_synthetic;

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Alzheimer&apos;s Disease — Regional Analysis</h1>
        <p className="page-subtitle">
          Brain-region level comparison of disease-associated measurements between
          Alzheimer&apos;s and control groups.
        </p>
      </div>

      {isSynthetic && (
        <div className="synthetic-banner">
          ⚠ SYNTHETIC DATA — These are not real scientific results. Run ingestion with real Allen Aging data to see genuine findings.
        </div>
      )}

      {/* Research question */}
      <div className="card" style={{ marginBottom: 24, borderLeft: '3px solid var(--color-accent)' }}>
        <div className="section-label">Research Question</div>
        <p style={{ fontWeight: 500, fontSize: '0.9rem' }}>
          Which brain regions show statistically significant differences in
          Alzheimer&apos;s-associated measurements compared to the control group,
          and how large are those differences?
        </p>
        <div style={{ display: 'flex', gap: 24, marginTop: 12, fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
          <span><strong>Data:</strong> Allen Aging, Dementia &amp; TBI Study</span>
          <span><strong>Method:</strong> Normality-adaptive group comparison</span>
          <span><strong>Correction:</strong> Benjamini-Hochberg FDR (α = 0.05)</span>
          <span><strong>Effect size:</strong> Cohen&apos;s d / rank-biserial r + bootstrap 95% CI</span>
        </div>
      </div>

      {/* Run selector */}
      {runs.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
          <span style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>Analysis Run:</span>
          <select
            value={selectedRun ?? ''}
            onChange={e => setSelectedRun(e.target.value)}
            style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem',
              border: '1px solid var(--color-border)', borderRadius: 4,
              padding: '5px 10px', background: 'var(--color-surface)' }}
          >
            {runs.map(r => (
              <option key={r.analysis_run_id} value={r.analysis_run_id}>
                {r.analysis_run_id} — {r.status}{r.is_synthetic ? ' [SYNTHETIC]' : ''}
              </option>
            ))}
          </select>
        </div>
      )}

      {loading && <div className="loading">Loading analysis data…</div>}

      {!loading && runs.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-title">No Alzheimer&apos;s analyses yet</div>
          <p style={{ fontSize: '0.82rem', marginTop: 4 }}>
            Trigger ingestion of Allen Aging data, then submit an analysis from the
            <a href="/analysis-runs" style={{ color: 'var(--color-accent)', marginLeft: 4 }}>Analysis Runs</a> page.
          </p>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <>
          {/* Summary stats */}
          <div className="stat-grid" style={{ marginBottom: 24 }}>
            <div className="stat-box">
              <div className="stat-value mono">{runDetail?.n_disease ?? '—'}</div>
              <div className="stat-label">Alzheimer&apos;s subjects</div>
            </div>
            <div className="stat-box">
              <div className="stat-value mono">{runDetail?.n_control ?? '—'}</div>
              <div className="stat-label">Control subjects</div>
            </div>
            <div className="stat-box">
              <div className="stat-value mono">{results.filter(r => r.significance_status === 'FDR_SIGNIFICANT').length}</div>
              <div className="stat-label">FDR-significant regions</div>
            </div>
            <div className="stat-box">
              <div className="stat-value mono">{results.length}</div>
              <div className="stat-label">Regions tested</div>
            </div>
          </div>

          {/* Results table */}
          <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Regional Results</h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
              Click column headers to sort · Click row to view region detail
            </span>
          </div>
          <div className="table-wrap" style={{ marginBottom: 24 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Region</th>
                  <th>Hemisphere</th>
                  <th onClick={() => sort('n_disease')} style={{ cursor: 'pointer' }}>N (AD)</th>
                  <th onClick={() => sort('n_control')} style={{ cursor: 'pointer' }}>N (Ctrl)</th>
                  <th onClick={() => sort('disease_mean')} style={{ cursor: 'pointer' }}>AD Mean</th>
                  <th onClick={() => sort('control_mean')} style={{ cursor: 'pointer' }}>Ctrl Mean</th>
                  <th onClick={() => sort('effect_size')} style={{ cursor: 'pointer' }}>
                    Effect Size {sortCol === 'effect_size' ? (sortDir === 'desc' ? '↓' : '↑') : ''}
                  </th>
                  <th>95% CI</th>
                  <th onClick={() => sort('p_value')} style={{ cursor: 'pointer' }}>p-value</th>
                  <th onClick={() => sort('adjusted_p_value')} style={{ cursor: 'pointer' }}>adj. p (BH)</th>
                  <th>Significance</th>
                  <th>Test</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map(r => (
                  <tr key={r.region_id}
                    onClick={() => window.location.href = `/brain-regions/${r.region_id}`}>
                    <td style={{ fontWeight: 500 }}>{r.region_name}</td>
                    <td style={{ color: 'var(--color-text-muted)', fontSize: '0.78rem' }}>{r.hemisphere}</td>
                    <td className="mono">{r.n_disease}</td>
                    <td className="mono">{r.n_control}</td>
                    <td className="mono">{fmt(r.disease_mean)}</td>
                    <td className="mono">{fmt(r.control_mean)}</td>
                    <td className="mono" style={{ fontWeight: 600, color: Math.abs(r.effect_size) > 0.5 ? 'var(--color-sig)' : undefined }}>
                      {fmt(r.effect_size, 3)}
                    </td>
                    <td className="mono" style={{ fontSize: '0.75rem' }}>
                      [{fmt(r.effect_size_ci_lower, 3)}, {fmt(r.effect_size_ci_upper, 3)}]
                    </td>
                    <td className="mono">{fmt(r.p_value, 4)}</td>
                    <td className="mono">{fmt(r.adjusted_p_value, 4)}</td>
                    <td><SignificanceBadge status={r.significance_status} /></td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{r.test_method}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Provenance */}
          {runDetail && (
            <div style={{ marginBottom: 24 }}>
              <div className="section-label" style={{ marginBottom: 8 }}>Analysis Provenance</div>
              <div className="provenance">
                {[
                  ['Analysis Run ID', runDetail.analysis_run_id],
                  ['Statistical method', runDetail.statistical_method],
                  ['Multiple testing', runDetail.correction_method],
                  ['Effect size measure', (runDetail as unknown as Record<string,unknown>)['effect_size_measure'] as string ?? '—'],
                  ['Covariates', ((runDetail as unknown as Record<string,unknown>)['covariates'] as string[] | undefined)?.join(', ') ?? '—'],
                  ['Started', runDetail.started_at ?? '—'],
                  ['Completed', runDetail.completed_at ?? '—'],
                  ['Data type', 'is_synthetic' in runDetail ? (runDetail.is_synthetic ? 'SYNTHETIC (not real results)' : 'REAL DATA') : '—'],
                ].map(([k, v]) => (
                  <div key={k} className="provenance-row">
                    <span className="provenance-key">{k}</span>
                    <span className="provenance-val">{String(v)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Limitations */}
          <div className="card" style={{ background: 'var(--color-surface-2)' }}>
            <div className="section-label" style={{ marginBottom: 8 }}>Limitations &amp; Interpretation</div>
            <ul style={{ fontSize: '0.82rem', color: 'var(--color-text-2)', paddingLeft: 20, lineHeight: 1.8 }}>
              <li>The Allen Aging dataset contains only 4 sampled brain regions — this is not a whole-brain survey.</li>
              <li>Post-mortem tissue measurements may not fully reflect in-vivo disease-associated changes.</li>
              <li>Statistical association does not imply causation.</li>
              <li>FDR correction is applied across tested regions; results may not generalize to untested regions.</li>
              <li>Cohort selection effects inherent to post-mortem brain banking studies may introduce bias.</li>
              <li>Findings require independent replication before scientific conclusions can be drawn.</li>
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
