'use client';
import { useEffect, useState } from 'react';
import { api, type AnalysisRun, type AnalysisResult } from '@/lib/api';

/**
 * Vascular Dementia Analysis Page
 * Compares "Vascular" diagnosis group vs "No Dementia" controls in Allen Aging.
 * Uses the same statistical engine as AD analysis.
 */

function fmt(n: number | null | undefined, digits = 3) {
  if (n == null) return '—';
  return Number(n).toFixed(digits);
}

function SignificanceBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    FDR_SIGNIFICANT:    { label: 'FDR Significant',    cls: 'badge-sig' },
    NOT_FDR_SIGNIFICANT:{ label: 'Not Significant',    cls: 'badge-not-sig' },
    INSUFFICIENT_DATA:  { label: 'Insufficient Data',  cls: 'badge-insufficient' },
    NOT_TESTED:         { label: 'Not Tested',          cls: 'badge-insufficient' },
  };
  const { label, cls } = map[status] ?? { label: status, cls: 'badge-insufficient' };
  return <span className={`badge ${cls}`}>{label}</span>;
}

// Allen Aging Vascular group summary (from real data — 15 donors)
const VASCULAR_CONTEXT = [
  { key: 'Diagnosis in Allen Aging', value: '"Vascular" — DSM-IV clinical label' },
  { key: 'N donors', value: '~15 (subset of 107 total)' },
  { key: 'Brain regions', value: 'HIP, TCx, PCx, FWM' },
  { key: 'Control group', value: '"No Dementia" donors' },
  { key: 'Key pathology', value: 'ihc_a_beta_ffpe, tau_ng_per_mg, isoprostane' },
  { key: 'Biological question', value: 'Do vascular dementia brains show distinct protein profiles vs controls and vs AD?' },
];

export default function VascularPage() {
  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [runDetail, setRunDetail] = useState<(AnalysisRun & { parameters: Record<string, unknown> }) | null>(null);
  const [loading, setLoading] = useState(true);
  const [sortCol, setSortCol] = useState<keyof AnalysisResult>('effect_size');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    api.analyses.list({ disease: 'Vascular', page: 1 }).then(data => {
      setRuns(data.runs);
      const done = data.runs.find(r => r.status === 'COMPLETED');
      if (done) setSelectedRun(done.analysis_run_id);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedRun) return;
    Promise.all([
      api.analyses.results(selectedRun, { page_size: 500 }),
      api.analyses.get(selectedRun),
    ]).then(([r, d]) => {
      setResults(r.results);
      setRunDetail(d as typeof runDetail);
    }).catch(() => {});
  }, [selectedRun]);

  const sorted = [...results].sort((a, b) => {
    const va = (a[sortCol] as number) ?? 0;
    const vb = (b[sortCol] as number) ?? 0;
    return sortDir === 'desc' ? vb - va : va - vb;
  });

  const sort = (col: keyof AnalysisResult) => {
    if (sortCol === col) setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setSortCol(col); setSortDir('desc'); }
  };

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Vascular Dementia — Regional Analysis</h1>
        <p className="page-subtitle">
          Brain-region comparison between Vascular Dementia and control donors from
          the Allen Aging, Dementia &amp; TBI Study.
          Protein quantification (Luminex), IHC pathology, and oxidative stress markers.
        </p>
      </div>

      {/* Disease context */}
      <div className="card" style={{ marginBottom: 24, borderLeft: '3px solid #7c3aed' }}>
        <div className="section-label" style={{ marginBottom: 10 }}>Disease Context</div>
        {VASCULAR_CONTEXT.map(({ key, value }) => (
          <div key={key} style={{ display: 'flex', gap: 16, padding: '4px 0', fontSize: '0.82rem', borderBottom: '1px solid var(--color-border)' }}>
            <span style={{ color: 'var(--color-text-muted)', width: 200, flexShrink: 0 }}>{key}</span>
            <span style={{ fontWeight: 500 }}>{value}</span>
          </div>
        ))}
      </div>

      {/* Key biological note */}
      <div className="card" style={{ marginBottom: 24, background: 'var(--color-surface-2)' }}>
        <div className="section-label" style={{ marginBottom: 8 }}>Scientific Context</div>
        <ul style={{ fontSize: '0.82rem', color: 'var(--color-text-2)', paddingLeft: 20, lineHeight: 1.9 }}>
          <li>Vascular dementia (VaD) arises from cerebrovascular disease rather than primary neurodegeneration</li>
          <li>Distinguishing VaD from AD is clinically challenging — mixed pathology is common</li>
          <li>In Allen Aging, <strong>isoprostane</strong> (oxidative stress) and vascular inflammation markers may differentiate VaD</li>
          <li>Low sample size (~15 donors) means results should be interpreted with extreme caution</li>
          <li>FDR correction becomes conservative with small N — unadjusted p-values also shown for reference</li>
        </ul>
      </div>

      {/* Run selector */}
      {runs.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
          <span style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>Analysis Run:</span>
          <select value={selectedRun ?? ''} onChange={e => setSelectedRun(e.target.value)}
            style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem',
              border: '1px solid var(--color-border)', borderRadius: 4,
              padding: '5px 10px', background: 'var(--color-surface)' }}>
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
          <div className="empty-state-title">No Vascular Dementia analyses yet</div>
          <p style={{ fontSize: '0.82rem', marginTop: 8, lineHeight: 1.7 }}>
            To run this analysis:<br />
            1. Ingest Allen Aging data: <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>POST /api/ingestion/allen-aging</code><br />
            2. Submit analysis with <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>disease: &quot;Vascular&quot;</code> from the{' '}
            <a href="/analysis-runs" style={{ color: 'var(--color-accent)' }}>Analysis Runs</a> page
          </p>
        </div>
      )}

      {results.length > 0 && (
        <>
          {runDetail?.is_synthetic && (
            <div className="synthetic-banner">⚠ SYNTHETIC DATA — not real results</div>
          )}

          <div className="stat-grid" style={{ marginBottom: 24 }}>
            <div className="stat-box">
              <div className="stat-value mono">{runDetail?.n_disease ?? '—'}</div>
              <div className="stat-label">Vascular donors</div>
            </div>
            <div className="stat-box">
              <div className="stat-value mono">{runDetail?.n_control ?? '—'}</div>
              <div className="stat-label">Control donors</div>
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

          <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between' }}>
            <h2 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Regional Results — Vascular vs Control</h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Click headers to sort</span>
          </div>
          <div className="table-wrap" style={{ marginBottom: 24 }}>
            <table className="data-table">
              <thead><tr>
                <th>Region</th>
                <th onClick={() => sort('n_disease')} style={{ cursor: 'pointer' }}>N (Vasc)</th>
                <th onClick={() => sort('n_control')} style={{ cursor: 'pointer' }}>N (Ctrl)</th>
                <th onClick={() => sort('effect_size')} style={{ cursor: 'pointer' }}>
                  Effect Size {sortCol === 'effect_size' ? (sortDir === 'desc' ? '↓' : '↑') : ''}
                </th>
                <th>95% CI</th>
                <th onClick={() => sort('p_value')} style={{ cursor: 'pointer' }}>p-value</th>
                <th onClick={() => sort('adjusted_p_value')} style={{ cursor: 'pointer' }}>adj. p (BH)</th>
                <th>Significance</th>
              </tr></thead>
              <tbody>
                {sorted.map(r => (
                  <tr key={r.region_id} onClick={() => window.location.href = `/brain-regions/${r.region_id}`}>
                    <td style={{ fontWeight: 500 }}>{r.region_name}</td>
                    <td className="mono">{r.n_disease}</td>
                    <td className="mono">{r.n_control}</td>
                    <td className="mono" style={{ fontWeight: 600,
                      color: Math.abs(r.effect_size) > 0.5 ? 'var(--color-sig)' : undefined }}>
                      {fmt(r.effect_size, 3)}
                    </td>
                    <td className="mono" style={{ fontSize: '0.75rem' }}>
                      [{fmt(r.effect_size_ci_lower, 2)}, {fmt(r.effect_size_ci_upper, 2)}]
                    </td>
                    <td className="mono">{fmt(r.p_value, 4)}</td>
                    <td className="mono">{fmt(r.adjusted_p_value, 4)}</td>
                    <td><SignificanceBadge status={r.significance_status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="card" style={{ background: 'var(--color-surface-2)' }}>
            <div className="section-label" style={{ marginBottom: 8 }}>Small-N Caution</div>
            <p style={{ fontSize: '0.82rem', color: 'var(--color-text-2)', lineHeight: 1.7 }}>
              The Vascular group in Allen Aging contains approximately 15 donors.
              With this N, statistical power is very limited. FDR-significant findings
              here require replication with larger vascular dementia cohorts before
              any scientific conclusions can be drawn. These results are exploratory only.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
