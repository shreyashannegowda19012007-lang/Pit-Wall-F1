import { Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import AppLayout from './layouts/AppLayout';
import OverviewPage from './pages/OverviewPage';
import TelemetryPage from './pages/TelemetryPage';
import ComparisonPage from './pages/ComparisonPage';
import TyresPage from './pages/TyresPage';
import StrategyPage from './pages/StrategyPage';
import PlaceholderPage from './pages/PlaceholderPage';
import { PitwallProvider } from './contexts/PitwallContext';
import { ReplayPage } from './pages/ReplayPage';
import { MLLabPage } from './pages/MLLabPage';
import { JarvisPage } from './pages/JarvisPage';
import { CircuitsPage } from './pages/CircuitsPage';
import { DriversPage } from './pages/DriversPage';

function App() {
  return (
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
  );
}

export default App;
