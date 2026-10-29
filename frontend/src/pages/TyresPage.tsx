import { useState, useEffect } from 'react';
import { usePitwall } from '../contexts/PitwallContext';
import { Target, CircleDashed, RefreshCw, GitMerge, Radio, BarChart2 } from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
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
    setProgressMsg('Connecting to Telemetry Ingestion Pipeline...');

    const progressInterval = setInterval(() => {
      setProgressMsg(prev => {
        if (prev.includes('Connecting')) return 'Fetching Tyre Stint Arrays (Applying Bayesian Cache)...';
        if (prev.includes('Fetching')) return 'Executing Ordinary Least Squares Degradation Regression...';
        return prev;
      });
    }, 8000);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    fetch(`/api/tyres/degradation?session_id=${session}&primary_driver=${primaryDriver}&ref_driver=${referenceDriver}`, { signal: controller.signal })
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
          setError('Request Timed Out. Server is loading telemetry cache.');
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
      <div className="tyres-container">
        <header className="tyres-header">
          <div className="header-titles">
            <div className="title-row">
              <CircleDashed size={20} className="header-icon text-cyan" />
              <h2>Tyre Degradation Modeling</h2>
              <span className="session-tag">{session}</span>
            </div>
            <p className="subtitle">{progressMsg}</p>
          </div>
          <div className="badge badge-cyan">
            <RefreshCw size={11} className="spin" />
            <span>SOLVING REGRESSION</span>
          </div>
        </header>

        <div className="tyres-grid">
          <div className="card-engineering tyre-chart-card" style={{ height: '340px' }}>
            <div className="skeleton" style={{ width: '220px', height: '16px', marginBottom: '14px' }}></div>
            <div className="skeleton" style={{ width: '100%', height: '260px' }}></div>
          </div>
          <div className="card-engineering tyre-chart-card" style={{ height: '340px' }}>
            <div className="skeleton" style={{ width: '220px', height: '16px', marginBottom: '14px' }}></div>
            <div className="skeleton" style={{ width: '100%', height: '260px' }}></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="tyres-error">
        <Target size={44} className="error-icon" />
        <h2>Degradation Modeling Unavailable</h2>
        <p>{error}</p>
        <button className="btn-retry" onClick={() => window.location.reload()}>Retry Connection</button>
      </div>
    );
  }

  if (!data) return null;

  const pData = data.primary_driver || {};
  const rData = data.reference_driver || {};

  const primaryPlotData = pData.success ? pData.data_points : [];
  const refPlotData = rData.success ? rData.data_points : [];

  const getCompoundColor = (compound?: string) => {
    switch (compound?.toUpperCase()) {
      case 'SOFT': return '#EF4444';
      case 'MEDIUM': return '#F59E0B';
      case 'HARD': return '#F8FAFC';
      case 'INTERMEDIATE': return '#10B981';
      case 'WET': return '#38BDF8';
      default: return '#94A3B8';
    }
  };

  return (
    <div className="tyres-container">
      <PageHeader
        hub="Strategy"
        title="Tyre Degradation & Thermal Physics"
        subtitle="Fuel-corrected lap time degradation curves, wear slopes, and 3-layer thermal stint models."
        badge={`${primaryDriver} vs ${referenceDriver}`}
        badgeType="gold"
        crossLinks={[
          { label: 'Strategy Optimizer', path: '/app/strategy', icon: GitMerge },
          { label: 'Monte Carlo Simulator', path: '/app/monte-carlo', icon: Radio },
          { label: 'Telemetry Stack', path: '/app/telemetry', icon: BarChart2 }
        ]}
      />

      {/* Header */}
      <header className="tyres-header" style={{ marginBottom: '16px' }}>

        <div className="header-stats">
          <div className="stat-pill primary">
            <span className="pill-label">{primaryDriver} DEG:</span>
            <span className="pill-val">+{pData.degradation_slope_s_per_lap || '0.000'} s/lap</span>
          </div>
          <div className="stat-pill comparison">
            <span className="pill-label">{referenceDriver} DEG:</span>
            <span className="pill-val">+{rData.degradation_slope_s_per_lap || '0.000'} s/lap</span>
          </div>
        </div>
      </header>

      {/* Degradation Chart Panels */}
      <div className="tyre-charts-grid">
        {/* Primary Driver */}
        <div className="card-engineering chart-panel">
          <div className="chart-header">
            <div className="driver-stint-meta">
              <span className="driver-tag primary">{primaryDriver}</span>
              <span className="compound-badge" style={{ borderColor: getCompoundColor(pData.compound), color: getCompoundColor(pData.compound) }}>
                {pData.compound || 'MEDIUM'}
              </span>
              <span className="stint-tag">STINT {pData.stint_number || 1}</span>
            </div>
            <span className="slope-tag">Slope: +{pData.degradation_slope_s_per_lap || '0.00'}s / lap</span>
          </div>

          {pData.success && primaryPlotData.length > 0 ? (
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={primaryPlotData} margin={{ top: 15, right: 15, bottom: 20, left: 10 }}>
                  <CartesianGrid strokeDasharray="2 2" stroke="rgba(255,255,255,0.06)" />
                  <XAxis
                    dataKey="tyre_age"
                    type="number"
                    stroke="#64748B"
                    fontSize={10}
                    label={{ value: 'Tyre Age (Laps)', position: 'insideBottom', offset: -10, fill: '#64748B', fontSize: 10, fontFamily: 'JetBrains Mono' }}
                  />
                  <YAxis
                    dataKey="fuel_corrected_lap_time_s"
                    type="number"
                    stroke="#64748B"
                    fontSize={10}
                    domain={['dataMin - 0.5', 'dataMax + 0.5']}
                    tickFormatter={(val) => `${val.toFixed(1)}s`}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0B0E14', borderColor: 'rgba(255,255,255,0.15)', color: '#F8FAFC', borderRadius: '4px', fontSize: '11px', fontFamily: 'JetBrains Mono' }}
                    labelFormatter={(val) => `Lap Age: ${val} Laps`}
                  />
                  <Legend verticalAlign="top" height={30} wrapperStyle={{ fontSize: '11px', fontFamily: 'JetBrains Mono' }} />
                  <Scatter name="Observed Laps" dataKey="fuel_corrected_lap_time_s" fill="#00F5D4" />
                  <Line
                    type="linear"
                    dataKey="trend_lap_time_s"
                    stroke="#10B981"
                    name="OLS Wear Slope"
                    dot={false}
                    strokeWidth={2}
                    isAnimationActive={false}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="empty-state">
              <p>No valid single-compound stint data available for {primaryDriver} in this session.</p>
            </div>
          )}
        </div>

        {/* Reference Driver */}
        <div className="card-engineering chart-panel">
          <div className="chart-header">
            <div className="driver-stint-meta">
              <span className="driver-tag reference">{referenceDriver}</span>
              <span className="compound-badge" style={{ borderColor: getCompoundColor(rData.compound), color: getCompoundColor(rData.compound) }}>
                {rData.compound || 'MEDIUM'}
              </span>
              <span className="stint-tag">STINT {rData.stint_number || 1}</span>
            </div>
            <span className="slope-tag">Slope: +{rData.degradation_slope_s_per_lap || '0.00'}s / lap</span>
          </div>

          {rData.success && refPlotData.length > 0 ? (
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={refPlotData} margin={{ top: 15, right: 15, bottom: 20, left: 10 }}>
                  <CartesianGrid strokeDasharray="2 2" stroke="rgba(255,255,255,0.06)" />
                  <XAxis
                    dataKey="tyre_age"
                    type="number"
                    stroke="#64748B"
                    fontSize={10}
                    label={{ value: 'Tyre Age (Laps)', position: 'insideBottom', offset: -10, fill: '#64748B', fontSize: 10, fontFamily: 'JetBrains Mono' }}
                  />
                  <YAxis
                    dataKey="fuel_corrected_lap_time_s"
                    type="number"
                    stroke="#64748B"
                    fontSize={10}
                    domain={['dataMin - 0.5', 'dataMax + 0.5']}
                    tickFormatter={(val) => `${val.toFixed(1)}s`}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0B0E14', borderColor: 'rgba(255,255,255,0.15)', color: '#F8FAFC', borderRadius: '4px', fontSize: '11px', fontFamily: 'JetBrains Mono' }}
                    labelFormatter={(val) => `Lap Age: ${val} Laps`}
                  />
                  <Legend verticalAlign="top" height={30} wrapperStyle={{ fontSize: '11px', fontFamily: 'JetBrains Mono' }} />
                  <Scatter name="Observed Laps" dataKey="fuel_corrected_lap_time_s" fill="#F59E0B" />
                  <Line
                    type="linear"
                    dataKey="trend_lap_time_s"
                    stroke="#EF4444"
                    name="OLS Wear Slope"
                    dot={false}
                    strokeWidth={2}
                    isAnimationActive={false}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="empty-state">
              <p>No valid single-compound stint data available for {referenceDriver} in this session.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
