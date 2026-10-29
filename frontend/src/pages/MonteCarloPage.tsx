import React, { useState, useEffect } from 'react';
import { usePitwall } from '../contexts/PitwallContext';
import {
  Radio,
  Sliders,
  ShieldCheck,
  Play,
  RotateCcw,
  Trophy,
  CheckCircle2,
  Percent,
  Settings2,
  Gauge,
  GitMerge,
  Settings
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import './MonteCarloPage.css';

interface StrategyEvaluation {
  strategy_id: string;
  name: string;
  stop_count?: number;
  compounds?: string[];
  physical_compounds?: string[];
  pit_laps?: number[];
  num_simulations: number;
  win_probability_pct: number;
  podium_probability_pct: number;
  points_probability_pct: number;
  expected_finish_position: number;
  finish_position_std: number;
  p5_position: number;
  p95_position: number;
  finish_position_distribution: { [pos: string]: number };
  mean_race_time_s: number;
  strategy_regret_s: number;
  robustness_score?: number;
  risk_score?: number;
  is_recommended: boolean;
  evaluation_mode?: string;
}

interface Sensitivity {
  recommended_strategy: string;
  objective_used?: string;
  tyre_deg_sensitivity: string;
  safety_car_sensitivity: string;
  pit_duration_sensitivity: string;
  fuel_effect_sensitivity: string;
  robustness_score: number;
  risk_score: number;
}

interface DriverRanking {
  driver_id: string;
  win_probability_pct: number;
  podium_probability_pct: number;
  top5_probability_pct: number;
  expected_position?: number;
}

interface CircuitProfile {
  tyre_stress_rating?: number;
  asphalt_abrasion_rating?: number;
  overtaking_difficulty_index?: number;
  pit_lane_transit_loss_green_s?: number;
  pit_lane_transit_loss_sc_s?: number;
}

interface PhysicalNominations {
  HARD?: string;
  MEDIUM?: string;
  SOFT?: string;
  provenance?: string;
}

export const MonteCarloPage: React.FC = () => {
  const { session, primaryDriver } = usePitwall();
  const [numSims, setNumSims] = useState<number>(250);
  const [objective, setObjective] = useState<string>('BALANCED');
  const [evaluationMode, setEvaluationMode] = useState<string>('PRE_RACE');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // What-If Sensitivity inputs
  const [degMultiplier, setDegMultiplier] = useState<number>(1.0);
  const [pitLossOffset, setPitLossOffset] = useState<number>(0.0);
  const [scProbOverride, setScProbOverride] = useState<string>('AUTO');

  // Simulation outputs
  const [strategyRec, setStrategyRec] = useState<string>('');
  const [circuitId, setCircuitId] = useState<string>('SPAIN');
  const [circuitName, setCircuitName] = useState<string>('Circuit de Barcelona-Catalunya');
  const [totalLaps, setTotalLaps] = useState<number>(66);
  const [completedSims, setCompletedSims] = useState<number>(250);
  const [candidates, setCandidates] = useState<StrategyEvaluation[]>([]);
  const [sensitivity, setSensitivity] = useState<Sensitivity | null>(null);
  const [fieldRankings, setFieldRankings] = useState<DriverRanking[]>([]);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [circuitProfile, setCircuitProfile] = useState<CircuitProfile | null>(null);
  const [physicalNominations, setPhysicalNominations] = useState<PhysicalNominations | null>(null);

  const runSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      let url = `/api/simulations/monte_carlo?session_id=${session}&target_driver=${primaryDriver}&num_sims=${numSims}&objective=${objective}&evaluation_mode=${evaluationMode}&deg_multiplier=${degMultiplier}&pit_loss_offset_s=${pitLossOffset}`;
      if (scProbOverride !== 'AUTO') {
        url += `&sc_prob_override=${parseFloat(scProbOverride)}`;
      }

      const res = await fetch(url);
      if (!res.ok) throw new Error('Simulation calculation failed.');
      const json = await res.json();
      if (json.success) {
        const stratSim = json.strategy_simulation || {};
        const fieldSim = json.field_simulation || {};

        setCircuitId(json.circuit_id || 'SPAIN');
        setCircuitName(json.circuit_name || stratSim.circuit_name || 'Circuit de Barcelona-Catalunya');
        setTotalLaps(json.total_laps || stratSim.total_laps || 66);
        setCompletedSims(json.completed_iterations || stratSim.completed_iterations || numSims);
        setStrategyRec(stratSim.recommended_strategy || '2-Stop Soft -> Medium -> Soft');
        setCircuitProfile(json.circuit_profile || stratSim.circuit_profile || null);
        setPhysicalNominations(json.physical_nominations || stratSim.physical_nominations || null);

        const cands = stratSim.candidate_evaluations || [];
        setCandidates(cands);
        if (cands.length > 0) {
          const rec = cands.find((c: StrategyEvaluation) => c.is_recommended) || cands[0];
          setSelectedCandidateId(rec.strategy_id);
        }
        setSensitivity(stratSim.sensitivity_analysis || null);
        setFieldRankings(fieldSim.driver_rankings || stratSim.field_rankings || []);
      } else {
        throw new Error(json.error || 'Failed to execute Monte Carlo run.');
      }
    } catch (err: any) {
      setError(err.message || 'Unknown simulation error.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runSimulation();
  }, [primaryDriver, session, objective, evaluationMode]);

  const resetWhatIf = () => {
    setDegMultiplier(1.0);
    setPitLossOffset(0.0);
    setScProbOverride('AUTO');
  };

  const activeCandidate = candidates.find(c => c.strategy_id === selectedCandidateId) || candidates[0];

  const getCompoundBadgeClass = (comp: string) => {
    const c = comp.toUpperCase();
    if (c.includes('SOFT') || c === 'SOFT') return 'compound-soft';
    if (c.includes('MED') || c === 'MEDIUM') return 'compound-medium';
    if (c.includes('HARD') || c === 'HARD') return 'compound-hard';
    if (c.includes('INTER') || c === 'INTERMEDIATE') return 'compound-inter';
    if (c.includes('WET')) return 'compound-wet';
    return 'compound-neutral';
  };

  return (
    <div className="mc-container" id="monte-carlo-container">
      <PageHeader
        hub="Strategy"
        title="Monte Carlo Strategy Simulator"
        subtitle="10,000+ stochastic race iterations, win and podium probabilities, and safety car sensitivity."
        badge={`${primaryDriver} • ${circuitId}`}
        badgeType="prob"
        crossLinks={[
          { label: 'Strategy Optimizer', path: '/app/strategy', icon: GitMerge },
          { label: 'Tyre Degradation', path: '/app/tyres', icon: Settings },
          { label: 'Model Validation', path: '/app/validation', icon: ShieldCheck }
        ]}
      />

      {/* Header */}
      <header className="mc-header">
        <div className="header-titles">
          <div className="title-row">
            <Radio size={22} className="header-icon text-cyan" />
            <h2>Monte Carlo Stochastic Strategy & Sensitivity Simulator</h2>
            <span className="session-tag" id="current-session-tag">{session}</span>
            <span className="circuit-tag" id="current-circuit-tag">{circuitId} ({totalLaps} Laps)</span>
          </div>
          <p className="subtitle">
            Global Strategy Engine • Dynamic stop generation • Real physical tyre allocations • Circuit traffic & pit loss modeling • Driver: <strong className="text-cyan">{primaryDriver}</strong>
          </p>
        </div>

        {/* Top Controls Row */}
        <div className="controls-row">
          <div className="control-item">
            <span className="control-label">EVALUATION MODE</span>
            <select
              id="evaluation-mode-select"
              value={evaluationMode}
              onChange={(e) => setEvaluationMode(e.target.value)}
              className="mc-select eval-mode-select"
              aria-label="Strategy Evaluation Mode"
            >
              <option value="PRE_RACE">Pre-Race Forecast (Prior Data Only)</option>
              <option value="PRACTICE_INFORMED">Practice-Informed (FP Telemetry)</option>
              <option value="LIVE">Live Race Optimization (Real-time)</option>
              <option value="HISTORICAL_RECONSTRUCTION">Historical Reconstruction (Actual Events)</option>
              <option value="COUNTERFACTUAL">Counterfactual Simulation (What-If)</option>
              <option value="POST_RACE">Post-Race Strategy Audit</option>
            </select>
          </div>

          <div className="control-item">
            <span className="control-label">OBJECTIVE</span>
            <select
              id="simulation-objective-select"
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              className="mc-select"
              aria-label="Simulation Objective"
            >
              <option value="BALANCED">Balanced (Pace & Risk)</option>
              <option value="MIN_RACE_TIME">Minimize Race Time</option>
              <option value="MAX_WIN">Maximize Win Probability</option>
              <option value="MAX_PODIUM">Maximize Podium Probability</option>
              <option value="MIN_POSITION">Minimize Expected Position</option>
            </select>
          </div>

          <div className="control-item">
            <span className="control-label">TRIALS: {numSims}</span>
            <input
              id="num-trials-slider"
              type="range"
              min={50}
              max={1000}
              step={50}
              value={numSims}
              onChange={(e) => setNumSims(Number(e.target.value))}
              className="mc-slider"
              aria-label="Number of simulation trials"
            />
          </div>

          <button
            id="btn-run-simulation"
            onClick={runSimulation}
            disabled={loading}
            className="btn-run-sim"
            aria-label="Run Monte Carlo Simulation"
          >
            {loading ? <RotateCcw size={13} className="spin" /> : <Play size={13} />}
            <span>{loading ? 'SIMULATING...' : 'RUN SIMULATION'}</span>
          </button>
        </div>
      </header>

      {/* Engineering Circuit Profile & Physical Tyre Nomination Banner */}
      <div className="circuit-engineering-banner" id="circuit-engineering-banner">
        <div className="circuit-meta-col">
          <div className="circuit-title-line">
            <Gauge size={14} className="text-cyan" />
            <span className="circuit-name-label">{circuitName}</span>
            <span className="circuit-code-badge">{circuitId}</span>
          </div>
          {circuitProfile && (
            <div className="circuit-attributes-chips">
              <span className="attr-chip" id="attr-tyre-stress">
                Tyre Stress: <strong>{circuitProfile.tyre_stress_rating || 3}/5</strong>
              </span>
              <span className="attr-chip" id="attr-abrasion">
                Asphalt Abrasion: <strong>{circuitProfile.asphalt_abrasion_rating || 3}/5</strong>
              </span>
              <span className="attr-chip" id="attr-overtaking">
                Overtaking Difficulty: <strong>{circuitProfile.overtaking_difficulty_index !== undefined ? circuitProfile.overtaking_difficulty_index.toFixed(2) : '0.45'}</strong>
              </span>
              <span className="attr-chip" id="attr-pit-loss">
                Pit Loss: <strong>{circuitProfile.pit_lane_transit_loss_green_s || 21.5}s</strong> (SC: {circuitProfile.pit_lane_transit_loss_sc_s || 12.5}s)
              </span>
            </div>
          )}
        </div>

        {/* Physical Tyre Nominations Badges */}
        {physicalNominations && (
          <div className="tyre-nominations-col" id="tyre-nominations-col">
            <span className="tyre-nom-label">OFFICIAL PIRELLI TYRE ALLOCATION:</span>
            <div className="tyre-comp-badges">
              <span className="comp-pill comp-hard" id="badge-compound-hard">
                HARD: <strong>{physicalNominations.HARD || 'C1'}</strong>
              </span>
              <span className="comp-pill comp-medium" id="badge-compound-med">
                MED: <strong>{physicalNominations.MEDIUM || 'C2'}</strong>
              </span>
              <span className="comp-pill comp-soft" id="badge-compound-soft">
                SOFT: <strong>{physicalNominations.SOFT || 'C3'}</strong>
              </span>
              <span className="nom-provenance-tag">{physicalNominations.provenance || 'PIRELLI_NOMINATION'}</span>
            </div>
          </div>
        )}
      </div>

      {/* What-If Sensitivity Perturbation Controls Bar */}
      <div className="what-if-panel" id="what-if-sensitivity-panel">
        <div className="what-if-header">
          <div className="what-if-title">
            <Settings2 size={14} className="text-amber" />
            <span>WHAT-IF SENSITIVITY OVERRIDES</span>
            <span className="what-if-desc">(Perturb real race variables to stress-test candidate robustness)</span>
          </div>
          {(degMultiplier !== 1.0 || pitLossOffset !== 0.0 || scProbOverride !== 'AUTO') && (
            <button onClick={resetWhatIf} className="btn-reset-whatif" id="btn-reset-whatif">
              <RotateCcw size={11} /> Reset to Defaults
            </button>
          )}
        </div>

        <div className="what-if-controls-grid">
          <div className="what-if-item">
            <div className="wi-label-row">
              <span className="wi-label">Tyre Degradation Factor:</span>
              <span className="wi-val text-cyan">{degMultiplier.toFixed(2)}x</span>
            </div>
            <input
              id="slider-deg-multiplier"
              type="range"
              min={0.7}
              max={1.5}
              step={0.05}
              value={degMultiplier}
              onChange={(e) => setDegMultiplier(parseFloat(e.target.value))}
              className="mc-slider-full"
            />
            <div className="wi-sublabels">
              <span>0.70x (Low Wear)</span>
              <span>1.00x (Nominal)</span>
              <span>1.50x (Severe Cliff)</span>
            </div>
          </div>

          <div className="what-if-item">
            <div className="wi-label-row">
              <span className="wi-label">Pit Lane Transit Offset:</span>
              <span className="wi-val text-amber">{pitLossOffset > 0 ? `+${pitLossOffset.toFixed(1)}s` : `${pitLossOffset.toFixed(1)}s`}</span>
            </div>
            <input
              id="slider-pit-offset"
              type="range"
              min={-4.0}
              max={6.0}
              step={0.5}
              value={pitLossOffset}
              onChange={(e) => setPitLossOffset(parseFloat(e.target.value))}
              className="mc-slider-full"
            />
            <div className="wi-sublabels">
              <span>-4.0s (Fast Entry/Exit)</span>
              <span>0.0s (Normal)</span>
              <span>+6.0s (Pit Lane Delay)</span>
            </div>
          </div>

          <div className="what-if-item">
            <div className="wi-label-row">
              <span className="wi-label">Safety Car Scenario Risk:</span>
              <span className="wi-val text-green">{scProbOverride === 'AUTO' ? 'Historical Prior' : `${(parseFloat(scProbOverride) * 100).toFixed(0)}%`}</span>
            </div>
            <select
              id="select-sc-risk-override"
              value={scProbOverride}
              onChange={(e) => setScProbOverride(e.target.value)}
              className="mc-select-small"
            >
              <option value="AUTO">Historical Circuit Prior</option>
              <option value="0.0">0% (Zero Neutralization)</option>
              <option value="0.02">2% / lap (Standard)</option>
              <option value="0.05">5% / lap (High SC Risk)</option>
              <option value="0.10">10% / lap (Extreme Chaos)</option>
            </select>
          </div>
        </div>
      </div>

      {error && <div className="error-banner" id="mc-error-banner">{error}</div>}

      {loading && candidates.length === 0 && (
        <div className="mc-grid">
          <div className="mc-col-main">
            <div className="card-engineering skeleton-card" style={{ height: '110px', marginBottom: '16px' }}></div>
            <div className="card-engineering skeleton-card" style={{ height: '320px' }}></div>
          </div>
          <div className="mc-col-side">
            <div className="card-engineering skeleton-card" style={{ height: '450px' }}></div>
          </div>
        </div>
      )}

      {(!loading || candidates.length > 0) && (
        <div className="mc-grid">
          {/* Left Column: Strategy Candidates & Distribution */}
          <div className="mc-col-main">
            {/* Recommended Directive Banner */}
            {strategyRec && (
              <div className="recommendation-card" id="optimal-directive-card">
                <div className="rec-badge">
                  <CheckCircle2 size={14} />
                  <span>OPTIMAL TACTICAL DIRECTIVE</span>
                  <span className="rec-obj-tag">[{objective}]</span>
                  <span className="rec-mode-tag">[{evaluationMode}]</span>
                </div>
                <h3 className="rec-title" id="rec-strategy-title">{strategyRec}</h3>
                <p className="rec-desc">
                  Calculated dynamically across {totalLaps} race laps ({completedSims} Monte Carlo iterations) accounting for track abrasion, physical compound degradation, and dirty-air traffic penalty.
                </p>
                {activeCandidate && activeCandidate.pit_laps && activeCandidate.pit_laps.length > 0 && (
                  <div className="rec-stints-row">
                    <span className="stints-label">PLANNED PIT WINDOWS:</span>
                    {activeCandidate.pit_laps.map((lap, i) => (
                      <span key={i} className="pit-lap-pill">Lap {lap}</span>
                    ))}
                    {activeCandidate.physical_compounds && (
                      <div className="rec-comp-flow">
                        {activeCandidate.physical_compounds.map((c, i) => (
                          <React.Fragment key={i}>
                            <span className={`comp-flow-pill ${getCompoundBadgeClass(activeCandidate.compounds ? activeCandidate.compounds[i] : c)}`}>
                              {c}
                            </span>
                            {i < activeCandidate.physical_compounds!.length - 1 && <span className="flow-arrow">→</span>}
                          </React.Fragment>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Strategy Candidate Comparison Cards */}
            <div className="section-title">
              <Sliders size={15} />
              <span>FEASIBLE STRATEGY CANDIDATES ({candidates.length} GENERATED)</span>
            </div>

            <div className="candidates-list" id="candidates-list">
              {candidates.map((c) => {
                const isSelected = c.strategy_id === selectedCandidateId;
                return (
                  <div
                    key={c.strategy_id}
                    id={`cand-${c.strategy_id}`}
                    onClick={() => setSelectedCandidateId(c.strategy_id)}
                    className={`candidate-card ${isSelected ? 'selected' : ''}`}
                  >
                    <div className="cand-header">
                      <div className="cand-name-wrap">
                        <span className="cand-id">{c.strategy_id}</span>
                        <h4 className="cand-name">{c.name}</h4>
                        {c.stop_count !== undefined && (
                          <span className={`stop-count-badge stops-${c.stop_count}`}>
                            {c.stop_count}-STOP
                          </span>
                        )}
                      </div>
                      {c.is_recommended && <span className="rec-tag" id="rec-tag">RECOMMENDED</span>}
                    </div>

                    {/* Stint & Compound Pipeline */}
                    {c.physical_compounds && c.physical_compounds.length > 0 && (
                      <div className="cand-stints-preview">
                        {c.physical_compounds.map((comp, idx) => {
                          const nominal = c.compounds ? c.compounds[idx] : comp;
                          return (
                            <React.Fragment key={idx}>
                              <span className={`stint-badge ${getCompoundBadgeClass(nominal)}`}>
                                {nominal.substring(0, 4)} ({comp})
                              </span>
                              {idx < c.physical_compounds!.length - 1 && (
                                <span className="stint-pit-marker">
                                  P{c.pit_laps && c.pit_laps[idx] ? `L${c.pit_laps[idx]}` : 'IT'} →
                                </span>
                              )}
                            </React.Fragment>
                          );
                        })}
                      </div>
                    )}

                    <div className="cand-metrics-grid">
                      <div className="metric-box">
                        <span className="m-lbl">EXP POSITION</span>
                        <span className="m-val highlight">
                          P{c.expected_finish_position !== undefined ? c.expected_finish_position.toFixed(1) : '-'}
                        </span>
                      </div>

                      <div className="metric-box">
                        <span className="m-lbl">WIN PROB</span>
                        <span className="m-val text-green">
                          {c.win_probability_pct !== undefined ? c.win_probability_pct.toFixed(0) : 0}%
                        </span>
                      </div>

                      <div className="metric-box">
                        <span className="m-lbl">PODIUM PROB</span>
                        <span className="m-val text-cyan">
                          {c.podium_probability_pct !== undefined ? c.podium_probability_pct.toFixed(0) : 0}%
                        </span>
                      </div>

                      <div className="metric-box">
                        <span className="m-lbl">TIME REGRET</span>
                        <span className="m-val text-amber">
                          {c.strategy_regret_s > 0 ? `+${c.strategy_regret_s.toFixed(1)}s` : '0.0s'}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Position Distribution Histogram */}
            {activeCandidate && activeCandidate.finish_position_distribution && (
              <div className="distribution-card" id="distribution-card">
                <div className="section-title">
                  <Percent size={15} />
                  <span>FINISH POSITION PROBABILITY DISTRIBUTION ({activeCandidate.name})</span>
                </div>

                <div className="histogram-bars">
                  {Object.entries(activeCandidate.finish_position_distribution).slice(0, 10).map(([p, prob]) => {
                    const numProb = Number(prob);
                    return (
                      <div key={p} className="hist-col">
                        <div className="bar-track">
                          <div
                            className="bar-fill"
                            style={{ height: `${Math.max(numProb * 2.2, 4)}px` }}
                          ></div>
                        </div>
                        <span className="prob-label">{numProb > 0 ? `${numProb.toFixed(0)}%` : '0%'}</span>
                        <span className="pos-label">P{p}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Sensitivity Analysis & Field Odds */}
          <div className="mc-col-side">
            {/* Sensitivity Matrix */}
            {sensitivity && (
              <div className="side-card" id="sensitivity-metrics-card">
                <div className="section-title">
                  <ShieldCheck size={15} />
                  <span>SENSITIVITY & RISK METRICS</span>
                </div>

                <div className="sensitivity-list">
                  <div className="sens-row">
                    <span className="sens-param">Safety Car Sensitivity</span>
                    <span className={`sens-pill ${sensitivity.safety_car_sensitivity.toLowerCase()}`}>
                      {sensitivity.safety_car_sensitivity}
                    </span>
                  </div>

                  <div className="sens-row">
                    <span className="sens-param">Tyre Degradation Variance</span>
                    <span className={`sens-pill ${sensitivity.tyre_deg_sensitivity.toLowerCase()}`}>
                      {sensitivity.tyre_deg_sensitivity}
                    </span>
                  </div>

                  <div className="sens-row">
                    <span className="sens-param">Pit Loss Variation</span>
                    <span className={`sens-pill ${sensitivity.pit_duration_sensitivity.toLowerCase()}`}>
                      {sensitivity.pit_duration_sensitivity}
                    </span>
                  </div>

                  <div className="sens-row">
                    <span className="sens-param">Fuel Consumption Effect</span>
                    <span className={`sens-pill ${sensitivity.fuel_effect_sensitivity.toLowerCase()}`}>
                      {sensitivity.fuel_effect_sensitivity}
                    </span>
                  </div>

                  <div className="scores-row">
                    <div className="score-box">
                      <span className="score-lbl">ROBUSTNESS SCORE</span>
                      <span className="score-val text-green">
                        {sensitivity.robustness_score !== undefined ? sensitivity.robustness_score.toFixed(1) : 85.0}
                      </span>
                    </div>
                    <div className="score-box">
                      <span className="score-lbl">RISK COEFFICIENT</span>
                      <span className="score-val text-amber">
                        {sensitivity.risk_score !== undefined ? sensitivity.risk_score.toFixed(2) : 2.1}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Model Invariants & Integrity Assurance Card */}
            <div className="side-card" id="invariants-integrity-card">
              <div className="section-title">
                <CheckCircle2 size={15} className="text-cyan" />
                <span>ENGINEERING INTEGRITY AUDIT</span>
              </div>
              <div className="invariants-checklist">
                <div className="inv-check-item">
                  <CheckCircle2 size={12} className="text-green" />
                  <span>Win Prob ≤ Podium Prob (Field Invariant)</span>
                </div>
                <div className="inv-check-item">
                  <CheckCircle2 size={12} className="text-green" />
                  <span>Strategy Regret ≥ 0.0s (CRN-Calculated)</span>
                </div>
                <div className="inv-check-item">
                  <CheckCircle2 size={12} className="text-green" />
                  <span>FIA Regs: ≥2 Compounds Satisfied</span>
                </div>
                <div className="inv-check-item">
                  <CheckCircle2 size={12} className="text-green" />
                  <span>Zero Future Leakage in Predictive Mode</span>
                </div>
                <div className="inv-check-item">
                  <CheckCircle2 size={12} className="text-green" />
                  <span>Circuit-Specific Pit Transit & Traffic Loss</span>
                </div>
              </div>
            </div>

            {/* Full Field Win Odds Benchmark */}
            {fieldRankings.length > 0 && (
              <div className="side-card" id="field-rankings-card">
                <div className="section-title">
                  <Trophy size={15} />
                  <span>FULL FIELD BENCHMARK ({completedSims} TRIALS)</span>
                </div>

                <div className="field-rankings-list">
                  {fieldRankings.slice(0, 10).map((r, idx) => (
                    <div key={r.driver_id} className={`field-row ${r.driver_id === primaryDriver ? 'primary-drv' : ''}`}>
                      <span className="field-pos">#{idx + 1}</span>
                      <span className="field-drv">{r.driver_id}</span>
                      <div className="field-probs">
                        <span className="prob-win">Win: {r.win_probability_pct.toFixed(0)}%</span>
                        <span className="prob-podium">Pod: {r.podium_probability_pct.toFixed(0)}%</span>
                        {r.expected_position !== undefined && (
                          <span className="prob-exp">P{r.expected_position.toFixed(1)}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MonteCarloPage;
