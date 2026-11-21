'use client';
import { useState, useEffect } from 'react';
import { api, type ModelMetadata, type ModelEvaluation } from '@/lib/api';

export default function ModelPerformancePage() {
  const [models, setModels] = useState<ModelMetadata[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>('MANAS-ML-AD-CLF-01');
  const [evaluation, setEvaluation] = useState<ModelEvaluation | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.predictions.models().then((mList) => {
      setModels(mList);
      if (mList.length > 0) {
        loadEvaluation(mList[0].model_id);
      }
    }).catch(() => setLoading(false));
  }, []);

  const loadEvaluation = async (mId: string) => {
    setLoading(true);
    setSelectedModelId(mId);
    try {
      const data = await api.predictions.evaluation(mId);
      setEvaluation(data);
    } catch {
      // Handled
    } finally {
      setLoading(false);
    }
  };

  const selectedModel = models.find((m) => m.model_id === selectedModelId);

  return (
    <div className="page-content">
      {/* Header */}
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 8 }}>
          <h1 className="page-title">Model Performance & Evaluation</h1>
          <span style={{ fontSize: '0.78rem', background: 'var(--color-accent-bg)', color: 'var(--color-accent)', border: '1px solid var(--color-border)', borderRadius: 4, padding: '2px 8px', fontWeight: 600 }}>
            MANAS V2
          </span>
        </div>
        <p className="page-subtitle">
          Transparent empirical validation metrics, cross-validated ROC/PR curves, confusion matrices, probability calibration,
          and global feature importances for all trained machine learning models.
        </p>
      </div>

      {/* Model Selector Tabs */}
      <div className="card card-sm" style={{ marginBottom: 20 }}>
        <div className="section-label" style={{ marginBottom: 8 }}>Select Predictive Model</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {models.map((m) => (
            <button
              key={m.model_id}
              onClick={() => loadEvaluation(m.model_id)}
              style={{
                padding: '8px 14px',
                borderRadius: 'var(--radius-sm)',
                border: selectedModelId === m.model_id ? '1px solid var(--color-accent)' : '1px solid var(--color-border)',
                background: selectedModelId === m.model_id ? 'var(--color-accent-bg)' : 'var(--color-surface-2)',
                color: selectedModelId === m.model_id ? 'var(--color-accent)' : 'var(--color-text)',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <div style={{ fontWeight: 600, fontSize: '0.82rem' }}>{m.name}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>{m.model_id} · v{m.version}</div>
            </button>
          ))}
        </div>
      </div>

      {selectedModel && evaluation && (
        <>
          {/* Key Metric Highlights */}
          <div className="stat-grid" style={{ marginBottom: 24 }}>
            <div className="stat-box">
              <div className="stat-value" style={{ color: 'var(--color-accent)' }}>
                {evaluation.metrics.roc_auc.toFixed(3)}
              </div>
              <div className="stat-label">Cross-Validated ROC-AUC</div>
            </div>

            <div className="stat-box">
              <div className="stat-value">
                {evaluation.metrics.pr_auc.toFixed(3)}
              </div>
              <div className="stat-label">Precision-Recall AUC</div>
            </div>

            <div className="stat-box">
              <div className="stat-value">
                {(evaluation.metrics.accuracy * 100).toFixed(1)}%
              </div>
              <div className="stat-label">Classification Accuracy</div>
            </div>

            <div className="stat-box">
              <div className="stat-value" style={{ color: 'var(--color-pass)' }}>
                {evaluation.metrics.brier_score.toFixed(3)}
              </div>
              <div className="stat-label">Brier Calibration Score</div>
            </div>
          </div>

          {/* Model Specification Card */}
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="section-label">Model Registry Specification</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, marginTop: 12 }}>
              <div>
                <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', display: 'block' }}>Algorithm</span>
                <strong style={{ fontSize: '0.85rem' }}>{evaluation.algorithm}</strong>
              </div>
              <div>
                <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', display: 'block' }}>Target Variable</span>
                <strong style={{ fontSize: '0.85rem' }}>{evaluation.target_variable}</strong>
              </div>
              <div>
                <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', display: 'block' }}>Training Cohorts</span>
                <strong style={{ fontSize: '0.85rem' }}>{selectedModel.training_dataset}</strong>
              </div>
              <div>
                <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', display: 'block' }}>Validation Protocol</span>
                <strong style={{ fontSize: '0.85rem' }}>{selectedModel.cv_method}</strong>
              </div>
            </div>
          </div>

          {/* Two-column layout: Confusion Matrix vs Calibration */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
            {/* Confusion Matrix */}
            <div className="card">
              <div className="section-label" style={{ marginBottom: 8 }}>Cross-Validated Confusion Matrix</div>
              <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: 14 }}>
                Evaluation on n = {evaluation.confusion_matrix.total_tested} test observations (decision threshold τ = {evaluation.confusion_matrix.threshold}):
              </p>

              <table className="data-table" style={{ width: '100%', textAlign: 'center', fontSize: '0.82rem' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Observed Class</th>
                    <th>Pred: Control</th>
                    <th>Pred: AD</th>
                    <th>Sensitivity / Specificity</th>
                  </tr>
                </thead>
                <tbody>
                  {evaluation.confusion_matrix.matrix.map((row, idx) => (
                    <tr key={idx}>
                      <td style={{ textAlign: 'left', fontWeight: 600 }}>{row.label}</td>
                      <td style={{ fontFamily: 'var(--font-mono)', background: idx === 0 ? 'var(--color-pass-bg)' : 'transparent', fontWeight: idx === 0 ? 700 : 400 }}>
                        {row.pred_control} {idx === 0 ? '(TN)' : '(FN)'}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', background: idx === 1 ? 'var(--color-pass-bg)' : 'transparent', fontWeight: idx === 1 ? 700 : 400 }}>
                        {row.pred_ad} {idx === 1 ? '(TP)' : '(FP)'}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                        {idx === 0
                          ? `Spec: ${((row.pred_control / (row.pred_control + row.pred_ad)) * 100).toFixed(1)}%`
                          : `Sens: ${((row.pred_ad / (row.pred_control + row.pred_ad)) * 100).toFixed(1)}%`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div style={{ marginTop: 14, fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                Balanced Accuracy: <strong>{(((evaluation.metrics.sensitivity + evaluation.metrics.specificity) / 2) * 100).toFixed(1)}%</strong>
              </div>
            </div>

            {/* Probability Calibration Curve */}
            <div className="card">
              <div className="section-label" style={{ marginBottom: 8 }}>Probability Calibration (Reliability)</div>
              <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: 14 }}>
                Comparison of model-predicted probabilities against empirical observed event frequencies:
              </p>

              <table className="data-table" style={{ width: '100%', fontSize: '0.82rem' }}>
                <thead>
                  <tr>
                    <th>Predicted Probability Bin</th>
                    <th>Observed AD Fraction</th>
                    <th>Calibration Deviation</th>
                  </tr>
                </thead>
                <tbody>
                  {evaluation.calibration_curve.prob_pred.map((p, i) => {
                    const actual = evaluation.calibration_curve.prob_true[i];
                    const diff = actual - p;
                    return (
                      <tr key={i}>
                        <td style={{ fontFamily: 'var(--font-mono)' }}>{(p * 100).toFixed(0)}%</td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{(actual * 100).toFixed(1)}%</td>
                        <td style={{ fontFamily: 'var(--font-mono)', color: Math.abs(diff) < 0.03 ? 'var(--color-pass)' : 'var(--color-warn)' }}>
                          {diff > 0 ? `+${(diff * 100).toFixed(1)}%` : `${(diff * 100).toFixed(1)}%`}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              <div style={{ marginTop: 14, fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                Brier Score: <strong>{evaluation.metrics.brier_score}</strong> (Lower is superior; 0.0 = perfect calibration).
              </div>
            </div>
          </div>

          {/* Global Feature Importance Breakdown */}
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="section-label" style={{ marginBottom: 8 }}>Global Feature Importance Breakdown</div>
            <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: 16 }}>
              Relative contribution across all validation folds based on mean absolute SHAP values:
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {evaluation.feature_importances.map((item, idx) => (
                <div key={idx} style={{ borderBottom: '1px solid var(--color-border)', paddingBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{item.feature}</span>
                      <span style={{ fontSize: '0.7rem', background: 'var(--color-surface-2)', padding: '2px 6px', borderRadius: 4, color: 'var(--color-text-muted)' }}>
                        {item.category}
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                      <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>{item.direction}</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 700, color: 'var(--color-accent)' }}>
                        {(item.importance * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  <div style={{ height: 6, background: 'var(--color-surface-2)', borderRadius: 3, overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${item.importance * 100}%`,
                        height: '100%',
                        background: 'var(--color-accent)',
                        borderRadius: 3,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Scientific Methodology & Limitations */}
          <div className="card" style={{ borderLeft: '3px solid var(--color-accent)' }}>
            <div className="section-label" style={{ marginBottom: 8 }}>Scientific Defensibility & Validation Boundaries</div>
            <div style={{ fontSize: '0.82rem', color: 'var(--color-text-2)', lineHeight: 1.6 }}>
              <p style={{ marginBottom: 8 }}>
                <strong>1. Cohort Representation:</strong> Training cohorts are pooled from OASIS-1 (cross-sectional community-dwelling cohort, n=436),
                OASIS-2 (longitudinal aging cohort, n=150, 373 visits), and the Allen Institute Aging, Dementia & TBI Study (post-mortem neuropathology, n=107).
              </p>
              <p style={{ marginBottom: 8 }}>
                <strong>2. Leakage Prevention:</strong> Cross-validation splits are grouped by unique subject identifier to guarantee that repeat visits
                from the same donor never appear simultaneously in training and test folds.
              </p>
              <p>
                <strong>3. Limitations:</strong> As per MANAS research guidelines, scalar volumetric measures (nWBV, eTIV) represent global rather than
                sub-field hippocampal segmentation. Independent external cohort validation on Alzheimer&apos;s Disease Neuroimaging Initiative (ADNI)
                data is scheduled as part of the MANAS V3 roadmap.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

