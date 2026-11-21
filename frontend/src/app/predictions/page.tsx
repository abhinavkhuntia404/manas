'use client';
import { useState, useEffect } from 'react';
import {
  api,
  type ClassificationRequest,
  type ClassificationResponse,
  type FeatureAttributionItem,
  type ResearchReportResponse
} from '@/lib/api';

const SAMPLE_PROFILES: Record<string, ClassificationRequest & { name: string; cohort: string }> = {
  oasis_control: {
    name: 'OASIS-1 Healthy Control (OAS1_0001)',
    cohort: 'OASIS-1 Cross-Sectional',
    age: 74,
    sex: 'F',
    mmse: 29,
    cdr: 0,
    nwbv: 0.743,
    etiv: 1450,
    apoe4_carrier: false,
    education_years: 16,
    ihc_at8_ffpe: 0.012,
  },
  oasis_mci: {
    name: 'OASIS-2 Borderline MCI (OAS2_0002_MR2)',
    cohort: 'OASIS-2 Longitudinal',
    age: 78,
    sex: 'M',
    mmse: 26,
    cdr: 0.5,
    nwbv: 0.708,
    etiv: 1520,
    apoe4_carrier: true,
    education_years: 14,
    ihc_at8_ffpe: 0.038,
  },
  allen_tau_ad: {
    name: 'Allen Aging High-Tau AD Donor (H14.09.022)',
    cohort: 'Allen Aging, Dementia & TBI',
    age: 83,
    sex: 'M',
    mmse: 18,
    cdr: 1.0,
    nwbv: 0.672,
    etiv: 1480,
    apoe4_carrier: true,
    education_years: 12,
    ihc_at8_ffpe: 0.145,
  },
};

export default function PredictionsPage() {
  const [form, setForm] = useState<ClassificationRequest>({
    age: 75,
    sex: 'M',
    mmse: 26,
    cdr: 0.5,
    nwbv: 0.715,
    etiv: 1485,
    apoe4_carrier: true,
    education_years: 14,
    ihc_at8_ffpe: 0.045,
    model_id: 'MANAS-ML-AD-CLF-01',
  });

  const [result, setResult] = useState<ClassificationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ResearchReportResponse | null>(null);
  const [reportLoading, setReportLoading] = useState(false);

  // Initial classification run
  useEffect(() => {
    runClassification(form);
  }, []);

  const runClassification = async (req: ClassificationRequest) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.predictions.classify(req);
      setResult(res);
      setReport(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Prediction request failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleSampleSelect = (key: string) => {
    const sample = SAMPLE_PROFILES[key];
    if (sample) {
      const newForm: ClassificationRequest = {
        age: sample.age,
        sex: sample.sex,
        mmse: sample.mmse,
        cdr: sample.cdr,
        nwbv: sample.nwbv,
        etiv: sample.etiv,
        apoe4_carrier: sample.apoe4_carrier,
        education_years: sample.education_years,
        ihc_at8_ffpe: sample.ihc_at8_ffpe,
        model_id: form.model_id,
      };
      setForm(newForm);
      runClassification(newForm);
    }
  };

  const handleGenerateReport = async () => {
    if (!result) return;
    setReportLoading(true);
    try {
      const rep = await api.predictions.generateReport({
        subject_identifier: `EXP-PRED-${Math.floor(1000 + Math.random() * 9000)}`,
        clinical_inputs: form as Record<string, unknown>,
        classification: result as unknown as Record<string, unknown>,
        investigator_notes: 'Multimodal biomarker prediction generated in MANAS V2 Predictive Research Workspace.',
      });
      setReport(rep);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Report generation failed';
      setError(msg);
    } finally {
      setReportLoading(false);
    }
  };

  return (
    <div className="page-content">
      {/* Page Header */}
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 8 }}>
          <h1 className="page-title">Predictions Workspace</h1>
          <span style={{ fontSize: '0.78rem', background: 'var(--color-accent-bg)', color: 'var(--color-accent)', border: '1px solid var(--color-border)', borderRadius: 4, padding: '2px 8px', fontWeight: 600 }}>
            MANAS V2
          </span>
        </div>
        <p className="page-subtitle">
          Multimodal Alzheimer&apos;s disease classification, uncertainty quantification, and explainable feature attribution
          derived from OASIS volumetrics and Allen Institute post-mortem neuropathology.
        </p>
      </div>

      {/* Scientific Disclaimer */}
      <div className="card card-sm" style={{ marginBottom: 20, borderLeft: '3px solid var(--color-warn)', background: 'var(--color-warn-bg)' }}>
        <p style={{ fontSize: '0.82rem', color: '#78350f', lineHeight: 1.5 }}>
          <strong>Research Platform Notice:</strong> MANAS predictive models are scientific research algorithms trained on retrospective public cohorts.
          They are designed for investigative hypothesis testing and exploratory biomarker modeling, <strong>not for clinical diagnosis or patient triage</strong>.
        </p>
      </div>

      {/* Preset Cohort Donors */}
      <div className="card card-sm" style={{ marginBottom: 24 }}>
        <div className="section-label" style={{ marginBottom: 8 }}>Load Validated Benchmark Profiles</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {Object.entries(SAMPLE_PROFILES).map(([key, sample]) => (
            <button
              key={key}
              onClick={() => handleSampleSelect(key)}
              style={{
                background: 'var(--color-surface-2)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-sm)',
                padding: '6px 12px',
                fontSize: '0.8rem',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <div style={{ fontWeight: 600, color: 'var(--color-text)' }}>{sample.name}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>{sample.cohort}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: Inputs vs Results */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 380px) 1fr', gap: 24, alignItems: 'start' }}>
        {/* Input Parameters Card */}
        <div className="card">
          <div className="section-label" style={{ marginBottom: 16 }}>Clinical & Neuropathological Inputs</div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              runClassification(form);
            }}
            style={{ display: 'flex', flexDirection: 'column', gap: 14 }}
          >
            {/* Age & Sex */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-2)', marginBottom: 4 }}>
                  Age (years)
                </label>
                <input
                  type="number"
                  min={45}
                  max={105}
                  value={form.age ?? 75}
                  onChange={(e) => setForm({ ...form, age: parseFloat(e.target.value) || null })}
                  style={{ width: '100%', padding: '6px 10px', borderRadius: 4, border: '1px solid var(--color-border)', fontSize: '0.85rem' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-2)', marginBottom: 4 }}>
                  Sex
                </label>
                <select
                  value={form.sex ?? 'M'}
                  onChange={(e) => setForm({ ...form, sex: e.target.value })}
                  style={{ width: '100%', padding: '6px 10px', borderRadius: 4, border: '1px solid var(--color-border)', fontSize: '0.85rem', background: '#fff' }}
                >
                  <option value="M">Male (M)</option>
                  <option value="F">Female (F)</option>
                </select>
              </div>
            </div>

            {/* MMSE & CDR */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-2)', marginBottom: 4 }}>
                  MMSE Score (0–30)
                </label>
                <input
                  type="number"
                  min={0}
                  max={30}
                  value={form.mmse ?? 26}
                  onChange={(e) => setForm({ ...form, mmse: parseFloat(e.target.value) })}
                  style={{ width: '100%', padding: '6px 10px', borderRadius: 4, border: '1px solid var(--color-border)', fontSize: '0.85rem' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-2)', marginBottom: 4 }}>
                  CDR Rating
                </label>
                <select
                  value={form.cdr ?? 0.5}
                  onChange={(e) => setForm({ ...form, cdr: parseFloat(e.target.value) })}
                  style={{ width: '100%', padding: '6px 10px', borderRadius: 4, border: '1px solid var(--color-border)', fontSize: '0.85rem', background: '#fff' }}
                >
                  <option value={0}>0 (Normal)</option>
                  <option value={0.5}>0.5 (Very Mild / MCI)</option>
                  <option value={1}>1.0 (Mild Dementia)</option>
                  <option value={2}>2.0 (Moderate)</option>
                </select>
              </div>
            </div>

            {/* nWBV & eTIV */}
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-2)', marginBottom: 4 }}>
                Whole Brain Volume (nWBV: {form.nwbv?.toFixed(3)})
              </label>
              <input
                type="range"
                min={0.62}
                max={0.84}
                step={0.005}
                value={form.nwbv ?? 0.72}
                onChange={(e) => setForm({ ...form, nwbv: parseFloat(e.target.value) })}
                style={{ width: '100%' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: 'var(--color-text-muted)' }}>
                <span>0.62 (Severe Atrophy)</span>
                <span>0.74 (Normative)</span>
                <span>0.84 (Preserved)</span>
              </div>
            </div>

            {/* APOE4 & Education */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-2)', marginBottom: 4 }}>
                  APOE ε4 Allele
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
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-2)', marginBottom: 4 }}>
                  Education (yrs)
                </label>
                <input
                  type="number"
                  min={0}
                  max={25}
                  value={form.education_years ?? 14}
                  onChange={(e) => setForm({ ...form, education_years: parseFloat(e.target.value) || null })}
                  style={{ width: '100%', padding: '6px 10px', borderRadius: 4, border: '1px solid var(--color-border)', fontSize: '0.85rem' }}
                />
              </div>
            </div>

            {/* AT8 Tau area fraction */}
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-2)', marginBottom: 4 }}>
                Hippocampal AT8 Tau (IHC Area Fraction)
              </label>
              <input
                type="number"
                step={0.005}
                min={0}
                max={0.5}
                value={form.ihc_at8_ffpe ?? 0.045}
                onChange={(e) => setForm({ ...form, ihc_at8_ffpe: parseFloat(e.target.value) || null })}
                style={{ width: '100%', padding: '6px 10px', borderRadius: 4, border: '1px solid var(--color-border)', fontSize: '0.85rem' }}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: 8,
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
              {loading ? 'Executing ML Inference...' : 'Run Multimodal Prediction →'}
            </button>
          </form>
        </div>

        {/* Prediction Results Display */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {error && (
            <div className="card" style={{ borderColor: 'var(--color-fail)', background: 'var(--color-fail-bg)', color: 'var(--color-fail)' }}>
              {error}
            </div>
          )}

          {result && (
            <>
              {/* Summary Score Card */}
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <div>
                    <div className="section-label">Classification Result</div>
                    <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-text)', marginTop: 2 }}>
                      {result.predicted_class_label}
                    </h2>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <span
                      style={{
                        padding: '4px 10px',
                        borderRadius: 12,
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        background:
                          result.risk_tier === 'VERY_HIGH' || result.risk_tier === 'HIGH'
                            ? 'var(--color-fail-bg)'
                            : result.risk_tier === 'MODERATE'
                              ? 'var(--color-warn-bg)'
                              : 'var(--color-pass-bg)',
                        color:
                          result.risk_tier === 'VERY_HIGH' || result.risk_tier === 'HIGH'
                            ? 'var(--color-fail)'
                            : result.risk_tier === 'MODERATE'
                              ? 'var(--color-warn)'
                              : 'var(--color-pass)',
                      }}
                    >
                      {result.risk_tier} RISK TIER
                    </span>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--color-text-muted)', marginTop: 4 }}>
                      {result.inference_id}
                    </div>
                  </div>
                </div>

                {/* Probability Bar */}
                <div style={{ marginBottom: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: 6 }}>
                    <span style={{ fontWeight: 600 }}>Estimated AD Phenotype Probability:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '1.1rem', color: 'var(--color-accent)' }}>
                      {(result.probability * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div style={{ height: 10, background: 'var(--color-surface-2)', borderRadius: 5, overflow: 'hidden', position: 'relative' }}>
                    <div
                      style={{
                        width: `${result.probability * 100}%`,
                        height: '100%',
                        background:
                          result.probability > 0.65 ? 'var(--color-fail)' : result.probability > 0.35 ? 'var(--color-warn)' : 'var(--color-pass)',
                        borderRadius: 5,
                        transition: 'width 0.4s ease',
                      }}
                    />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--color-text-muted)', marginTop: 4 }}>
                    <span>0% (Normative)</span>
                    <span>
                      95% Confidence Interval: [{(result.confidence_interval_low * 100).toFixed(1)}% – {(result.confidence_interval_high * 100).toFixed(1)}%]
                    </span>
                    <span>100% (High Pathology)</span>
                  </div>
                </div>

                <p style={{ fontSize: '0.85rem', color: 'var(--color-text-2)', lineHeight: 1.6, background: 'var(--color-surface-2)', padding: '10px 14px', borderRadius: 4 }}>
                  {result.risk_summary}
                </p>

                <div style={{ display: 'flex', gap: 16, marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--color-border)', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                  <span>Model: <code>{result.model_id}</code></span>
                  <span>Cross-Validated AUC: <strong>{result.model_roc_auc}</strong></span>
                  <span>Accuracy: <strong>{(result.model_accuracy * 100).toFixed(1)}%</strong></span>
                </div>
              </div>

              {/* Explainable AI: Feature Attributions */}
              <div className="card">
                <div className="section-label" style={{ marginBottom: 4 }}>Explainable AI — Feature Attributions</div>
                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: 16 }}>
                  Directional contribution of each patient variable to the predicted log-odds (SHAP-aligned decomposition):
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {result.feature_attributions.map((attr: FeatureAttributionItem) => {
                    const isRisk = attr.effect === 'INCREASES_RISK';
                    const absVal = Math.min(100, Math.abs(attr.contribution) * 40);
                    return (
                      <div key={attr.feature} style={{ borderBottom: '1px solid var(--color-border)', paddingBottom: 8 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
                          <span style={{ fontSize: '0.82rem', fontWeight: 600 }}>{attr.feature_label}</span>
                          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: isRisk ? 'var(--color-fail)' : 'var(--color-pass)' }}>
                              {attr.contribution > 0 ? `+${attr.contribution.toFixed(3)}` : attr.contribution.toFixed(3)} log-odds
                            </span>
                            {attr.odds_ratio && (
                              <span style={{ fontSize: '0.72rem', background: 'var(--color-surface-2)', padding: '1px 6px', borderRadius: 4 }}>
                                OR {attr.odds_ratio.toFixed(2)}x
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Attribution bar */}
                        <div style={{ display: 'flex', height: 6, background: 'var(--color-surface-2)', borderRadius: 3, overflow: 'hidden' }}>
                          <div
                            style={{
                              width: `${absVal}%`,
                              background: isRisk ? 'var(--color-fail)' : 'var(--color-pass)',
                              borderRadius: 3,
                            }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end' }}>
                  <button
                    onClick={handleGenerateReport}
                    disabled={reportLoading}
                    style={{
                      padding: '7px 14px',
                      background: 'var(--color-surface-2)',
                      border: '1px solid var(--color-border-strong)',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      cursor: reportLoading ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {reportLoading ? 'Compiling Report...' : '📄 Generate Full Research Report'}
                  </button>
                </div>
              </div>

              {/* Research Report Display */}
              {report && (
                <div className="card" style={{ borderLeft: '4px solid var(--color-accent)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                    <div>
                      <div className="section-label">Generated Research Document</div>
                      <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>{report.title}</h3>
                    </div>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                      {report.report_id}
                    </span>
                  </div>

                  <div
                    style={{
                      maxHeight: 380,
                      overflowY: 'auto',
                      padding: 16,
                      background: 'var(--color-surface-2)',
                      borderRadius: 4,
                      fontSize: '0.82rem',
                      fontFamily: 'var(--font-mono)',
                      whiteSpace: 'pre-wrap',
                      lineHeight: 1.5,
                    }}
                  >
                    {report.content_markdown}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

