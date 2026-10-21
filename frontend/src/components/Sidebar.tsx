'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const NAV = [
  {
    section: 'Diseases & Research',
    links: [
      { href: '/', label: 'Overview', icon: '⬡' },
      { href: '/alzheimers', label: "Alzheimer's Disease", icon: '🧠' },
      { href: '/vascular', label: 'Vascular Dementia', icon: '🩸' },
      { href: '/lewy-body', label: "Lewy Body / Parkinson's", icon: '⚡' },
      { href: '/brain-maps', label: 'Brain Maps', icon: '◉' },
      { href: '/brain-regions', label: 'Brain Regions', icon: '⬢' },
    ],
  },
  {
    section: 'Data',
    links: [
      { href: '/datasets', label: 'Datasets', icon: '⊞' },
      { href: '/data-explorer', label: 'Data Explorer', icon: '⊡' },
    ],
  },
  {
    section: 'Analysis',
    links: [
      { href: '/analysis-runs', label: 'Analysis Runs', icon: '▶' },
      { href: '/reproducibility', label: 'Reproducibility', icon: '⟳' },
      { href: '/evidence', label: 'Research Evidence', icon: '📄' },
    ],
  },
  {
    section: 'System',
    links: [
      { href: '/docs', label: 'Documentation', icon: '?' },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-title">MANAS &nbsp;<span style={{ fontWeight: 300, fontSize: '0.85rem' }}>मनस्</span></div>
        <div className="sidebar-logo-sub">Computational Brain Disease Mapping</div>
      </div>

      {NAV.map(({ section, links }) => (
        <div key={section} className="sidebar-section">
          <div className="sidebar-section-label">{section}</div>
          {links.map(({ href, label, icon }) => {
            const isActive = pathname === href || (href !== '/' && pathname.startsWith(href));
            return (
              <Link
                key={href}
                href={href}
                className={`sidebar-link ${isActive ? 'active' : ''}`}
              >
                <span style={{ fontSize: '0.75rem', width: 16, textAlign: 'center' }}>{icon}</span>
                {label}
              </Link>
            );
          })}
        </div>
      ))}

      <div style={{ marginTop: 'auto', padding: '12px 16px', borderTop: '1px solid var(--color-border)' }}>
        <p style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
          MANAS v1.0 · Research Platform<br />
          Not a medical device.
        </p>
      </div>
    </aside>
  );
}
