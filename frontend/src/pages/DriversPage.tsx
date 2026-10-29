import React, { useState, useEffect } from 'react';
import { usePitwall } from '../contexts/PitwallContext';
import { Users, Award, Search, Check, Crosshair, Trophy, Shield, RefreshCw } from 'lucide-react';
import './DriversPage.css';

interface DriverInfo {
  driver_number: string;
  broadcast_name: string;
  abbreviation: string;
  team_name: string;
  team_color: string;
  headshot_url?: string;
  position: number;
  points: number;
}

interface DriversResponse {
  success: boolean;
  session_id: string;
  drivers: DriverInfo[];
}

export const DriversPage: React.FC = () => {
  const { session, season, primaryDriver, setPrimaryDriver, referenceDriver, setReferenceDriver } = usePitwall();
  const [activeTab, setActiveTab] = useState<'lineup' | 'drivers_champ' | 'constructors_champ'>('lineup');
  const [drivers, setDrivers] = useState<DriverInfo[]>([]);
  const [driverStandings, setDriverStandings] = useState<any[]>([]);
  const [constructorStandings, setConstructorStandings] = useState<any[]>([]);
  const [standingsLoading, setStandingsLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [failedImages, setFailedImages] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const fetchDrivers = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`/api/drivers?session_id=${session}`);
        const data: DriversResponse = await res.json();
        if (data.success && Array.isArray(data.drivers)) {
          setDrivers(data.drivers);
        } else {
          setError('No official driver classification records found for this session.');
        }
      } catch (err: any) {
        setError(err.message || 'Failed to connect to backend telemetry service.');
      } finally {
        setLoading(false);
      }
    };

    fetchDrivers();
  }, [session]);

  useEffect(() => {
    if (activeTab === 'drivers_champ' && driverStandings.length === 0) {
      setStandingsLoading(true);
      fetch(`/api/standings/drivers?year=${season}`)
        .then(r => r.json())
        .then(data => {
          if (data.success && Array.isArray(data.standings)) {
            setDriverStandings(data.standings);
          }
        })
        .catch(console.error)
        .finally(() => setStandingsLoading(false));
    } else if (activeTab === 'constructors_champ' && constructorStandings.length === 0) {
      setStandingsLoading(true);
      fetch(`/api/standings/constructors?year=${season}`)
        .then(r => r.json())
        .then(data => {
          if (data.success && Array.isArray(data.standings)) {
            setConstructorStandings(data.standings);
          }
        })
        .catch(console.error)
        .finally(() => setStandingsLoading(false));
    }
  }, [activeTab, season, driverStandings.length, constructorStandings.length]);

  const handleImageError = (abbr: string) => {
    setFailedImages(prev => ({ ...prev, [abbr]: true }));
  };

  const filteredDrivers = drivers.filter(d =>
    d.broadcast_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    d.abbreviation.toLowerCase().includes(searchQuery.toLowerCase()) ||
    d.team_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    d.driver_number.includes(searchQuery)
  );

  return (
    <div className="drivers-container">
      {/* Page Header */}
      <header className="drivers-header">
        <div className="header-titles">
          <div className="title-row">
            <Users size={20} className="header-icon text-red" />
            <h2>Driver & Team Lineup</h2>
            <span className="session-tag">{session}</span>
          </div>
          <p className="subtitle">
            Driver grid classification, telemetry context management, and FIA World Championship Standings.
          </p>
        </div>

        {/* Search Bar & Tab Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div className="search-box">
            <Search size={14} className="search-icon" />
            <input
              type="text"
              placeholder="Search driver or team..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </div>
        </div>
      </header>

      {/* Tab Switcher */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-default)', paddingBottom: '8px' }}>
        <button
          onClick={() => setActiveTab('lineup')}
          style={{
            background: activeTab === 'lineup' ? 'rgba(0, 240, 255, 0.15)' : 'transparent',
            border: activeTab === 'lineup' ? '1px solid var(--f1-cyan)' : '1px solid var(--border-default)',
            color: activeTab === 'lineup' ? 'var(--f1-cyan)' : 'var(--text-muted)',
            padding: '6px 14px',
            borderRadius: '4px',
            fontSize: '11px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <Users size={13} />
          SESSION GRID LINEUP
        </button>
        <button
          onClick={() => setActiveTab('drivers_champ')}
          style={{
            background: activeTab === 'drivers_champ' ? 'rgba(0, 240, 255, 0.15)' : 'transparent',
            border: activeTab === 'drivers_champ' ? '1px solid var(--f1-cyan)' : '1px solid var(--border-default)',
            color: activeTab === 'drivers_champ' ? 'var(--f1-cyan)' : 'var(--text-muted)',
            padding: '6px 14px',
            borderRadius: '4px',
            fontSize: '11px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <Trophy size={13} />
          DRIVERS CHAMPIONSHIP ({season})
        </button>
        <button
          onClick={() => setActiveTab('constructors_champ')}
          style={{
            background: activeTab === 'constructors_champ' ? 'rgba(0, 240, 255, 0.15)' : 'transparent',
            border: activeTab === 'constructors_champ' ? '1px solid var(--f1-cyan)' : '1px solid var(--border-default)',
            color: activeTab === 'constructors_champ' ? 'var(--f1-cyan)' : 'var(--text-muted)',
            padding: '6px 14px',
            borderRadius: '4px',
            fontSize: '11px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <Shield size={13} />
          CONSTRUCTORS CHAMPIONSHIP ({season})
        </button>
      </div>

      {/* Standings View: Drivers */}
      {activeTab === 'drivers_champ' && (
        <div className="card-engineering" style={{ padding: '16px' }}>
          {standingsLoading ? (
            <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
              <RefreshCw size={18} className="spin" style={{ marginBottom: '8px' }} />
              <p>Fetching official FIA Driver Standings from Ergast API...</p>
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-default)', color: 'var(--text-muted)', textAlign: 'left' }}>
                  <th style={{ padding: '8px' }}>POS</th>
                  <th style={{ padding: '8px' }}>DRIVER</th>
                  <th style={{ padding: '8px' }}>NO</th>
                  <th style={{ padding: '8px' }}>TEAM</th>
                  <th style={{ padding: '8px' }}>NAT</th>
                  <th style={{ padding: '8px' }}>WINS</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>POINTS</th>
                </tr>
              </thead>
              <tbody>
                {driverStandings.map((s: any) => (
                  <tr key={s.driver_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '8px', fontWeight: 700, color: s.position <= 3 ? 'var(--f1-gold)' : 'var(--text-primary)' }}>
                      P{s.position}
                    </td>
                    <td style={{ padding: '8px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {s.driver_name} <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>({s.driver_code})</span>
                    </td>
                    <td style={{ padding: '8px', color: 'var(--text-muted)' }}>#{s.permanent_number || '-'}</td>
                    <td style={{ padding: '8px', color: 'var(--f1-cyan)' }}>{s.team_name}</td>
                    <td style={{ padding: '8px', color: 'var(--text-muted)' }}>{s.nationality}</td>
                    <td style={{ padding: '8px' }}>{s.wins}</td>
                    <td style={{ padding: '8px', textAlign: 'right', fontWeight: 700, color: 'var(--f1-gold)' }}>
                      {s.points} PTS
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Standings View: Constructors */}
      {activeTab === 'constructors_champ' && (
        <div className="card-engineering" style={{ padding: '16px' }}>
          {standingsLoading ? (
            <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
              <RefreshCw size={18} className="spin" style={{ marginBottom: '8px' }} />
              <p>Fetching official FIA Constructor Standings from Ergast API...</p>
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-default)', color: 'var(--text-muted)', textAlign: 'left' }}>
                  <th style={{ padding: '8px' }}>POS</th>
                  <th style={{ padding: '8px' }}>CONSTRUCTOR</th>
                  <th style={{ padding: '8px' }}>NATIONALITY</th>
                  <th style={{ padding: '8px' }}>WINS</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>POINTS</th>
                </tr>
              </thead>
              <tbody>
                {constructorStandings.map((c: any) => (
                  <tr key={c.constructor_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '8px', fontWeight: 700, color: c.position <= 3 ? 'var(--f1-gold)' : 'var(--text-primary)' }}>
                      P{c.position}
                    </td>
                    <td style={{ padding: '8px', fontWeight: 600, color: 'var(--f1-cyan)' }}>
                      {c.constructor_name}
                    </td>
                    <td style={{ padding: '8px', color: 'var(--text-muted)' }}>{c.nationality}</td>
                    <td style={{ padding: '8px' }}>{c.wins}</td>
                    <td style={{ padding: '8px', textAlign: 'right', fontWeight: 700, color: 'var(--f1-gold)' }}>
                      {c.points} PTS
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Driver Grid Content (Lineup Tab) */}
      {activeTab === 'lineup' && (
      <div className="drivers-content">
        {loading && (
          <div className="drivers-grid">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="driver-card-skeleton">
                <div className="skeleton-header skeleton"></div>
                <div className="skeleton-body">
                  <div className="skeleton-avatar skeleton"></div>
                  <div className="skeleton-lines">
                    <div className="skeleton-line skeleton" style={{ width: '70%' }}></div>
                    <div className="skeleton-line skeleton" style={{ width: '45%' }}></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {error && (
          <div className="error-banner">
            <span>{error}</span>
          </div>
        )}

        {!loading && !error && filteredDrivers.length === 0 && (
          <div className="empty-state">
            <Users size={36} />
            <p>No drivers match "{searchQuery}" in this session classification.</p>
          </div>
        )}

        {!loading && !error && filteredDrivers.length > 0 && (
          <div className="drivers-grid">
            {filteredDrivers.map(d => {
              const isPrimary = d.abbreviation === primaryDriver;
              const isReference = d.abbreviation === referenceDriver;
              const pos = Number(d.position);
              const hasHeadshot = Boolean(d.headshot_url) && !failedImages[d.abbreviation];

              return (
                <div
                  key={d.abbreviation}
                  onClick={() => setPrimaryDriver(d.abbreviation)}
                  className={`driver-card ${isPrimary ? 'primary-selected' : ''} ${isReference ? 'ref-selected' : ''}`}
                  style={{ '--team-color': d.team_color || '#E10600' } as React.CSSProperties}
                >
                  {/* Team Color Top Accent Strip */}
                  <div className="card-team-strip" style={{ backgroundColor: d.team_color || '#E10600' }}></div>

                  {/* Watermark Car Number */}
                  <div className="car-number-watermark">
                    #{d.driver_number}
                  </div>

                  {/* Card Top Row: Position & Points */}
                  <div className="card-top-row">
                    <div className={`pos-badge ${pos === 1 ? 'gold' : pos === 2 ? 'silver' : pos === 3 ? 'bronze' : pos <= 10 ? 'points' : 'classified'}`}>
                      {pos === 1 && <Award size={12} className="pos-icon" />}
                      <span>P{pos || '-'}</span>
                    </div>

                    <div className="driver-points">
                      <Trophy size={11} style={{ opacity: 0.6 }} />
                      <span>{d.points} PTS</span>
                    </div>
                  </div>

                  {/* Driver Visual Portrait & Identity */}
                  <div className="driver-identity-row">
                    <div className="driver-avatar-wrap">
                      {hasHeadshot ? (
                        <img
                          src={d.headshot_url}
                          alt={d.broadcast_name}
                          onError={() => handleImageError(d.abbreviation)}
                          className="driver-portrait-img"
                          loading="lazy"
                        />
                      ) : (
                        <div
                          className="driver-avatar-fallback"
                          style={{ borderColor: d.team_color || '#E10600' }}
                        >
                          <span>{d.abbreviation}</span>
                        </div>
                      )}
                    </div>

                    <div className="driver-meta">
                      <div className="driver-code-row">
                        <span className="driver-code">{d.abbreviation}</span>
                        <span className="driver-car-num">#{d.driver_number}</span>
                      </div>
                      <h3 className="driver-name" title={d.broadcast_name}>{d.broadcast_name}</h3>
                      <div className="driver-team-pill">
                        <span className="team-dot" style={{ backgroundColor: d.team_color || '#94A3B8' }}></span>
                        <span className="team-text">{d.team_name}</span>
                      </div>
                    </div>
                  </div>

                  {/* Selection Status Tag */}
                  <div className="selection-tag-row">
                    {isPrimary && (
                      <span className="status-pill primary">
                        <Check size={11} /> PRIMARY WORKSTATION
                      </span>
                    )}
                    {isReference && (
                      <span className="status-pill reference">
                        <Crosshair size={11} /> REFERENCE DELTA
                      </span>
                    )}
                    {!isPrimary && !isReference && (
                      <span className="status-pill unselected">AVAILABLE</span>
                    )}
                  </div>

                  {/* Action Quick-Buttons */}
                  <div className="card-actions" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => setPrimaryDriver(d.abbreviation)}
                      className={`btn-action btn-primary ${isPrimary ? 'active' : ''}`}
                    >
                      {isPrimary ? 'Active Primary' : 'Set Primary'}
                    </button>
                    <button
                      onClick={() => setReferenceDriver(d.abbreviation)}
                      className={`btn-action btn-comp ${isReference ? 'active' : ''}`}
                    >
                      {isReference ? 'Active Comp' : 'Set Comp'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
      )}
    </div>
  );
};

export default DriversPage;
