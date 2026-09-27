import { useState, useEffect } from 'react';
import { usePitwall } from '../contexts/PitwallContext';
import { Target, Users, AlertTriangle } from 'lucide-react';
import './ComparisonPage.css';

export default function ComparisonPage() {
  const { session, primaryDriver, referenceDriver } = usePitwall();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    fetch(`http://localhost:8000/api/telemetry/compare?session_id=${session}&target_driver=${primaryDriver}&ref_driver=${referenceDriver}`)
      .then(r => r.json())
      .then(res => {
        if (!mounted) return;
        if (res.success === false) {
          setError(res.error || 'Failed to fetch comparison');
        } else {
          setData(res);
          setError('');
        }
      })
      .catch(err => {
        if (!mounted) return;
        console.error(err);
        setError('Network error fetching comparison');
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => { mounted = false; };
  }, [session, primaryDriver, referenceDriver]);

  if (loading && !data) {
    return (
      <div className="comparison-loading">
        <div className="spinner"></div>
        <p>Analyzing Time Loss Attribution...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="comparison-error">
        <Target size={48} className="error-icon" />
        <h2>Comparison Analysis Failed</h2>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={() => window.location.reload()}>Retry Connection</button>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="comparison-container">
      <header className="comparison-header">
        <h1 className="flex items-center gap-sm">
          <Users size={24} style={{ color: 'var(--accent-blue)' }} />
          Driver Head-to-Head
        </h1>
        <div className="matchup-banner">
          <span className="driver-pill primary">{primaryDriver}</span>
          <span className="vs">VS</span>
          <span className="driver-pill reference">{referenceDriver}</span>
        </div>
      </header>

      <div className="grid grid-cols-3 gap-md" style={{ marginBottom: '1.5rem' }}>
        <div className="card stat-card">
          <div className="stat-content">
            <span className="metric-label">Sector 1 Delta</span>
            <span className="metric-value" style={{ color: data.sector_time_loss.sector_1_s > 0 ? 'var(--error)' : 'var(--accent-green)' }}>
              {data.sector_time_loss.sector_1_s > 0 ? '+' : ''}{data.sector_time_loss.sector_1_s}s
            </span>
          </div>
        </div>
        <div className="card stat-card">
          <div className="stat-content">
            <span className="metric-label">Sector 2 Delta</span>
            <span className="metric-value" style={{ color: data.sector_time_loss.sector_2_s > 0 ? 'var(--error)' : 'var(--accent-green)' }}>
              {data.sector_time_loss.sector_2_s > 0 ? '+' : ''}{data.sector_time_loss.sector_2_s}s
            </span>
          </div>
        </div>
        <div className="card stat-card">
          <div className="stat-content">
            <span className="metric-label">Sector 3 Delta</span>
            <span className="metric-value" style={{ color: data.sector_time_loss.sector_3_s > 0 ? 'var(--error)' : 'var(--accent-green)' }}>
              {data.sector_time_loss.sector_3_s > 0 ? '+' : ''}{data.sector_time_loss.sector_3_s}s
            </span>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="flex items-center gap-sm" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem', marginBottom: '1rem', color: 'var(--text-primary)' }}>
          <AlertTriangle size={18} style={{ color: 'var(--error)' }} />
          Top Weaknesses & Time Loss Attributions
        </h3>

        {data.top_opportunities && data.top_opportunities.length > 0 ? (
          <table className="comparison-table">
            <thead>
              <tr>
                <th>Corner</th>
                <th>Total Loss (s)</th>
                <th>Braking Phase</th>
                <th>Apex Phase</th>
                <th>Exit Phase</th>
                <th>Driver Weakness</th>
              </tr>
            </thead>
            <tbody>
              {data.top_opportunities.map((opp: any, idx: number) => (
                <tr key={idx}>
                  <td>T{opp.corner_number}</td>
                  <td style={{ color: 'var(--error)', fontWeight: 600 }}>+{opp.measured_time_loss_s?.toFixed(3) || '0.000'}s</td>
                  <td>{opp.braking_loss_s > 0.05 ? <span style={{ color: 'var(--error)' }}>Early Brake (+{opp.braking_loss_s?.toFixed(2)}s)</span> : <span style={{ color: 'var(--text-secondary)' }}>-</span>}</td>
                  <td>{opp.apex_loss_s > 0.05 ? <span style={{ color: 'var(--error)' }}>Low Min Speed (+{opp.apex_loss_s?.toFixed(2)}s)</span> : <span style={{ color: 'var(--text-secondary)' }}>-</span>}</td>
                  <td>{opp.exit_loss_s > 0.05 ? <span style={{ color: 'var(--error)' }}>Late Throttle (+{opp.exit_loss_s?.toFixed(3)}s)</span> : 'Neutral'}</td>
                  <td>
                    {opp.braking_loss_s > opp.apex_loss_s && opp.braking_loss_s > opp.exit_loss_s ? 'Braking Confidence' :
                     opp.exit_loss_s > opp.apex_loss_s ? 'Traction / Throttle' : 'Corner Speed'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state">
            <p>No significant time-loss corners detected or telemetry aligned perfectly.</p>
          </div>
        )}
      </div>
    </div>
  );
}
