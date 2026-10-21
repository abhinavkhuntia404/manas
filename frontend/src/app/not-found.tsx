import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="page-content" style={{ textAlign: 'center', padding: '80px 24px' }}>
      <h1 style={{ fontSize: '3rem', fontFamily: 'var(--font-mono)', color: 'var(--color-accent)', marginBottom: 12 }}>
        404
      </h1>
      <h2 style={{ fontSize: '1.25rem', marginBottom: 12 }}>Page Not Found</h2>
      <p style={{ color: 'var(--color-text-muted)', fontSize: '0.88rem', maxWidth: 450, margin: '0 auto 24px' }}>
        The requested neuroinformatics view or resource could not be found in the MANAS repository.
      </p>
      <Link href="/" className="btn btn-primary" style={{ textDecoration: 'none' }}>
        Return to Dashboard
      </Link>
    </div>
  );
}
