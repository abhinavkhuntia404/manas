'use client';
import { useEffect, useState } from 'react';
import { api, type AnalysisRun } from '@/lib/api';

export default function AnalysisRunsPage() {
  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [pollId, setPollId] = useState<string|null>(null);
  const [filterStatus, setFilterStatus] = useState('');

  // Form state
  const [form, setForm] = useState({
    version_id: 1,
    disease: "Alzheimer's Disease",
    measurement_type_name: 'ihc_at8_ffpe',
    random_seed: 42,
  });

  const load = () => {
    api.analyses.list({ status: filterStatus || undefined, page: 1 })
      .then(d => { setRuns(d.runs); setTotal(d.total); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { load(); }, [filterStatus]);

  // Poll running job
  useEffect(() => {
    if (!pollId) return;
    const t = setInterval(() => {
      api.analyses.get(pollId).then(d => {
        if (d.status === 'COMPLETED' || d.status === 'FAILED') {
          clearInterval(t); setPollId(null); load();
        }
      }).catch(() => clearInterval(t));
    }, 2000);
    return () => clearInterval(t);
  }, [pollId]);

  const submit = async () => {
    setSubmitting(true);
    try {
      const r = await api.analyses.submit({ ...form, covariates: ['age', 'sex'] });
      setPollId(r.analysis_run_id);
      load();
    } catch (e: unknown) {
      alert(`Submit failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally { setSubmitting(false); }
  };

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Analysis Runs</h1>
        <p className="page-subtitle">Submit, monitor, and audit all analysis jobs. Every run gets a permanent reproducible ID.</p>
      </div>

      <div className="grid-2" style={{ gap:24, alignItems:'start', marginBottom:32 }}>
        {/* Submit form */}
        <div className="card">
          <div className="card-header"><div className="card-title">Submit New Analysis</div></div>
          <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
            {[
              { label:'Disease', name:'disease', type:'select', options:["Alzheimer's Disease", 'Vascular', 'Lewy Body'] },
              { label:'Measurement type', name:'measurement_type_name', type:'select',
                options:['ihc_at8_ffpe','ihc_a_beta_ffpe','tau_ng_per_mg','ptau_ng_per_mg','ab42_pg_per_mg',
                         'ihc_a_syn','normalized_whole_brain_volume','mmse_score','cdr_score'] },
              { label:'Dataset version ID', name:'version_id', type:'number' },
              { label:'Random seed', name:'random_seed', type:'number' },
            ].map(f => (
              <div key={f.name}>
                <label style={{ fontSize:'0.78rem', color:'var(--color-text-muted)', display:'block', marginBottom:4 }}>{f.label}</label>
                {f.type === 'select' ? (
                  <select value={(form as Record<string,unknown>)[f.name] as string}
                    onChange={e => setForm(prev => ({ ...prev, [f.name]: e.target.value }))}
                    style={{ width:'100%', padding:'7px 10px', border:'1px solid var(--color-border)', borderRadius:4, fontSize:'0.85rem', background:'var(--color-surface)' }}>
                    {f.options?.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                ) : (
                  <input type={f.type} value={(form as Record<string,unknown>)[f.name] as string|number}
                    onChange={e => setForm(prev => ({ ...prev, [f.name]: Number(e.target.value) }))}
                    style={{ width:'100%', padding:'7px 10px', border:'1px solid var(--color-border)', borderRadius:4, fontSize:'0.85rem', fontFamily:'var(--font-mono)' }} />
                )}
              </div>
            ))}
            <div style={{ fontSize:'0.75rem', color:'var(--color-text-muted)', background:'var(--color-surface-2)', borderRadius:4, padding:'8px 10px' }}>
              Covariates: age, sex (applied automatically)
            </div>
            <button className="btn btn-primary" onClick={submit} disabled={submitting}>
              {submitting ? 'Submitting…' : pollId ? `⟳ Running ${pollId}…` : 'Submit Analysis'}
            </button>
          </div>
        </div>

        {/* Quick guide */}
        <div className="card" style={{ background:'var(--color-surface-2)' }}>
          <div className="card-header"><div className="card-title">How to run</div></div>
          <ol style={{ fontSize:'0.82rem', color:'var(--color-text-2)', paddingLeft:20, lineHeight:2 }}>
            <li>Trigger ingestion: <code style={{ fontFamily:'var(--font-mono)', fontSize:'0.75rem' }}>POST /api/ingestion/allen-aging</code></li>
            <li>Note the <code style={{ fontFamily:'var(--font-mono)', fontSize:'0.75rem' }}>version_id</code> returned</li>
            <li>Enter the version_id and measurement type above</li>
            <li>Click Submit — analysis runs in background</li>
            <li>Results appear in the Alzheimer&apos;s Analysis page and Brain Maps</li>
          </ol>
          <div style={{ marginTop:16, fontSize:'0.75rem', color:'var(--color-text-muted)' }}>
            Each run gets a permanent <code style={{ fontFamily:'var(--font-mono)' }}>MANAS-AD-YYYY-NNNNN</code> ID
            for full reproducibility.
          </div>
        </div>
      </div>

      {/* Filter + list */}
      <div style={{ display:'flex', gap:12, marginBottom:16, alignItems:'center' }}>
        <h2 style={{ fontSize:'1rem', fontWeight:600, flex:1 }}>All Runs ({total})</h2>
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
          style={{ padding:'6px 10px', border:'1px solid var(--color-border)', borderRadius:4, fontSize:'0.82rem', background:'var(--color-surface)' }}>
          <option value="">All statuses</option>
          {['QUEUED','RUNNING','COMPLETED','FAILED'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <button className="btn btn-secondary btn-sm" onClick={load}>↻ Refresh</button>
      </div>

      {loading && <div className="loading">Loading runs…</div>}
      {!loading && runs.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-title">No analysis runs yet</div>
          <p style={{ fontSize:'0.82rem', marginTop:4 }}>Ingest data and submit an analysis above.</p>
        </div>
      )}
      {runs.length > 0 && (
        <div className="table-wrap">
          <table className="data-table">
            <thead><tr>
              <th>Run ID</th><th>Disease</th><th>Status</th><th>Data</th>
              <th>N total</th><th>Method</th><th>Started</th><th>Completed</th>
            </tr></thead>
            <tbody>
              {runs.map(r => (
                <tr key={r.analysis_run_id} onClick={() => window.location.href=`/analysis-runs/${r.analysis_run_id}`}>
                  <td><span className="run-id">{r.analysis_run_id}</span></td>
                  <td>{r.disease}</td>
                  <td>
                    <span className={`badge ${r.status==='COMPLETED'?'badge-pass':r.status==='FAILED'?'badge-fail':'badge-warn'}`}>{r.status}</span>
                    {r.is_synthetic && <span className="badge" style={{ marginLeft:4, background:'var(--color-synthetic-bg)', color:'var(--color-synthetic)' }}>SYNTH</span>}
                  </td>
                  <td style={{ fontSize:'0.75rem', color:'var(--color-text-muted)' }}>{r.is_synthetic?'Synthetic':'Real'}</td>
                  <td className="mono">{r.n_total??'—'}</td>
                  <td style={{ fontSize:'0.72rem', color:'var(--color-text-muted)', maxWidth:180, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{r.statistical_method?.split('(')[0]??'—'}</td>
                  <td style={{ fontSize:'0.75rem', color:'var(--color-text-muted)' }}>{r.started_at?new Date(r.started_at).toLocaleTimeString():'-'}</td>
                  <td style={{ fontSize:'0.75rem', color:'var(--color-text-muted)' }}>{r.completed_at?new Date(r.completed_at).toLocaleDateString():'-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
