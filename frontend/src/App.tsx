import { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import AppLayout from './layouts/AppLayout';
import { PitwallProvider } from './contexts/PitwallContext';

const OverviewPage = lazy(() => import('./pages/OverviewPage'));
const TelemetryPage = lazy(() => import('./pages/TelemetryPage'));
const ComparisonPage = lazy(() => import('./pages/ComparisonPage'));
const TyresPage = lazy(() => import('./pages/TyresPage'));
const StrategyPage = lazy(() => import('./pages/StrategyPage'));
const PlaceholderPage = lazy(() => import('./pages/PlaceholderPage'));
const ReplayPage = lazy(() => import('./pages/ReplayPage').then(m => ({ default: m.ReplayPage })));
const MLLabPage = lazy(() => import('./pages/MLLabPage').then(m => ({ default: m.MLLabPage })));
const JarvisPage = lazy(() => import('./pages/JarvisPage').then(m => ({ default: m.JarvisPage })));
const CircuitsPage = lazy(() => import('./pages/CircuitsPage').then(m => ({ default: m.CircuitsPage })));
const DriversPage = lazy(() => import('./pages/DriversPage').then(m => ({ default: m.DriversPage })));

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
        <Route path="/app" element={<PitwallProvider><AppLayout /></PitwallProvider>}>
          <Route index element={<OverviewPage />} />
          <Route path="live" element={<PlaceholderPage title="Live / Session Dashboard" />} />
          <Route path="telemetry" element={<TelemetryPage />} />
          <Route path="comparison" element={<ComparisonPage />} />
          <Route path="strategy" element={<StrategyPage />} />
          <Route path="monte-carlo" element={<PlaceholderPage title="Monte Carlo / Sensitivity" />} />
          <Route path="replay" element={<ReplayPage />} />
          <Route path="tyres" element={<TyresPage />} />
          <Route path="ml-lab" element={<MLLabPage />} />
          <Route path="jarvis" element={<JarvisPage />} />
          <Route path="circuits" element={<CircuitsPage />} />
          <Route path="drivers" element={<DriversPage />} />
        </Route>
      </Routes>
    </Suspense>
  );
}

export default App;
