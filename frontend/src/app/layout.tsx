import type { Metadata } from 'next';
import './globals.css';
import Sidebar from '@/components/Sidebar';

export const metadata: Metadata = {
  title: { default: 'MANAS — Computational Brain Disease Mapping', template: '%s | MANAS' },
  description:
    'MANAS (मनस्) is a computational neuroscience research platform for mapping disease-associated regional changes in Alzheimer\'s and Parkinson\'s disease using publicly available human brain data.',
  keywords: ['computational neuroscience', 'Alzheimer\'s disease', 'brain mapping', 'Allen Brain Atlas', 'OASIS'],
  authors: [{ name: 'MANAS Research Platform' }],
  robots: { index: true, follow: true },
  openGraph: {
    title: 'MANAS — Computational Brain Disease Mapping',
    description: 'Research-grade computational neuroscience platform integrating public human brain data for Alzheimer\'s and Parkinson\'s disease analysis.',
    type: 'website',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="layout">
          <Sidebar />
          <div className="main">
            <div className="disclaimer-bar">
              MANAS is a computational research platform. Results represent statistical analyses
              of research datasets and should not be interpreted as medical diagnosis or proof
              of biological causation.
            </div>
            <main>{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
