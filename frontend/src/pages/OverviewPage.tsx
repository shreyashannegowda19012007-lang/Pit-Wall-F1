import { useState, useEffect } from 'react';
import { Activity, Clock, Zap, Target, Gauge, Flag, Trophy } from 'lucide-react';
import { usePitwall } from '../contexts/PitwallContext';
import './OverviewPage.css';

export default function OverviewPage() {
  const { session, primaryDriver, referenceDriver } = usePitwall();
  const [timing, setTiming] = useState<any>(null);
  const [telemetry, setTelemetry] = useState<any>(null);
  const [strategy, setStrategy] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    Promise.all([
      fetch(`http://localhost:8000/api/timing/summary?session_id=${session}`).then(r => r.json()),
      fetch(`http://localhost:8000/api/telemetry/profile/${primaryDriver}`).then(r => r.json()),
      fetch(`http://localhost:8000/api/strategy/summary?session_id=${session}&driver_id=${primaryDriver}`).then(r => r.json())
    ])
    .then(([timingData, telemetryData, strategyData]) => {
      if (!mounted) return;
      setTiming(timingData);
      setTelemetry(telemetryData);
      setStrategy(strategyData);
      setError('');
    })
    .catch(err => {
      if (!mounted) return;
      console.error(err);
      setError('Failed to load authoritative data. Ensure Python backend is running.');
    })
    .finally(() => {
      if (mounted) setLoading(false);
    });

    return () => { mounted = false; };
  }, [session, primaryDriver]);

  if (loading) {
    return (
      <div className="overview-loading">
        <div className="spinner"></div>
        <p>Initializing Session Context...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="overview-error">
        <Target size={48} className="error-icon" />
        <h2>Data Telemetry Error</h2>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={() => window.location.reload()}>Retry Connection</button>
      </div>
    );
  }

  const sessionName = timing?.manifest?.session_id || session;

  const drsEfficiency = telemetry?.drs_efficiency_metric || 'N/A';
  const apexSpeed = telemetry?.avg_apex_speed_kph ? `${Math.round(telemetry.avg_apex_speed_kph)} kph` : 'N/A';
  const consistency = telemetry?.lap_consistency_rating || 'N/A';
  const tyreManagement = telemetry?.tyre_management_score || 'N/A';

  const currentStint = strategy?.stints?.[strategy.stints.length - 1];
  const tyreCompound = currentStint?.compound || 'N/A';
  const tyreAge = currentStint?.laps_on_tyre || 'N/A';
  const pitWindow = strategy?.optimal_pit_window || 'N/A';
  const projectedFinish = strategy?.projected_finish_position || 'N/A';

  return (
    <div className="overview-container">
      <header className="overview-header">
        <div className="flex items-center gap-md">
          <h1 style={{ marginBottom: 0 }}>Driver Dashboard: <span style={{ color: 'var(--accent-blue)' }}>{primaryDriver}</span></h1>
          <div className="badge badge-green">LIVE TELEMETRY</div>
        </div>
        <div className="session-info-badge">
          <Flag size={14} /> {sessionName} | Reference: {referenceDriver}
        </div>
      </header>

      <div className="grid grid-cols-4 gap-md" style={{ marginBottom: '2rem' }}>
        <div className="card stat-card">
          <Activity className="stat-icon" size={20} />
          <div className="stat-content">
            <span className="metric-label">Session ID</span>
            <span className="metric-value" style={{ fontSize: '1.25rem' }}>{sessionName}</span>
          </div>
        </div>
        <div className="card stat-card">
          <Clock className="stat-icon" size={20} />
          <div className="stat-content">
            <span className="metric-label">DRS Efficiency</span>
            <span className="metric-value" style={{ fontSize: '1.25rem' }}>{drsEfficiency}</span>
          </div>
        </div>
        <div className="card stat-card">
          <Zap className="stat-icon" size={20} />
          <div className="stat-content">
            <span className="metric-label">Avg Apex Speed</span>
            <span className="metric-value" style={{ fontSize: '1.25rem' }}>{apexSpeed}</span>
          </div>
        </div>
        <div className="card stat-card">
          <Target className="stat-icon" size={20} />
          <div className="stat-content">
            <span className="metric-label">Active Compound</span>
            <span className="metric-value" style={{ fontSize: '1.25rem', color: tyreCompound === 'SOFT' ? '#ff3333' : tyreCompound === 'HARD' ? '#f1f3f5' : '#ffeb3b' }}>
              {tyreCompound} ({tyreAge} L)
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-lg">
        <div className="card">
          <h3 className="flex items-center gap-sm" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem', marginBottom: '1rem', color: 'var(--text-primary)' }}>
            <Gauge size={18} style={{ color: 'var(--accent-blue)' }} />
            Performance Profile
          </h3>
          <div className="profile-stats">
            <div className="profile-stat-item">
              <span className="stat-label">Lap Consistency</span>
              <span className="stat-val">{consistency}</span>
            </div>
            <div className="profile-stat-item">
              <span className="stat-label">Tyre Management</span>
              <span className="stat-val">{tyreManagement}</span>
            </div>
            <div className="profile-stat-item">
              <span className="stat-label">Braking Stability</span>
              <span className="stat-val">{telemetry?.braking_stability || 'N/A'}</span>
            </div>
            <div className="profile-stat-item">
              <span className="stat-label">Throttle Application</span>
              <span className="stat-val">{telemetry?.throttle_application || 'N/A'}</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="flex items-center gap-sm" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem', marginBottom: '1rem', color: 'var(--text-primary)' }}>
            <Trophy size={18} style={{ color: 'var(--neon-purple)' }} />
            Strategy & Projections
          </h3>
          <div className="profile-stats">
            <div className="profile-stat-item">
              <span className="stat-label">Optimal Pit Window</span>
              <span className="stat-val">{pitWindow}</span>
            </div>
            <div className="profile-stat-item">
              <span className="stat-label">Projected Finish</span>
              <span className="stat-val" style={{ color: 'var(--accent-green)' }}>{projectedFinish}</span>
            </div>
            <div className="profile-stat-item">
              <span className="stat-label">Undercut Threat</span>
              <span className="stat-val" style={{ color: 'var(--error)' }}>{strategy?.undercut_threat || 'N/A'}</span>
            </div>
            <div className="profile-stat-item">
              <span className="stat-label">Overtake Delta Required</span>
              <span className="stat-val">{strategy?.overtake_delta || 'N/A'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
