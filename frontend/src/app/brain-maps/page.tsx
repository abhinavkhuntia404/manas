'use client';
import { useEffect, useRef, useState } from 'react';
import { api, type AnalysisResult, type AnalysisRun } from '@/lib/api';

/**
 * Brain Maps — D3-style SVG schematic of the 4 Allen Aging brain regions
 * coloured by effect size from the latest analysis run.
 *
 * Regions: HIP (Hippocampus), TCx (Temporal Cortex),
 *          PCx (Parietal Cortex), FWM (Frontal White Matter)
 */

// Schematic positions for each region in SVG space (650×420 viewBox)
const REGION_SHAPES: Record<string, {
  path: string; label: string; cx: number; cy: number;
}> = {
  TCx: {
    label: 'Temporal Cortex',
    cx: 180, cy: 200,
    path: 'M 120,140 Q 80,100 90,180 Q 95,240 150,260 Q 195,270 210,240 Q 240,200 220,160 Q 200,120 160,130 Z',
  },
  PCx: {
    label: 'Parietal Cortex',
    cx: 340, cy: 130,
    path: 'M 240,80 Q 280,50 360,60 Q 420,70 440,120 Q 450,160 420,180 Q 380,200 320,190 Q 270,180 240,150 Q 220,120 240,80 Z',
  },
  FWM: {
    label: 'Frontal White Matter',
    cx: 490, cy: 200,
    path: 'M 440,150 Q 480,110 540,130 Q 590,150 600,200 Q 610,250 580,280 Q 545,300 500,290 Q 455,275 440,240 Q 425,210 440,150 Z',
  },
  HIP: {
    label: 'Hippocampus',
    cx: 320, cy: 300,
    path: 'M 260,270 Q 270,240 310,235 Q 360,230 390,255 Q 415,275 400,305 Q 385,330 350,340 Q 300,345 275,325 Q 255,305 260,270 Z',
  },
};

function effectToColor(effect: number | null | undefined): string {
  if (effect == null) return '#e2e8f0';
  const abs = Math.abs(effect);
  if (abs < 0.2) return '#e2e8f0';         // negligible
  if (effect > 0) {
    // AD > Control — disease-associated increase (orange-red)
    if (abs < 0.5) return '#fed7aa';
    if (abs < 0.8) return '#f97316';
    return '#dc2626';
  } else {
    // AD < Control — disease-associated decrease (blue)
    if (abs < 0.5) return '#bfdbfe';
    if (abs < 0.8) return '#3b82f6';
    return '#1d4ed8';
  }
}

export default function BrainMapsPage() {
  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, AnalysisResult>>({});
  const [hovered, setHovered] = useState<string | null>(null);
  const [isSynthetic, setIsSynthetic] = useState(false);

  useEffect(() => {
    api.analyses.list({ disease: "Alzheimer", status: "COMPLETED" }).then(d => {
      setRuns(d.runs);
      if (d.runs[0]) setSelectedRun(d.runs[0].analysis_run_id);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedRun) return;
    api.analyses.results(selectedRun, { page_size: 500 }).then(d => {
      setIsSynthetic(d.is_synthetic);
      const map: Record<string, AnalysisResult> = {};
      d.results.forEach(r => { map[r.region_name] = r; });
      // Also key by abbreviation
      d.results.forEach(r => {
        const abbrev = Object.entries(REGION_SHAPES).find(
          ([, v]) => v.label.toLowerCase() === r.region_name.toLowerCase()
        )?.[0];
        if (abbrev) map[abbrev] = r;
      });
      setResults(map);
    }).catch(() => {});
  }, [selectedRun]);

  const hoveredResult = hovered
    ? results[hovered] ?? Object.values(results).find(r => r.region_name === REGION_SHAPES[hovered]?.label)
    : null;

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Brain Maps</h1>
        <p className="page-subtitle">
          Schematic brain visualisation — regions coloured by Alzheimer&apos;s-associated
          effect size from the selected analysis run. Red = AD &gt; Control; Blue = AD &lt; Control.
        </p>
      </div>

      {isSynthetic && (
        <div className="synthetic-banner">
          ⚠ SYNTHETIC DATA — Colours represent synthetic demo results, not real biological findings.
        </div>
      )}

      <div className="grid-2" style={{ gap: 24, alignItems: 'start' }}>
        {/* SVG brain schematic */}
        <div className="brain-map-container">
          <div className="section-label" style={{ marginBottom: 12 }}>
            Allen Aging Study — 4 Sampled Brain Regions
          </div>
          <svg viewBox="0 0 680 400" style={{ width: '100%', height: 'auto' }}>
            {/* Brain outline */}
            <ellipse cx="340" cy="210" rx="300" ry="180" fill="#f8f9fb" stroke="#dde1e9" strokeWidth="1.5" />
            {/* Corpus callosum hint */}
            <path d="M 200,210 Q 340,170 480,210" fill="none" stroke="#dde1e9" strokeWidth="1" strokeDasharray="4,3" />

            {Object.entries(REGION_SHAPES).map(([key, shape]) => {
              const res = results[key];
              const effect = res?.effect_size;
              const fill = effectToColor(effect);
              const sig = res?.significance_status === 'FDR_SIGNIFICANT';
              const isHov = hovered === key;
              return (
                <g key={key}
                  onMouseEnter={() => setHovered(key)}
                  onMouseLeave={() => setHovered(null)}
                  onClick={() => res && (window.location.href = `/brain-regions/${res.region_id}`)}
                  style={{ cursor: res ? 'pointer' : 'default' }}>
                  <path
                    d={shape.path}
                    fill={fill}
                    stroke={isHov ? '#1a56db' : sig ? '#1a56db' : '#b0b8c8'}
                    strokeWidth={isHov ? 2.5 : sig ? 1.5 : 1}
                    opacity={isHov ? 1 : 0.85}
                    style={{ transition: 'all 0.15s' }}
                  />
                  {/* Region label */}
                  <text x={shape.cx} y={shape.cy - 8} textAnchor="middle"
                    style={{ fontSize: '11px', fontWeight: 600, fill: '#1a1f2e', pointerEvents: 'none' }}>
                    {key}
                  </text>
                  <text x={shape.cx} y={shape.cy + 6} textAnchor="middle"
                    style={{ fontSize: '9px', fill: '#4a5568', pointerEvents: 'none' }}>
                    {shape.label}
                  </text>
                  {effect != null && (
                    <text x={shape.cx} y={shape.cy + 19} textAnchor="middle"
                      style={{ fontSize: '10px', fontFamily: 'monospace', fill: '#1a1f2e', fontWeight: 700, pointerEvents: 'none' }}>
                      d={effect >= 0 ? '+' : ''}{effect.toFixed(2)}
                    </text>
                  )}
                  {sig && (
                    <text x={shape.cx} y={shape.cy + 31} textAnchor="middle"
                      style={{ fontSize: '9px', fill: '#1a56db', pointerEvents: 'none' }}>
                      ✓ FDR sig.
                    </text>
                  )}
                </g>
              );
            })}
          </svg>

          {/* Legend */}
          <div className="brain-map-legend">
            <span style={{ fontWeight: 600 }}>Effect size colour scale:</span>
            {[
              { color: '#dc2626', label: 'Large AD > Ctrl (d>0.8)' },
              { color: '#f97316', label: 'Medium (0.5–0.8)' },
              { color: '#fed7aa', label: 'Small (0.2–0.5)' },
              { color: '#e2e8f0', label: 'Negligible (<0.2)' },
              { color: '#3b82f6', label: 'Medium AD < Ctrl' },
              { color: '#1d4ed8', label: 'Large AD < Ctrl' },
            ].map(({ color, label }) => (
              <span key={label} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 12, height: 12, borderRadius: 2, background: color, flexShrink: 0 }} />
                {label}
              </span>
            ))}
          </div>
        </div>

        {/* Detail panel */}
        <div>
          {/* Run selector */}
          {runs.length > 0 && (
            <div className="card card-sm" style={{ marginBottom: 16 }}>
              <div className="section-label" style={{ marginBottom: 6 }}>Analysis Run</div>
              <select value={selectedRun ?? ''} onChange={e => setSelectedRun(e.target.value)}
                style={{ width: '100%', fontFamily: 'var(--font-mono)', fontSize: '0.8rem',
                  border: '1px solid var(--color-border)', borderRadius: 4,
                  padding: '6px 10px', background: 'var(--color-surface)' }}>
                {runs.map(r => (
                  <option key={r.analysis_run_id} value={r.analysis_run_id}>
                    {r.analysis_run_id}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Hover detail */}
          {hovered && (
            <div className="card" style={{ marginBottom: 16, borderColor: 'var(--color-accent)' }}>
              <div style={{ fontWeight: 600, marginBottom: 8 }}>{REGION_SHAPES[hovered]?.label}</div>
              {hoveredResult ? (
                <div style={{ fontSize: '0.82rem', display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {[
                    ['Effect size (d)', hoveredResult.effect_size?.toFixed(3)],
                    ['95% CI', `[${hoveredResult.effect_size_ci_lower?.toFixed(3)}, ${hoveredResult.effect_size_ci_upper?.toFixed(3)}]`],
                    ['p-value', hoveredResult.p_value?.toFixed(4)],
                    ['adj. p (BH)', hoveredResult.adjusted_p_value?.toFixed(4)],
                    ['AD mean', hoveredResult.disease_mean?.toFixed(4)],
                    ['Control mean', hoveredResult.control_mean?.toFixed(4)],
                    ['N (AD/Ctrl)', `${hoveredResult.n_disease} / ${hoveredResult.n_control}`],
                    ['Test', hoveredResult.test_method],
                    ['Significance', hoveredResult.significance_status],
                  ].map(([k, v]) => (
                    <div key={k} style={{ display: 'flex', gap: 8 }}>
                      <span style={{ color: 'var(--color-text-muted)', width: 130, flexShrink: 0 }}>{k}</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}>{v ?? '—'}</span>
                    </div>
                  ))}
                  <a href={`/brain-regions/${hoveredResult.region_id}`}
                    style={{ marginTop: 8, color: 'var(--color-accent)', fontSize: '0.8rem' }}>
                    View region detail →
                  </a>
                </div>
              ) : (
                <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>
                  No analysis results for this region yet.
                </p>
              )}
            </div>
          )}

          {/* All region summary */}
          <div className="card">
            <div className="section-label" style={{ marginBottom: 10 }}>Region Summary</div>
            {Object.entries(REGION_SHAPES).map(([key, shape]) => {
              const res = results[key];
              const fill = effectToColor(res?.effect_size);
              return (
                <div key={key}
                  onClick={() => setHovered(hovered === key ? null : key)}
                  style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0',
                    borderBottom: '1px solid var(--color-border)', cursor: 'pointer',
                    background: hovered === key ? 'var(--color-accent-bg)' : undefined }}>
                  <span style={{ width: 14, height: 14, borderRadius: 3, background: fill, flexShrink: 0, border: '1px solid #b0b8c8' }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 500 }}>{shape.label}</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {res ? `d = ${res.effect_size?.toFixed(3) ?? '—'} · ${res.significance_status}` : 'No result'}
                    </div>
                  </div>
                  {res?.significance_status === 'FDR_SIGNIFICANT' && (
                    <span className="badge badge-sig" style={{ fontSize: '0.65rem' }}>★ FDR</span>
                  )}
                </div>
              );
            })}
          </div>

          <div style={{ marginTop: 16, fontSize: '0.72rem', color: 'var(--color-text-muted)', lineHeight: 1.6 }}>
            <strong>Note:</strong> Only 4 brain regions are sampled in the Allen Aging Study.
            This schematic is anatomically approximate, not a full MRI atlas.
            Regions are shown bilaterally (Allen Aging measures are not hemisphere-specific).
          </div>
        </div>
      </div>
    </div>
  );
}
