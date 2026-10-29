import React, { useState, useEffect } from 'react';
import { usePitwall } from '../contexts/PitwallContext';
import {
  RadioTower,
  RefreshCw,
  Clock,
  Layers,
  Fuel,
  Volume2,
  BookOpen,
  Flag,
  Timer,
  Activity
} from 'lucide-react';
import { LiveTelemetrySection } from './LiveTelemetrySection';
import './LivePage.css';

interface TimingTowerEntry {
  position: number;
  driver_code: string;
  driver_number: string;
  team_name: string;
  team_color: string;
  gap_to_leader_s: string;
  interval_ahead_s: string;
  last_lap_time_s: string;
  current_compound: string;
  tyre_age_laps: number;
  pit_stops_count: number;
  status: string;
}

interface PitStopEvent {
  lap: number;
  driver_code: string;
  driver_number: string;
  team_name: string;
  stop_number: number;
  stationary_time_s: number;
  pit_lane_time_s: number;
  compound_fitted: string;
}

interface RaceControlMessage {
  lap: number | null;
  timestamp: string;
  flag: string | null;
  category: string;
  message: string;
  status: string;
}

interface TeamRadioEntry {
  timestamp: string;
  driver_code: string;
  driver_number: string;
  lap: number | null;
  transcript: string;
  audio_url: string | null;
  confidence_level: string;
  strategic_context: string;
}

interface RegulationDossier {
  regulation_id: string;
  title: string;
  effective_season: number;
  article_reference: string;
  summary: string;
  penalty_guideline: string;
  technical_specifications: Record<string, any>;
}

export const LivePage: React.FC = () => {
  const { season, session, primaryDriver } = usePitwall();
  const [activeTab, setActiveTab] = useState<'telemetry' | 'tower' | 'pitstops' | 'racecontrol' | 'radio' | 'regulations'>('telemetry');
  
  const [timingTower, setTimingTower] = useState<TimingTowerEntry[]>([]);
  const [pitStops, setPitStops] = useState<PitStopEvent[]>([]);
  const [raceControl, setRaceControl] = useState<RaceControlMessage[]>([]);
  const [teamRadio, setTeamRadio] = useState<TeamRadioEntry[]>([]);
  const [regulations, setRegulations] = useState<RegulationDossier[]>([]);
  
  const [loading, setLoading] = useState<boolean>(true);
  const [lastCheck, setLastCheck] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);

  const fetchRaceOpsData = async () => {
    try {
      setLoading(true);
      const [towerRes, stopsRes, rcRes, radioRes, regsRes] = await Promise.all([
        fetch(`/api/race-operations/timing-tower?session_id=${session}`).then(r => r.json()).catch(() => ({ timing_tower: [] })),
        fetch(`/api/race-operations/pit-stops?session_id=${session}`).then(r => r.json()).catch(() => ({ pit_stops: [] })),
        fetch(`/api/race-operations/race-control?session_id=${session}`).then(r => r.json()).catch(() => ({ race_control: [] })),
        fetch(`/api/race-operations/team-radio?session_id=${session}&driver_code=${primaryDriver}`).then(r => r.json()).catch(() => ({ team_radio: [] })),
        fetch(`/api/race-operations/regulations`).then(r => r.json()).catch(() => ({ regulations: [] }))
      ]);

      if (towerRes.timing_tower) setTimingTower(towerRes.timing_tower);
      if (stopsRes.pit_stops) setPitStops(stopsRes.pit_stops);
      if (rcRes.race_control) setRaceControl(rcRes.race_control);
      if (radioRes.team_radio) setTeamRadio(radioRes.team_radio);
      if (regsRes.regulations) setRegulations(regsRes.regulations);
      setLastCheck(new Date());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRaceOpsData();
    if (!autoRefresh) return;
    const interval = setInterval(fetchRaceOpsData, 15000);
    return () => clearInterval(interval);
  }, [session, primaryDriver, autoRefresh]);

  const getCompoundBadgeClass = (compound: string) => {
    const c = (compound || '').toUpperCase();
    if (c.includes('SOFT')) return 'soft';
    if (c.includes('MEDIUM')) return 'medium';
    if (c.includes('HARD')) return 'hard';
    if (c.includes('INTER')) return 'intermediate';
    if (c.includes('WET')) return 'wet';
    return 'hard';
  };

  return (
    <div className="live-container">
      {/* Page Header */}
      <header className="live-header">
        <div className="header-titles">
          <div className="title-row">
            <RadioTower size={22} className="header-icon text-red pulse-fast" />
            <h2>Race Operations & Pit-Wall Command</h2>
            <span className="live-status-pill active">
              <span className="live-dot"></span>
              SESSION SYNCHRONIZED
            </span>
          </div>
          <p className="subtitle">
            Timing tower gaps, stationary wheel-stop durations, race control incident feed, team radio, and FIA sporting regulations.
          </p>
        </div>

        {/* Polling & Refresh Controls */}
        <div className="live-controls">
          <div className="poll-info">
            <Clock size={12} />
            <span>Updated: {lastCheck.toLocaleTimeString()}</span>
          </div>

          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`btn-toggle-auto ${autoRefresh ? 'active' : ''}`}
          >
            <RefreshCw size={12} className={loading || autoRefresh ? 'spin' : ''} />
            <span>{loading ? 'Syncing...' : `Live Feed: ${autoRefresh ? 'ON' : 'OFF'}`}</span>
          </button>
        </div>
      </header>

      {/* Operational Overview Metrics Row */}
      <div className="live-metrics-row">
        <div className="metric-card">
          <div className="m-header">
            <Timer size={14} className="text-cyan" />
            <span>FASTEST PIT STOP</span>
          </div>
          <div className="m-value">
            {pitStops.length > 0 ? `${Math.min(...pitStops.map(s => s.stationary_time_s)).toFixed(2)}s` : '2.34s'}
          </div>
          <div className="m-sub">
            {pitStops.length > 0 ? `Total Pit Stops: ${pitStops.length}` : 'Stationary wheel-stop'}
          </div>
        </div>

        <div className="metric-card">
          <div className="m-header">
            <Flag size={14} className="text-amber" />
            <span>RACE CONTROL NOTICES</span>
          </div>
          <div className="m-value">
            {raceControl.length} EVENTS
          </div>
          <div className="m-sub">
            Track clear / DRS active
          </div>
        </div>

        <div className="metric-card">
          <div className="m-header">
            <Volume2 size={14} className="text-green" />
            <span>TEAM RADIO CAPTURES</span>
          </div>
          <div className="m-value">
            {teamRadio.length} BROADCASTS
          </div>
          <div className="m-sub">
            OpenF1 audio synchronized
          </div>
        </div>

        <div className="metric-card">
          <div className="m-header">
            <BookOpen size={14} className="text-blue" />
            <span>FIA REGULATION DOSSIERS</span>
          </div>
          <div className="m-value">
            {regulations.length} ARTICLES
          </div>
          <div className="m-sub">
            Season {season} certified
          </div>
        </div>
      </div>

      {/* Operational Sub-Navigation Tabs */}
      <div className="ops-tabs-nav" style={{ display: 'flex', gap: '8px', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '12px' }}>
        <button
          onClick={() => setActiveTab('telemetry')}
          className={`tab-btn ${activeTab === 'telemetry' ? 'active' : ''}`}
          style={{
            background: activeTab === 'telemetry' ? 'rgba(0, 245, 212, 0.15)' : 'rgba(255,255,255,0.03)',
            color: activeTab === 'telemetry' ? '#00F5D4' : '#94A3B8',
            border: activeTab === 'telemetry' ? '1px solid #00F5D4' : '1px solid rgba(255,255,255,0.08)',
            padding: '6px 14px',
            borderRadius: '4px',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <Activity size={13} />
          <span>LIVE TELEMETRY</span>
        </button>

        <button
          onClick={() => setActiveTab('tower')}
          className={`tab-btn ${activeTab === 'tower' ? 'active' : ''}`}
          style={{
            background: activeTab === 'tower' ? 'rgba(0, 245, 212, 0.15)' : 'rgba(255,255,255,0.03)',
            color: activeTab === 'tower' ? '#00F5D4' : '#94A3B8',
            border: activeTab === 'tower' ? '1px solid #00F5D4' : '1px solid rgba(255,255,255,0.08)',
            padding: '6px 14px',
            borderRadius: '4px',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <Layers size={13} />
          <span>TIMING TOWER</span>
        </button>

        <button
          onClick={() => setActiveTab('pitstops')}
          className={`tab-btn ${activeTab === 'pitstops' ? 'active' : ''}`}
          style={{
            background: activeTab === 'pitstops' ? 'rgba(0, 245, 212, 0.15)' : 'rgba(255,255,255,0.03)',
            color: activeTab === 'pitstops' ? '#00F5D4' : '#94A3B8',
            border: activeTab === 'pitstops' ? '1px solid #00F5D4' : '1px solid rgba(255,255,255,0.08)',
            padding: '6px 14px',
            borderRadius: '4px',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <Fuel size={13} />
          <span>PIT-STOP TIMELINE</span>
        </button>

        <button
          onClick={() => setActiveTab('racecontrol')}
          className={`tab-btn ${activeTab === 'racecontrol' ? 'active' : ''}`}
          style={{
            background: activeTab === 'racecontrol' ? 'rgba(0, 245, 212, 0.15)' : 'rgba(255,255,255,0.03)',
            color: activeTab === 'racecontrol' ? '#00F5D4' : '#94A3B8',
            border: activeTab === 'racecontrol' ? '1px solid #00F5D4' : '1px solid rgba(255,255,255,0.08)',
            padding: '6px 14px',
            borderRadius: '4px',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <Flag size={13} />
          <span>RACE CONTROL FEED</span>
        </button>

        <button
          onClick={() => setActiveTab('radio')}
          className={`tab-btn ${activeTab === 'radio' ? 'active' : ''}`}
          style={{
            background: activeTab === 'radio' ? 'rgba(0, 245, 212, 0.15)' : 'rgba(255,255,255,0.03)',
            color: activeTab === 'radio' ? '#00F5D4' : '#94A3B8',
            border: activeTab === 'radio' ? '1px solid #00F5D4' : '1px solid rgba(255,255,255,0.08)',
            padding: '6px 14px',
            borderRadius: '4px',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <Volume2 size={13} />
          <span>TEAM RADIO</span>
        </button>

        <button
          onClick={() => setActiveTab('regulations')}
          className={`tab-btn ${activeTab === 'regulations' ? 'active' : ''}`}
          style={{
            background: activeTab === 'regulations' ? 'rgba(0, 245, 212, 0.15)' : 'rgba(255,255,255,0.03)',
            color: activeTab === 'regulations' ? '#00F5D4' : '#94A3B8',
            border: activeTab === 'regulations' ? '1px solid #00F5D4' : '1px solid rgba(255,255,255,0.08)',
            padding: '6px 14px',
            borderRadius: '4px',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <BookOpen size={13} />
          <span>FIA REGULATIONS</span>
        </button>
      </div>

      {/* Tab 0: Live Telemetry Stream */}
      {activeTab === 'telemetry' && <LiveTelemetrySection />}

      {/* Tab 1: Timing Tower */}
      {activeTab === 'tower' && (
        <div className="live-table-card">
          <div className="table-header-row">
            <div className="th-title">
              <Layers size={15} />
              <span>OFFICIAL TIMING TOWER ({session})</span>
            </div>
            <span className="th-badge">LIVE FOM BROADCAST TELEMETRY</span>
          </div>

          <div className="table-responsive">
            <table className="timing-table">
              <thead>
                <tr>
                  <th>POS</th>
                  <th>DRIVER</th>
                  <th>NO</th>
                  <th>TEAM</th>
                  <th>GAP TO LEADER</th>
                  <th>INTERVAL</th>
                  <th>TYRE</th>
                  <th>AGE</th>
                  <th>STOPS</th>
                  <th>STATUS</th>
                </tr>
              </thead>
              <tbody>
                {timingTower.length > 0 ? (
                  timingTower.map((row) => (
                    <tr key={row.driver_code} className={row.position === 1 ? 'leader-row' : ''}>
                      <td className="col-pos">P{row.position}</td>
                      <td className="col-drv">
                        <span style={{ color: row.team_color || '#FFFFFF', fontWeight: 700 }}>
                          {row.driver_code}
                        </span>
                      </td>
                      <td className="col-stint">#{row.driver_number}</td>
                      <td className="col-team">{row.team_name}</td>
                      <td className="col-time">{row.gap_to_leader_s}</td>
                      <td className="col-sector">{row.interval_ahead_s}</td>
                      <td>
                        <span className={`tyre-tag ${getCompoundBadgeClass(row.current_compound)}`}>
                          {row.current_compound[0]}
                        </span>
                      </td>
                      <td className="col-stint">{row.tyre_age_laps} LAPS</td>
                      <td className="col-stint">{row.pit_stops_count}</td>
                      <td>
                        <span style={{
                          fontSize: '10px',
                          fontWeight: 700,
                          color: row.status === 'ON_TRACK' ? '#10B981' : (row.status === 'IN_PIT' ? '#F59E0B' : '#EF4444')
                        }}>
                          {row.status}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={10} style={{ textAlign: 'center', padding: '24px', color: '#64748B' }}>
                      Loading official timing tower telemetry for session {session}...
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Pit Stops */}
      {activeTab === 'pitstops' && (
        <div className="live-table-card">
          <div className="table-header-row">
            <div className="th-title">
              <Fuel size={15} />
              <span>OFFICIAL PIT-STOP CHRONOLOGY & STATIONARY TIMES</span>
            </div>
            <span className="th-badge">DIRECT TRANSPONDER MEASUREMENT</span>
          </div>

          <div className="table-responsive">
            <table className="timing-table">
              <thead>
                <tr>
                  <th>LAP</th>
                  <th>DRIVER</th>
                  <th>TEAM</th>
                  <th>STOP NO</th>
                  <th>WHEEL-STOP STATIONARY</th>
                  <th>NET PIT-LANE TIME</th>
                  <th>COMPOUND FITTED</th>
                </tr>
              </thead>
              <tbody>
                {pitStops.length > 0 ? (
                  pitStops.map((stop, i) => (
                    <tr key={i}>
                      <td className="col-pos">LAP {stop.lap}</td>
                      <td className="col-drv">{stop.driver_code} (#{stop.driver_number})</td>
                      <td className="col-team">{stop.team_name}</td>
                      <td className="col-stint">Stop #{stop.stop_number}</td>
                      <td className="col-time font-bold" style={{ color: stop.stationary_time_s < 2.6 ? '#10B981' : '#F59E0B' }}>
                        {stop.stationary_time_s.toFixed(2)}s
                      </td>
                      <td className="col-sector">{stop.pit_lane_time_s.toFixed(2)}s</td>
                      <td>
                        <span className={`tyre-tag ${getCompoundBadgeClass(stop.compound_fitted)}`}>
                          {stop.compound_fitted[0]}
                        </span>
                        <span style={{ marginLeft: '6px', fontSize: '11px', color: '#CBD5E1' }}>{stop.compound_fitted}</span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} style={{ textAlign: 'center', padding: '24px', color: '#64748B' }}>
                      No pit stops recorded yet for session {session}.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Race Control */}
      {activeTab === 'racecontrol' && (
        <div className="live-table-card">
          <div className="table-header-row">
            <div className="th-title">
              <Flag size={15} />
              <span>RACE CONTROL & STEWARD INCIDENT MESSAGES</span>
            </div>
            <span className="th-badge">OFFICIAL FIA RACE DIRECTOR FEED</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '12px 0' }}>
            {raceControl.map((rc, idx) => (
              <div key={idx} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 14px',
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '6px'
              }}>
                <span style={{ fontSize: '11px', color: '#64748B', fontFamily: 'JetBrains Mono', minWidth: '70px' }}>
                  {rc.timestamp}
                </span>
                {rc.lap && (
                  <span style={{ fontSize: '11px', fontWeight: 700, color: '#00F5D4', minWidth: '60px' }}>
                    LAP {rc.lap}
                  </span>
                )}
                {rc.flag && (
                  <span style={{
                    fontSize: '10px',
                    fontWeight: 800,
                    padding: '2px 6px',
                    borderRadius: '3px',
                    background: rc.flag === 'YELLOW' ? 'rgba(245,158,11,0.2)' : (rc.flag === 'GREEN' ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'),
                    color: rc.flag === 'YELLOW' ? '#F59E0B' : (rc.flag === 'GREEN' ? '#10B981' : '#EF4444')
                  }}>
                    {rc.flag} FLAG
                  </span>
                )}
                <span style={{ fontSize: '12px', color: '#E2E8F0', flex: 1, fontFamily: 'JetBrains Mono' }}>
                  {rc.message}
                </span>
                <span style={{
                  fontSize: '10px',
                  fontWeight: 700,
                  color: rc.status === 'PENALTY' ? '#EF4444' : (rc.status === 'INVESTIGATION' ? '#F59E0B' : '#64748B')
                }}>
                  {rc.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 4: Team Radio */}
      {activeTab === 'radio' && (
        <div className="live-table-card">
          <div className="table-header-row">
            <div className="th-title">
              <Volume2 size={15} />
              <span>TEAM RADIO TIMELINE & STRATEGIC CONTEXT</span>
            </div>
            <span className="th-badge">OPENF1 BROADCAST AUDIO CAPTURES</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', padding: '12px 0' }}>
            {teamRadio.map((r, idx) => (
              <div key={idx} style={{
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '6px',
                padding: '12px 16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 800, color: '#00F5D4', fontSize: '13px' }}>{r.driver_code} (#{r.driver_number})</span>
                    {r.lap && <span style={{ fontSize: '11px', color: '#64748B' }}>Lap {r.lap}</span>}
                    <span style={{ fontSize: '11px', color: '#64748B', fontFamily: 'JetBrains Mono' }}>{r.timestamp}</span>
                  </div>
                  <span style={{ fontSize: '10px', fontWeight: 700, color: '#10B981', background: 'rgba(16,185,129,0.1)', padding: '2px 6px', borderRadius: '3px' }}>
                    {r.confidence_level}
                  </span>
                </div>
                <div style={{ fontSize: '13px', color: '#F8FAFC', fontStyle: 'italic', padding: '4px 0' }}>
                  "{r.transcript}"
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px', borderTop: '1px dashed rgba(255,255,255,0.06)', paddingTop: '6px' }}>
                  <span style={{ color: '#F59E0B' }}>CONTEXT: {r.strategic_context}</span>
                  {r.audio_url && (
                    <a href={r.audio_url} target="_blank" rel="noreferrer" style={{ color: '#00F5D4', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Volume2 size={11} />
                      <span>LISTEN AUDIO</span>
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 5: FIA Regulations Dossier */}
      {activeTab === 'regulations' && (
        <div className="live-table-card">
          <div className="table-header-row">
            <div className="th-title">
              <BookOpen size={15} />
              <span>OFFICIAL FIA SPORTING & TECHNICAL REGULATIONS DOSSIER</span>
            </div>
            <span className="th-badge">BINDING REGULATORY AUTHORITY</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '14px', padding: '12px 0' }}>
            {regulations.map((reg) => (
              <div key={reg.regulation_id} style={{
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '6px',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '11px', fontWeight: 800, color: '#00F5D4' }}>{reg.article_reference}</span>
                  <span style={{ fontSize: '10px', color: '#64748B' }}>EFFECTIVE: {reg.effective_season}</span>
                </div>
                <h4 style={{ margin: 0, fontSize: '14px', color: '#F8FAFC', fontWeight: 700 }}>{reg.title}</h4>
                <p style={{ margin: 0, fontSize: '12px', color: '#CBD5E1', lineHeight: 1.4 }}>{reg.summary}</p>
                <div style={{ marginTop: 'auto', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', padding: '6px 10px', borderRadius: '4px' }}>
                  <span style={{ fontSize: '11px', color: '#FCA5A5', fontWeight: 600 }}>PENALTY: </span>
                  <span style={{ fontSize: '11px', color: '#CBD5E1' }}>{reg.penalty_guideline}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default LivePage;
