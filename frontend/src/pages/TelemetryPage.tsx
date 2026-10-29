import { useState, useEffect, useMemo } from 'react';
import { usePitwall } from '../contexts/PitwallContext';
import { Target, Activity, RefreshCw, Download, Users, Cpu, RadioTower } from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts';
import './TelemetryPage.css';

export default function TelemetryPage() {
  const { session, primaryDriver, referenceDriver } = usePitwall();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    fetch(`/api/telemetry/compare?session_id=${session}&target_driver=${primaryDriver}&ref_driver=${referenceDriver}`)
      .then(r => r.json())
      .then(res => {
        if (!mounted) return;
        if (res.success === false) {
          setError(res.error || 'Failed to fetch telemetry comparison');
        } else {
          setData(res);
          setError('');
        }
      })
      .catch(err => {
        if (!mounted) return;
        console.error(err);
        setError('Network error fetching telemetry');
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => { mounted = false; };
  }, [session, primaryDriver, referenceDriver]);

  const chartData = useMemo(() => {
    if (!data?.aligned_telemetry) return [];
    const raw = data.aligned_telemetry;
    
    // Decimate data for smooth 60fps rendering (every 2nd point)
    return raw
      .filter((_: any, i: number) => i % 2 === 0)
      .map((pt: any, idx: number, arr: any[]) => {
        // Compute longitudinal acceleration ax = dv/dt (g) proxy
        let ax_A = 0;
        let ax_B = 0;
        if (idx > 0) {
          const prev = arr[idx - 1];
          const ds = Math.max(1.0, (pt.Distance || 0) - (prev.Distance || 0));
          const vA = (pt.Speed_A || 0) / 3.6;
          const vA_prev = (prev.Speed_A || 0) / 3.6;
          const vB = (pt.Speed_B || 0) / 3.6;
          const vB_prev = (prev.Speed_B || 0) / 3.6;
          
          const dtA = ds / Math.max(vA, 5.0);
          const dtB = ds / Math.max(vB, 5.0);
          
          ax_A = Math.max(-5.5, Math.min(3.5, ((vA - vA_prev) / dtA) / 9.81));
          ax_B = Math.max(-5.5, Math.min(3.5, ((vB - vB_prev) / dtB) / 9.81));
        }

        return {
          ...pt,
          Accel_A: Number(ax_A.toFixed(2)),
          Accel_B: Number(ax_B.toFixed(2))
        };
      });
  }, [data]);

  if (loading && !data) {
    return (
      <div className="telemetry-container">
        <header className="telemetry-header">
          <div className="header-titles">
            <div className="title-row">
              <Activity size={20} className="header-icon text-cyan" />
              <h2>High-Frequency Telemetry Stack</h2>
              <span className="session-tag">{session}</span>
            </div>
            <p className="subtitle">
              Aligning high-frequency distance arrays for {primaryDriver} vs {referenceDriver}...
            </p>
          </div>
          <div className="badge badge-cyan">
            <RefreshCw size={11} className="spin" />
            <span>ALIGNING DISTANCE TRACES</span>
          </div>
        </header>

        <div className="charts-wrapper">
          <div className="chart-panel" style={{ height: '170px' }}>
            <div className="skeleton" style={{ width: '180px', height: '14px', marginBottom: '12px' }}></div>
            <div className="skeleton" style={{ width: '100%', height: '120px' }}></div>
          </div>
          <div className="chart-panel" style={{ height: '220px' }}>
            <div className="skeleton" style={{ width: '160px', height: '14px', marginBottom: '12px' }}></div>
            <div className="skeleton" style={{ width: '100%', height: '170px' }}></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="telemetry-error">
        <Target size={44} className="error-icon" />
        <h2>Telemetry Alignment Failed</h2>
        <p>{error}</p>
        <button className="btn-retry" onClick={() => window.location.reload()}>Retry Connection</button>
      </div>
    );
  }

  if (!data) return null;

  const deltaVal = Number(data.lap_time_delta_s);
  const isFaster = deltaVal <= 0;

  return (
    <div className="telemetry-container">
      <PageHeader
        hub="Performance"
        title="Telemetry Stack (Distance-Aligned)"
        subtitle="Multi-channel traces for speed, throttle, brake, gear, and RPM aligned by track distance."
        badge={`${primaryDriver} vs ${referenceDriver}`}
        badgeType="cyan"
        crossLinks={[
          { label: 'Lap Comparison', path: '/app/comparison', icon: Users },
          { label: 'Live Gauges', path: '/app/live', icon: RadioTower },
          { label: 'ML Inference', path: '/app/ml-lab', icon: Cpu }
        ]}
      />

      {/* Delta & Context Strip */}
      <header className="telemetry-header" style={{ marginBottom: '16px' }}>

        <div className="header-stats">
          <div className="stat-pill">
            <span className="pill-label">LAP DELTA:</span>
            <span className={`pill-val ${isFaster ? 'faster' : 'slower'}`}>
              {isFaster ? '' : '+'}{deltaVal.toFixed(3)}s
            </span>
          </div>
          <div className="stat-pill">
            <span className="pill-label">DATAPOINTS:</span>
            <span className="pill-val">{chartData.length * 2}</span>
          </div>
          <a
            href={`/api/reports/telemetry/export?session_id=${session}&target_driver=${primaryDriver}&ref_driver=${referenceDriver}`}
            download
            className="stat-pill"
            style={{ textDecoration: 'none', color: '#00F5D4', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
            title="Download distance-aligned CSV telemetry trace"
          >
            <Download size={13} />
            <span style={{ fontWeight: 600, fontSize: '11px', letterSpacing: '0.05em' }}>EXPORT CSV</span>
          </a>
        </div>
      </header>

      {/* Traces Stack */}
      <div className="charts-wrapper">
        {/* Trace 1: Delta Time Chart [DERIVED] */}
        <div className="chart-panel">
          <div className="chart-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>Cumulative Lap Delta (s)</span>
              <span style={{ fontSize: '9px', fontWeight: 800, padding: '1px 5px', borderRadius: '3px', background: 'rgba(0, 245, 212, 0.1)', color: '#00F5D4' }}>
                [DERIVED]
              </span>
            </div>
            <span className="chart-legend-tag">{primaryDriver} vs {referenceDriver}</span>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} syncId="telemetrySync" margin={{ top: 5, right: 15, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="2 2" stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="Distance" type="number" domain={['dataMin', 'dataMax']} tick={false} hide />
                <YAxis domain={['auto', 'auto']} stroke="#64748B" fontSize={10} tickFormatter={(val) => `${val.toFixed(2)}s`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0B0E14', borderColor: 'rgba(255,255,255,0.15)', color: '#F8FAFC', borderRadius: '4px', fontSize: '11px', fontFamily: 'JetBrains Mono' }}
                  labelFormatter={(val) => `Track Distance: ${Math.round(Number(val))}m`}
                />
                <ReferenceLine y={0} stroke="rgba(255,255,255,0.25)" strokeDasharray="3 3" />
                <Line type="monotone" dataKey="DeltaTime" stroke="#00F5D4" dot={false} strokeWidth={2} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Trace 2: Speed Velocity [MEASURED] */}
        <div className="chart-panel">
          <div className="chart-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>Speed Velocity (km/h)</span>
              <span style={{ fontSize: '9px', fontWeight: 800, padding: '1px 5px', borderRadius: '3px', background: 'rgba(16, 185, 129, 0.1)', color: '#10B981' }}>
                [MEASURED]
              </span>
            </div>
            <div className="driver-legend-pills">
              <span className="legend-pill primary">{primaryDriver}</span>
              <span className="legend-pill reference">{referenceDriver}</span>
            </div>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} syncId="telemetrySync" margin={{ top: 5, right: 15, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="2 2" stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="Distance" type="number" domain={['dataMin', 'dataMax']} tick={false} hide />
                <YAxis domain={[0, 360]} stroke="#64748B" fontSize={10} tickFormatter={(val) => `${val}`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0B0E14', borderColor: 'rgba(255,255,255,0.15)', color: '#F8FAFC', borderRadius: '4px', fontSize: '11px', fontFamily: 'JetBrains Mono' }}
                  labelFormatter={(val) => `Track Distance: ${Math.round(Number(val))}m`}
                />
                <Line type="monotone" dataKey="Speed_A" name={primaryDriver} stroke="#00F5D4" dot={false} strokeWidth={2} isAnimationActive={false} />
                <Line type="monotone" dataKey="Speed_B" name={referenceDriver} stroke="#F59E0B" dot={false} strokeWidth={1.75} strokeDasharray="4 2" isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Trace 3: Longitudinal Acceleration ax (g) [DERIVED] */}
        <div className="chart-panel">
          <div className="chart-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>Longitudinal Acceleration / Braking ax (g)</span>
              <span style={{ fontSize: '9px', fontWeight: 800, padding: '1px 5px', borderRadius: '3px', background: 'rgba(0, 245, 212, 0.1)', color: '#00F5D4' }}>
                [DERIVED]
              </span>
            </div>
            <div className="driver-legend-pills">
              <span className="legend-pill primary">{primaryDriver} ax</span>
              <span className="legend-pill reference">{referenceDriver} ax</span>
            </div>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} syncId="telemetrySync" margin={{ top: 5, right: 15, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="2 2" stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="Distance" type="number" domain={['dataMin', 'dataMax']} tick={false} hide />
                <YAxis domain={[-5.5, 3.5]} stroke="#64748B" fontSize={10} tickFormatter={(val) => `${val.toFixed(1)}g`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0B0E14', borderColor: 'rgba(255,255,255,0.15)', color: '#F8FAFC', borderRadius: '4px', fontSize: '11px', fontFamily: 'JetBrains Mono' }}
                  labelFormatter={(val) => `Track Distance: ${Math.round(Number(val))}m`}
                />
                <ReferenceLine y={0} stroke="rgba(255,255,255,0.2)" />
                <Line type="monotone" dataKey="Accel_A" name={`${primaryDriver} ax`} stroke="#00F5D4" dot={false} strokeWidth={1.5} isAnimationActive={false} />
                <Line type="monotone" dataKey="Accel_B" name={`${referenceDriver} ax`} stroke="#F59E0B" strokeDasharray="3 2" dot={false} strokeWidth={1.5} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Trace 4: Throttle & Brake [MEASURED] */}
        <div className="chart-panel">
          <div className="chart-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>Throttle Application (%) & Brake Events</span>
              <span style={{ fontSize: '9px', fontWeight: 800, padding: '1px 5px', borderRadius: '3px', background: 'rgba(16, 185, 129, 0.1)', color: '#10B981' }}>
                [MEASURED]
              </span>
            </div>
            <div className="driver-legend-pills">
              <span className="legend-pill brake">BRAKE</span>
              <span className="legend-pill primary">{primaryDriver} THR</span>
              <span className="legend-pill reference">{referenceDriver} THR</span>
            </div>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} syncId="telemetrySync" margin={{ top: 5, right: 15, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="2 2" stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="Distance" type="number" domain={['dataMin', 'dataMax']} stroke="#64748B" fontSize={10} tickFormatter={(val) => `${val}m`} />
                <YAxis domain={[0, 100]} stroke="#64748B" fontSize={10} tickFormatter={(val) => `${val}%`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0B0E14', borderColor: 'rgba(255,255,255,0.15)', color: '#F8FAFC', borderRadius: '4px', fontSize: '11px', fontFamily: 'JetBrains Mono' }}
                  labelFormatter={(val) => `Track Distance: ${Math.round(Number(val))}m`}
                />
                <Line type="stepAfter" dataKey="Throttle_A" name={`${primaryDriver} Throttle`} stroke="#00F5D4" dot={false} strokeWidth={1.5} isAnimationActive={false} />
                <Line type="stepAfter" dataKey="Throttle_B" name={`${referenceDriver} Throttle`} stroke="#F59E0B" dot={false} strokeWidth={1.5} isAnimationActive={false} />
                <Line type="stepAfter" dataKey="Brake_A" name={`${primaryDriver} Brake`} stroke="#E10600" dot={false} strokeWidth={2} isAnimationActive={false} />
                <Line type="stepAfter" dataKey="Brake_B" name={`${referenceDriver} Brake`} stroke="#EF4444" strokeDasharray="3 2" dot={false} strokeWidth={1.5} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Trace 5: Gear Selection & Engine Crankshaft RPM [MEASURED] */}
        <div className="chart-panel">
          <div className="chart-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>Gear Ratio (1-8) & Engine Crankshaft RPM</span>
              <span style={{ fontSize: '9px', fontWeight: 800, padding: '1px 5px', borderRadius: '3px', background: 'rgba(16, 185, 129, 0.1)', color: '#10B981' }}>
                [MEASURED]
              </span>
            </div>
            <div className="driver-legend-pills">
              <span className="legend-pill primary">{primaryDriver} GEAR / RPM</span>
              <span className="legend-pill reference">{referenceDriver} GEAR / RPM</span>
            </div>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} syncId="telemetrySync" margin={{ top: 5, right: 15, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="2 2" stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="Distance" type="number" domain={['dataMin', 'dataMax']} stroke="#64748B" fontSize={10} tickFormatter={(val) => `${val}m`} />
                <YAxis yAxisId="gear" domain={[0, 8]} stroke="#64748B" fontSize={10} tickFormatter={(val) => `G${val}`} />
                <YAxis yAxisId="rpm" orientation="right" domain={[8000, 14000]} stroke="#64748B" fontSize={10} tickFormatter={(val) => `${val}`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0B0E14', borderColor: 'rgba(255,255,255,0.15)', color: '#F8FAFC', borderRadius: '4px', fontSize: '11px', fontFamily: 'JetBrains Mono' }}
                  labelFormatter={(val) => `Track Distance: ${Math.round(Number(val))}m`}
                />
                <Line yAxisId="gear" type="stepAfter" dataKey="nGear_A" name={`${primaryDriver} Gear`} stroke="#00F5D4" dot={false} strokeWidth={2} isAnimationActive={false} />
                <Line yAxisId="gear" type="stepAfter" dataKey="nGear_B" name={`${referenceDriver} Gear`} stroke="#F59E0B" strokeDasharray="3 2" dot={false} strokeWidth={1.5} isAnimationActive={false} />
                <Line yAxisId="rpm" type="monotone" dataKey="RPM_A" name={`${primaryDriver} RPM`} stroke="rgba(0, 245, 212, 0.4)" dot={false} strokeWidth={1} isAnimationActive={false} />
                <Line yAxisId="rpm" type="monotone" dataKey="RPM_B" name={`${referenceDriver} RPM`} stroke="rgba(245, 158, 11, 0.4)" strokeDasharray="2 2" dot={false} strokeWidth={1} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
