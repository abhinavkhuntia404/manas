'use client';
import { useEffect, useState } from 'react';
import { api, type Dataset } from '@/lib/api';

const ACCESS_LABELS: Record<string, { label: string; cls: string }> = {
  OPEN_DIRECT:           { label: 'Open — No Registration', cls: 'badge-pass' },
  OPEN_WITH_TERMS:       { label: 'Open with Terms',        cls: 'badge-warn' },
  REGISTRATION_REQUIRED: { label: 'Registration Required',  cls: 'badge-warn' },
  APPLICATION_REQUIRED:  { label: 'Application Required',   cls: 'badge-fail' },
  RESTRICTED:            { label: 'Restricted',             cls: 'badge-fail' },
  UNKNOWN:               { label: 'Unknown',                cls: 'badge-insufficient' },
};

// Always show the real datasets we have, even before DB is seeded
const KNOWN_DATASETS = [
  {
    name: 'Allen Aging, Dementia & TBI Study',
    short_name: 'allen_aging',
    source_org: 'Allen Institute for Brain Science',
    official_url: 'https://aging.brain-map.org/download/index',
    access_type: 'OPEN_DIRECT',
    license: 'Allen Institute Terms of Use (open, attribution)',
    primary_disease: ["Alzheimer's Disease", 'TBI', 'Dementia'],
    description: 'De-identified clinical, protein quantification (Luminex, isoprostane), and immunohistochemistry pathology data from 107 post-mortem brain donors.',
    stats: { subjects: 107, regions: 4, measurements: '32 per region', diseases: 'AD, No Dementia, Vascular' },
    files: ['DonorInformation.csv', 'ProteinAndPathologyQuantifications.csv', 'DescriptionOfStains.csv'],
    downloaded: true,
  },
  {
    name: 'Allen Human Brain Atlas',
    short_name: 'allen_atlas',
    source_org: 'Allen Institute for Brain Science',
    official_url: 'https://human.brain-map.org/static/download',
    access_type: 'OPEN_DIRECT',
    license: 'Allen Institute Terms of Use (CC Attribution)',
    primary_disease: ['Reference'],
    description: 'Regional gene-expression microarray data from 6 healthy post-mortem human brains. Provides canonical brain-region ontology used as the reference atlas.',
    stats: { subjects: 6, regions: '~900 structures', measurements: 'microarray expression', diseases: 'Healthy reference' },
    files: ['H0351.2001.zip', 'H0351.2002.zip', 'ontology JSON'],
    downloaded: false,
  },
  {
    name: 'OASIS-1 Cross-Sectional',
    short_name: 'oasis_1',
    source_org: 'Washington University, St. Louis',
    official_url: 'https://www.oasis-brains.org',
    access_type: 'OPEN_DIRECT',
    license: 'CC BY 4.0',
    primary_disease: ["Alzheimer's Disease"],
    description: '436 subjects aged 18–96. Clinical Dementia Rating (CDR), MMSE, normalized whole-brain volume (nWBV), estimated intracranial volume (eTIV).',
    stats: { subjects: 436, regions: 'Whole brain (scalar)', measurements: 'CDR, MMSE, nWBV, eTIV, ASF', diseases: 'CDR 0–2' },
    files: ['oasis_cross_sectional.xlsx'],
    downloaded: true,
  },
  {
    name: 'OASIS-2 Longitudinal',
    short_name: 'oasis_2',
    source_org: 'Washington University, St. Louis',
    official_url: 'https://www.oasis-brains.org',
    access_type: 'OPEN_DIRECT',
    license: 'CC BY 4.0',
    primary_disease: ["Alzheimer's Disease"],
    description: '150 subjects with 2+ longitudinal MRI visits. Groups: Nondemented, Demented, Converted. Enables longitudinal trajectory analysis.',
    stats: { subjects: 150, regions: 'Whole brain (scalar)', measurements: 'CDR, MMSE, nWBV, eTIV per visit', diseases: 'Nondemented / Demented / Converted' },
    files: ['oasis_longitudinal_demographics.xlsx'],
    downloaded: true,
  },
];

export default function DatasetsPage() {
  const [dbDatasets, setDbDatasets] = useState<Dataset[]>([]);

  useEffect(() => {
    api.datasets.list().then(setDbDatasets).catch(() => {});
  }, []);

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Datasets</h1>
        <p className="page-subtitle">
          All data sources used in MANAS. Access type, download status, and provenance
          are documented for every dataset. No registration required for V1 primary sources.
        </p>
      </div>

      {/* Access legend */}
      <div className="card card-sm" style={{ marginBottom: 24, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>Access types:</span>
        {Object.values(ACCESS_LABELS).map(({ label, cls }) => (
          <span key={label} className={`badge ${cls}`}>{label}</span>
        ))}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {KNOWN_DATASETS.map(ds => {
          const inDb = dbDatasets.some(d => d.short_name === ds.short_name);
          const { label, cls } = ACCESS_LABELS[ds.access_type] ?? ACCESS_LABELS.UNKNOWN;
          return (
            <div key={ds.short_name} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <h2 style={{ fontSize: '1rem', fontWeight: 600 }}>{ds.name}</h2>
                    <span className={`badge ${cls}`}>{label}</span>
                    {ds.downloaded && <span className="badge badge-pass">✓ Downloaded</span>}
                    {inDb && <span className="badge badge-sig">In Database</span>}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{ds.source_org}</div>
                </div>
                <a href={ds.official_url} target="_blank" rel="noreferrer"
                  className="btn btn-secondary btn-sm">Official Source ↗</a>
              </div>

              <p style={{ fontSize: '0.85rem', color: 'var(--color-text-2)', marginBottom: 16 }}>{ds.description}</p>

              <div className="grid-2" style={{ gap: 12, marginBottom: 16 }}>
                {Object.entries(ds.stats).map(([k, v]) => (
                  <div key={k} style={{ display: 'flex', gap: 8, fontSize: '0.8rem' }}>
                    <span style={{ color: 'var(--color-text-muted)', width: 120, flexShrink: 0, textTransform: 'capitalize' }}>
                      {k.replace(/_/g, ' ')}
                    </span>
                    <span style={{ fontWeight: 500 }}>{String(v)}</span>
                  </div>
                ))}
              </div>

              <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 12 }}>
                <div className="section-label" style={{ marginBottom: 6 }}>Files</div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {ds.files.map(f => (
                    <span key={f} style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem',
                      background: 'var(--color-surface-2)', border: '1px solid var(--color-border)',
                      borderRadius: 4, padding: '2px 8px' }}>{f}</span>
                  ))}
                </div>
                <div style={{ marginTop: 8, fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                  License: {ds.license}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
