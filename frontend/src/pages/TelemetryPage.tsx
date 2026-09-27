import { useState, useEffect, useMemo } from 'react';
import { usePitwall } from '../contexts/PitwallContext';
import { Target, Activity } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine
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

    fetch(`http://localhost:8000/api/telemetry/compare?session_id=${session}&target_driver=${primaryDriver}&ref_driver=${referenceDriver}`)
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
    // Decimate data for performance (every 2nd point)
    return data.aligned_telemetry.filter((_: any, i: number) => i % 2 === 0);
  }, [data]);

  if (loading && !data) {
    return (
      <div className="telemetry-loading">
        <div className="spinner"></div>
        <p>Aligning Lap Telemetry (Distance Integration)...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="telemetry-error">
        <Target size={48} className="error-icon" />
        <h2>Telemetry Alignment Failed</h2>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={() => window.location.reload()}>Retry Connection</button>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="telemetry-container">
      <header className="telemetry-header">
        <h1 className="flex items-center gap-sm">
          <Activity size={24} style={{ color: 'var(--accent-blue)' }} />
          Telemetry Workspace: <span style={{ color: 'var(--accent-blue)' }}>{primaryDriver}</span> vs <span style={{ color: 'var(--neon-purple)' }}>{referenceDriver}</span>
        </h1>
        <div className="header-stats flex gap-md">
          <div className="stat-pill">
            Lap Delta: <span style={{ color: data.lap_time_delta_s > 0 ? 'var(--error)' : 'var(--accent-green)' }}>
              {data.lap_time_delta_s > 0 ? '+' : ''}{data.lap_time_delta_s}s
            </span>
          </div>
        </div>
      </header>

      <div className="charts-wrapper">
        {/* Delta Time Chart */}
        <div className="chart-panel">
          <div className="chart-title">Time Delta (s) - {primaryDriver} vs {referenceDriver}</div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} syncId="telemetrySync" margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                <XAxis dataKey="Distance" type="number" domain={['dataMin', 'dataMax']} tick={false} hide />
                <YAxis domain={['auto', 'auto']} stroke="#64748B" fontSize={11} tickFormatter={(val) => val.toFixed(2)} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0d0e12', borderColor: '#1e293b', color: '#fff' }}
                  labelFormatter={(val) => `Distance: ${Math.round(Number(val))}m`}
                />
                <ReferenceLine y={0} stroke="rgba(255,255,255,0.3)" />
                <Line type="monotone" dataKey="DeltaTime" stroke="#fff" dot={false} strokeWidth={2} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Speed Chart */}
        <div className="chart-panel">
          <div className="chart-title">Speed (kph)</div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} syncId="telemetrySync" margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                <XAxis dataKey="Distance" type="number" domain={['dataMin', 'dataMax']} tick={false} hide />
                <YAxis domain={[0, 350]} stroke="#64748B" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0d0e12', borderColor: '#1e293b', color: '#fff' }}
                  labelFormatter={(val) => `Distance: ${Math.round(Number(val))}m`}
                />
                <Legend />
                <Line type="monotone" dataKey="Speed_A" name={primaryDriver} stroke="var(--accent-blue)" dot={false} strokeWidth={2} isAnimationActive={false} />
                <Line type="monotone" dataKey="Speed_B" name={referenceDriver} stroke="var(--neon-purple)" dot={false} strokeWidth={2} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Throttle / Brake Chart */}
        <div className="chart-panel">
          <div className="chart-title">Throttle (%) & Brake</div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} syncId="telemetrySync" margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                <XAxis dataKey="Distance" type="number" domain={['dataMin', 'dataMax']} stroke="#64748B" fontSize={11} tickFormatter={(val) => `${val}m`} />
                <YAxis domain={[0, 100]} stroke="#64748B" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0d0e12', borderColor: '#1e293b', color: '#fff' }}
                  labelFormatter={(val) => `Distance: ${Math.round(Number(val))}m`}
                />
                <Line type="stepAfter" dataKey="Throttle_A" name={`${primaryDriver} Thr`} stroke="var(--accent-blue)" dot={false} strokeWidth={1.5} isAnimationActive={false} />
                <Line type="stepAfter" dataKey="Throttle_B" name={`${referenceDriver} Thr`} stroke="var(--neon-purple)" dot={false} strokeWidth={1.5} isAnimationActive={false} />
                <Line type="stepAfter" dataKey="Brake_A" name={`${primaryDriver} Brk`} stroke="#ff3333" dot={false} strokeWidth={1.5} isAnimationActive={false} />
                <Line type="stepAfter" dataKey="Brake_B" name={`${referenceDriver} Brk`} stroke="#ff7777" dot={false} strokeWidth={1.5} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
