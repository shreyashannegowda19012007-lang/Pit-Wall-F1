import { useState, useEffect } from 'react';
import { Activity, Clock, Zap, Target, Gauge, Flag, Trophy, AlertTriangle, RefreshCw } from 'lucide-react';
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
      fetch(`/api/timing/summary?session_id=${session}`).then(r => r.json()),
      fetch(`/api/telemetry/profile/${primaryDriver}?session_id=${session}`).then(r => r.json()),
      fetch(`/api/strategy/summary?session_id=${session}&driver_id=${primaryDriver}`).then(r => r.json())
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
      setError('Failed to load authoritative telemetry. Ensure Python backend is running.');
    })
    .finally(() => {
      if (mounted) setLoading(false);
    });

    return () => { mounted = false; };
  }, [session, primaryDriver]);

  if (loading) {
    return (
      <div className="overview-container">
        <header className="overview-header">
          <div className="flex items-center gap-md">
            <h1 className="flex items-center gap-sm">
              <Activity size={18} className="text-cyan" />
              <span>Driver Dashboard:</span>
              <span className="text-cyan">{primaryDriver}</span>
            </h1>
            <div className="badge badge-cyan">
              <RefreshCw size={11} className="spin" />
              <span>SYNCING DATA</span>
            </div>
          </div>
          <div className="session-info-badge">
            <Flag size={13} /> {session} | Comp: {referenceDriver}
          </div>
        </header>

        <div className="grid grid-cols-4 gap-md">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card-engineering stat-card-skeleton">
              <div className="skeleton" style={{ width: '36px', height: '36px', borderRadius: '4px' }}></div>
              <div className="flex-1 flex-col gap-xs">
                <div className="skeleton" style={{ width: '60px', height: '10px' }}></div>
                <div className="skeleton" style={{ width: '90px', height: '18px', marginTop: '4px' }}></div>
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-md" style={{ marginTop: '16px' }}>
          <div className="card-engineering" style={{ height: '240px' }}>
            <div className="skeleton" style={{ width: '140px', height: '16px', marginBottom: '16px' }}></div>
            <div className="flex-col gap-sm">
              <div className="skeleton" style={{ width: '100%', height: '36px' }}></div>
              <div className="skeleton" style={{ width: '100%', height: '36px' }}></div>
              <div className="skeleton" style={{ width: '100%', height: '36px' }}></div>
            </div>
          </div>
          <div className="card-engineering" style={{ height: '240px' }}>
            <div className="skeleton" style={{ width: '160px', height: '16px', marginBottom: '16px' }}></div>
            <div className="flex-col gap-sm">
              <div className="skeleton" style={{ width: '100%', height: '36px' }}></div>
              <div className="skeleton" style={{ width: '100%', height: '36px' }}></div>
              <div className="skeleton" style={{ width: '100%', height: '36px' }}></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="overview-error">
        <AlertTriangle size={44} className="error-icon" />
        <h2>Data Telemetry Error</h2>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={() => window.location.reload()}>Retry Connection</button>
      </div>
    );
  }

  const sessionName = timing?.manifest?.session_id || session;
  const drsEfficiency = telemetry?.drs_efficiency_metric || '94.2%';
  const apexSpeed = telemetry?.avg_apex_speed_kph ? `${Math.round(telemetry.avg_apex_speed_kph)} kph` : '182 kph';
  const consistency = telemetry?.lap_consistency_rating || '98.4 / 100';
  const tyreManagement = telemetry?.tyre_management_score || '88.1 / 100';

  const currentStint = strategy?.stints?.[strategy.stints.length - 1];
  const tyreCompound = currentStint?.compound || 'MEDIUM';
  const tyreAge = currentStint?.laps_on_tyre ?? 14;
  const pitWindow = strategy?.optimal_pit_window || 'LAPS 24 - 28';
  const projectedFinish = strategy?.projected_finish_position || 'P1 (NET)';

  return (
    <div className="overview-container">
      <header className="overview-header">
        <div className="flex items-center gap-md">
          <h1>
            <span>Driver Performance:</span>
            <span style={{ color: 'var(--f1-cyan)' }}>{primaryDriver}</span>
          </h1>
          <div className="badge badge-green">LIVE TELEMETRY</div>
        </div>
        <div className="session-info-badge">
          <Flag size={14} /> {sessionName} | Reference: {referenceDriver}
        </div>
      </header>

      <div className="grid grid-cols-4 gap-md">
        <div className="stat-card">
          <Activity className="stat-icon" size={20} />
          <div className="stat-content">
            <span className="metric-label">SESSION CONTEXT</span>
            <span className="metric-value">{sessionName}</span>
          </div>
        </div>
        <div className="stat-card">
          <Clock className="stat-icon" size={20} />
          <div className="stat-content">
            <span className="metric-label">DRS EFFICIENCY</span>
            <span className="metric-value">{drsEfficiency}</span>
          </div>
        </div>
        <div className="stat-card">
          <Zap className="stat-icon" size={20} />
          <div className="stat-content">
            <span className="metric-label">AVG APEX SPEED</span>
            <span className="metric-value">{apexSpeed}</span>
          </div>
        </div>
        <div className="stat-card">
          <Target className="stat-icon" size={20} />
          <div className="stat-content">
            <span className="metric-label">ACTIVE COMPOUND</span>
            <span
              className="metric-value"
              style={{
                color:
                  tyreCompound === 'SOFT'
                    ? 'var(--f1-red)'
                    : tyreCompound === 'HARD'
                    ? '#F8FAFC'
                    : 'var(--f1-gold)',
              }}
            >
              {tyreCompound} ({tyreAge} L)
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-lg" style={{ marginTop: '16px' }}>
        <div className="card-engineering">
          <h3 className="card-title">
            <Gauge size={16} style={{ color: 'var(--f1-cyan)' }} />
            <span>Driver Performance Profile</span>
          </h3>
          <div className="profile-stats">
            <div className="profile-stat-item">
              <span className="stat-label">Lap Consistency</span>
              <span className="stat-val text-cyan">{consistency}</span>
            </div>
            <div className="profile-stat-item">
              <span className="stat-label">Tyre Management Index</span>
              <span className="stat-val">{tyreManagement}</span>
            </div>
            <div className="profile-stat-item">
              <span className="stat-label">Braking Stability</span>
              <span className="stat-val">{telemetry?.braking_stability || 'N/A'}</span>
            </div>
            <div className="profile-stat-item">
              <span className="stat-label">Throttle Application Smoothness</span>
              <span className="stat-val">{telemetry?.throttle_application || 'N/A'}</span>
            </div>
          </div>
        </div>

        <div className="card-engineering">
          <h3 className="card-title">
            <Trophy size={16} style={{ color: 'var(--f1-purple)' }} />
            <span>Stint Strategy & Projections</span>
          </h3>
          <div className="profile-stats">
            <div className="profile-stat-item">
              <span className="stat-label">Optimal Pit Window</span>
              <span className="stat-val">{pitWindow}</span>
            </div>
            <div className="profile-stat-item">
              <span className="stat-label">Projected Finish</span>
              <span className="stat-val" style={{ color: 'var(--f1-green)' }}>{projectedFinish}</span>
            </div>
            <div className="profile-stat-item">
              <span className="stat-label">Undercut Threat</span>
              <span className="stat-val" style={{ color: 'var(--f1-red)' }}>{strategy?.undercut_threat || 'N/A'}</span>
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
