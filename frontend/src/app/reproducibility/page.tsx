'use client';
import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';

type RunDetail = {
  analysis_run_id: string; analysis_type: string; disease: string; status: string;
  is_synthetic: boolean; statistical_method: string|null; correction_method: string|null;
  effect_size_measure: string|null; covariates: string[]|null; parameters: Record<string,unknown>;
  random_seed: number|null; n_total: number|null; n_disease: number|null; n_control: number|null;
  software_env: Record<string,string>|null; code_commit: string|null;
  ingestion_version: string|null; preprocessing_version: string|null;
  started_at: string|null; completed_at: string|null; error_message: string|null;
};

export default function ReproducibilityPage() {
  return (
    <Suspense fallback={<div className="page-content"><div className="card">Loading reproducibility viewer...</div></div>}>
      <ReproducibilityContent />
    </Suspense>
  );
}

function ReproducibilityContent() {
  const searchParams = useSearchParams();
  const [runId, setRunId] = useState(searchParams.get('run') ?? '');
  const [detail, setDetail] = useState<RunDetail|null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetch = () => {
    if (!runId.trim()) return;
    setLoading(true); setError(''); setDetail(null);
    api.analyses.get(runId.trim())
      .then(d => { setDetail(d as RunDetail); setLoading(false); })
      .catch(e => { setError(String(e.message)); setLoading(false); });
  };

  useEffect(() => { if (searchParams.get('run')) fetch(); }, []);

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Reproducibility</h1>
        <p className="page-subtitle">
          Look up any analysis run by ID to inspect full parameters, software environment,
          and data provenance. Every MANAS run is permanently reproducible.
        </p>
      </div>

      {/* Lookup */}
      <div className="card" style={{ marginBottom:24 }}>
        <div className="section-label" style={{ marginBottom:8 }}>Look up analysis run</div>
        <div style={{ display:'flex', gap:8 }}>
          <input
            value={runId} onChange={e => setRunId(e.target.value)}
            placeholder="e.g. MANAS-AD-2026-00001"
            onKeyDown={e => e.key==='Enter' && fetch()}
            style={{ flex:1, padding:'8px 12px', border:'1px solid var(--color-border)', borderRadius:4,
              fontFamily:'var(--font-mono)', fontSize:'0.85rem' }}
          />
          <button className="btn btn-primary" onClick={fetch} disabled={loading}>
            {loading ? '…' : 'Look up'}
          </button>
        </div>
        {error && <div style={{ marginTop:8, fontSize:'0.8rem', color:'var(--color-fail)' }}>{error}</div>}
      </div>

      {detail && (
        <>
          {detail.is_synthetic && <div className="synthetic-banner" style={{ marginBottom:16 }}>⚠ SYNTHETIC DATA — not real scientific results</div>}

          <div className="grid-2" style={{ gap:24, marginBottom:24 }}>
            {/* Identification */}
            <div className="card">
              <div className="card-header"><div className="card-title">Run Identification</div></div>
              <ProvenanceTable rows={[
                ['Run ID',              detail.analysis_run_id],
                ['Analysis type',       detail.analysis_type],
                ['Disease',             detail.disease],
                ['Status',              detail.status],
                ['Data type',           detail.is_synthetic?'SYNTHETIC':'REAL DATA'],
                ['Started',             detail.started_at ?? '—'],
                ['Completed',           detail.completed_at ?? '—'],
              ]} />
            </div>

            {/* Sample sizes */}
            <div className="card">
              <div className="card-header"><div className="card-title">Sample Sizes</div></div>
              <div className="stat-grid" style={{ gridTemplateColumns:'1fr 1fr', gap:12 }}>
                {[
                  { val: detail.n_total ?? '—',   label: 'Total subjects' },
                  { val: detail.n_disease ?? '—',  label: 'Disease group' },
                  { val: detail.n_control ?? '—',  label: 'Control group' },
                  { val: detail.random_seed ?? '—', label: 'Random seed' },
                ].map(({ val, label }) => (
                  <div key={label} className="stat-box" style={{ padding:'10px 12px' }}>
                    <div style={{ fontFamily:'var(--font-mono)', fontWeight:700, fontSize:'1.1rem' }}>{String(val)}</div>
                    <div className="stat-label">{label}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Statistical specification */}
          <div className="card" style={{ marginBottom:24 }}>
            <div className="card-header"><div className="card-title">Statistical Specification</div></div>
            <ProvenanceTable rows={[
              ['Statistical method',   detail.statistical_method ?? '—'],
              ['Correction',           detail.correction_method ?? '—'],
              ['Effect size measure',  detail.effect_size_measure ?? '—'],
              ['Covariates',           detail.covariates?.join(', ') ?? '—'],
            ]} />
          </div>

          {/* Data provenance */}
          <div className="card" style={{ marginBottom:24 }}>
            <div className="card-header"><div className="card-title">Data Provenance</div></div>
            <ProvenanceTable rows={[
              ['Ingestion version',    detail.ingestion_version ?? '—'],
              ['Preprocessing version',detail.preprocessing_version ?? '—'],
              ['Code commit',          detail.code_commit ?? '—'],
            ]} />
          </div>

          {/* Software environment */}
          {detail.software_env && (
            <div className="card" style={{ marginBottom:24 }}>
              <div className="card-header"><div className="card-title">Software Environment</div></div>
              <ProvenanceTable rows={Object.entries(detail.software_env).map(([k, v]) => [k, v])} />
            </div>
          )}

          {/* Full parameters JSON */}
          <div className="card" style={{ marginBottom:24 }}>
            <div className="card-header"><div className="card-title">Full Parameters (JSON)</div></div>
            <pre style={{ fontFamily:'var(--font-mono)', fontSize:'0.78rem', background:'var(--color-surface-2)',
              border:'1px solid var(--color-border)', borderRadius:4, padding:12,
              overflow:'auto', maxHeight:240, color:'var(--color-text)' }}>
              {JSON.stringify(detail.parameters, null, 2)}
            </pre>
          </div>

          {/* Reproducibility note */}
          <div className="card" style={{ borderColor:'var(--color-accent)', borderLeftWidth:3 }}>
            <div className="section-label" style={{ marginBottom:8 }}>Reproducibility</div>
            <p style={{ fontSize:'0.82rem', color:'var(--color-text-2)', lineHeight:1.7 }}>
              To reproduce this exact analysis:<br />
              1. Use dataset version ID: <code style={{ fontFamily:'var(--font-mono)' }}>{detail.parameters?.version_id as string ?? '—'}</code><br />
              2. Use random seed: <code style={{ fontFamily:'var(--font-mono)' }}>{detail.random_seed}</code><br />
              3. Submit via <code style={{ fontFamily:'var(--font-mono)' }}>POST /api/analyses/</code> with the parameters JSON above.<br />
              The output should be statistically identical given the same data version.
            </p>
          </div>
        </>
      )}

      {/* Reproducibility principles */}
      {!detail && !loading && (
        <div className="card" style={{ background:'var(--color-surface-2)' }}>
          <div className="section-label" style={{ marginBottom:12 }}>MANAS Reproducibility Guarantees</div>
          <ul style={{ fontSize:'0.82rem', color:'var(--color-text-2)', paddingLeft:20, lineHeight:2 }}>
            <li>Every analysis run has a permanent ID: <code style={{ fontFamily:'var(--font-mono)' }}>MANAS-AD-YYYY-NNNNN</code></li>
            <li>All parameters are stored: random seed, covariates, test selection criteria, correction method</li>
            <li>Data version is pinned: checksum + download date recorded at ingestion time</li>
            <li>Software environment is logged: Python, scipy, numpy, pandas versions</li>
            <li>Re-running with the same run ID and data version produces identical results</li>
            <li>QC records are preserved: every check result is queryable</li>
          </ul>
        </div>
      )}
    </div>
  );
}

function ProvenanceTable({ rows }: { rows: [string, string][] }) {
  return (
    <div className="provenance">
      {rows.map(([k, v]) => (
        <div key={k} className="provenance-row">
          <span className="provenance-key">{k}</span>
          <span className="provenance-val">{v}</span>
        </div>
      ))}
    </div>
  );
}
