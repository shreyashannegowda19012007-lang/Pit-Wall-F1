import { Outlet, NavLink, Link } from 'react-router-dom';
import {
  LayoutDashboard, Activity, BarChart2, Users,
  GitMerge, FastForward, PlayCircle, Settings,
  Cpu, Map, Flag, ShieldAlert
} from 'lucide-react';
import { usePitwall } from '../contexts/PitwallContext';
import './AppLayout.css';

const NAV_ITEMS = [
  { path: '', label: 'Overview', icon: LayoutDashboard },
  { path: 'live', label: 'Live Session', icon: Activity },
  { path: 'telemetry', label: 'Telemetry', icon: BarChart2 },
  { path: 'comparison', label: 'Comparison', icon: Users },
  { path: 'strategy', label: 'Race Strategy', icon: GitMerge },
  { path: 'monte-carlo', label: 'Monte Carlo', icon: FastForward },
  { path: 'replay', label: '3D Replay', icon: PlayCircle },
  { path: 'tyres', label: 'Tyre Intel', icon: Settings },
  { path: 'ml-lab', label: 'ML Lab', icon: Cpu },
  { path: 'jarvis', label: 'JARVIS', icon: ShieldAlert },
  { path: 'circuits', label: 'Circuits', icon: Map },
  { path: 'drivers', label: 'Drivers', icon: Flag },
];

export default function AppLayout() {
  const {
    session, setSession,
    primaryDriver, setPrimaryDriver,
    referenceDriver, setReferenceDriver,
    apiStatus
  } = usePitwall();

  return (
    <div className="app-layout">
      <aside className="app-sidebar">
        <div className="sidebar-header">
          <Link to="/" className="logo">Pitwall <span className="logo-accent">F1</span></Link>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-group-label">Intelligence Core</div>
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.path}
              to={`/app${item.path ? '/' + item.path : ''}`}
              end={item.path === ''}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <item.icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="app-main">
        <header className="app-topbar">
          <div className="topbar-selectors flex items-center gap-md">
            <div className="selector-group">
              <span className="metric-label">Session</span>
              <select value={session} onChange={(e) => setSession(e.target.value)} className="selector">
                <option value="S-2024-SPAIN">2024 Spain (Race)</option>
                <option value="S-2024-MONACO">2024 Monaco (Race)</option>
              </select>
            </div>

            <div className="selector-group">
              <span className="metric-label">Primary Driver</span>
              <select value={primaryDriver} onChange={(e) => setPrimaryDriver(e.target.value)} className="selector">
                <option value="VER">VER - Max Verstappen</option>
                <option value="NOR">NOR - Lando Norris</option>
                <option value="HAM">HAM - Lewis Hamilton</option>
                <option value="LEC">LEC - Charles Leclerc</option>
                <option value="SAI">SAI - Carlos Sainz</option>
                <option value="PIA">PIA - Oscar Piastri</option>
                <option value="RUS">RUS - George Russell</option>
              </select>
            </div>

            <div className="selector-group">
              <span className="metric-label">Reference Driver</span>
              <select value={referenceDriver} onChange={(e) => setReferenceDriver(e.target.value)} className="selector">
                <option value="HAM">HAM - Lewis Hamilton</option>
                <option value="VER">VER - Max Verstappen</option>
                <option value="NOR">NOR - Lando Norris</option>
                <option value="LEC">LEC - Charles Leclerc</option>
                <option value="SAI">SAI - Carlos Sainz</option>
                <option value="PIA">PIA - Oscar Piastri</option>
                <option value="RUS">RUS - George Russell</option>
              </select>
            </div>
          </div>

          <div className="topbar-status flex items-center gap-sm">
            <span className={`status-indicator ${apiStatus}`}></span>
            <span className="metric-label">
              {apiStatus === 'healthy' ? 'DATA ACTIVE' : apiStatus === 'error' ? 'API DISCONNECTED' : 'CONNECTING...'}
            </span>
          </div>
        </header>

        <div className="app-content">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

