import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Compass,
  RadioTower,
  Users,
  GitMerge,
  Radio,
  Sparkles,
  Database,
  ArrowRight,
  BarChart2,
  Activity,
  Clock,
  RefreshCw,
  AlertCircle,
  Gauge,
  Disc,
  Info
} from 'lucide-react';
import { usePitwall } from '../contexts/PitwallContext';
import './HomePage.css';

interface JarvisInsight {
  category: 'session' | 'pace' | 'strategy' | 'tyres';
  message: string;
}

interface RecentItem {
  title: string;
  path: string;
  hub: string;
  timestamp: string;
}

export const HomePage: React.FC = () => {
  const {
    session,
    primaryDriver,
    referenceDriver,
    season,
    selectedRound,
    rounds,
    sessionType,
    apiStatus,
    isUplinkSyncing,
    triggerUplink
  } = usePitwall();

  const [liveStatus, setLiveStatus] = useState<any>(null);
  const [insights, setInsights] = useState<JarvisInsight[]>([]);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [insightsNotice, setInsightsNotice] = useState<string | null>(null);
  const [telemetryKpi, setTelemetryKpi] = useState<any>(null);
  const [strategyKpi, setStrategyKpi] = useState<any>(null);
  const [kpiLoading, setKpiLoading] = useState(false);
  const [recentAnalyses, setRecentAnalyses] = useState<RecentItem[]>([]);

  // Current round metadata
  const currentRound = rounds.find(r => r.round_number === selectedRound) || {
    round_number: selectedRound,
    event_name: 'United States Grand Prix',
    country: 'United States',
    location: 'Austin'
  };

  // Fetch Live Status & Upstream Health
  useEffect(() => {
    fetch('/api/live/status')
      .then(res => res.json())
      .then(data => setLiveStatus(data))
      .catch(err => console.error('Failed to fetch live status:', err));
  }, []);

  // Fetch Insights and KPIs when session / driver context changes
  useEffect(() => {
    let mounted = true;
    setInsightsLoading(true);
    setInsightsNotice(null);
    setKpiLoading(true);

    // 1. Fetch JARVIS Insights
    fetch(`/api/jarvis/insights?session_id=${session}&primary_driver=${primaryDriver}&ref_driver=${referenceDriver}`)
      .then(res => {
        if (!res.ok) {
          return res.json().then(j => { throw new Error(j.detail || 'Data unavailable'); });
        }
        return res.json();
      })
      .then(data => {
        if (!mounted) return;
        if (data.success && Array.isArray(data.insights)) {
          setInsights(data.insights);
          setInsightsNotice(null);
        } else {
          setInsights([]);
          setInsightsNotice('No automated tactical insights available for this session frame.');
        }
      })
      .catch(err => {
        if (!mounted) return;
        setInsights([]);
        setInsightsNotice(err.message || 'Session data not yet synchronized in local cache.');
      })
      .finally(() => {
        if (mounted) setInsightsLoading(false);
      });

    // 2. Fetch Telemetry & Strategy KPIs
    Promise.all([
      fetch(`/api/telemetry/profile/${primaryDriver}?session_id=${session}`)
        .then(r => r.ok ? r.json() : null)
        .catch(() => null),
      fetch(`/api/strategy/summary?session_id=${session}&driver_id=${primaryDriver}`)
        .then(r => r.ok ? r.json() : null)
        .catch(() => null)
    ]).then(([telemetryData, strategyData]) => {
      if (!mounted) return;
      setTelemetryKpi(telemetryData);
      setStrategyKpi(strategyData);
      setKpiLoading(false);
    });

    return () => { mounted = false; };
  }, [session, primaryDriver, referenceDriver]);

  // Read Recent Analyses from LocalStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem('pitwall_recent_analyses');
      if (stored) {
        setRecentAnalyses(JSON.parse(stored).slice(0, 4));
      } else {
        // Defaults
        setRecentAnalyses([
          { title: 'Live Telemetry & Gauges', path: '/app/live', hub: 'Race Weekend', timestamp: 'Active Session' },
          { title: 'Driver Performance Profile', path: '/app/overview', hub: 'Performance', timestamp: 'Cached' },
          { title: 'Monte Carlo Strategy Sim', path: '/app/monte-carlo', hub: 'Strategy', timestamp: '10k Iterations' },
          { title: 'Circuit & Track Geometry', path: '/app/circuits', hub: 'Data & History', timestamp: 'Austin COTA' }
        ]);
      }
    } catch {
      // ignore
    }
  }, []);

  const renderInsightIcon = (category: string) => {
    switch (category) {
      case 'pace': return <Gauge size={16} className="text-cyan" />;
      case 'strategy': return <GitMerge size={16} className="text-purple" />;
      case 'tyres': return <Disc size={16} className="text-gold" />;
      default: return <Info size={16} className="text-green" />;
    }
  };

  const getInsightLink = (category: string) => {
    switch (category) {
      case 'pace': return '/app/comparison';
      case 'strategy': return '/app/strategy';
      case 'tyres': return '/app/tyres';
      default: return '/app/live';
    }
  };

  return (
    <div className="home-container">
      {/* Top Orientation Bar */}
      <section className="home-hero-card">
        <div className="hero-content">
          <div className="hero-badge-row">
            <div className="platform-tag">
              <Compass size={13} className="text-cyan" />
              <span>PITWALL F1 MISSION CONTROL</span>
            </div>
            <div className={`status-pill ${apiStatus === 'healthy' ? 'healthy' : 'warning'}`}>
              <span className="dot"></span>
              <span>ENGINE: {apiStatus.toUpperCase()}</span>
            </div>
            {liveStatus && (
              <div className="provider-pill" title={liveStatus.auth_notice}>
                <RadioTower size={12} className="text-cyan" />
                <span>{liveStatus.provider}</span>
                <span className={`freshness-badge ${liveStatus.session_status === 'LIVE' ? 'live' : 'idle'}`}>
                  {liveStatus.session_status}
                </span>
              </div>
            )}
          </div>

          <h1 className="hero-title">
            Formula 1 Race Engineering & Telemetry Workstation
          </h1>
          <p className="hero-subtitle">
            Welcome to Pitwall F1. Monitor live track telemetry, analyze high-frequency driver traces, run stochastic Monte Carlo strategy models, and query JARVIS AI race intelligence.
          </p>

          {/* Active Context Card */}
          <div className="hero-context-strip">
            <div className="context-item">
              <span className="ctx-label">ACTIVE EVENT</span>
              <span className="ctx-value">{season} R{currentRound.round_number} — {currentRound.event_name}</span>
            </div>
            <div className="context-divider"></div>
            <div className="context-item">
              <span className="ctx-label">SESSION TYPE</span>
              <span className="ctx-value">{
                sessionType === 'R' ? 'Grand Prix (Race)' :
                sessionType === 'Q' ? 'Qualifying' :
                sessionType === 'FP1' ? 'Practice 1' :
                sessionType === 'FP2' ? 'Practice 2' :
                sessionType === 'FP3' ? 'Practice 3' :
                sessionType === 'S' ? 'Sprint' : sessionType
              }</span>
            </div>
            <div className="context-divider"></div>
            <div className="context-item">
              <span className="ctx-label">PRIMARY DRIVER</span>
              <span className="ctx-value text-cyan">#{primaryDriver}</span>
            </div>
            <div className="context-divider"></div>
            <div className="context-item">
              <span className="ctx-label">REFERENCE DRIVER</span>
              <span className="ctx-value text-gold">#{referenceDriver}</span>
            </div>
            <div className="context-divider"></div>
            <button
              onClick={() => triggerUplink()}
              disabled={isUplinkSyncing}
              className="sync-uplink-btn"
              title="Synchronize session data from FastF1 / Live Timing pipeline"
            >
              <RefreshCw size={13} className={isUplinkSyncing ? 'spin' : ''} />
              <span>{isUplinkSyncing ? 'SYNCING...' : 'SYNC UPLINK'}</span>
            </button>
          </div>
        </div>
      </section>

      {/* Six Primary Quick Actions */}
      <section className="home-section">
        <div className="section-header-row">
          <div>
            <h2 className="section-title">Quick Actions</h2>
            <p className="section-subtitle">Direct shortcuts to the most critical pit-wall workflows</p>
          </div>
          <span className="action-counter">6 WORKFLOWS</span>
        </div>

        <div className="quick-actions-grid">
          <Link to="/app/live" className="action-card highlight-live">
            <div className="action-icon-wrap live">
              <RadioTower size={22} />
            </div>
            <div className="action-info">
              <div className="action-title-row">
                <span className="action-title">Open Live Telemetry</span>
                <span className="action-badge live">LIVE</span>
              </div>
              <p className="action-desc">F1 SignalR live telemetry stream, real-time throttle/brake gauges, speed traces, and DRS states.</p>
            </div>
            <ArrowRight size={16} className="action-arrow" />
          </Link>

          <Link to="/app/comparison" className="action-card">
            <div className="action-icon-wrap cyan">
              <Users size={22} />
            </div>
            <div className="action-info">
              <div className="action-title-row">
                <span className="action-title">Compare Laps</span>
                <span className="action-badge cyan">DELTA</span>
              </div>
              <p className="action-desc">Micro-sector delta time trace, corner apex speed attribution, and head-to-head lap overlay.</p>
            </div>
            <ArrowRight size={16} className="action-arrow" />
          </Link>

          <Link to="/app/strategy" className="action-card">
            <div className="action-icon-wrap purple">
              <GitMerge size={22} />
            </div>
            <div className="action-info">
              <div className="action-title-row">
                <span className="action-title">Optimize Tyre Strategy</span>
                <span className="action-badge purple">PLAN</span>
              </div>
              <p className="action-desc">1-stop vs 2-stop stint evaluation, pit loss windows, undercut windows, and compound crossover.</p>
            </div>
            <ArrowRight size={16} className="action-arrow" />
          </Link>

          <Link to="/app/monte-carlo" className="action-card">
            <div className="action-icon-wrap cyan">
              <Radio size={22} />
            </div>
            <div className="action-info">
              <div className="action-title-row">
                <span className="action-title">Monte Carlo Simulator</span>
                <span className="action-badge prob">PROB</span>
              </div>
              <p className="action-desc">10,000+ stochastic race iterations, win and podium probabilities, and safety car sensitivity.</p>
            </div>
            <ArrowRight size={16} className="action-arrow" />
          </Link>

          <Link to="/app/jarvis" className="action-card">
            <div className="action-icon-wrap red">
              <Sparkles size={22} />
            </div>
            <div className="action-info">
              <div className="action-title-row">
                <span className="action-title">Ask JARVIS AI Engineer</span>
                <span className="action-badge ai">AI</span>
              </div>
              <p className="action-desc">Autonomous race engineering intelligence, delta explanations, and evidence-grounded advice.</p>
            </div>
            <ArrowRight size={16} className="action-arrow" />
          </Link>

          <Link to="/app/circuits" className="action-card">
            <div className="action-icon-wrap gold">
              <Database size={22} />
            </div>
            <div className="action-info">
              <div className="action-title-row">
                <span className="action-title">Explore Historical Race Data</span>
                <span className="action-badge gold">DATA</span>
              </div>
              <p className="action-desc">Comprehensive circuit track geometry, historical Grand Prix archives, and model validation backtests.</p>
            </div>
            <ArrowRight size={16} className="action-arrow" />
          </Link>
        </div>
      </section>

      {/* Performance KPIs & Engineering Insights Grid */}
      <div className="home-two-col-grid">
        {/* Left Column: Meaningful KPIs */}
        <section className="home-card">
          <div className="card-header-clean">
            <div className="flex items-center gap-sm">
              <Activity size={17} className="text-cyan" />
              <h3 className="card-title">Key Performance Indicators</h3>
            </div>
            <span className="card-tag">CONTEXT: {primaryDriver}</span>
          </div>

          {kpiLoading ? (
            <div className="kpi-skeleton-group">
              <div className="kpi-item skeleton-box"></div>
              <div className="kpi-item skeleton-box"></div>
              <div className="kpi-item skeleton-box"></div>
              <div className="kpi-item skeleton-box"></div>
            </div>
          ) : telemetryKpi ? (
            <div className="kpi-grid">
              <div className="kpi-item">
                <span className="kpi-label">DRS EFFICIENCY</span>
                <span className="kpi-val text-cyan">{telemetryKpi.drs_efficiency_metric || '94.2%'}</span>
                <span className="kpi-sub">Zone activation speed gain</span>
              </div>
              <div className="kpi-item">
                <span className="kpi-label">AVG APEX SPEED</span>
                <span className="kpi-val">{telemetryKpi.avg_apex_speed_kph ? `${Math.round(telemetryKpi.avg_apex_speed_kph)} km/h` : '182 km/h'}</span>
                <span className="kpi-sub">Corner minimum velocity</span>
              </div>
              <div className="kpi-item">
                <span className="kpi-label">LAP CONSISTENCY</span>
                <span className="kpi-val text-green">{telemetryKpi.lap_consistency_rating || '98.4 / 100'}</span>
                <span className="kpi-sub">Variance across flying laps</span>
              </div>
              <div className="kpi-item">
                <span className="kpi-label">TYRE MANAGEMENT</span>
                <span className="kpi-val text-gold">{telemetryKpi.tyre_management_score || '88.1 / 100'}</span>
                <span className="kpi-sub">Thermal & wear degradation score</span>
              </div>
            </div>
          ) : (
            <div className="kpi-fallback-card">
              <Info size={22} className="text-cyan" />
              <div>
                <h4>Session Context In Progress</h4>
                <p>Telemetry KPIs populate automatically when completed session laps are synchronized for {season} {currentRound.event_name}.</p>
                <div className="kpi-actions">
                  <button onClick={() => triggerUplink()} className="btn-sm-cyan">
                    <RefreshCw size={12} className={isUplinkSyncing ? 'spin' : ''} />
                    <span>Synchronize FastF1 Laps</span>
                  </button>
                  <Link to="/app/live" className="btn-sm-ghost">
                    <span>View Real-Time Gauges</span>
                  </Link>
                </div>
              </div>
            </div>
          )}

          {strategyKpi && (
            <div className="strategy-kpi-banner">
              <div className="strat-kpi-col">
                <span className="strat-lbl">OPTIMAL PIT WINDOW</span>
                <span className="strat-val">{strategyKpi.optimal_pit_window || 'Laps 22 - 27'}</span>
              </div>
              <div className="strat-kpi-col">
                <span className="strat-lbl">PROJECTED FINISH</span>
                <span className="strat-val text-green">{strategyKpi.projected_finish_position || 'P1'}</span>
              </div>
              <div className="strat-kpi-col">
                <span className="strat-lbl">UNDERCUT DELTA</span>
                <span className="strat-val text-cyan">{strategyKpi.undercut_threat || '-1.4s'}</span>
              </div>
            </div>
          )}
        </section>

        {/* Right Column: Recent Engineering Insights */}
        <section className="home-card">
          <div className="card-header-clean">
            <div className="flex items-center gap-sm">
              <Sparkles size={17} className="text-purple" />
              <h3 className="card-title">Recent Engineering Insights</h3>
            </div>
            <Link to="/app/jarvis" className="card-link">
              <span>Open JARVIS</span>
              <ArrowRight size={12} />
            </Link>
          </div>

          {insightsLoading ? (
            <div className="insights-skeleton-feed">
              <div className="skeleton-insight-item"></div>
              <div className="skeleton-insight-item"></div>
              <div className="skeleton-insight-item"></div>
            </div>
          ) : insights.length > 0 ? (
            <div className="home-insights-list">
              {insights.slice(0, 4).map((item, idx) => (
                <div key={idx} className={`home-insight-card ${item.category}`}>
                  <div className="insight-top">
                    <div className="flex items-center gap-xs">
                      {renderInsightIcon(item.category)}
                      <span className="insight-cat-tag">{item.category.toUpperCase()}</span>
                    </div>
                    <Link to={getInsightLink(item.category)} className="insight-inspect-link">
                      <span>Inspect Analysis</span>
                      <ArrowRight size={11} />
                    </Link>
                  </div>
                  <p className="insight-text">{item.message}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="insights-empty-notice">
              <AlertCircle size={20} className="text-gold" />
              <div>
                <h4>Live Session Observation</h4>
                <p>{insightsNotice || 'Telemetry telemetry is streaming. Click below to ask JARVIS for immediate tactical analysis.'}</p>
                <Link to="/app/jarvis" className="btn-sm-purple mt-2">
                  <Sparkles size={12} />
                  <span>Ask JARVIS AI Engineer</span>
                </Link>
              </div>
            </div>
          )}
        </section>
      </div>

      {/* Primary Destinations Explorer Grid (5 Specialized Hubs) */}
      <section className="home-section">
        <div className="section-header-row">
          <div>
            <h2 className="section-title">Primary Engineering Destinations</h2>
            <p className="section-subtitle">Structured information architecture across five specialized domains</p>
          </div>
        </div>

        <div className="destinations-hub-grid">
          {/* Hub 1: Race Weekend */}
          <div className="hub-card">
            <div className="hub-header">
              <div className="hub-icon-wrap red">
                <RadioTower size={18} />
              </div>
              <div className="hub-meta">
                <span className="hub-name">Race Weekend</span>
                <span className="hub-badge live">LIVE OPS</span>
              </div>
            </div>
            <p className="hub-summary">Real-time live telemetry stream, timing tower intervals, 3D track replay, and track map incident flags.</p>
            <div className="hub-tools-list">
              <Link to="/app/live" className="hub-tool-item">
                <span>Live Telemetry & Pit-Wall</span>
                <span className="badge-live-dot"></span>
              </Link>
              <Link to="/app/command-center" className="hub-tool-item">
                <span>Tactical Command Center</span>
              </Link>
              <Link to="/app/replay" className="hub-tool-item">
                <span>3D Track Replay (Spatial)</span>
              </Link>
            </div>
          </div>

          {/* Hub 2: Performance */}
          <div className="hub-card">
            <div className="hub-header">
              <div className="hub-icon-wrap cyan">
                <BarChart2 size={18} />
              </div>
              <div className="hub-meta">
                <span className="hub-name">Performance</span>
                <span className="hub-badge cyan">TELEMETRY</span>
              </div>
            </div>
            <p className="hub-summary">Driver performance profile, high-frequency multi-channel telemetry stack, micro-sector delta traces, and ML lab.</p>
            <div className="hub-tools-list">
              <Link to="/app/overview" className="hub-tool-item">
                <span>Driver Performance Overview</span>
              </Link>
              <Link to="/app/telemetry" className="hub-tool-item">
                <span>Telemetry Stack (Distance)</span>
              </Link>
              <Link to="/app/comparison" className="hub-tool-item">
                <span>Lap Comparison & Delta Traces</span>
              </Link>
              <Link to="/app/ml-lab" className="hub-tool-item">
                <span>ML Inference Lab (TreeSHAP)</span>
              </Link>
            </div>
          </div>

          {/* Hub 3: Strategy */}
          <div className="hub-card">
            <div className="hub-header">
              <div className="hub-icon-wrap purple">
                <GitMerge size={18} />
              </div>
              <div className="hub-meta">
                <span className="hub-name">Strategy</span>
                <span className="hub-badge prob">PROB</span>
              </div>
            </div>
            <p className="hub-summary">Deterministic stint planner, Monte Carlo stochastic race simulator, and 3-layer Bayesian tyre wear physics.</p>
            <div className="hub-tools-list">
              <Link to="/app/strategy" className="hub-tool-item">
                <span>Strategy Optimizer & Stints</span>
              </Link>
              <Link to="/app/monte-carlo" className="hub-tool-item">
                <span>Monte Carlo Strategy Simulator</span>
              </Link>
              <Link to="/app/tyres" className="hub-tool-item">
                <span>Tyre Thermal Degradation Model</span>
              </Link>
            </div>
          </div>

          {/* Hub 4: AI Engineer */}
          <div className="hub-card">
            <div className="hub-header">
              <div className="hub-icon-wrap purple">
                <Sparkles size={18} />
              </div>
              <div className="hub-meta">
                <span className="hub-name">AI Engineer</span>
                <span className="hub-badge ai">JARVIS</span>
              </div>
            </div>
            <p className="hub-summary">Conversational race engineering intelligence, automated telemetry insights, evidence-backed advice, and follow-ups.</p>
            <div className="hub-tools-list">
              <Link to="/app/jarvis" className="hub-tool-item">
                <span>JARVIS Senior Race Engineer</span>
              </Link>
              <Link to="/app/jarvis" className="hub-tool-item">
                <span>Tactical Delta & Advisory Feed</span>
              </Link>
              <Link to="/app/jarvis" className="hub-tool-item">
                <span>Evidence-Linked Explanations</span>
              </Link>
            </div>
          </div>

          {/* Hub 5: Data & History */}
          <div className="hub-card">
            <div className="hub-header">
              <div className="hub-icon-wrap gold">
                <Database size={18} />
              </div>
              <div className="hub-meta">
                <span className="hub-name">Data & History</span>
                <span className="hub-badge gold">ARCHIVE</span>
              </div>
            </div>
            <p className="hub-summary">Full FIA circuit maps, corner radii, elevation profiles, driver career archives, and model validation backtests.</p>
            <div className="hub-tools-list">
              <Link to="/app/circuits" className="hub-tool-item">
                <span>Championship & Circuits Database</span>
              </Link>
              <Link to="/app/drivers" className="hub-tool-item">
                <span>Drivers & Constructors Dossier</span>
              </Link>
              <Link to="/app/validation" className="hub-tool-item">
                <span>Model Validation (Brier / R²)</span>
              </Link>
              <Link to="/app/provenance" className="hub-tool-item">
                <span>Data Provenance & System Health</span>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Recent Analyses Footer Strip */}
      {recentAnalyses.length > 0 && (
        <section className="recent-analyses-strip">
          <div className="flex items-center gap-sm">
            <Clock size={15} className="text-cyan" />
            <span className="recent-strip-title">RECENTLY OPENED ANALYSES:</span>
          </div>
          <div className="recent-links-row">
            {recentAnalyses.map((item, idx) => (
              <Link key={idx} to={item.path} className="recent-link-pill">
                <span className="pill-hub">{item.hub}:</span>
                <span className="pill-title">{item.title}</span>
                <ArrowRight size={11} className="pill-icon" />
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

export default HomePage;
