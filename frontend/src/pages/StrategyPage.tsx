import { useState, useEffect } from 'react';
import { usePitwall } from '../contexts/PitwallContext';
import { Target, GitMerge, AlertTriangle, ChevronRight } from 'lucide-react';
import './StrategyPage.css';

export default function StrategyPage() {
  const { session, primaryDriver, referenceDriver } = usePitwall();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    fetch(`http://localhost:8000/api/strategy/simulation?session_id=${session}&primary_driver=${primaryDriver}&ref_driver=${referenceDriver}`)
      .then(r => r.json())
      .then(res => {
        if (!mounted) return;
        if (res.success === false) {
          setError(res.error || 'Failed to fetch strategy simulation');
        } else {
          setData(res);
          setError('');
        }
      })
      .catch(err => {
        if (!mounted) return;
        console.error(err);
        setError('Network error fetching strategy simulation');
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => { mounted = false; };
  }, [session, primaryDriver, referenceDriver]);

  if (loading && !data) {
    return (
      <div className="strategy-loading">
        <div className="spinner"></div>
        <p>Running 10,000 Monte Carlo Simulations...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="strategy-error">
        <Target size={48} className="error-icon" />
        <h2>Strategy Simulation Failed</h2>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={() => window.location.reload()}>Retry Connection</button>
      </div>
    );
  }

  if (!data) return null;

  const sim = data.synthetic_scenario; // we reused the synthetic key, but it's now real data!
  const undercutProb = data.undercut_success_probability * 100;
  const overcutProb = data.overcut_success_probability * 100;

  return (
    <div className="strategy-container">
      <header className="strategy-header">
        <h1 className="flex items-center gap-sm">
          <GitMerge size={24} style={{ color: 'var(--accent-blue)' }} />
          Monte Carlo Strategy Simulation
        </h1>
        <div className="header-stats flex gap-md">
          <div className="stat-pill">
            Live Track Gap: <span style={{ color: 'var(--error)' }}>{sim.current_gap_s}s</span>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-2 gap-lg">
        {/* Undercut Panel */}
        <div className="card">
          <h3 className="flex items-center justify-between" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem', marginBottom: '1rem', color: 'var(--text-primary)' }}>
            <span>Undercut Threat ({primaryDriver} pits first)</span>
            {undercutProb > 50 && <AlertTriangle size={18} style={{ color: 'var(--error)' }} />}
          </h3>
          <div className="prob-display">
            <div className="prob-label">Success Probability</div>
            <div className="prob-value" style={{ color: undercutProb > 50 ? 'var(--accent-green)' : 'var(--error)' }}>
              {undercutProb.toFixed(1)}%
            </div>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${undercutProb}%`, backgroundColor: undercutProb > 50 ? 'var(--accent-green)' : 'var(--error)' }}></div>
          </div>
          <div className="strat-details mt-md">
            <div className="strat-row">
              <span className="strat-key">Expected Time Gain</span>
              <span className="strat-val">{data.expected_undercut_time_gain_s.toFixed(2)}s</span>
            </div>
          </div>
        </div>

        {/* Overcut Panel */}
        <div className="card">
          <h3 className="flex items-center justify-between" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem', marginBottom: '1rem', color: 'var(--text-primary)' }}>
            <span>Overcut Viability ({primaryDriver} stays out)</span>
          </h3>
          <div className="prob-display">
            <div className="prob-label">Success Probability</div>
            <div className="prob-value" style={{ color: overcutProb > 50 ? 'var(--accent-green)' : 'var(--error)' }}>
              {overcutProb.toFixed(1)}%
            </div>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${overcutProb}%`, backgroundColor: overcutProb > 50 ? 'var(--accent-green)' : 'var(--error)' }}></div>
          </div>
          <div className="strat-details mt-md">
            <div className="strat-row">
              <span className="strat-key">Expected Time Gain</span>
              <span className="strat-val">{data.expected_overcut_time_gain_s.toFixed(2)}s</span>
            </div>
          </div>
        </div>
      </div>

      <div className="card mt-lg">
        <h3 style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem', marginBottom: '1rem', color: 'var(--text-primary)' }}>
          Tactical Directive
        </h3>
        <div className="directive-box flex items-start gap-md">
          <ChevronRight size={24} style={{ color: 'var(--accent-blue)', marginTop: '2px' }} />
          <div>
            <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-primary)' }}>
              {undercutProb > overcutProb ? `Prioritize Undercut` : `Extend Stint (Overcut Potential)`}
            </h4>
            <p style={{ margin: 0, color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              Based on 10,000 Monte Carlo simulations utilizing real FastF1 track gaps ({sim.current_gap_s}s),
              the optimal strategy against {referenceDriver} is to {undercutProb > overcutProb ? 'box immediately to leverage fresh rubber pace advantage.' : 'maintain track position. The tyre delta is not sufficient to overcome the pit loss.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
