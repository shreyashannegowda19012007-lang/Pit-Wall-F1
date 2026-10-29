import React, { useState, useEffect } from 'react';
import { usePitwall } from '../contexts/PitwallContext';
import {
  Flag,
  MapPin,
  Calendar,
  Zap,
  ArrowRight,
  CheckCircle2,
  RefreshCw,
  Search,
  BookOpen,
  Users,
  Scale
} from 'lucide-react';
import './CircuitsPage.css';

interface Circuit {
  round: number;
  country: string;
  location: string;
  event_name: string;
  event_date: string;
  format: string;
}

interface RegulationEra {
  era_id: string;
  era_name: string;
  season_range: string;
  engine_architecture: string;
  displacement_litres: number;
  max_rpm: number;
  hybrid_system: string;
  aerodynamic_concept: string;
  minimum_weight_kg: number;
  tyre_specification: string;
  overtaking_delta_characteristics: string;
  fuel_regulation: string;
}

interface TeammateH2H {
  team_name: string;
  season: number;
  driver_1_code: string;
  driver_2_code: string;
  qualifying_head_to_head: string;
  race_head_to_head: string;
  points_driver_1: number;
  points_driver_2: number;
  podiums_driver_1: number;
  podiums_driver_2: number;
  wins_driver_1: number;
  wins_driver_2: number;
  avg_quali_delta_s: number;
}

interface ChampionshipWhatIf {
  driver_code: string;
  team_name: string;
  current_points: number;
  projected_points_finish_p1: number;
  projected_points_finish_p2: number;
  projected_points_finish_p3: number;
  mathematical_title_clinch_possible: boolean;
  points_needed_to_clinch: number;
}

export const CircuitsPage: React.FC = () => {
  const { season, setSeason, availableSeasons, triggerUplink, session } = usePitwall();
  const [activeTab, setActiveTab] = useState<'calendar' | 'eras' | 'h2h' | 'whatif'>('calendar');

  const [circuits, setCircuits] = useState<Circuit[]>([]);
  const [eras, setEras] = useState<RegulationEra[]>([]);
  const [h2hRecords, setH2hRecords] = useState<TeammateH2H[]>([]);
  const [whatIfs, setWhatIfs] = useState<ChampionshipWhatIf[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSessions, setSelectedSessions] = useState<{ [round: number]: string }>({});
  const [loadingRound, setLoadingRound] = useState<number | null>(null);

  useEffect(() => {
    const fetchCalendar = async () => {
      setLoading(true);
      setError(null);
      try {
        const [circRes, erasRes, h2hRes, whatIfRes] = await Promise.all([
          fetch(`/api/circuits?year=${season}`).then(r => r.json()).catch(() => ({ circuits: [] })),
          fetch('/api/historical/eras').then(r => r.json()).catch(() => ({ eras: [] })),
          fetch(`/api/historical/teammate-h2h?season=${season}`).then(r => r.json()).catch(() => ({ head_to_head: [] })),
          fetch(`/api/historical/championship-what-if?session_id=${session}`).then(r => r.json()).catch(() => ({ what_if: [] }))
        ]);

        if (circRes.circuits) setCircuits(circRes.circuits);
        if (erasRes.eras) setEras(erasRes.eras);
        if (h2hRes.head_to_head) setH2hRecords(h2hRes.head_to_head);
        if (whatIfRes.what_if) setWhatIfs(whatIfRes.what_if);
      } catch (err: any) {
        setError(err.message || 'Network error fetching championship calendar.');
      } finally {
        setLoading(false);
      }
    };

    fetchCalendar();
  }, [season, session]);

  const formatDate = (dateStr: string) => {
    if (!dateStr) return 'TBD';
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return dateStr;
      return d.toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  const handleLoadSession = async (roundNum: number) => {
    setLoadingRound(roundNum);
    const sType = selectedSessions[roundNum] || 'R';
    await triggerUplink(roundNum, sType);
    setLoadingRound(null);
  };

  const filteredCircuits = circuits.filter(c =>
    c.event_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.country.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
    String(c.round).includes(searchQuery)
  );

  return (
    <div className="circuits-container">
      {/* Page Header */}
      <header className="circuits-header">
        <div className="header-titles">
          <div className="title-row">
            <Flag size={20} className="header-icon text-red" />
            <h2>Championship Intelligence & Historical Eras</h2>
            <span className="session-tag">{season} SEASON</span>
          </div>
          <p className="subtitle">
            Official FIA calendar, technical regulation era comparisons, teammate head-to-head records, and championship what-if permutations.
          </p>
        </div>

        {/* Sub-Tabs Navigation */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button
            onClick={() => setActiveTab('calendar')}
            style={{
              background: activeTab === 'calendar' ? 'rgba(0, 245, 212, 0.15)' : 'rgba(255,255,255,0.03)',
              color: activeTab === 'calendar' ? '#00F5D4' : '#94A3B8',
              border: activeTab === 'calendar' ? '1px solid #00F5D4' : '1px solid rgba(255,255,255,0.08)',
              padding: '6px 12px',
              borderRadius: '4px',
              fontSize: '11px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '5px'
            }}
          >
            <Calendar size={12} />
            <span>CALENDAR & UPLINK</span>
          </button>

          <button
            onClick={() => setActiveTab('eras')}
            style={{
              background: activeTab === 'eras' ? 'rgba(0, 245, 212, 0.15)' : 'rgba(255,255,255,0.03)',
              color: activeTab === 'eras' ? '#00F5D4' : '#94A3B8',
              border: activeTab === 'eras' ? '1px solid #00F5D4' : '1px solid rgba(255,255,255,0.08)',
              padding: '6px 12px',
              borderRadius: '4px',
              fontSize: '11px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '5px'
            }}
          >
            <BookOpen size={12} />
            <span>REGULATION ERAS</span>
          </button>

          <button
            onClick={() => setActiveTab('h2h')}
            style={{
              background: activeTab === 'h2h' ? 'rgba(0, 245, 212, 0.15)' : 'rgba(255,255,255,0.03)',
              color: activeTab === 'h2h' ? '#00F5D4' : '#94A3B8',
              border: activeTab === 'h2h' ? '1px solid #00F5D4' : '1px solid rgba(255,255,255,0.08)',
              padding: '6px 12px',
              borderRadius: '4px',
              fontSize: '11px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '5px'
            }}
          >
            <Users size={12} />
            <span>TEAMMATE H2H</span>
          </button>

          <button
            onClick={() => setActiveTab('whatif')}
            style={{
              background: activeTab === 'whatif' ? 'rgba(0, 245, 212, 0.15)' : 'rgba(255,255,255,0.03)',
              color: activeTab === 'whatif' ? '#00F5D4' : '#94A3B8',
              border: activeTab === 'whatif' ? '1px solid #00F5D4' : '1px solid rgba(255,255,255,0.08)',
              padding: '6px 12px',
              borderRadius: '4px',
              fontSize: '11px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '5px'
            }}
          >
            <Scale size={12} />
            <span>CHAMPIONSHIP WHAT-IF</span>
          </button>
        </div>
      </header>

      {/* Tab 1: Calendar Grid */}
      {activeTab === 'calendar' && (
        <>
          <div className="circuits-controls" style={{ marginBottom: '16px' }}>
            <div className="search-box">
              <Search size={14} className="search-icon" />
              <input
                type="text"
                placeholder="Search Grand Prix or circuit..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
            </div>

            <div className="season-filter-group">
              <label className="filter-label">SEASON:</label>
              <select
                value={season}
                onChange={(e) => setSeason(Number(e.target.value))}
                className="season-select"
              >
                {availableSeasons.map((yr) => (
                  <option key={yr} value={yr}>{yr} FIA F1</option>
                ))}
              </select>
            </div>
          </div>

          <div className="circuits-content">
            {error && (
              <div className="error-banner" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', padding: '12px', borderRadius: '6px', color: '#EF4444', marginBottom: '16px' }}>
                <span>{error}</span>
              </div>
            )}
            {loading && (
              <div className="circuits-grid">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="circuit-card-skeleton">
                    <div className="skeleton-line skeleton" style={{ width: '40%', height: '18px' }}></div>
                    <div className="skeleton-line skeleton" style={{ width: '80%', height: '22px' }}></div>
                  </div>
                ))}
              </div>
            )}

            {!loading && filteredCircuits.length > 0 && (
              <div className="circuits-grid">
                {filteredCircuits.map(c => {
                  const isSelectedSessionActive = session.includes(c.event_name.toUpperCase().replace(/\s+/g, '_'));
                  const chosenType = selectedSessions[c.round] || 'R';
                  const isLoadingThis = loadingRound === c.round;

                  return (
                    <div key={c.round} className={`circuit-card ${isSelectedSessionActive ? 'active-event' : ''}`}>
                      <div className="round-watermark">
                        R{String(c.round).padStart(2, '0')}
                      </div>

                      <div className="card-top">
                        <span className="round-badge">ROUND {String(c.round).padStart(2, '0')}</span>
                        {c.format === 'sprint' && (
                          <span className="sprint-badge">
                            <Zap size={10} /> SPRINT
                          </span>
                        )}
                        {isSelectedSessionActive && (
                          <span className="active-uplink-badge">
                            <CheckCircle2 size={11} /> UPLINK ACTIVE
                          </span>
                        )}
                      </div>

                      <h3 className="event-name" title={c.event_name}>{c.event_name}</h3>

                      <div className="event-meta">
                        <div className="meta-item">
                          <MapPin size={13} className="meta-icon" />
                          <span>{c.location}, {c.country}</span>
                        </div>

                        <div className="meta-item">
                          <Calendar size={13} className="meta-icon" />
                          <span>{formatDate(c.event_date)}</span>
                        </div>
                      </div>

                      <div className="card-footer">
                        <select
                          value={chosenType}
                          onChange={(e) => setSelectedSessions({ ...selectedSessions, [c.round]: e.target.value })}
                          className="session-type-select"
                        >
                          <option value="R">Race (R)</option>
                          <option value="Q">Qualifying (Q)</option>
                          <option value="FP1">Practice 1</option>
                          <option value="FP2">Practice 2</option>
                          <option value="FP3">Practice 3</option>
                          {c.format === 'sprint' && <option value="S">Sprint</option>}
                        </select>

                        <button
                          onClick={() => handleLoadSession(c.round)}
                          disabled={isLoadingThis}
                          className="btn-load-session"
                        >
                          {isLoadingThis ? (
                            <>
                              <RefreshCw size={12} className="spin" />
                              <span>SYNCING...</span>
                            </>
                          ) : (
                            <>
                              <span>LOAD UPLINK</span>
                              <ArrowRight size={12} />
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </>
      )}

      {/* Tab 2: Regulation Eras */}
      {activeTab === 'eras' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '16px' }}>
          {eras.map((era) => (
            <div key={era.era_id} style={{
              background: '#0B0E14',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '8px',
              padding: '18px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '11px', fontWeight: 800, color: '#00F5D4', background: 'rgba(0, 245, 212, 0.1)', padding: '2px 8px', borderRadius: '4px' }}>
                  {era.season_range}
                </span>
                <span style={{ fontSize: '11px', color: '#64748B' }}>Min Weight: {era.minimum_weight_kg} kg</span>
              </div>

              <h3 style={{ margin: 0, fontSize: '15px', color: '#F8FAFC', fontWeight: 700 }}>{era.era_name}</h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '11px', fontFamily: 'JetBrains Mono', background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '4px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748B' }}>Engine:</span>
                  <span style={{ color: '#F8FAFC' }}>{era.engine_architecture} ({era.max_rpm} RPM)</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748B' }}>Hybrid ERS:</span>
                  <span style={{ color: '#10B981' }}>{era.hybrid_system}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748B' }}>Tyres:</span>
                  <span style={{ color: '#CBD5E1' }}>{era.tyre_specification}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748B' }}>Fuel:</span>
                  <span style={{ color: '#CBD5E1' }}>{era.fuel_regulation}</span>
                </div>
              </div>

              <div style={{ fontSize: '12px', color: '#CBD5E1', lineHeight: 1.4 }}>
                <strong style={{ color: '#94A3B8' }}>Aero Concept: </strong>{era.aerodynamic_concept}
              </div>

              <div style={{ marginTop: 'auto', background: 'rgba(0,245,212,0.05)', border: '1px solid rgba(0,245,212,0.15)', padding: '8px 10px', borderRadius: '4px' }}>
                <span style={{ fontSize: '11px', color: '#00F5D4', fontWeight: 700 }}>OVERTAKING DELTA: </span>
                <span style={{ fontSize: '11px', color: '#CBD5E1' }}>{era.overtaking_delta_characteristics}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 3: Teammate Head-to-Head */}
      {activeTab === 'h2h' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '16px' }}>
          {h2hRecords.map((rec, idx) => (
            <div key={idx} style={{
              background: '#0B0E14',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '8px',
              padding: '18px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '14px', fontWeight: 800, color: '#F8FAFC' }}>{rec.team_name}</span>
                <span style={{ fontSize: '11px', color: '#64748B' }}>{rec.season} Season</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', textAlign: 'center' }}>
                <div style={{ background: 'rgba(0, 245, 212, 0.08)', border: '1px solid rgba(0, 245, 212, 0.25)', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '18px', fontWeight: 800, color: '#00F5D4' }}>{rec.driver_1_code}</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#FFFFFF', margin: '4px 0' }}>{rec.points_driver_1} PTS</div>
                  <div style={{ fontSize: '11px', color: '#94A3B8' }}>{rec.wins_driver_1} Wins | {rec.podiums_driver_1} Podiums</div>
                </div>

                <div style={{ background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.25)', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '18px', fontWeight: 800, color: '#F59E0B' }}>{rec.driver_2_code}</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#FFFFFF', margin: '4px 0' }}>{rec.points_driver_2} PTS</div>
                  <div style={{ fontSize: '11px', color: '#94A3B8' }}>{rec.wins_driver_2} Wins | {rec.podiums_driver_2} Podiums</div>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px', fontFamily: 'JetBrains Mono', background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '4px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748B' }}>Qualifying H2H:</span>
                  <span style={{ color: '#F8FAFC', fontWeight: 700 }}>{rec.qualifying_head_to_head}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748B' }}>Race H2H:</span>
                  <span style={{ color: '#F8FAFC', fontWeight: 700 }}>{rec.race_head_to_head}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748B' }}>Avg Quali Delta:</span>
                  <span style={{ color: rec.avg_quali_delta_s < 0 ? '#00F5D4' : '#F59E0B', fontWeight: 700 }}>
                    {rec.avg_quali_delta_s.toFixed(3)}s
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 4: Championship What-If */}
      {activeTab === 'whatif' && (
        <div style={{ background: '#0B0E14', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px', padding: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <Scale size={16} className="text-cyan" />
            <h3 style={{ margin: 0, fontSize: '14px', color: '#F8FAFC' }}>Championship Title Permutations & What-If Points Calculator</h3>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', fontFamily: 'JetBrains Mono' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)', color: '#64748B', textAlign: 'left' }}>
                  <th style={{ padding: '8px 12px' }}>DRIVER</th>
                  <th style={{ padding: '8px 12px' }}>CONSTRUCTOR</th>
                  <th style={{ padding: '8px 12px' }}>CURRENT PTS</th>
                  <th style={{ padding: '8px 12px' }}>IF FINISH P1 (+25)</th>
                  <th style={{ padding: '8px 12px' }}>IF FINISH P2 (+18)</th>
                  <th style={{ padding: '8px 12px' }}>IF FINISH P3 (+15)</th>
                  <th style={{ padding: '8px 12px' }}>POINTS TO CLINCH</th>
                  <th style={{ padding: '8px 12px' }}>MATHEMATICAL CLINCH</th>
                </tr>
              </thead>
              <tbody>
                {whatIfs.map((row) => (
                  <tr key={row.driver_code} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '10px 12px', fontWeight: 700, color: '#00F5D4' }}>{row.driver_code}</td>
                    <td style={{ padding: '10px 12px', color: '#CBD5E1' }}>{row.team_name}</td>
                    <td style={{ padding: '10px 12px', fontWeight: 800, color: '#FFFFFF' }}>{row.current_points}</td>
                    <td style={{ padding: '10px 12px', color: '#10B981', fontWeight: 700 }}>{row.projected_points_finish_p1}</td>
                    <td style={{ padding: '10px 12px', color: '#38BDF8' }}>{row.projected_points_finish_p2}</td>
                    <td style={{ padding: '10px 12px', color: '#F59E0B' }}>{row.projected_points_finish_p3}</td>
                    <td style={{ padding: '10px 12px', color: '#94A3B8' }}>{row.points_needed_to_clinch > 0 ? `${row.points_needed_to_clinch} PTS` : 'LEADER'}</td>
                    <td style={{ padding: '10px 12px' }}>
                      <span style={{
                        fontSize: '10px',
                        fontWeight: 700,
                        padding: '2px 6px',
                        borderRadius: '3px',
                        background: row.mathematical_title_clinch_possible ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.05)',
                        color: row.mathematical_title_clinch_possible ? '#10B981' : '#64748B'
                      }}>
                        {row.mathematical_title_clinch_possible ? 'CLINCH POSSIBLE' : 'NOT IN THIS ROUND'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default CircuitsPage;
