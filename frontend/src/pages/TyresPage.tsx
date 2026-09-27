import { useState, useEffect } from 'react';
import { usePitwall } from '../contexts/PitwallContext';
import { Target, CircleDashed } from 'lucide-react';
import {
  Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Line, ComposedChart
} from 'recharts';
import './TyresPage.css';

export default function TyresPage() {
  const { session, primaryDriver, referenceDriver } = usePitwall();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [progressMsg, setProgressMsg] = useState('Connecting...');

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setProgressMsg('Connecting...');

    const progressInterval = setInterval(() => {
      setProgressMsg(prev => {
        if (prev === 'Connecting...') return 'Fetching Telemetry Data (This may take up to 2 minutes on cold start)...';
        if (prev === 'Fetching Telemetry Data (This may take up to 2 minutes on cold start)...') return 'Applying Regression Model...';
        return prev;
      });
    }, 10000);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    fetch(`http://localhost:8000/api/tyres/degradation?session_id=${session}&primary_driver=${primaryDriver}&ref_driver=${referenceDriver}`, { signal: controller.signal })
      .then(async r => {
        const json = await r.json();
        if (!r.ok) {
          throw new Error(json.detail || json.error || `HTTP error ${r.status}`);
        }
        return json;
      })
      .then(res => {
        if (!mounted) return;
        if (res.success === false) {
          setError(res.error || 'Failed to fetch tyre degradation data');
        } else {
          setData(res);
          setError('');
        }
      })
      .catch(err => {
        if (!mounted) return;
        console.error(err);
        if (err.name === 'AbortError') {
          setError('Request Timed Out. The server is taking too long to load FastF1 data.');
        } else {
          setError('Network error fetching tyre intelligence');
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
        clearTimeout(timeoutId);
        clearInterval(progressInterval);
      });

    return () => {
      mounted = false;
      controller.abort();
      clearTimeout(timeoutId);
      clearInterval(progressInterval);
    };
  }, [session, primaryDriver, referenceDriver]);

  if (loading && !data) {
    return (
      <div className="tyres-loading">
        <div className="spinner"></div>
        <p>{progressMsg}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="tyres-error">
        <Target size={48} className="error-icon" />
        <h2>Degradation Modeling Failed</h2>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={() => window.location.reload()}>Retry Connection</button>
      </div>
    );
  }

  if (!data) return null;

  const pData = data.primary_driver;
  const rData = data.reference_driver;

  const primaryPlotData = pData.success ? pData.data_points : [];
  const refPlotData = rData.success ? rData.data_points : [];

  return (
    <div className="tyres-container">
      <header className="tyres-header">
        <h1 className="flex items-center gap-sm">
          <CircleDashed size={24} style={{ color: 'var(--accent-blue)' }} />
          Tyre Degradation Intelligence
        </h1>
        <div className="header-stats flex gap-md">
          <div className="stat-pill">
            {primaryDriver} Deg: <span style={{ color: 'var(--accent-blue)' }}>+{pData.degradation_slope_s_per_lap} s/lap</span>
          </div>
          <div className="stat-pill">
            {referenceDriver} Deg: <span style={{ color: 'var(--neon-purple)' }}>+{rData.degradation_slope_s_per_lap} s/lap</span>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-2 gap-lg" style={{ flex: 1, minHeight: 0 }}>
        {/* Primary Driver */}
        <div className="card chart-panel">
          <div className="chart-title">{primaryDriver} - {pData.compound} (Stint {pData.stint_number})</div>
          {pData.success ? (
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis
                    dataKey="tyre_age"
                    type="number"
                    name="Tyre Age"
                    stroke="#64748B"
                    label={{ value: 'Tyre Age (Laps)', position: 'insideBottom', offset: -10, fill: '#64748B' }}
                  />
                  <YAxis
                    yAxisId="left"
                    dataKey="fuel_corrected_lap_time_s"
                    type="number"
                    name="Lap Time (s)"
                    stroke="#64748B"
                    domain={['dataMin - 1', 'dataMax + 1']}
                    label={{ value: 'Fuel-Corrected Pace (s)', angle: -90, position: 'insideLeft', fill: '#64748B' }}
                  />
                  <Tooltip
                    cursor={{ strokeDasharray: '3 3' }}
                    contentStyle={{ backgroundColor: '#0d0e12', borderColor: '#1e293b', color: '#fff' }}
                  />
                  <Legend verticalAlign="top" height={36}/>
                  <Scatter yAxisId="left" name="Actual Laps" data={primaryPlotData} fill="var(--accent-blue)" />
                  <Line
                    yAxisId="left"
                    data={primaryPlotData}
                    type="linear"
                    dataKey="trend_lap_time_s"
                    stroke="var(--accent-green)"
                    name="OLS Trend"
                    dot={false}
                    strokeWidth={2}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="empty-state">No valid stint data for {primaryDriver}</div>
          )}
        </div>

        {/* Reference Driver */}
        <div className="card chart-panel">
          <div className="chart-title">{referenceDriver} - {rData.compound} (Stint {rData.stint_number})</div>
          {rData.success ? (
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis
                    dataKey="tyre_age"
                    type="number"
                    name="Tyre Age"
                    stroke="#64748B"
                    label={{ value: 'Tyre Age (Laps)', position: 'insideBottom', offset: -10, fill: '#64748B' }}
                  />
                  <YAxis
                    yAxisId="left"
                    dataKey="fuel_corrected_lap_time_s"
                    type="number"
                    name="Lap Time (s)"
                    stroke="#64748B"
                    domain={['dataMin - 1', 'dataMax + 1']}
                    label={{ value: 'Fuel-Corrected Pace (s)', angle: -90, position: 'insideLeft', fill: '#64748B' }}
                  />
                  <Tooltip
                    cursor={{ strokeDasharray: '3 3' }}
                    contentStyle={{ backgroundColor: '#0d0e12', borderColor: '#1e293b', color: '#fff' }}
                  />
                  <Legend verticalAlign="top" height={36}/>
                  <Scatter yAxisId="left" name="Actual Laps" data={refPlotData} fill="var(--neon-purple)" />
                  <Line
                    yAxisId="left"
                    data={refPlotData}
                    type="linear"
                    dataKey="trend_lap_time_s"
                    stroke="var(--error)"
                    name="OLS Trend"
                    dot={false}
                    strokeWidth={2}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="empty-state">No valid stint data for {referenceDriver}</div>
          )}
        </div>
      </div>
    </div>
  );
}
