import { useEffect, useState } from 'react';
import { usePitwall } from '../contexts/PitwallContext';
import { AlertTriangle, Clock, Activity, Target, Shield, Gauge, GitMerge } from 'lucide-react';
import './CommandCenterPage.css';

interface CommandCenterData {
  success: boolean;
  error?: string;
  session: {
    name: string;
    type: string;
    date: string;
    current_lap: number;
    total_laps: number | null;
  };
  primary_driver: {
    id: string;
    position: number | null;
    current_lap: number;
    last_lap_time: number | null;
    best_lap_time: number | null;
    sector_1: number | null;
    sector_2: number | null;
    sector_3: number | null;
    pit_status: boolean;
  };
  reference_driver: {
    id: string;
    position: number | null;
    gap: number | null;
    current_lap: number | null;
  } | null;
  tyres: {
    primary: { compound: string; age: number; estimated_degradation: number | null };
    reference: { compound: string; age: number; estimated_degradation: number | null } | null;
  };
  pace: {
    primary_rolling_avg: number | null;
    reference_rolling_avg: number | null;
    delta: number | null;
  };
  strategy: {
    undercut_opportunity?: boolean;
    overcut_opportunity?: boolean;
    recommendation?: string;
    confidence?: number;
  };
  jarvis: {
    summary: string[];
  };
  race_control: {
    track_status: string;
  };
  changes: string[];
}

function formatTime(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || isNaN(seconds)) return 'Unavailable';
  if (seconds < 0) return '-' + formatTime(Math.abs(seconds));
  const m = Math.floor(seconds / 60);
  const s = (seconds % 60).toFixed(3);
  return m > 0 ? `${m}:${s.padStart(6, '0')}` : s;
}

function formatDelta(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || isNaN(seconds)) return 'Unavailable';
  return (seconds > 0 ? '+' : '') + seconds.toFixed(3);
}

export function CommandCenterPage() {
  const { session, primaryDriver, referenceDriver } = usePitwall();
  const [data, setData] = useState<CommandCenterData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    let isMounted = true;
    let isFetching = false;
    
    const fetchData = async () => {
      if (isFetching) return;
      isFetching = true;
      if (!data) setLoading(true);
      setError(null);
      try {
        console.log("CommandCenter: Making API call...");
        const res = await fetch(`/api/command-center?session_id=${session}&primary_driver=${primaryDriver}&ref_driver=${referenceDriver}`);
        if (!res.ok) {
          throw new Error('Failed to fetch command center data');
        }
        const json = await res.json();
        console.log("CommandCenter: API response success:", json.success);
        if (json.success) {
          if (isMounted) {
            setData(json);
            setLastUpdate(new Date());
            setError(null);
          }
        } else {
          throw new Error(json.error || 'Data unavailable');
        }
      } catch (err: any) {
        console.error("CommandCenter: API Error:", err);
        if (isMounted) setError(err.message || 'Unknown error');
      } finally {
        isFetching = false;
        if (isMounted) setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 15000); // refresh every 15s

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [session, primaryDriver, referenceDriver]);

  if (loading && !data) {
    return (
      <div className="command-center">
        <div className="cc-header">
          <div className="cc-header-info flex-col gap-xs">
            <div className="skeleton" style={{ width: '280px', height: '22px' }}></div>
            <div className="skeleton" style={{ width: '120px', height: '14px', marginTop: '4px' }}></div>
          </div>
          <div className="badge badge-cyan">
            <span>SYNCING TACTICAL MATRIX...</span>
          </div>
        </div>

        <div className="cc-main-grid">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="cc-panel" style={{ height: '200px' }}>
              <div className="skeleton" style={{ width: '160px', height: '14px', marginBottom: '14px' }}></div>
              <div className="skeleton" style={{ width: '100%', height: '120px' }}></div>
            </div>
            <div className="cc-row">
              <div className="cc-panel" style={{ height: '140px' }}>
                <div className="skeleton" style={{ width: '120px', height: '14px', marginBottom: '12px' }}></div>
                <div className="skeleton" style={{ width: '100%', height: '80px' }}></div>
              </div>
              <div className="cc-panel" style={{ height: '140px' }}>
                <div className="skeleton" style={{ width: '140px', height: '14px', marginBottom: '12px' }}></div>
                <div className="skeleton" style={{ width: '100%', height: '80px' }}></div>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="cc-panel" style={{ height: '150px' }}>
              <div className="skeleton" style={{ width: '130px', height: '14px', marginBottom: '12px' }}></div>
              <div className="skeleton" style={{ width: '100%', height: '80px' }}></div>
            </div>
            <div className="cc-panel" style={{ height: '200px' }}>
              <div className="skeleton" style={{ width: '180px', height: '14px', marginBottom: '12px' }}></div>
              <div className="skeleton" style={{ width: '100%', height: '130px' }}></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="cc-panel" style={{ borderColor: '#ef4444' }}>
        <h2 style={{ color: '#ef4444', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertTriangle /> COMMAND CENTER ERROR
        </h2>
        <p>{error}</p>
        <p className="cc-unavailable">Session data is currently unavailable. Please verify session readiness.</p>
      </div>
    );
  }

  if (!data) return null;

  const trackStatusMap: Record<string, string> = {
    "1": "TRACK CLEAR",
    "2": "YELLOW FLAG",
    "3": "UNAVAILABLE", // not strictly 3, fastf1 uses different codes
    "4": "SAFETY CAR",
    "5": "RED FLAG",
    "6": "VSC DEPLOYED",
    "7": "VSC ENDING"
  };
  const statusLabel = trackStatusMap[data.race_control?.track_status] || "TRACK CLEAR";

  return (
    <div className="command-center">
      <div className="cc-header">
        <div className="cc-header-info">
          <h1>{data.session.name} <span style={{color: 'var(--text-secondary)', fontWeight: 'normal'}}>| {data.session.type}</span></h1>
          <p>LAP {data.session.current_lap} {data.session.total_laps ? `/ ${data.session.total_laps}` : ''}</p>
        </div>
        <div className="cc-header-status">
          <div className="cc-status-badge live">LIVE / UPDATED {lastUpdate ? lastUpdate.toLocaleTimeString() : ''}</div>
          <p style={{ marginTop: 4, fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 'bold' }}>
            {statusLabel}
          </p>
        </div>
      </div>

      <div className="cc-main-grid">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' }}>
          {/* Primary Driver */}
          <div className="cc-panel cc-driver-primary">
            <div className="cc-panel-header"><Target size={16}/> PRIMARY DRIVER</div>
            <div className="cc-driver-header">
              <h2 className="cc-driver-name">{data.primary_driver.id}</h2>
              <span className="cc-driver-position">P{data.primary_driver.position ?? '-'}</span>
            </div>
            
            <div className="cc-metric-grid">
              <div className="cc-metric">
                <div className="cc-metric-label">Last Lap</div>
                <div className="cc-metric-value">{formatTime(data.primary_driver.last_lap_time)}</div>
              </div>
              <div className="cc-metric">
                <div className="cc-metric-label">Best Lap</div>
                <div className="cc-metric-value">{formatTime(data.primary_driver.best_lap_time)}</div>
              </div>
              <div className="cc-metric">
                <div className="cc-metric-label">Tyre</div>
                <div className="cc-metric-value">{data.tyres.primary.compound} (L{data.tyres.primary.age})</div>
              </div>
              <div className="cc-metric">
                <div className="cc-metric-label">Pit Status</div>
                <div className="cc-metric-value" style={{ color: data.primary_driver.pit_status ? '#fbbf24' : 'var(--text-primary)' }}>
                  {data.primary_driver.pit_status ? 'IN PIT' : 'ON TRACK'}
                </div>
              </div>
            </div>

            <div className="cc-sectors mt-sm">
              <div className="cc-sector">
                <div className="cc-sector-label">S1</div>
                <div className="cc-sector-value">{data.primary_driver.sector_1 ? data.primary_driver.sector_1.toFixed(3) : '-'}</div>
              </div>
              <div className="cc-sector">
                <div className="cc-sector-label">S2</div>
                <div className="cc-sector-value">{data.primary_driver.sector_2 ? data.primary_driver.sector_2.toFixed(3) : '-'}</div>
              </div>
              <div className="cc-sector">
                <div className="cc-sector-label">S3</div>
                <div className="cc-sector-value">{data.primary_driver.sector_3 ? data.primary_driver.sector_3.toFixed(3) : '-'}</div>
              </div>
            </div>
          </div>

          <div className="cc-row">
            {/* Pace Monitor */}
            <div className="cc-panel">
              <div className="cc-panel-header"><Gauge size={16}/> PACE MONITOR</div>
              <div className="cc-metric-grid">
                <div className="cc-metric">
                  <div className="cc-metric-label">Primary Avg</div>
                  <div className="cc-metric-value">{formatTime(data.pace.primary_rolling_avg)}</div>
                </div>
                <div className="cc-metric">
                  <div className="cc-metric-label">Reference Avg</div>
                  <div className="cc-metric-value">{formatTime(data.pace.reference_rolling_avg)}</div>
                </div>
                <div className="cc-metric">
                  <div className="cc-metric-label">Delta</div>
                  <div className={`cc-metric-value ${data.pace.delta && data.pace.delta < 0 ? 'delta-neg' : 'delta-pos'}`}>
                    {formatDelta(data.pace.delta)}
                  </div>
                </div>
              </div>
            </div>

            {/* Strategy Status */}
            <div className="cc-panel">
              <div className="cc-panel-header"><GitMerge size={16}/> STRATEGY STATUS</div>
              <div className="cc-metric-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
                <div className="cc-metric">
                  <div className="cc-metric-label">Recommendation</div>
                  <div className="cc-metric-value">{data.strategy.recommendation || 'MAINTAIN'}</div>
                </div>
                <div className="cc-metric">
                  <div className="cc-metric-label">Confidence</div>
                  <div className="cc-metric-value">{data.strategy.confidence ? data.strategy.confidence.toFixed(1) + '%' : 'Unavailable'}</div>
                </div>
                <div className="cc-metric">
                  <div className="cc-metric-label">Undercut</div>
                  <div className="cc-metric-value" style={{ color: data.strategy.undercut_opportunity ? '#10b981' : 'var(--text-secondary)' }}>
                    {data.strategy.undercut_opportunity ? 'VIABLE' : 'NO'}
                  </div>
                </div>
                <div className="cc-metric">
                  <div className="cc-metric-label">Overcut</div>
                  <div className="cc-metric-value" style={{ color: data.strategy.overcut_opportunity ? '#10b981' : 'var(--text-secondary)' }}>
                    {data.strategy.overcut_opportunity ? 'VIABLE' : 'NO'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' }}>
          {/* Rival Watch */}
          <div className="cc-panel cc-rival-watch">
            <div className="cc-panel-header"><Activity size={16}/> RIVAL WATCH</div>
            {data.reference_driver ? (
              <>
                <div className="cc-driver-header mb-md">
                  <h2 className="cc-driver-name" style={{ fontSize: '1.8rem' }}>{data.reference_driver.id}</h2>
                  <span className="cc-driver-position" style={{ fontSize: '1.5rem', color: 'var(--text-primary)' }}>
                    P{data.reference_driver.position ?? '-'}
                  </span>
                </div>
                <div className="cc-metric-grid">
                  <div className="cc-metric">
                    <div className="cc-metric-label">Gap</div>
                    <div className="cc-metric-value">{formatDelta(data.reference_driver.gap)}</div>
                  </div>
                  <div className="cc-metric">
                    <div className="cc-metric-label">Tyre</div>
                    <div className="cc-metric-value">{data.tyres.reference?.compound} (L{data.tyres.reference?.age})</div>
                  </div>
                </div>
              </>
            ) : (
              <p className="cc-unavailable">No reference driver selected.</p>
            )}
          </div>

          {/* JARVIS Summary */}
          <div className="cc-panel cc-jarvis-summary">
            <div className="cc-panel-header"><Shield size={16}/> JARVIS ENGINEERING</div>
            {data.jarvis.summary && data.jarvis.summary.length > 0 ? (
              <div className="jarvis-content">
                {data.jarvis.summary.map((item: any, idx: number) => (
                  <div key={idx} className="jarvis-item">
                    <div className="jarvis-item-text">
                      {typeof item === 'object' ? (
                        <><strong>{item.category}:</strong> {item.message}</>
                      ) : (
                        item
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="cc-unavailable">No active insights.</p>
            )}
          </div>

          {/* Changes */}
          <div className="cc-panel">
            <div className="cc-panel-header"><Clock size={16}/> WHAT CHANGED?</div>
            <div className="cc-changes">
              {data.changes && data.changes.length > 0 ? (
                data.changes.map((change, idx) => (
                  <div key={idx} className="cc-change-item">{change}</div>
                ))
              ) : (
                <p className="cc-unavailable">No significant change</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
