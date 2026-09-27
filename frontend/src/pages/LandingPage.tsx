import { Link } from 'react-router-dom';
import { ChevronRight, Activity, Zap, BarChart2 } from 'lucide-react';
import './LandingPage.css';

export default function LandingPage() {
  return (
    <div className="landing-container">
      <header className="landing-header">
        <div className="logo">
          Pitwall <span className="logo-accent">F1</span>
        </div>
        <nav>
          <Link to="/app" className="btn btn-primary">
            Enter Pitwall <ChevronRight size={16} style={{ marginLeft: 4 }} />
          </Link>
        </nav>
      </header>

      <main className="landing-hero flex-col items-center">
        <div className="badge badge-purple" style={{ marginBottom: '1rem' }}>
          Phase 1 Modernization Active
        </div>
        <h1 className="hero-title">
          Authoritative Race <br />
          <span className="hero-accent">Engineering Intelligence</span>
        </h1>
        <p className="hero-subtitle">
          Advanced telemetry analysis, probabilistic Monte Carlo strategy,
          and AI-driven race engineering insights built for F1 performance analysis.
        </p>

        <div className="hero-actions">
          <Link to="/app" className="btn btn-primary" style={{ fontSize: '1.1rem', padding: '0.75rem 1.5rem' }}>
            Initialize Environment
          </Link>
        </div>

        <div className="features-grid grid grid-cols-3 gap-lg">
          <div className="feature-card card">
            <Activity size={32} className="feature-icon" />
            <h3>Telemetry Pipeline</h3>
            <p>10-stage automated ingestion with spatial-alignment and corner time-loss attribution.</p>
          </div>
          <div className="feature-card card">
            <Zap size={32} className="feature-icon" />
            <h3>Monte Carlo Engine</h3>
            <p>Full-field 20-car simulations running 100,000+ stochastic branches for strategy optimization.</p>
          </div>
          <div className="feature-card card">
            <BarChart2 size={32} className="feature-icon" />
            <h3>Tyre Intelligence</h3>
            <p>Bayesian degradation modeling with probabilistic crossover forecasting.</p>
          </div>
        </div>
      </main>
    </div>
  );
}
