'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

type MeasRow = { region_name: string; disease_status: string; value: number; measurement_name: string; };

const MEASUREMENTS = [
  'ihc_at8_ffpe','ihc_a_beta_ffpe','tau_ng_per_mg','ptau_ng_per_mg','ab42_pg_per_mg',
  'ihc_a_syn','normalized_whole_brain_volume','mmse_score','cdr_score',
];

export default function DataExplorerPage() {
  const [regions, setRegions] = useState<{ region_id:number; name:string; abbreviation:string }[]>([]);
  const [selectedRegion, setSelectedRegion] = useState('');
  const [selectedMeasure, setSelectedMeasure] = useState(MEASUREMENTS[0]);
  const [note] = useState('Connect to the backend and run an ingestion first to explore real data.');

  useEffect(() => {
    api.regions.list({ page_size: 100 }).then(d => setRegions(d.regions)).catch(() => {});
  }, []);

  // Placeholder data for demo — grouped by disease
  const demoData = [
    { region:'HIP', disease:'AD', n:50, mean:0.0024, sd:0.0008, label:'Hippocampus' },
    { region:'HIP', disease:'Control', n:52, mean:0.0011, sd:0.0004, label:'Hippocampus' },
    { region:'TCx', disease:'AD', n:50, mean:0.0038, sd:0.0012, label:'Temporal Cortex' },
    { region:'TCx', disease:'Control', n:52, mean:0.0016, sd:0.0006, label:'Temporal Cortex' },
    { region:'PCx', disease:'AD', n:50, mean:0.0029, sd:0.0009, label:'Parietal Cortex' },
    { region:'PCx', disease:'Control', n:52, mean:0.0013, sd:0.0005, label:'Parietal Cortex' },
    { region:'FWM', disease:'AD', n:50, mean:0.0041, sd:0.0015, label:'Frontal White Matter' },
    { region:'FWM', disease:'Control', n:52, mean:0.0019, sd:0.0007, label:'Frontal White Matter' },
  ];

  const maxMean = Math.max(...demoData.map(d => d.mean));

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Data Explorer</h1>
        <p className="page-subtitle">
          Query and visualise measurement distributions by region, disease group, and measurement type.
        </p>
      </div>

      <div className="synthetic-banner" style={{ marginBottom:24 }}>
        ⚠ Showing illustrative summary statistics — ingest real data to explore actual values.
      </div>

      {/* Controls */}
      <div className="card card-sm" style={{ marginBottom:24, display:'flex', gap:16, flexWrap:'wrap', alignItems:'flex-end' }}>
        <div>
          <label style={{ fontSize:'0.75rem', color:'var(--color-text-muted)', display:'block', marginBottom:4 }}>Measurement</label>
          <select value={selectedMeasure} onChange={e => setSelectedMeasure(e.target.value)}
            style={{ padding:'7px 12px', border:'1px solid var(--color-border)', borderRadius:4, fontSize:'0.82rem', background:'var(--color-surface)', fontFamily:'var(--font-mono)' }}>
            {MEASUREMENTS.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>
        {regions.length > 0 && (
          <div>
            <label style={{ fontSize:'0.75rem', color:'var(--color-text-muted)', display:'block', marginBottom:4 }}>Region</label>
            <select value={selectedRegion} onChange={e => setSelectedRegion(e.target.value)}
              style={{ padding:'7px 12px', border:'1px solid var(--color-border)', borderRadius:4, fontSize:'0.82rem', background:'var(--color-surface)' }}>
              <option value="">All regions</option>
              {regions.map(r => <option key={r.region_id} value={String(r.region_id)}>{r.name}</option>)}
            </select>
          </div>
        )}
      </div>

      <div className="grid-2" style={{ gap:24 }}>
        {/* Bar chart — mean by region × group */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">Group Means by Region</div>
            <div className="card-subtitle">{selectedMeasure} — AD vs Control</div>
          </div>
          <div style={{ padding:'8px 0' }}>
            {['HIP','TCx','PCx','FWM'].map(reg => {
              const ad  = demoData.find(d => d.region===reg && d.disease==='AD');
              const ctrl = demoData.find(d => d.region===reg && d.disease==='Control');
              if (!ad || !ctrl) return null;
              return (
                <div key={reg} style={{ marginBottom:16 }}>
                  <div style={{ fontSize:'0.8rem', fontWeight:600, marginBottom:6 }}>{ad.label} ({reg})</div>
                  {/* AD bar */}
                  <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:4 }}>
                    <span style={{ fontSize:'0.72rem', color:'var(--color-text-muted)', width:50 }}>AD</span>
                    <div style={{ flex:1, background:'var(--color-surface-2)', borderRadius:2, height:12, position:'relative' }}>
                      <div style={{ position:'absolute', left:0, top:0, height:'100%', borderRadius:2,
                        background:'#dc2626', width:`${(ad.mean/maxMean)*100}%` }} />
                    </div>
                    <span style={{ fontFamily:'var(--font-mono)', fontSize:'0.72rem', width:60, textAlign:'right' }}>
                      {ad.mean.toFixed(4)}
                    </span>
                  </div>
                  {/* Control bar */}
                  <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                    <span style={{ fontSize:'0.72rem', color:'var(--color-text-muted)', width:50 }}>Ctrl</span>
                    <div style={{ flex:1, background:'var(--color-surface-2)', borderRadius:2, height:12, position:'relative' }}>
                      <div style={{ position:'absolute', left:0, top:0, height:'100%', borderRadius:2,
                        background:'#3b82f6', width:`${(ctrl.mean/maxMean)*100}%` }} />
                    </div>
                    <span style={{ fontFamily:'var(--font-mono)', fontSize:'0.72rem', width:60, textAlign:'right' }}>
                      {ctrl.mean.toFixed(4)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
          <div style={{ fontSize:'0.72rem', color:'var(--color-text-muted)', marginTop:8 }}>
            🔴 AD · 🔵 Control · Values are illustrative summary statistics
          </div>
        </div>

        {/* Summary table */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">Summary Statistics</div>
            <div className="card-subtitle">Mean ± SD per region × group</div>
          </div>
          <div className="table-wrap" style={{ border:'none' }}>
            <table className="data-table">
              <thead><tr><th>Region</th><th>Group</th><th>N</th><th>Mean</th><th>SD</th></tr></thead>
              <tbody>
                {demoData.map((d, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight:500 }}>{d.label}</td>
                    <td><span className={`badge ${d.disease==='AD'?'badge-fail':'badge-sig'}`}>{d.disease}</span></td>
                    <td className="mono">{d.n}</td>
                    <td className="mono">{d.mean.toFixed(4)}</td>
                    <td className="mono">{d.sd.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ marginTop:12, fontSize:'0.72rem', color:'var(--color-text-muted)' }}>
            {note}
          </div>
        </div>
      </div>
    </div>
  );
}
