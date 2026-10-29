import { useState, useEffect } from 'react';
import { usePitwall } from '../contexts/PitwallContext';
import { Target, GitMerge, AlertTriangle, RefreshCw, Radio, Download, Settings, Sparkles } from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import './StrategyPage.css';

export default function StrategyPage() {
  const { session, primaryDriver, referenceDriver } = usePitwall();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    fetch(`/api/strategy/simulation?session_id=${session}&primary_driver=${primaryDriver}&ref_driver=${referenceDriver}`)
      .then(r => r.json())
      .then(res => {
        if (!mounted) return;
        if (res.success === false) {
          setError(res.error || 'Failed to fetch strategy simulation');
        } else {
          setData(res);
          setError('');
        }
      })
      .catch(err => {
        if (!mounted) return;
        console.error(err);
        setError('Network error fetching strategy simulation');
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => { mounted = false; };
  }, [session, primaryDriver, referenceDriver]);

  if (loading && !data) {
    return (
      <div className="strategy-container">
        <header className="strategy-header">
          <div className="header-titles">
            <div className="title-row">
              <GitMerge size={20} className="header-icon text-cyan" />
              <h2>Stint & Undercut Strategy Optimizer</h2>
              <span className="session-tag">{session}</span>
            </div>
            <p className="subtitle">
              Evaluating pit-stop delta windows and tire warm-up models for {primaryDriver} vs {referenceDriver}...
            </p>
          </div>
          <div className="badge badge-cyan">
            <RefreshCw size={11} className="spin" />
            <span>CALCULATING DELTA WINDOWS</span>
          </div>
        </header>

        <div className="strat-panels-grid">
          <div className="card-engineering strat-card" style={{ height: '220px' }}>
            <div className="skeleton" style={{ width: '220px', height: '16px', marginBottom: '16px' }}></div>
            <div className="skeleton" style={{ width: '80px', height: '36px', marginBottom: '14px' }}></div>
            <div className="skeleton" style={{ width: '100%', height: '8px', marginBottom: '16px' }}></div>
            <div className="skeleton" style={{ width: '100%', height: '30px' }}></div>
          </div>
          <div className="card-engineering strat-card" style={{ height: '220px' }}>
            <div className="skeleton" style={{ width: '220px', height: '16px', marginBottom: '16px' }}></div>
            <div className="skeleton" style={{ width: '80px', height: '36px', marginBottom: '14px' }}></div>
            <div className="skeleton" style={{ width: '100%', height: '8px', marginBottom: '16px' }}></div>
            <div className="skeleton" style={{ width: '100%', height: '30px' }}></div>
          </div>
        </div>

        <div className="card-engineering directive-card directive-box" style={{ height: '120px', marginTop: '16px' }}>
          <div className="skeleton" style={{ width: '240px', height: '16px', marginBottom: '12px' }}></div>
          <div className="skeleton" style={{ width: '100%', height: '40px' }}></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="strategy-error">
        <Target size={44} className="error-icon" />
        <h2>Strategy Simulation Failed</h2>
        <p>{error}</p>
        <button className="btn-retry" onClick={() => window.location.reload()}>Retry Connection</button>
      </div>
    );
  }

  if (!data) return null;

  const sim = data.synthetic_scenario || {};
  const undercutProb = Number(data.undercut_success_probability || 0) * 100;
  const overcutProb = Number(data.overcut_success_probability || 0) * 100;
  const isUndercutFavorable = undercutProb > overcutProb;

  return (
    <div className="strategy-container">
      <PageHeader
        hub="Strategy"
        title="Strategy Optimizer & Undercut Planner"
        subtitle="1-stop vs 2-stop stint evaluation, pit loss windows, undercut calculations, and tyre crossover."
        badge={`${primaryDriver} vs ${referenceDriver}`}
        badgeType="prob"
        crossLinks={[
          { label: 'Monte Carlo Simulator', path: '/app/monte-carlo', icon: Radio },
          { label: 'Tyre Degradation', path: '/app/tyres', icon: Settings },
          { label: 'Ask JARVIS', path: '/app/jarvis', icon: Sparkles }
        ]}
      />

      {/* Header */}
      <header className="strategy-header" style={{ marginBottom: '16px' }}>

        <div className="header-stats">
          <div className="stat-pill">
            <span className="pill-label">LIVE TRACK GAP:</span>
            <span className="pill-val text-red">{sim.current_gap_s || '0.00'}s</span>
          </div>
          <div className="stat-pill">
            <span className="pill-label">HEAD-TO-HEAD:</span>
            <span className="pill-val">{primaryDriver} vs {referenceDriver}</span>
          </div>
          <a
            href={`/api/reports/strategy/export?session_id=${session}&primary_driver=${primaryDriver}&ref_driver=${referenceDriver}`}
            download={`strategy_brief_${session}_${primaryDriver}_vs_${referenceDriver}.json`}
            className="stat-pill"
            style={{ textDecoration: 'none', cursor: 'pointer', background: 'rgba(0, 240, 255, 0.1)', border: '1px solid rgba(0, 240, 255, 0.3)' }}
            title="Download strategic engineering advisory JSON"
          >
            <Download size={13} className="text-cyan" style={{ marginRight: '6px' }} />
            <span className="pill-val text-cyan">EXPORT BRIEF</span>
          </a>
        </div>
      </header>

      {/* Undercut vs Overcut Probability Panels */}
      <div className="strat-panels-grid">
        {/* Undercut Card */}
        <div className="card-engineering strat-card">
          <div className="strat-card-header">
            <h3>Undercut Viability ({primaryDriver} Pits First)</h3>
            {undercutProb > 50 && <AlertTriangle size={16} className="text-gold" />}
          </div>

          <div className="prob-display">
            <span className="prob-label">Success Probability</span>
            <span className={`prob-value ${undercutProb > 50 ? 'favorable' : 'unfavorable'}`}>
              {undercutProb.toFixed(1)}%
            </span>
          </div>

          <div className="progress-bar-wrap">
            <div
              className={`progress-fill ${undercutProb > 50 ? 'green' : 'red'}`}
              style={{ width: `${Math.min(undercutProb, 100)}%` }}
            ></div>
          </div>

          <div className="strat-metrics">
            <div className="metric-row">
              <span className="row-label">Expected Time Gain / Lap</span>
              <span className="row-val">+{Number(data.expected_undercut_time_gain_s || 0).toFixed(2)}s</span>
            </div>
            <div className="metric-row">
              <span className="row-label">Delta Target</span>
              <span className="row-val">{Number(data.expected_undercut_time_gain_s || 0) > 1.2 ? 'Critical Opportunity' : 'Marginal Gain'}</span>
            </div>
          </div>
        </div>

        {/* Overcut Card */}
        <div className="card-engineering strat-card">
          <div className="strat-card-header">
            <h3>Overcut Viability ({primaryDriver} Extends Stint)</h3>
          </div>

          <div className="prob-display">
            <span className="prob-label">Success Probability</span>
            <span className={`prob-value ${overcutProb > 50 ? 'favorable' : 'unfavorable'}`}>
              {overcutProb.toFixed(1)}%
            </span>
          </div>

          <div className="progress-bar-wrap">
            <div
              className={`progress-fill ${overcutProb > 50 ? 'green' : 'red'}`}
              style={{ width: `${Math.min(overcutProb, 100)}%` }}
            ></div>
          </div>

          <div className="strat-metrics">
            <div className="metric-row">
              <span className="row-label">Expected Overcut Gain</span>
              <span className="row-val">+{Number(data.expected_overcut_time_gain_s || 0).toFixed(2)}s</span>
            </div>
            <div className="metric-row">
              <span className="row-label">Delta Target</span>
              <span className="row-val">{Number(data.expected_overcut_time_gain_s || 0) > 1.0 ? 'High Out-lap Value' : 'Standard Deg'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tactical Engineering Directive Box */}
      <div className="card-engineering directive-card directive-box">
        <div className="directive-header">
          <Radio size={16} className="text-cyan" />
          <h3>Tactical Race Engineer Advisory</h3>
        </div>

        <div className="directive-body">
          <div className="directive-action-tag">
            RECOMMENDATION: {isUndercutFavorable ? `TRIGGER UNDERCUT WINDOW` : `EXTEND STINT FOR OVERCUT`}
          </div>
          <p className="directive-narrative">
            Based on stochastic track gap evaluation ({sim.current_gap_s || '0.00'}s) and fuel-corrected tyre life curves,
            {isUndercutFavorable
              ? ` box ${primaryDriver} to undercut ${referenceDriver}. The fresh tire delta yields an estimated net gain of +${Number(data.expected_undercut_time_gain_s || 0).toFixed(2)}s over the reference car out-lap.`
              : ` preserve tire temperature and extend current stint. The undercut delta is insufficient to overcome pit loss penalty.`}
          </p>
        </div>
      </div>
    </div>
  );
}
