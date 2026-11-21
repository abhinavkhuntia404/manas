'use client';
import { useState, useEffect } from 'react';
import {
  api,
  type LongitudinalRequest,
  type LongitudinalResponse,
  type VisitPoint,
  type FittedTrajectoryPoint,
} from '@/lib/api';

const OASIS_CASES: Record<string, { label: string; cohort: string; visits: VisitPoint[] }> = {
  converted: {
    label: 'OAS2_0031 — Demented Converter (Visit 1 to 3)',
    cohort: 'OASIS-2 Longitudinal (Converted)',
    visits: [
      { visit_id: 1, time_days: 0, age: 78.0, mmse: 28, cdr: 0.0, nwbv: 0.748, etiv: 1475 },
      { visit_id: 2, time_days: 706, age: 79.9, mmse: 26, cdr: 0.5, nwbv: 0.729, etiv: 1480 },
      { visit_id: 3, time_days: 1461, age: 82.0, mmse: 22, cdr: 1.0, nwbv: 0.704, etiv: 1485 },
    ],
  },
  stable_control: {
    label: 'OAS2_0001 — Nondemented Stable Control',
    cohort: 'OASIS-2 Longitudinal (Nondemented)',
    visits: [
      { visit_id: 1, time_days: 0, age: 87.0, mmse: 27, cdr: 0.0, nwbv: 0.696, etiv: 1987 },
      { visit_id: 2, time_days: 753, age: 89.1, mmse: 30, cdr: 0.0, nwbv: 0.681, etiv: 2004 },
    ],
  },
  progressive_ad: {
    label: 'OAS2_0002 — Rapid Progressive Alzheimer’s',
    cohort: 'OASIS-2 Longitudinal (Demented)',
    visits: [
      { visit_id: 1, time_days: 0, age: 75.0, mmse: 23, cdr: 0.5, nwbv: 0.736, etiv: 1678 },
      { visit_id: 2, time_days: 560, age: 76.5, mmse: 22, cdr: 0.5, nwbv: 0.716, etiv: 1689 },
      { visit_id: 3, time_days: 1395, age: 78.8, mmse: 16, cdr: 1.0, nwbv: 0.680, etiv: 1690 },
    ],
  },
};

export default function LongitudinalPage() {
  const [selectedCase, setSelectedCase] = useState<string>('converted');
  const [subjectId, setSubjectId] = useState<string>('OAS2_0031');
  const [visits, setVisits] = useState<VisitPoint[]>(OASIS_CASES.converted.visits);
  const [analysis, setAnalysis] = useState<LongitudinalResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    runAnalysis(subjectId, visits);
  }, []);

  const runAnalysis = async (subj: string, vList: VisitPoint[]) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.predictions.longitudinal({
        subject_id: subj,
        visits: vList,
      });
      setAnalysis(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Longitudinal modeling failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectCase = (key: string) => {
    setSelectedCase(key);
    const item = OASIS_CASES[key];
    if (item) {
      setSubjectId(key === 'converted' ? 'OAS2_0031' : key === 'stable_control' ? 'OAS2_0001' : 'OAS2_0002');
      setVisits(item.visits);
      runAnalysis(item.label.split(' ')[0], item.visits);
    }
  };

  const handleVisitChange = (index: number, field: keyof VisitPoint, value: number) => {
    const updated = [...visits];
    updated[index] = { ...updated[index], [field]: value };
    setVisits(updated);
  };

  const addVisit = () => {
    const last = visits[visits.length - 1];
    const newVisit: VisitPoint = {
      visit_id: visits.length + 1,
      time_days: (last ? last.time_days : 0) + 365,
      age: (last ? last.age : 75) + 1,
      mmse: last?.mmse ? Math.max(0, last.mmse - 1) : 25,
      cdr: last?.cdr ?? 0.5,
      nwbv: last?.nwbv ? Math.max(0.6, last.nwbv - 0.01) : 0.72,
      etiv: last?.etiv ?? 1500,
    };
    const updated = [...visits, newVisit];
    setVisits(updated);
    runAnalysis(subjectId, updated);
  };

  return (
    <div className="page-content">
      {/* Page Header */}
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 8 }}>
          <h1 className="page-title">Longitudinal Research</h1>
          <span style={{ fontSize: '0.78rem', background: 'var(--color-accent-bg)', color: 'var(--color-accent)', border: '1px solid var(--color-border)', borderRadius: 4, padding: '2px 8px', fontWeight: 600 }}>
            MANAS V2
          </span>
        </div>
        <p className="page-subtitle">
          Longitudinal trajectory modeling, annualized brain parenchyma loss (% nWBV/year), rate of cognitive decline,
          and conversion risk estimation calibrated on OASIS-2 repeat visit cohorts.
        </p>
      </div>

      {/* Case Presets */}
      <div className="card card-sm" style={{ marginBottom: 20 }}>
        <div className="section-label" style={{ marginBottom: 8 }}>OASIS-2 Longitudinal Cohort Trajectories</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {Object.entries(OASIS_CASES).map(([key, item]) => (
            <button
              key={key}
              onClick={() => handleSelectCase(key)}
              style={{
                padding: '6px 12px',
                borderRadius: 'var(--radius-sm)',
                border: selectedCase === key ? '1px solid var(--color-accent)' : '1px solid var(--color-border)',
                background: selectedCase === key ? 'var(--color-accent-bg)' : 'var(--color-surface-2)',
                color: selectedCase === key ? 'var(--color-accent)' : 'var(--color-text)',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <div style={{ fontWeight: 600, fontSize: '0.8rem' }}>{item.label}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>{item.cohort}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Multi-Visit Observation Table Card */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <div>
            <div className="section-label">Observed Longitudinal Visits</div>
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Subject: {subjectId}</h3>
          </div>
          <button
            onClick={addVisit}
            style={{
              padding: '5px 12px',
              borderRadius: 4,
              border: '1px solid var(--color-border-strong)',
              background: 'var(--color-surface-2)',
              fontSize: '0.78rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            + Add Observation Visit
          </button>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="data-table" style={{ width: '100%', fontSize: '0.82rem' }}>
            <thead>
              <tr>
                <th>Visit</th>
                <th>Days from Baseline</th>
                <th>Subject Age</th>
                <th>MMSE Score (0–30)</th>
                <th>CDR Rating</th>
                <th>Whole Brain Vol (nWBV)</th>
                <th>Intracranial Vol (eTIV)</th>
              </tr>
            </thead>
            <tbody>
              {visits.map((v, i) => (
                <tr key={v.visit_id}>
                  <td><strong>Visit {v.visit_id}</strong></td>
                  <td>
                    <input
                      type="number"
                      value={v.time_days}
                      onChange={(e) => handleVisitChange(i, 'time_days', parseFloat(e.target.value) || 0)}
                      style={{ width: 80, padding: '3px 6px', border: '1px solid var(--color-border)', borderRadius: 3 }}
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      step={0.1}
                      value={v.age}
                      onChange={(e) => handleVisitChange(i, 'age', parseFloat(e.target.value) || 0)}
                      style={{ width: 70, padding: '3px 6px', border: '1px solid var(--color-border)', borderRadius: 3 }}
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      value={v.mmse ?? 30}
                      onChange={(e) => handleVisitChange(i, 'mmse', parseFloat(e.target.value) || 0)}
                      style={{ width: 60, padding: '3px 6px', border: '1px solid var(--color-border)', borderRadius: 3 }}
                    />
                  </td>
                  <td>
                    <select
                      value={v.cdr ?? 0}
                      onChange={(e) => handleVisitChange(i, 'cdr', parseFloat(e.target.value))}
                      style={{ padding: '3px 6px', border: '1px solid var(--color-border)', borderRadius: 3, background: '#fff' }}
                    >
                      <option value={0}>0 (Normal)</option>
                      <option value={0.5}>0.5 (MCI)</option>
                      <option value={1}>1.0 (Mild)</option>
                      <option value={2}>2.0 (Moderate)</option>
                    </select>
                  </td>
                  <td>
                    <input
                      type="number"
                      step={0.001}
                      value={v.nwbv ?? 0.72}
                      onChange={(e) => handleVisitChange(i, 'nwbv', parseFloat(e.target.value) || 0)}
                      style={{ width: 80, padding: '3px 6px', border: '1px solid var(--color-border)', borderRadius: 3 }}
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      value={v.etiv ?? 1500}
                      onChange={(e) => handleVisitChange(i, 'etiv', parseFloat(e.target.value) || 0)}
                      style={{ width: 75, padding: '3px 6px', border: '1px solid var(--color-border)', borderRadius: 3 }}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ marginTop: 14, display: 'flex', justifyContent: 'flex-end' }}>
          <button
            onClick={() => runAnalysis(subjectId, visits)}
            disabled={loading}
            style={{
              padding: '7px 16px',
              background: 'var(--color-accent)',
              color: '#fff',
              border: 'none',
              borderRadius: 4,
              fontWeight: 600,
              fontSize: '0.82rem',
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Computing Mixed-Effects Trajectory...' : 'Recalculate Trajectory →'}
          </button>
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--color-fail)', background: 'var(--color-fail-bg)', color: 'var(--color-fail)', marginBottom: 20 }}>
          {error}
        </div>
      )}

      {analysis && (
        <>
          {/* Metrics Stat Grid */}
          <div className="stat-grid" style={{ marginBottom: 24 }}>
            <div className="stat-box">
              <div className="stat-value" style={{ color: analysis.annualized_brain_atrophy_pct > 1.0 ? 'var(--color-fail)' : 'var(--color-accent)' }}>
                {analysis.annualized_brain_atrophy_pct.toFixed(2)}%
              </div>
              <div className="stat-label">Annual Brain Atrophy Rate</div>
            </div>

            <div className="stat-box">
              <div className="stat-value" style={{ color: analysis.annualized_mmse_change < -1.0 ? 'var(--color-fail)' : 'var(--color-accent)' }}>
                {analysis.annualized_mmse_change.toFixed(2)} pts
              </div>
              <div className="stat-label">Annual MMSE Slope</div>
            </div>

            <div className="stat-box">
              <div className="stat-value">
                {(analysis.conversion_risk_5year * 100).toFixed(1)}%
              </div>
              <div className="stat-label">5-Year Conversion Probability</div>
            </div>

            <div className="stat-box">
              <div className="stat-value" style={{ fontSize: '1.25rem' }}>
                {analysis.total_followup_years.toFixed(1)} yrs
              </div>
              <div className="stat-label">Follow-up Interval</div>
            </div>
          </div>

          {/* Trajectory Classification & Clinical Synthesis */}
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="section-label">Trajectory Classification</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginTop: 4, marginBottom: 8 }}>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--color-text)' }}>
                {analysis.trajectory_type.replace(/_/g, ' ')}
              </h2>
            </div>
            <p style={{ fontSize: '0.88rem', color: 'var(--color-text-2)', lineHeight: 1.6, marginBottom: 12 }}>
              {analysis.trajectory_description}
            </p>
            <div style={{ background: 'var(--color-surface-2)', padding: '12px 16px', borderRadius: 6, fontSize: '0.82rem', color: 'var(--color-text)', borderLeft: '3px solid var(--color-accent)' }}>
              <strong>Clinical Inference:</strong> {analysis.clinical_interpretation}
            </div>
          </div>

          {/* Fitted 5-Year Trajectory Projection Table */}
          <div className="card">
            <div className="section-label" style={{ marginBottom: 8 }}>Parametric 5-Year Projected Trajectory</div>
            <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: 14 }}>
              Mixed-effects linear projection extrapolating brain volume loss and cognitive score with expanding 95% confidence intervals:
            </p>

            <table className="data-table" style={{ width: '100%', fontSize: '0.82rem' }}>
              <thead>
                <tr>
                  <th>Projection Year</th>
                  <th>Predicted nWBV</th>
                  <th>Predicted MMSE</th>
                  <th>95% Confidence Band</th>
                  <th>Projected Clinical State</th>
                </tr>
              </thead>
              <tbody>
                {analysis.fitted_trajectory.map((pt: FittedTrajectoryPoint) => (
                  <tr key={pt.year}>
                    <td><strong>Year +{pt.year.toFixed(0)}</strong></td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{pt.predicted_nwbv.toFixed(4)}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{pt.predicted_mmse.toFixed(1)}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-text-muted)' }}>
                      [{pt.ci_lower.toFixed(1)} – {pt.ci_upper.toFixed(1)}]
                    </td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          background: pt.predicted_mmse < 20 ? 'var(--color-fail-bg)' : pt.predicted_mmse < 25 ? 'var(--color-warn-bg)' : 'var(--color-pass-bg)',
                          color: pt.predicted_mmse < 20 ? 'var(--color-fail)' : pt.predicted_mmse < 25 ? 'var(--color-warn)' : 'var(--color-pass)',
                        }}
                      >
                        {pt.predicted_mmse < 20 ? 'Moderate Dementia' : pt.predicted_mmse < 25 ? 'Mild Impairment' : 'Preserved Cognition'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

