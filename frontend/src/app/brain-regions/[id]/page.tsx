'use client';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';

interface Region {
  region_id: number; name: string; abbreviation: string;
  hemisphere: string; anatomical_category: string; lobe: string;
  mni_x: number|null; mni_y: number|null; mni_z: number|null;
  is_leaf: boolean; depth: number;
  atlas: { atlas_id: number; name: string; version: string } | null;
  parent: { region_id: number; name: string } | null;
  analysis_results: {
    analysis_run_id: string; disease: string; is_synthetic: boolean;
    n_disease: number; n_control: number;
    disease_mean: number; control_mean: number; mean_difference: number;
    effect_size: number; effect_size_ci_lower: number; effect_size_ci_upper: number;
    p_value: number; adjusted_p_value: number;
    significance_status: string; test_method: string;
  }[];
}

function fmt(n: number|null|undefined, d=3) { return n==null?'—':Number(n).toFixed(d); }

export default function RegionDetailPage() {
  const params = useParams();
  const regionId = params?.id ? Number(params.id) : null;
  const [region, setRegion] = useState<Region|null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!regionId) return;
    api.regions.get(regionId)
      .then(r => { setRegion(r as unknown as Region); setLoading(false); })
      .catch(() => setLoading(false));
  }, [regionId]);

  if (loading) return <div className="page-content"><div className="loading">Loading region…</div></div>;
  if (!region) return <div className="page-content"><div className="empty-state"><div className="empty-state-title">Region not found</div></div></div>;

  return (
    <div className="page-content">
      <div style={{ marginBottom: 16 }}>
        <a href="/brain-regions" style={{ fontSize: '0.82rem', color: 'var(--color-accent)' }}>← Brain Regions</a>
      </div>
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
          <h1 className="page-title">{region.name}</h1>
          {region.abbreviation && <span style={{ fontFamily:'var(--font-mono)', fontSize:'1rem', color:'var(--color-text-muted)', border:'1px solid var(--color-border)', borderRadius:4, padding:'2px 8px' }}>{region.abbreviation}</span>}
        </div>
        <p className="page-subtitle">{region.anatomical_category} · {region.lobe ?? 'no lobe'} · {region.hemisphere}</p>
      </div>

      <div className="grid-2" style={{ gap:24, marginBottom:24 }}>
        {/* Region metadata */}
        <div className="card">
          <div className="card-header"><div className="card-title">Region Information</div></div>
          {[
            ['Atlas', region.atlas?.name ?? '—'],
            ['Atlas version', region.atlas?.version ?? '—'],
            ['Category', region.anatomical_category],
            ['Hemisphere', region.hemisphere],
            ['Lobe', region.lobe ?? '—'],
            ['Depth', String(region.depth)],
            ['Leaf node', region.is_leaf ? 'Yes' : 'No'],
            ['Parent region', region.parent ? region.parent.name : '— (root)'],
            ['MNI X', fmt(region.mni_x, 1)],
            ['MNI Y', fmt(region.mni_y, 1)],
            ['MNI Z', fmt(region.mni_z, 1)],
          ].map(([k, v]) => (
            <div key={k} style={{ display:'flex', gap:16, padding:'5px 0', borderBottom:'1px solid var(--color-border)', fontSize:'0.82rem' }}>
              <span style={{ color:'var(--color-text-muted)', width:130, flexShrink:0 }}>{k}</span>
              <span style={{ fontWeight:500 }}>{v}</span>
            </div>
          ))}
        </div>

        {/* Quick stats from latest result */}
        {region.analysis_results.length > 0 && (() => {
          const r = region.analysis_results[0];
          return (
            <div className="card">
              <div className="card-header">
                <div className="card-title">Latest Analysis Result</div>
                <div className="card-subtitle">{r.disease} · <span className="run-id">{r.analysis_run_id}</span></div>
              </div>
              {r.is_synthetic && <div className="synthetic-banner" style={{ marginBottom:12 }}>⚠ SYNTHETIC DATA</div>}
              <div className="stat-grid" style={{ gridTemplateColumns:'1fr 1fr', gap:12 }}>
                {[
                  { val: fmt(r.effect_size), label: 'Effect size (d)' },
                  { val: `${fmt(r.effect_size_ci_lower,2)}, ${fmt(r.effect_size_ci_upper,2)}`, label: '95% CI' },
                  { val: fmt(r.p_value, 4), label: 'p-value' },
                  { val: fmt(r.adjusted_p_value, 4), label: 'adj. p (BH FDR)' },
                  { val: String(r.n_disease), label: 'N (AD)' },
                  { val: String(r.n_control), label: 'N (Control)' },
                  { val: fmt(r.disease_mean), label: 'AD mean' },
                  { val: fmt(r.control_mean), label: 'Control mean' },
                ].map(({ val, label }) => (
                  <div key={label} className="stat-box" style={{ padding:'10px 12px' }}>
                    <div style={{ fontFamily:'var(--font-mono)', fontWeight:700, fontSize:'1rem' }}>{val}</div>
                    <div className="stat-label">{label}</div>
                  </div>
                ))}
              </div>
              <div style={{ marginTop:16 }}>
                <span className={`badge ${r.significance_status==='FDR_SIGNIFICANT'?'badge-sig':r.significance_status==='INSUFFICIENT_DATA'?'badge-insufficient':'badge-not-sig'}`}>
                  {r.significance_status.replace(/_/g,' ')}
                </span>
                <span style={{ fontSize:'0.75rem', color:'var(--color-text-muted)', marginLeft:8 }}>{r.test_method}</span>
              </div>
            </div>
          );
        })()}
      </div>

      {/* All results across runs */}
      {region.analysis_results.length > 1 && (
        <div className="card" style={{ marginBottom:24 }}>
          <div className="card-header"><div className="card-title">All Analysis Results for this Region</div></div>
          <div className="table-wrap">
            <table className="data-table">
              <thead><tr>
                <th>Run ID</th><th>Disease</th><th>N AD</th><th>N Ctrl</th>
                <th>Effect size</th><th>95% CI</th><th>adj. p</th><th>Significance</th><th>Test</th>
              </tr></thead>
              <tbody>
                {region.analysis_results.map(r => (
                  <tr key={r.analysis_run_id} onClick={() => window.location.href=`/analysis-runs/${r.analysis_run_id}`}>
                    <td><span className="run-id">{r.analysis_run_id}</span></td>
                    <td>{r.disease}</td>
                    <td className="mono">{r.n_disease}</td>
                    <td className="mono">{r.n_control}</td>
                    <td className="mono">{fmt(r.effect_size)}</td>
                    <td className="mono" style={{ fontSize:'0.75rem' }}>[{fmt(r.effect_size_ci_lower,2)}, {fmt(r.effect_size_ci_upper,2)}]</td>
                    <td className="mono">{fmt(r.adjusted_p_value,4)}</td>
                    <td><span className={`badge ${r.significance_status==='FDR_SIGNIFICANT'?'badge-sig':'badge-not-sig'}`}>{r.significance_status.replace(/_/g,' ')}</span></td>
                    <td style={{ fontSize:'0.75rem', color:'var(--color-text-muted)' }}>{r.test_method}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="card" style={{ background:'var(--color-surface-2)', fontSize:'0.78rem', color:'var(--color-text-muted)' }}>
        Statistical associations from post-mortem research datasets. Not a medical finding.
      </div>
    </div>
  );
}
