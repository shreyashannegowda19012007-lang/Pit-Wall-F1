export default function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="placeholder-page" style={{ paddingTop: '2rem' }}>
      <h1 style={{ fontSize: '2rem', marginBottom: '1rem' }}>{title}</h1>
      <div className="card" style={{ padding: '3rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--text-muted)' }}>
          This module is part of Phase 2 modernization. The authoritative backend engine
          for {title} is currently active and can be accessed via the legacy Streamlit interface.
        </p>
      </div>
    </div>
  );
}
