import { useState, useEffect } from 'react';
import { usePitwall } from '../contexts/PitwallContext';
import {
  Target,
  Users,
  RefreshCw,
  Download,
  Gauge,
  Activity,
  Layers,
  Sparkles,
  Info
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { BarChart2, Cpu } from 'lucide-react';
import './ComparisonPage.css';

interface CornerDynamic {
  corner_number: number;
  corner_name: string;
  corner_type: string;
  braking_distance_m: number;
  braking_entry_speed_kmh: number;
  apex_speed_kmh: number;
  peak_deceleration_g: number;
  peak_lateral_g: number;
  throttle_pickup_delay_s: number;
  throttle_pickup_distance_m: number;
  full_throttle_distance_m: number;
  exit_speed_kmh: number;
  time_loss_vs_ref_s: number;
}

interface MicroSector {
  mini_sector_idx: number;
  start_distance_m: number;
  end_distance_m: number;
  primary_speed_kmh: number;
  reference_speed_kmh: number;
  speed_delta_kmh: number;
  time_delta_s: number;
  dominant_driver: string;
}

interface ConsistencyProfile {
  driver_id: string;
  total_laps_analyzed: number;
  clean_laps_count: number;
  mean_lap_time_s: number;
  std_dev_lap_time_s: number;
  iqr_lap_time_s: number;
  consistency_rating_pct: number;
  lap_to_lap_delta_mean_s: number;
}

interface IdealLap {
  driver_id: string;
  actual_best_lap_s: number;
  ideal_lap_s: number;
  potential_gain_s: number;
  sector_1_best_s: number;
  sector_2_best_s: number;
  sector_3_best_s: number;
  num_laps_synthesized: number;
  limitations_disclaimer: string;
}

export default function ComparisonPage() {
  const { session, primaryDriver, referenceDriver } = usePitwall();
  const [data, setData] = useState<any>(null);
  const [corners, setCorners] = useState<CornerDynamic[]>([]);
  const [microSectors, setMicroSectors] = useState<MicroSector[]>([]);
  const [consistency, setConsistency] = useState<ConsistencyProfile | null>(null);
  const [idealLap, setIdealLap] = useState<IdealLap | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    Promise.all([
      fetch(`/api/telemetry/compare?session_id=${session}&target_driver=${primaryDriver}&ref_driver=${referenceDriver}`).then(r => r.json()),
      fetch(`/api/driver-performance/corners?session_id=${session}&primary_driver=${primaryDriver}&ref_driver=${referenceDriver}`).then(r => r.json()).catch(() => ({ corners: [] })),
      fetch(`/api/driver-performance/micro-sectors?session_id=${session}&primary_driver=${primaryDriver}&ref_driver=${referenceDriver}&sectors_count=25`).then(r => r.json()).catch(() => ({ micro_sectors: [] })),
      fetch(`/api/driver-performance/consistency?session_id=${session}&primary_driver=${primaryDriver}`).then(r => r.json()).catch(() => ({ consistency: null })),
      fetch(`/api/driver-performance/ideal-lap?session_id=${session}&primary_driver=${primaryDriver}`).then(r => r.json()).catch(() => ({ ideal_lap: null }))
    ])
      .then(([compRes, cornRes, microRes, consRes, idealRes]) => {
        if (!mounted) return;
        if (compRes.success === false) {
          setError(compRes.error || 'Failed to fetch comparison');
        } else {
          setData(compRes);
          setCorners(cornRes.corners || []);
          setMicroSectors(microRes.micro_sectors || []);
          setConsistency(consRes.consistency || null);
          setIdealLap(idealRes.ideal_lap || null);
          setError('');
        }
      })
      .catch(err => {
        if (!mounted) return;
        console.error(err);
        setError('Network error fetching performance comparison');
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => { mounted = false; };
  }, [session, primaryDriver, referenceDriver]);

  if (loading && !data) {
    return (
      <div className="comparison-container">
        <header className="comparison-header">
          <div className="header-titles">
            <div className="title-row">
              <Users size={20} className="header-icon text-cyan" />
              <h2>Driver Head-to-Head & Vehicle Dynamics</h2>
              <span className="session-tag">{session}</span>
            </div>
            <p className="subtitle">
              Attributing corner-by-corner time loss and micro-sectors for {primaryDriver} vs {referenceDriver}...
            </p>
          </div>
          <div className="badge badge-cyan">
            <RefreshCw size={11} className="spin" />
            <span>CALCULATING 5-PHASE DYNAMICS</span>
          </div>
        </header>

        <div className="sector-deltas-row">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="card-engineering sector-card" style={{ height: '110px' }}>
              <div className="skeleton" style={{ width: '100px', height: '12px', marginBottom: '8px' }}></div>
              <div className="skeleton" style={{ width: '80px', height: '28px', marginBottom: '8px' }}></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="comparison-error">
        <Target size={44} className="error-icon" />
        <h2>Comparison Analysis Failed</h2>
        <p>{error}</p>
        <button className="btn-retry" onClick={() => window.location.reload()}>Retry Connection</button>
      </div>
    );
  }

  if (!data) return null;

  const s1 = Number(data.sector_time_loss?.sector_1_s || 0);
  const s2 = Number(data.sector_time_loss?.sector_2_s || 0);
  const s3 = Number(data.sector_time_loss?.sector_3_s || 0);

  return (
    <div className="comparison-container">
      <PageHeader
        hub="Performance"
        title="Lap Comparison (Delta Trace)"
        subtitle="Sector-by-sector time delta, 25 micro-sectors, 5-phase corner dynamics, and theoretical ideal lap."
        badge={`${primaryDriver} vs ${referenceDriver}`}
        badgeType="cyan"
        crossLinks={[
          { label: 'Telemetry Stack', path: '/app/telemetry', icon: BarChart2 },
          { label: 'ML Inference Lab', path: '/app/ml-lab', icon: Cpu },
          { label: 'Ask JARVIS', path: '/app/jarvis', icon: Sparkles }
        ]}
      />

      {/* Matchup & Export Banner */}
      <header className="comparison-header" style={{ marginBottom: '16px' }}>

        <div className="matchup-banner" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span className="driver-pill primary">{primaryDriver}</span>
          <span className="vs">VS</span>
          <span className="driver-pill reference">{referenceDriver}</span>
          <a
            href={`/api/reports/comparison/export?session_id=${session}&target_driver=${primaryDriver}&ref_driver=${referenceDriver}`}
            download
            className="btn-export-pill"
            style={{ textDecoration: 'none', color: '#00F5D4', background: 'rgba(0, 245, 212, 0.08)', border: '1px solid rgba(0, 245, 212, 0.25)', borderRadius: '4px', padding: '4px 10px', fontSize: '11px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '5px', marginLeft: 'auto' }}
            title="Download 5-phase corner time loss CSV attribution breakdown"
          >
            <Download size={12} />
            <span>EXPORT CSV</span>
          </a>
        </div>
      </header>

      {/* Sector Deltas */}
      <div className="sector-deltas-row">
        <div className="card-engineering sector-card">
          <span className="metric-label">SECTOR 1 DELTA</span>
          <span className={`metric-value ${s1 > 0 ? 'slower' : 'faster'}`}>
            {s1 > 0 ? '+' : ''}{s1.toFixed(3)}s
          </span>
          <span className="sector-detail">{s1 <= 0 ? `${primaryDriver} faster in Sector 1` : `${referenceDriver} faster in Sector 1`}</span>
        </div>

        <div className="card-engineering sector-card">
          <span className="metric-label">SECTOR 2 DELTA</span>
          <span className={`metric-value ${s2 > 0 ? 'slower' : 'faster'}`}>
            {s2 > 0 ? '+' : ''}{s2.toFixed(3)}s
          </span>
          <span className="sector-detail">{s2 <= 0 ? `${primaryDriver} faster in Sector 2` : `${referenceDriver} faster in Sector 2`}</span>
        </div>

        <div className="card-engineering sector-card">
          <span className="metric-label">SECTOR 3 DELTA</span>
          <span className={`metric-value ${s3 > 0 ? 'slower' : 'faster'}`}>
            {s3 > 0 ? '+' : ''}{s3.toFixed(3)}s
          </span>
          <span className="sector-detail">{s3 <= 0 ? `${primaryDriver} faster in Sector 3` : `${referenceDriver} faster in Sector 3`}</span>
        </div>
      </div>

      {/* Micro-Sectors 25-Segment Track Strip */}
      {microSectors.length > 0 && (
        <div className="card-engineering" style={{ padding: '16px' }}>
          <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={16} className="panel-icon text-cyan" />
              <h3 style={{ margin: 0, fontSize: '13px' }}>25 Equidistant Micro-Sector Dominance Strip</h3>
            </div>
            <div style={{ display: 'flex', gap: '10px', fontSize: '11px' }}>
              <span style={{ color: '#00F5D4', fontWeight: 700 }}>■ {primaryDriver} Dominant</span>
              <span style={{ color: '#F59E0B', fontWeight: 700 }}>■ {referenceDriver} Dominant</span>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(25, 1fr)', gap: '3px', marginTop: '12px' }}>
            {microSectors.map((ms) => {
              const isPri = ms.dominant_driver === primaryDriver;
              return (
                <div
                  key={ms.mini_sector_idx}
                  title={`Sector ${ms.mini_sector_idx}: ${ms.start_distance_m}m - ${ms.end_distance_m}m | Delta: ${ms.time_delta_s > 0 ? '+' : ''}${ms.time_delta_s}s (${ms.dominant_driver})`}
                  style={{
                    height: '28px',
                    borderRadius: '2px',
                    background: isPri ? '#00F5D4' : '#F59E0B',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '9px',
                    fontWeight: 800,
                    color: '#000000',
                    cursor: 'default',
                    opacity: 0.9
                  }}
                >
                  S{ms.mini_sector_idx}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 5-Phase Corner Dynamics Profile Table */}
      <div className="card-engineering table-panel">
        <div className="panel-header">
          <Activity size={16} className="panel-icon text-cyan" />
          <h3>5-Phase Corner Dynamics Decomposition ({corners.length} Corners Detected)</h3>
        </div>

        {corners.length > 0 ? (
          <div className="table-responsive">
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>Corner</th>
                  <th>Type</th>
                  <th>Entry Speed</th>
                  <th>Braking Dist</th>
                  <th>Peak Decel</th>
                  <th>Apex Min Speed</th>
                  <th>Peak Lateral</th>
                  <th>Throttle Pickup</th>
                  <th>Exit Speed</th>
                  <th>Delta vs Ref</th>
                </tr>
              </thead>
              <tbody>
                {corners.map((c) => (
                  <tr key={c.corner_number}>
                    <td className="corner-tag">{c.corner_name}</td>
                    <td>
                      <span style={{
                        fontSize: '9px',
                        fontWeight: 700,
                        padding: '2px 5px',
                        borderRadius: '3px',
                        background: c.corner_type === 'LOW_SPEED' ? 'rgba(239,68,68,0.15)' : (c.corner_type === 'MEDIUM_SPEED' ? 'rgba(245,158,11,0.15)' : 'rgba(16,185,129,0.15)'),
                        color: c.corner_type === 'LOW_SPEED' ? '#EF4444' : (c.corner_type === 'MEDIUM_SPEED' ? '#F59E0B' : '#10B981')
                      }}>
                        {c.corner_type}
                      </span>
                    </td>
                    <td>{c.braking_entry_speed_kmh.toFixed(0)} km/h</td>
                    <td>{c.braking_distance_m.toFixed(0)}m</td>
                    <td style={{ color: '#EF4444', fontWeight: 700 }}>{c.peak_deceleration_g.toFixed(1)}g</td>
                    <td style={{ color: '#00F5D4', fontWeight: 700 }}>{c.apex_speed_kmh.toFixed(1)} km/h</td>
                    <td style={{ color: '#FBBF24' }}>{c.peak_lateral_g.toFixed(1)}g</td>
                    <td>+{c.throttle_pickup_delay_s.toFixed(2)}s ({c.throttle_pickup_distance_m.toFixed(0)}m)</td>
                    <td>{c.exit_speed_kmh.toFixed(0)} km/h</td>
                    <td style={{ color: c.time_loss_vs_ref_s > 0 ? '#EF4444' : '#10B981', fontWeight: 700 }}>
                      {c.time_loss_vs_ref_s > 0 ? '+' : ''}{c.time_loss_vs_ref_s.toFixed(3)}s
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <p>Decomposing corner trajectory dynamics for session {session}...</p>
          </div>
        )}
      </div>

      {/* Driver Consistency & Ideal Lap Side-by-Side */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '16px' }}>
        {/* Driver Consistency Profile */}
        {consistency && (
          <div className="card-engineering">
            <div className="panel-header">
              <Gauge size={16} className="panel-icon text-cyan" />
              <h3>Driver Pace Consistency Rating ({consistency.driver_id})</h3>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '12px', fontFamily: 'JetBrains Mono' }}>
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '4px' }}>
                <div style={{ color: '#64748B', fontSize: '10px' }}>CONSISTENCY RATING</div>
                <div style={{ fontSize: '20px', fontWeight: 800, color: '#00F5D4', margin: '4px 0' }}>
                  {consistency.consistency_rating_pct.toFixed(1)}%
                </div>
                <div style={{ color: '#94A3B8', fontSize: '10px' }}>Based on clean stint laps</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '4px' }}>
                <div style={{ color: '#64748B', fontSize: '10px' }}>LAP TIME SIGMA (std dev)</div>
                <div style={{ fontSize: '20px', fontWeight: 800, color: '#F8FAFC', margin: '4px 0' }}>
                  &plusmn;{consistency.std_dev_lap_time_s.toFixed(3)}s
                </div>
                <div style={{ color: '#94A3B8', fontSize: '10px' }}>IQR: {consistency.iqr_lap_time_s.toFixed(3)}s</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '4px' }}>
                <div style={{ color: '#64748B', fontSize: '10px' }}>CLEAN LAPS ANALYZED</div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: '#CBD5E1', margin: '4px 0' }}>
                  {consistency.clean_laps_count} / {consistency.total_laps_analyzed} Laps
                </div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '4px' }}>
                <div style={{ color: '#64748B', fontSize: '10px' }}>AVG LAP-TO-LAP DELTA</div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: '#10B981', margin: '4px 0' }}>
                  {consistency.lap_to_lap_delta_mean_s.toFixed(3)}s
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Ideal Lap Reconstruction */}
        {idealLap && (
          <div className="card-engineering">
            <div className="panel-header">
              <Sparkles size={16} className="panel-icon text-gold" />
              <h3>Theoretical Ideal-Lap Reconstruction ({idealLap.driver_id})</h3>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px', fontFamily: 'JetBrains Mono' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed rgba(255,255,255,0.08)', paddingBottom: '4px' }}>
                <span style={{ color: '#94A3B8' }}>Actual Personal Best:</span>
                <span style={{ fontWeight: 700, color: '#FFFFFF' }}>{idealLap.actual_best_lap_s.toFixed(3)}s</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed rgba(255,255,255,0.08)', paddingBottom: '4px' }}>
                <span style={{ color: '#00F5D4' }}>Theoretical Composite Best:</span>
                <span style={{ fontWeight: 800, color: '#00F5D4' }}>{idealLap.ideal_lap_s.toFixed(3)}s</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed rgba(255,255,255,0.08)', paddingBottom: '4px' }}>
                <span style={{ color: '#FBBF24' }}>Potential Untapped Delta:</span>
                <span style={{ fontWeight: 800, color: '#FBBF24' }}>-{idealLap.potential_gain_s.toFixed(3)}s</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#64748B', paddingTop: '4px' }}>
                <span>S1: {idealLap.sector_1_best_s.toFixed(3)}s</span>
                <span>S2: {idealLap.sector_2_best_s.toFixed(3)}s</span>
                <span>S3: {idealLap.sector_3_best_s.toFixed(3)}s</span>
              </div>
              <div style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.25)', padding: '8px 10px', borderRadius: '4px', marginTop: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#F59E0B', fontSize: '10px', fontWeight: 700, marginBottom: '2px' }}>
                  <Info size={11} />
                  <span>CONTINUOUS-LAP TRACTION & THERMAL LIMITATION</span>
                </div>
                <div style={{ fontSize: '10px', color: '#CBD5E1', lineHeight: 1.3, fontFamily: 'Inter, sans-serif' }}>
                  {idealLap.limitations_disclaimer}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
