import { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import AppLayout from './layouts/AppLayout';
import { PitwallProvider } from './contexts/PitwallContext';

// Primary 1: Home
const HomePage = lazy(() => import('./pages/HomePage'));

// Primary 2: Race Weekend Tools
const LivePage = lazy(() => import('./pages/LivePage').then(m => ({ default: m.LivePage })));
const CommandCenterPage = lazy(() => import('./pages/CommandCenterPage').then(m => ({ default: m.CommandCenterPage })));
const ReplayPage = lazy(() => import('./pages/ReplayPage').then(m => ({ default: m.ReplayPage })));

// Primary 3: Performance Tools
const OverviewPage = lazy(() => import('./pages/OverviewPage'));
const TelemetryPage = lazy(() => import('./pages/TelemetryPage'));
const ComparisonPage = lazy(() => import('./pages/ComparisonPage'));
const MLLabPage = lazy(() => import('./pages/MLLabPage').then(m => ({ default: m.MLLabPage })));

// Primary 4: Strategy Tools
const StrategyPage = lazy(() => import('./pages/StrategyPage'));
const MonteCarloPage = lazy(() => import('./pages/MonteCarloPage').then(m => ({ default: m.MonteCarloPage })));
const TyresPage = lazy(() => import('./pages/TyresPage'));

// Primary 5: AI Engineer
const JarvisPage = lazy(() => import('./pages/JarvisPage').then(m => ({ default: m.JarvisPage })));

// Primary 6: Data & History Tools
const CircuitsPage = lazy(() => import('./pages/CircuitsPage').then(m => ({ default: m.CircuitsPage })));
const DriversPage = lazy(() => import('./pages/DriversPage').then(m => ({ default: m.DriversPage })));
const ModelValidationPage = lazy(() => import('./pages/ModelValidationPage').then(m => ({ default: m.ModelValidationPage })));
const ProvenancePage = lazy(() => import('./pages/ProvenancePage').then(m => ({ default: m.ProvenancePage })));

const LoadingScreen = () => (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', width: '100vw', background: '#0a0a0a', color: '#E10600' }}>
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
      <div className="spinner" style={{ width: '40px', height: '40px', border: '3px solid rgba(225, 6, 0, 0.3)', borderTop: '3px solid #E10600', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
      <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
      <span style={{ fontFamily: 'Inter, sans-serif', fontWeight: 600, letterSpacing: '0.1em' }}>LOADING MODULE...</span>
    </div>
  </div>
);

function App() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        
        {/* Main Application with Global Race Context */}
        <Route path="/app" element={<PitwallProvider><AppLayout /></PitwallProvider>}>
          {/* Primary Destination 1: Home (Orientation & Next Actions) */}
          <Route index element={<HomePage />} />
          <Route path="home" element={<HomePage />} />

          {/* Primary Destination 2: Race Weekend */}
          <Route path="live" element={<LivePage />} />
          <Route path="command-center" element={<CommandCenterPage />} />
          <Route path="replay" element={<ReplayPage />} />
          <Route path="race-weekend" element={<LivePage />} />
          <Route path="race-weekend/live" element={<LivePage />} />
          <Route path="race-weekend/command-center" element={<CommandCenterPage />} />
          <Route path="race-weekend/replay" element={<ReplayPage />} />

          {/* Primary Destination 3: Performance */}
          <Route path="overview" element={<OverviewPage />} />
          <Route path="telemetry" element={<TelemetryPage />} />
          <Route path="comparison" element={<ComparisonPage />} />
          <Route path="ml-lab" element={<MLLabPage />} />
          <Route path="performance" element={<OverviewPage />} />
          <Route path="performance/overview" element={<OverviewPage />} />
          <Route path="performance/telemetry" element={<TelemetryPage />} />
          <Route path="performance/comparison" element={<ComparisonPage />} />
          <Route path="performance/ml-lab" element={<MLLabPage />} />

          {/* Primary Destination 4: Strategy */}
          <Route path="strategy" element={<StrategyPage />} />
          <Route path="monte-carlo" element={<MonteCarloPage />} />
          <Route path="tyres" element={<TyresPage />} />
          <Route path="strategy-hub" element={<StrategyPage />} />
          <Route path="strategy/optimizer" element={<StrategyPage />} />
          <Route path="strategy/monte-carlo" element={<MonteCarloPage />} />
          <Route path="strategy/tyres" element={<TyresPage />} />

          {/* Primary Destination 5: AI Engineer */}
          <Route path="jarvis" element={<JarvisPage />} />
          <Route path="ai-engineer" element={<JarvisPage />} />

          {/* Primary Destination 6: Data & History */}
          <Route path="circuits" element={<CircuitsPage />} />
          <Route path="drivers" element={<DriversPage />} />
          <Route path="validation" element={<ModelValidationPage />} />
          <Route path="provenance" element={<ProvenancePage />} />
          <Route path="data-history" element={<CircuitsPage />} />
          <Route path="data-history/circuits" element={<CircuitsPage />} />
          <Route path="data-history/drivers" element={<DriversPage />} />
          <Route path="data-history/validation" element={<ModelValidationPage />} />
          <Route path="data-history/provenance" element={<ProvenancePage />} />
        </Route>
      </Routes>
    </Suspense>
  );
}

export default App;
