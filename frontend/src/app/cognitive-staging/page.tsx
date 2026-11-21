'use client';
import { useState, useEffect } from 'react';
import { api, type CognitiveStagingRequest, type CognitiveStagingResponse, type StageProbability } from '@/lib/api';

export default function CognitiveStagingPage() {
  const [form, setForm] = useState<CognitiveStagingRequest>({
    age: 76,
    sex: 'M',
    mmse: 25,
    nwbv: 0.718,
    etiv: 1490,
    apoe4_carrier: true,
    composite_pathology_z: 1.2,
  });

  const [staging, setStaging] = useState<CognitiveStagingResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    runStaging(form);
  }, []);

  const runStaging = async (req: CognitiveStagingRequest) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.predictions.stage(req);
      setStaging(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Cognitive staging failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-content">
      {/* Page Header */}
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 8 }}>
          <h1 className="page-title">Cognitive-Stage Estimation</h1>
          <span style={{ fontSize: '0.78rem', background: 'var(--color-accent-bg)', color: 'var(--color-accent)', border: '1px solid var(--color-border)', borderRadius: 4, padding: '2px 8px', fontWeight: 600 }}>
            MANAS V2
          </span>
        </div>
        <p className="page-subtitle">
          Ordinal cognitive-stage modeling (CDR 0 to 2+), continuous MMSE score expectation, and anatomical
          Braak neuropathological progression mapping.
        </p>
      </div>

      {/* Grid: Controls & Staging Output */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(300px, 360px) 1fr', gap: 24, alignItems: 'start' }}>
        {/* Controls Card */}
        <div className="card">
          <div className="section-label" style={{ marginBottom: 14 }}>Biomarker & Clinical Predictors</div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              runStaging(form);
            }}
            style={{ display: 'flex', flexDirection: 'column', gap: 14 }}
          >
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-2)', marginBottom: 4 }}>
                Subject Age: {form.age} years
              </label>
              <input
                type="range"
                min={50}
                max={95}
                value={form.age ?? 76}
                onChange={(e) => setForm({ ...form, age: parseFloat(e.target.value) })}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-2)', marginBottom: 4 }}>
                Reported MMSE Score (0–30)
              </label>
              <input
                type="number"
                min={0}
                max={30}
                value={form.mmse ?? 25}
                onChange={(e) => setForm({ ...form, mmse: parseFloat(e.target.value) })}
                style={{ width: '100%', padding: '6px 10px', borderRadius: 4, border: '1px solid var(--color-border)', fontSize: '0.85rem' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-2)', marginBottom: 4 }}>
                Whole Brain Volume (nWBV: {form.nwbv?.toFixed(3)})
              </label>
              <input
                type="range"
                min={0.62}
                max={0.82}
                step={0.005}
                value={form.nwbv ?? 0.718}
                onChange={(e) => setForm({ ...form, nwbv: parseFloat(e.target.value) })}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-2)', marginBottom: 4 }}>
                Composite Pathology Burden (Z-score: {form.composite_pathology_z?.toFixed(1)})
              </label>
              <input
                type="range"
                min={-2.0}
                max={4.0}
                step={0.1}
                value={form.composite_pathology_z ?? 1.2}
                onChange={(e) => setForm({ ...form, composite_pathology_z: parseFloat(e.target.value) })}
                style={{ width: '100%' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: 'var(--color-text-muted)' }}>
                <span>-2.0 (Negligible)</span>
                <span>0.0 (Population Avg)</span>
                <span>+4.0 (Severe)</span>
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-2)', marginBottom: 4 }}>
                APOE ε4 Allele Carrier
              </label>
              <select
                value={form.apoe4_carrier ? 'yes' : 'no'}
                onChange={(e) => setForm({ ...form, apoe4_carrier: e.target.value === 'yes' })}
                style={{ width: '100%', padding: '6px 10px', borderRadius: 4, border: '1px solid var(--color-border)', fontSize: '0.85rem', background: '#fff' }}
              >
                <option value="no">Non-Carrier (ε4-)</option>
                <option value="yes">Carrier (ε4+)</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: 6,
                padding: '9px 16px',
                background: 'var(--color-accent)',
                color: '#fff',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? 'Estimating Stage...' : 'Re-estimate Cognitive Stage →'}
            </button>
          </form>
        </div>

        {/* Staging Results Card */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {error && (
            <div className="card" style={{ borderColor: 'var(--color-fail)', background: 'var(--color-fail-bg)', color: 'var(--color-fail)' }}>
              {error}
            </div>
          )}

          {staging && (
            <>
              {/* Primary Stage Overview */}
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 12 }}>
                  <div>
                    <div className="section-label">Most Likely Cognitive Category</div>
                    <h2 style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--color-text)', marginTop: 4 }}>
                      {staging.primary_stage_label}
                    </h2>
                  </div>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.75rem',
                      background: 'var(--color-surface-2)',
                      padding: '3px 8px',
                      borderRadius: 4,
                      color: 'var(--color-text-muted)',
                    }}
                  >
                    {staging.inference_id}
                  </span>
                </div>

                {/* Multiclass Probability Distribution */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 16 }}>
                  {staging.stage_probabilities.map((sp: StageProbability) => {
                    const isPrimary = sp.stage === staging.primary_stage;
                    return (
                      <div
                        key={sp.stage}
                        style={{
                          padding: 12,
                          borderRadius: 6,
                          border: isPrimary ? '1px solid var(--color-accent)' : '1px solid var(--color-border)',
                          background: isPrimary ? 'var(--color-accent-bg)' : 'var(--color-surface)',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                          <div>
                            <span style={{ fontSize: '0.85rem', fontWeight: isPrimary ? 700 : 500 }}>{sp.stage_name}</span>
                            {isPrimary && (
                              <span style={{ marginLeft: 8, fontSize: '0.68rem', background: 'var(--color-accent)', color: '#fff', padding: '1px 6px', borderRadius: 10 }}>
                                PRIMARY
                              </span>
                            )}
                          </div>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', fontWeight: 700, color: isPrimary ? 'var(--color-accent)' : 'var(--color-text-2)' }}>
                            {(sp.probability * 100).toFixed(1)}%
                          </span>
                        </div>

                        <div style={{ height: 6, background: 'var(--color-surface-2)', borderRadius: 3, overflow: 'hidden', marginBottom: 6 }}>
                          <div
                            style={{
                              width: `${sp.probability * 100}%`,
                              height: '100%',
                              background: isPrimary ? 'var(--color-accent)' : 'var(--color-text-muted)',
                              borderRadius: 3,
                            }}
                          />
                        </div>

                        <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', lineHeight: 1.4 }}>
                          {sp.clinical_description}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Anatomical and Monitoring Indicators */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div className="card">
                  <div className="section-label" style={{ marginBottom: 8 }}>Estimated MMSE Expectation</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.8rem', fontWeight: 700, color: 'var(--color-accent)' }}>
                    {staging.estimated_mmse.toFixed(1)} <span style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>/ 30</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 4 }}>
                    Estimated 95% Confidence Band: [{staging.estimated_mmse_range[0]} – {staging.estimated_mmse_range[1]}]
                  </div>
                </div>

                <div className="card">
                  <div className="section-label" style={{ marginBottom: 8 }}>Progression Velocity</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.4rem', fontWeight: 700, color: staging.progression_velocity === 'ACCELERATED' ? 'var(--color-fail)' : 'var(--color-warn)' }}>
                    {staging.progression_velocity}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 4 }}>
                    Recommended: {staging.recommended_monitoring_interval}
                  </div>
                </div>
              </div>

              {/* Neuropathology Correlation Card */}
              <div className="card">
                <div className="section-label" style={{ marginBottom: 8 }}>Braak Staging Anatomical Correlation</div>
                <p style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--color-text)' }}>
                  {staging.braak_anatomical_correlation}
                </p>
                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginTop: 6, lineHeight: 1.5 }}>
                  Based on Allen Aging donor histopathology and OASIS regional atrophy mapping, this cognitive stage
                  typically coincides with tau tangle propagation into temporal and parietal isocortex.
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

