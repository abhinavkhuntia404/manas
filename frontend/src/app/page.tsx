'use client';
import { useEffect, useState } from 'react';
import { api, type AnalysisRun, type Dataset } from '@/lib/api';

export default function HomePage() {
  const [health, setHealth] = useState<{ status: string; database: string; version: string } | null>(null);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [recentRuns, setRecentRuns] = useState<AnalysisRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      api.health(),
      api.datasets.list(),
      api.analyses.list({ page: 1 }),
    ]).then(([h, d, r]) => {
      if (h.status === 'fulfilled') setHealth(h.value);
      if (d.status === 'fulfilled') setDatasets(d.value as Dataset[]);
      if (r.status === 'fulfilled') setRecentRuns((r.value as { runs: AnalysisRun[] }).runs.slice(0, 5));
      setLoading(false);
    });
  }, []);

  const completedRuns = recentRuns.filter(r => r.status === 'COMPLETED').length;
  const syntheticDatasets = datasets.filter(d => d.latest_version?.is_synthetic).length;

  return (
    <div className="page-content">
      {/* Header */}
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 8 }}>
          <h1 className="page-title">MANAS &nbsp;<span style={{ fontWeight: 300, color: 'var(--color-text-2)' }}>मनस्</span></h1>
          <span style={{ fontSize: '0.78rem', background: 'var(--color-surface-2)', border: '1px solid var(--color-border)', borderRadius: 4, padding: '2px 8px', color: 'var(--color-text-muted)' }}>v1.0</span>
        </div>
        <p className="page-subtitle">
          Computational Neuroscience Research Platform — Integrating publicly available human brain,
          molecular, pathological and clinical data to investigate disease-associated regional
          patterns in Alzheimer&apos;s and Parkinson&apos;s disease.
        </p>
      </div>

      {/* Research question */}
      <div className="card" style={{ marginBottom: 24, borderLeft: '3px solid var(--color-accent)' }}>
        <div className="section-label">Primary Research Question — V1</div>
        <p style={{ fontSize: '0.95rem', fontWeight: 500, color: 'var(--color-text)', lineHeight: 1.6 }}>
          Which brain regions exhibit statistically robust Alzheimer&apos;s-associated differences
          in public human data, and how reproducible are those patterns?
        </p>
      </div>

      {/* System status */}
      {!loading && (
        <div className="stat-grid">
          <div className="stat-box">
            <div className="stat-value">{datasets.length}</div>
            <div className="stat-label">Registered Datasets</div>
          </div>
          <div className="stat-box">
            <div className="stat-value">{recentRuns.length}</div>
            <div className="stat-label">Analysis Runs</div>
          </div>
          <div className="stat-box">
            <div className="stat-value">{completedRuns}</div>
            <div className="stat-label">Completed Analyses</div>
          </div>
          <div className="stat-box">
            <div className="stat-value" style={{ color: health?.status === 'ok' ? 'var(--color-pass)' : 'var(--color-fail)' }}>
              {health?.status === 'ok' ? '✓' : '✗'}
            </div>
            <div className="stat-label">System Status</div>
          </div>
        </div>
      )}

      {/* Datasets */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 600 }}>Data Sources</h2>
          <a href="/datasets" style={{ fontSize: '0.8rem', color: 'var(--color-accent)' }}>View all →</a>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {/* Always show known datasets even if DB not yet seeded */}
          {[
            {
              name: 'Allen Aging, Dementia & TBI Study',
              org: 'Allen Institute for Brain Science',
              access: 'OPEN_DIRECT',
              diseases: ['Alzheimer\'s Disease'],
              note: '107 donors · 4 brain regions · protein + pathology + RNA-seq',
              url: 'https://aging.brain-map.org/download/index',
              registered: datasets.some(d => d.short_name === 'allen_aging'),
            },
            {
              name: 'Allen Human Brain Atlas',
              org: 'Allen Institute for Brain Science',
              access: 'OPEN_DIRECT',
              diseases: ['Reference'],
              note: '6 brains · microarray · canonical region ontology',
              url: 'https://human.brain-map.org/static/download',
              registered: datasets.some(d => d.short_name === 'allen_atlas'),
            },
            {
              name: 'OASIS-1 Cross-Sectional',
              org: 'Washington University',
              access: 'OPEN_DIRECT',
              diseases: ['Alzheimer\'s Disease'],
              note: '436 subjects · CDR, MMSE, nWBV, eTIV — longitudinal available',
              url: 'https://www.oasis-brains.org',
              registered: datasets.some(d => d.short_name === 'oasis_1'),
            },
          ].map(ds => (
            <div key={ds.name} className="card card-sm" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                  <span style={{ fontWeight: 600, fontSize: '0.88rem' }}>{ds.name}</span>
                  <span className={`badge ${ds.access === 'OPEN_DIRECT' ? 'badge-pass' : 'badge-warn'}`}>
                    {ds.access === 'OPEN_DIRECT' ? '✓ Open — No Registration' : 'Terms Required'}
                  </span>
                  {ds.registered && <span className="badge badge-sig">In Database</span>}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                  {ds.org} · {ds.note}
                </div>
              </div>
              <a href={ds.url} target="_blank" rel="noreferrer" style={{ fontSize: '0.75rem', color: 'var(--color-accent)', whiteSpace: 'nowrap' }}>
                Source ↗
              </a>
            </div>
          ))}
        </div>
      </div>

      {/* Recent analysis runs */}
      {recentRuns.length > 0 && (
        <div style={{ marginBottom: 32 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 600 }}>Recent Analysis Runs</h2>
            <a href="/analysis-runs" style={{ fontSize: '0.8rem', color: 'var(--color-accent)' }}>View all →</a>
          </div>
          <div className="table-wrap">
            <table className="data-table">
              <thead><tr>
                <th>Run ID</th><th>Disease</th><th>Status</th><th>N</th><th>Completed</th>
              </tr></thead>
              <tbody>
                {recentRuns.map(run => (
                  <tr key={run.analysis_run_id} onClick={() => window.location.href = `/analysis-runs/${run.analysis_run_id}`}>
                    <td><span className="run-id">{run.analysis_run_id}</span></td>
                    <td>{run.disease}</td>
                    <td>
                      <span className={`badge ${run.status === 'COMPLETED' ? 'badge-pass' : run.status === 'FAILED' ? 'badge-fail' : 'badge-warn'}`}>
                        {run.status}
                      </span>
                      {run.is_synthetic && <span className="badge" style={{ marginLeft: 4, background: 'var(--color-synthetic-bg)', color: 'var(--color-synthetic)' }}>SYNTHETIC</span>}
                    </td>
                    <td className="mono">{run.n_total ?? '—'}</td>
                    <td style={{ color: 'var(--color-text-muted)', fontSize: '0.8rem' }}>
                      {run.completed_at ? new Date(run.completed_at).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Scientific disclaimer */}
      <div className="card" style={{ background: 'var(--color-surface-2)', borderColor: 'var(--color-border)' }}>
        <p style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', lineHeight: 1.6 }}>
          <strong>Scientific Disclaimer:</strong> MANAS is a computational research platform.
          Its results represent statistical analyses of publicly available research datasets.
          They should not be interpreted as medical diagnosis, clinical advice, treatment
          recommendations, or proof of biological causation. All analyses are exploratory
          unless explicitly stated otherwise. Findings must be independently validated before
          drawing scientific conclusions.
        </p>
      </div>
    </div>
  );
}
