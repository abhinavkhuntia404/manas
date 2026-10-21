'use client';
import { useEffect, useState } from 'react';
import { api, type AnalysisRun, type AnalysisResult } from '@/lib/api';

/**
 * Lewy Body / Parkinson's Analysis Page
 * Explores α-synuclein pathology, tau/amyloid co-pathology, and regional differences.
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

const LEWY_CONTEXT = [
  { key: 'Target Pathology', value: 'α-synuclein (SNCA) aggregates & Lewy bodies' },
  { key: 'Available Marker', value: 'ihc_a_syn (immunohistochemistry fraction area)' },
  { key: 'Cohort Source', value: 'Allen Aging, Dementia & TBI (post-mortem donors)' },
  { key: 'Brain Regions', value: 'HIP (Hippocampus), TCx (Temporal Cortex), PCx (Parietal), FWM' },
  { key: 'Co-pathology', value: 'pTau (AT8), Amyloid-β (IHC / Luminex), oxidative stress (8-isoprostane)' },
  { key: 'Scientific Question', value: 'Regional distribution of α-synuclein load and its correlation with cognitive decline & AD co-pathology' },
];

export default function LewyBodyPage() {
  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [runDetail, setRunDetail] = useState<(AnalysisRun & { parameters: Record<string, unknown> }) | null>(null);
  const [loading, setLoading] = useState(true);
  const [sortCol, setSortCol] = useState<keyof AnalysisResult>('effect_size');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    api.analyses.list({ disease: 'Lewy Body', page: 1 }).then(data => {
      setRuns(data.runs);
      const done = data.runs.find(r => r.status === 'COMPLETED');
      if (done) setSelectedRun(done.analysis_run_id);
      setLoading(false);
    }).catch(() => {
      // Fallback: try querying without disease filter or general runs
      api.analyses.list({ page: 1 }).then(data => {
        setRuns(data.runs);
        const done = data.runs.find(r => r.status === 'COMPLETED');
        if (done) setSelectedRun(done.analysis_run_id);
        setLoading(false);
      }).catch(() => setLoading(false));
    });
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
        <h1 className="page-title">Lewy Body &amp; Parkinsonian Pathology</h1>
        <p className="page-subtitle">
          Computational analysis of α-synuclein burden, co-pathologies, and regional vulnerability
          in the Allen Institute Aging &amp; Dementia donor cohort.
        </p>
      </div>

      {/* Disease context */}
      <div className="card" style={{ marginBottom: 24, borderLeft: '3px solid #e11d48' }}>
        <div className="section-label" style={{ marginBottom: 10 }}>Pathology &amp; Clinical Context</div>
        {LEWY_CONTEXT.map(({ key, value }) => (
          <div key={key} style={{ display: 'flex', gap: 16, padding: '4px 0', fontSize: '0.82rem', borderBottom: '1px solid var(--color-border)' }}>
            <span style={{ color: 'var(--color-text-muted)', width: 200, flexShrink: 0 }}>{key}</span>
            <span style={{ fontWeight: 500 }}>{value}</span>
          </div>
        ))}
      </div>

      {/* Scientific context card */}
      <div className="card" style={{ marginBottom: 24, background: 'var(--color-surface-2)' }}>
        <div className="section-label" style={{ marginBottom: 8 }}>Neurobiology of Lewy Body Spectrum</div>
        <ul style={{ fontSize: '0.82rem', color: 'var(--color-text-2)', paddingLeft: 20, lineHeight: 1.9 }}>
          <li>
            <strong>α-Synuclein IHC (<code>ihc_a_syn</code>):</strong> Quantified by DAB immunohistochemistry in the Allen Aging pipeline, detecting Lewy bodies, Lewy neurites, and diffuse neuropil aggregates across Hippocampus (HIP), Temporal Cortex (TCx), Parietal Cortex (PCx), and Forebrain White Matter (FWM).
          </li>
          <li>
            <strong>Mixed Neuropathology:</strong> Over 50% of advanced Alzheimer&apos;s cases exhibit concomitant Lewy bodies, particularly in the amygdala and limbic regions. MANAS disentangles pure vs mixed pathology by evaluating cross-marker correlations.
          </li>
          <li>
            <strong>V2 Roadmap Extension:</strong> In addition to post-mortem IHC, full integration with Parkinson&apos;s Progression Markers Initiative (PPMI) DaTscan SPECT and clinical motor metrics (UPDRS) is planned for the v2 pipeline.
          </li>
        </ul>
      </div>

      {loading ? (
        <div className="card" style={{ textAlign: 'center', padding: 48 }}>
          <div className="spinner" style={{ margin: '0 auto 16px' }} />
          <p style={{ color: 'var(--color-text-muted)' }}>Loading Lewy Body analysis data...</p>
        </div>
      ) : results.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 48 }}>
          <p style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: 8 }}>
            Lewy Body Analysis Model Initialized
          </p>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', maxWidth: 600, margin: '0 auto 20px' }}>
            The pipeline is configured for α-synuclein (<code>ihc_a_syn</code>) quantification and regional testing.
            Run or select an analysis run to view regional statistics and effect sizes.
          </p>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
            <a href="/analysis-runs" className="btn btn-primary">Go to Analysis Runs</a>
            <a href="/data-explorer" className="btn btn-secondary">Explore Raw Biomarkers</a>
          </div>
        </div>
      ) : (
        <>
          {/* Active run selector if runs exist */}
          {runs.length > 0 && (
            <div className="card" style={{ marginBottom: 20, display: 'flex', alignItems: 'center', gap: 16 }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Active Run:</span>
              <select
                className="select"
                value={selectedRun ?? ''}
                onChange={e => setSelectedRun(e.target.value)}
                style={{ maxWidth: 360 }}
              >
                {runs.map(r => (
                  <option key={r.analysis_run_id} value={r.analysis_run_id}>
                    {r.analysis_run_id} ({r.disease})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Table */}
          <div className="table-wrap" style={{ marginBottom: 24 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Brain Region</th>
                  <th>N (Disease)</th>
                  <th>N (Control)</th>
                  <th onClick={() => sort('effect_size')} style={{ cursor: 'pointer' }}>
                    Effect Size (Hedges&apos; g) {sortCol === 'effect_size' ? (sortDir === 'desc' ? '▼' : '▲') : ''}
                  </th>
                  <th>95% CI</th>
                  <th onClick={() => sort('p_value')} style={{ cursor: 'pointer' }}>p-value</th>
                  <th onClick={() => sort('adjusted_p_value')} style={{ cursor: 'pointer' }}>adj. p (BH)</th>
                  <th>Significance</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map(r => (
                  <tr key={r.region_id} onClick={() => window.location.href = `/brain-regions/${r.region_id}`} style={{ cursor: 'pointer' }}>
                    <td style={{ fontWeight: 500 }}>{r.region_name}</td>
                    <td className="mono">{r.n_disease}</td>
                    <td className="mono">{r.n_control}</td>
                    <td className="mono" style={{ fontWeight: 600, color: Math.abs(r.effect_size) > 0.5 ? 'var(--color-sig)' : undefined }}>
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
            <div className="section-label" style={{ marginBottom: 8 }}>Exploratory &amp; Biomarker Considerations</div>
            <p style={{ fontSize: '0.82rem', color: 'var(--color-text-2)', lineHeight: 1.7 }}>
              Immunohistochemical α-synuclein staining (AT8/synuclein co-panels) exhibits high variance
              depending on post-mortem interval (PMI) and tissue preservation.
              Results should be viewed as cross-cohort exploratory hypotheses and benchmarked against
              formal consensus criteria (McKeith et al. 2017) for Dementia with Lewy Bodies.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
