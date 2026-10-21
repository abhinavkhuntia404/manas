'use client';
import { useEffect, useState } from 'react';
import { api, type BrainRegion } from '@/lib/api';

export default function BrainRegionsPage() {
  const [regions, setRegions] = useState<BrainRegion[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [hemisphere, setHemisphere] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.regions.list({ page, page_size: 50, search: search || undefined, hemisphere: hemisphere || undefined })
      .then(d => { setRegions(d.regions); setTotal(d.total); setLoading(false); })
      .catch(() => setLoading(false));
  }, [page, search, hemisphere]);

  const CATEGORY_COLORS: Record<string, string> = {
    cortical: '#3b82f6', subcortical: '#8b5cf6', limbic: '#f59e0b',
    cerebellar: '#10b981', brainstem: '#ef4444', white_matter: '#6b7280',
    whole_brain: '#1a56db', other: '#9ca3af',
  };

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Brain Regions</h1>
        <p className="page-subtitle">
          Canonical brain region registry from the Allen Human Reference Atlas.
          Click any region to view analysis results and provenance.
        </p>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <input
          type="search"
          placeholder="Search regions…"
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1); }}
          style={{ padding: '7px 12px', border: '1px solid var(--color-border)',
            borderRadius: 4, fontSize: '0.85rem', fontFamily: 'inherit', width: 240 }}
        />
        <select value={hemisphere} onChange={e => { setHemisphere(e.target.value); setPage(1); }}
          style={{ padding: '7px 12px', border: '1px solid var(--color-border)',
            borderRadius: 4, fontSize: '0.85rem', background: 'var(--color-surface)' }}>
          <option value="">All hemispheres</option>
          <option value="left">Left</option>
          <option value="right">Right</option>
          <option value="bilateral">Bilateral</option>
        </select>
        <span style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', alignSelf: 'center' }}>
          {total} regions
        </span>
      </div>

      {loading && <div className="loading">Loading regions…</div>}

      {!loading && regions.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-title">No regions found</div>
          <p style={{ fontSize: '0.82rem', marginTop: 4 }}>
            Trigger Allen Atlas ingestion to populate the region registry.
          </p>
        </div>
      )}

      {regions.length > 0 && (
        <div className="table-wrap" style={{ marginBottom: 24 }}>
          <table className="data-table">
            <thead><tr>
              <th>Name</th><th>Abbrev.</th><th>Category</th>
              <th>Hemisphere</th><th>Lobe</th><th>Leaf</th>
            </tr></thead>
            <tbody>
              {regions.map(r => (
                <tr key={r.region_id} onClick={() => window.location.href = `/brain-regions/${r.region_id}`}>
                  <td style={{ fontWeight: 500 }}>{r.name}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{r.abbreviation || '—'}</td>
                  <td>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                      <span style={{ width: 8, height: 8, borderRadius: '50%',
                        background: CATEGORY_COLORS[r.anatomical_category] ?? '#9ca3af',
                        flexShrink: 0 }} />
                      <span style={{ fontSize: '0.78rem' }}>{r.anatomical_category || '—'}</span>
                    </span>
                  </td>
                  <td style={{ fontSize: '0.78rem' }}>{r.hemisphere}</td>
                  <td style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>{r.lobe || '—'}</td>
                  <td>{r.is_leaf ? '✓' : ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {total > 50 && (
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: '0.82rem' }}>
          <button className="btn btn-secondary btn-sm" onClick={() => setPage(p => Math.max(1, p-1))} disabled={page === 1}>← Prev</button>
          <span style={{ color: 'var(--color-text-muted)' }}>Page {page} of {Math.ceil(total/50)}</span>
          <button className="btn btn-secondary btn-sm" onClick={() => setPage(p => p+1)} disabled={page * 50 >= total}>Next →</button>
        </div>
      )}
    </div>
  );
}
