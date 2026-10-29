import React, { useState, useEffect } from 'react';
import {
  Database,
  Lock,
  Layers,
  ExternalLink,
  AlertOctagon,
  Cpu,
  RefreshCw
} from 'lucide-react';
import './ProvenancePage.css';

interface ProviderInfo {
  provider_id: string;
  display_name: string;
  doc_url: string;
  licensing: string;
  update_frequency: string;
  typical_latency_s: number;
  supported_domains: string[];
  rate_limit_policy: string;
  authenticity_level: string;
  description: string;
}

interface ProvenanceSummary {
  providers: Record<string, ProviderInfo>;
  channels_count: number;
  confidential_boundaries: string[];
  classification_definitions: Record<string, string>;
}

export const ProvenancePage: React.FC = () => {
  const [data, setData] = useState<ProvenanceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    fetch('/api/provenance/summary')
      .then(res => res.json())
      .then(json => {
        if (!mounted) return;
        setData(json);
        setError(null);
      })
      .catch(err => {
        if (!mounted) return;
        setError(err.message || 'Failed to fetch data provenance registry');
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => { mounted = false; };
  }, []);

  if (loading && !data) {
    return (
      <div className="provenance-container" style={{ padding: '40px', textAlign: 'center', color: '#64748B' }}>
        <RefreshCw size={24} className="spin text-cyan" style={{ margin: '0 auto 12px' }} />
        <p>Synchronizing data provenance and source specifications...</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="provenance-container" style={{ padding: '40px', textAlign: 'center', color: '#EF4444' }}>
        <p>{error}</p>
      </div>
    );
  }

  const classifications = [
    {
      tier: 'MEASURED',
      badgeClass: 'badge-measured',
      desc: 'Direct sensor readings from official timing & broadcast car telemetry.',
      examples: 'Wheel Speed (km/h), Throttle %, Brake Flag, Crankshaft RPM, nGear, Air/Track Temp, Transponder Lap Times'
    },
    {
      tier: 'DERIVED',
      badgeClass: 'badge-derived',
      desc: 'Deterministic mathematical and physical calculations strictly derived from measurements.',
      examples: 'Longitudinal Accel ax = dv/dt (g), Lateral Accel ay = v²/R (g), Distance Delta t (s), Curvature kappa, Micro-Sector Splits'
    },
    {
      tier: 'ESTIMATED',
      badgeClass: 'badge-estimated',
      desc: 'Statistical regressions, machine learning inference, and empirical tyre wear rates.',
      examples: 'Tyre Degradation Slope beta (s/lap), Fuel-Corrected Pace, Compound Crossover Laps, Stint Life Limit'
    },
    {
      tier: 'HYPOTHETICAL',
      badgeClass: 'badge-hypothetical',
      desc: 'Counterfactual what-if scenarios and stochastic outcome distributions.',
      examples: 'Theoretical Ideal Lap Reconstruction, Alternative Pit Stop Strategies, Monte Carlo Finishing Distributions'
    },
    {
      tier: 'UNAVAILABLE',
      badgeClass: 'badge-unavailable',
      desc: 'Proprietary or confidential telemetry strictly protected by Formula One teams.',
      examples: 'Suspension travel, damper velocities, internal tyre carcass temps, real-time fuel mass flow, ERS cell SOC'
    }
  ];

  return (
    <div className="provenance-container">
      {/* Header */}
      <header className="provenance-header">
        <div className="header-titles">
          <div className="title-row">
            <Database size={22} className="header-icon text-cyan" />
            <h2>Data Provenance & Engineering Boundaries Registry</h2>
            <span className="provenance-pill green">AUTHORITATIVE FOM & FIA SOURCES</span>
          </div>
          <p className="subtitle">
            Formal architectural pedigree, data classification tiers, upstream provider specifications, and confidential boundaries.
          </p>
        </div>
      </header>

      {/* 5-Tier Data Pedigree Standards */}
      <div className="card-engineering">
        <div className="panel-header">
          <Layers size={16} className="panel-icon text-cyan" />
          <h3>5-Tier Engineering Classification Hierarchy</h3>
        </div>

        <div className="tiers-grid">
          {classifications.map((c) => (
            <div key={c.tier} className="tier-card">
              <div className="tier-top">
                <span className={`tier-badge ${c.badgeClass}`}>{c.tier}</span>
              </div>
              <p className="tier-desc">{c.desc}</p>
              <div className="tier-examples">
                <span className="ex-label">CHANNELS:</span>
                <span className="ex-val">{c.examples}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Upstream Providers Matrix */}
      <div className="card-engineering">
        <div className="panel-header">
          <Cpu size={16} className="panel-icon text-cyan" />
          <h3>Upstream Provider Architecture & Provenance Matrix</h3>
        </div>

        <div className="providers-grid">
          {data?.providers && Object.values(data.providers).map((p) => (
            <div key={p.provider_id} className="provider-card">
              <div className="p-header">
                <div className="p-title-wrap">
                  <span className="p-id">{p.provider_id}</span>
                  <span className="p-name">{p.display_name}</span>
                </div>
                <a href={p.doc_url} target="_blank" rel="noreferrer" className="doc-link">
                  <ExternalLink size={12} />
                  <span>DOCS</span>
                </a>
              </div>

              <p className="p-desc">{p.description}</p>

              <div className="p-specs">
                <div className="spec-row">
                  <span>Licensing:</span>
                  <span className="spec-val">{p.licensing}</span>
                </div>
                <div className="spec-row">
                  <span>Update Frequency:</span>
                  <span className="spec-val">{p.update_frequency}</span>
                </div>
                <div className="spec-row">
                  <span>Latency:</span>
                  <span className="spec-val text-green">~{p.typical_latency_s}s</span>
                </div>
                <div className="spec-row">
                  <span>Rate Limit:</span>
                  <span className="spec-val">{p.rate_limit_policy}</span>
                </div>
                <div className="spec-row">
                  <span>Authority:</span>
                  <span className="spec-val text-cyan">{p.authenticity_level}</span>
                </div>
              </div>

              <div className="p-domains">
                {p.supported_domains.map((dom, i) => (
                  <span key={i} className="domain-tag">{dom}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Confidentiality Boundaries & Technical Limitations */}
      <div className="card-engineering confidential-card">
        <div className="panel-header">
          <Lock size={16} className="panel-icon text-red" />
          <h3 className="text-red">Confidentiality Boundaries — Protected F1 Team Telemetry</h3>
        </div>

        <p className="confidential-lead">
          Pitwall F1 maximizes engineering intelligence from verified public sources. In accordance with technical integrity standards,
          the platform explicitly <strong>refuses to fabricate or simulate fake telemetry</strong> for confidential engineering parameters:
        </p>

        <div className="boundaries-list">
          {data?.confidential_boundaries ? (
            data.confidential_boundaries.map((boundary, idx) => (
              <div key={idx} className="boundary-item">
                <AlertOctagon size={14} className="b-icon text-red" />
                <span>{boundary}</span>
              </div>
            ))
          ) : (
            <>
              <div className="boundary-item">
                <AlertOctagon size={14} className="b-icon text-red" />
                <span>Suspension kinematics, spring rates, roll bar stiffness, and damper stroke telemetry.</span>
              </div>
              <div className="boundary-item">
                <AlertOctagon size={14} className="b-icon text-red" />
                <span>Aerodynamic downforce (Cl*A) and drag (Cd*A) look-up tables in engineering units.</span>
              </div>
              <div className="boundary-item">
                <AlertOctagon size={14} className="b-icon text-red" />
                <span>Internal tyre carcass temperature, tyre cavity air pressure, and contact patch thermal maps.</span>
              </div>
              <div className="boundary-item">
                <AlertOctagon size={14} className="b-icon text-red" />
                <span>Engine combustion chamber pressure, air-fuel ratio (lambda), and instant fuel mass flow.</span>
              </div>
              <div className="boundary-item">
                <AlertOctagon size={14} className="b-icon text-red" />
                <span>Hybrid battery cell State-of-Charge (SOC), MGU-K electrical torque curves, and power unit maps.</span>
              </div>
              <div className="boundary-item">
                <AlertOctagon size={14} className="b-icon text-red" />
                <span>Confidential car setup sheets: toe, camber, brake bias migration tables, and ballast distribution.</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProvenancePage;
