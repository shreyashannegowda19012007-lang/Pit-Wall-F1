import { useState, useEffect } from 'react';
import { Outlet, NavLink, Link, useLocation } from 'react-router-dom';
import {
  Compass,
  RadioTower,
  BarChart2,
  GitMerge,
  Sparkles,
  Database,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Search,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  Target,
  PlayCircle,
  LayoutDashboard,
  Users,
  Cpu,
  Radio,
  Settings,
  Map,
  Flag,
  ShieldCheck
} from 'lucide-react';
import { usePitwall } from '../contexts/PitwallContext';
import { CommandPalette } from '../components/CommandPalette';
import './AppLayout.css';

interface PrimaryNavDestination {
  id: string;
  label: string;
  defaultPath: string;
  icon: any;
  badge?: string;
  badgeType?: 'live' | 'ai' | 'prob';
  matches: string[];
  subTabs: {
    path: string;
    label: string;
    icon: any;
    badge?: string;
  }[];
}

const PRIMARY_DESTINATIONS: PrimaryNavDestination[] = [
  {
    id: 'home',
    label: 'Home',
    defaultPath: '/app',
    icon: Compass,
    matches: ['/app', '/app/', '/app/home'],
    subTabs: []
  },
  {
    id: 'race-weekend',
    label: 'Race Weekend',
    defaultPath: '/app/live',
    icon: RadioTower,
    badge: 'LIVE',
    badgeType: 'live',
    matches: ['/app/live', '/app/command-center', '/app/replay', '/app/race-weekend'],
    subTabs: [
      { path: '/app/live', label: 'Live Telemetry & Pit-Wall', icon: RadioTower, badge: 'LIVE' },
      { path: '/app/command-center', label: 'Tactical Command Center', icon: Target },
      { path: '/app/replay', label: '3D Track Replay', icon: PlayCircle }
    ]
  },
  {
    id: 'performance',
    label: 'Performance',
    defaultPath: '/app/overview',
    icon: BarChart2,
    matches: ['/app/overview', '/app/telemetry', '/app/comparison', '/app/ml-lab', '/app/performance'],
    subTabs: [
      { path: '/app/overview', label: 'Driver Overview', icon: LayoutDashboard },
      { path: '/app/telemetry', label: 'Telemetry Stack', icon: BarChart2 },
      { path: '/app/comparison', label: 'Lap Comparison', icon: Users },
      { path: '/app/ml-lab', label: 'ML Inference Lab', icon: Cpu }
    ]
  },
  {
    id: 'strategy',
    label: 'Strategy',
    defaultPath: '/app/strategy',
    icon: GitMerge,
    badge: 'PROB',
    badgeType: 'prob',
    matches: ['/app/strategy', '/app/monte-carlo', '/app/tyres', '/app/strategy-hub'],
    subTabs: [
      { path: '/app/strategy', label: 'Strategy Optimizer', icon: GitMerge },
      { path: '/app/monte-carlo', label: 'Monte Carlo Simulator', icon: Radio, badge: 'PROB' },
      { path: '/app/tyres', label: 'Tyre Degradation', icon: Settings }
    ]
  },
  {
    id: 'ai-engineer',
    label: 'AI Engineer',
    defaultPath: '/app/jarvis',
    icon: Sparkles,
    badge: 'AI',
    badgeType: 'ai',
    matches: ['/app/jarvis', '/app/ai-engineer'],
    subTabs: [
      { path: '/app/jarvis', label: 'JARVIS AI Race Engineer', icon: Sparkles, badge: 'AI' }
    ]
  },
  {
    id: 'data-history',
    label: 'Data & History',
    defaultPath: '/app/circuits',
    icon: Database,
    matches: ['/app/circuits', '/app/drivers', '/app/validation', '/app/provenance', '/app/data-history'],
    subTabs: [
      { path: '/app/circuits', label: 'Championship & Circuits', icon: Map },
      { path: '/app/drivers', label: 'Drivers & Teams', icon: Flag },
      { path: '/app/validation', label: 'Model Validation', icon: ShieldCheck, badge: 'R²' },
      { path: '/app/provenance', label: 'Data Provenance', icon: Database }
    ]
  }
];

export default function AppLayout() {
  const location = useLocation();
  const {
    session,
    primaryDriver, setPrimaryDriver,
    referenceDriver, setReferenceDriver,
    apiStatus,
    availableDrivers,
    season, setSeason,
    availableSeasons,
    rounds,
    selectedRound, setSelectedRound,
    sessionType, setSessionType,
    isUplinkSyncing,
    uplinkNotice,
    triggerUplink
  } = usePitwall();

  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(() => {
    return localStorage.getItem('pitwall_sidebar_collapsed') === 'true';
  });
  const [isMobileDrawerOpen, setIsMobileDrawerOpen] = useState(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);

  // Toggle sidebar collapse
  const toggleSidebar = () => {
    setIsSidebarCollapsed(prev => {
      const next = !prev;
      localStorage.setItem('pitwall_sidebar_collapsed', String(next));
      return next;
    });
  };

  // Keyboard shortcut for Command Palette: Ctrl+K / Cmd+K or "/"
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      // Ctrl+K or Cmd+K
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen(prev => !prev);
        return;
      }

      // "/" key when not focused in input/textarea/select
      if (e.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes((document.activeElement?.tagName || ''))) {
        e.preventDefault();
        setIsCommandPaletteOpen(true);
      }
    };

    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, []);

  // Track recent page visits in localStorage for Home
  useEffect(() => {
    const currentPath = location.pathname;
    for (const dest of PRIMARY_DESTINATIONS) {
      for (const tab of dest.subTabs) {
        if (currentPath === tab.path) {
          try {
            const raw = localStorage.getItem('pitwall_recent_analyses');
            let list = raw ? JSON.parse(raw) : [];
            list = list.filter((item: any) => item.path !== tab.path);
            list.unshift({
              title: tab.label,
              path: tab.path,
              hub: dest.label,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            });
            localStorage.setItem('pitwall_recent_analyses', JSON.stringify(list.slice(0, 8)));
          } catch {
            // ignore
          }
          break;
        }
      }
    }
  }, [location.pathname]);

  // Identify currently active primary destination
  const activeDestination = PRIMARY_DESTINATIONS.find(dest =>
    dest.matches.some(pattern => {
      if (pattern === '/app' || pattern === '/app/') {
        return location.pathname === '/app' || location.pathname === '/app/';
      }
      return location.pathname.startsWith(pattern);
    })
  ) || PRIMARY_DESTINATIONS[0];

  return (
    <div className={`app-layout ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      {/* Universal Command Palette Modal */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
      />

      {/* Mobile Drawer Backdrop */}
      {isMobileDrawerOpen && (
        <div className="mobile-drawer-backdrop" onClick={() => setIsMobileDrawerOpen(false)} />
      )}

      {/* Primary Desktop Sidebar (6 Destinations) */}
      <aside className={`app-sidebar ${isMobileDrawerOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-header">
          <Link to="/app" className="logo" onClick={() => setIsMobileDrawerOpen(false)}>
            <span className="logo-pit">PITWALL</span>
            <span className="logo-accent">F1</span>
          </Link>
          {!isSidebarCollapsed && (
            <div className="sidebar-build-badge">R7 PROD</div>
          )}
          <button
            className="sidebar-collapse-toggle desktop-only"
            onClick={toggleSidebar}
            title={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-label="Toggle sidebar width"
          >
            {isSidebarCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
          </button>
          <button
            className="mobile-close-btn mobile-only"
            onClick={() => setIsMobileDrawerOpen(false)}
            aria-label="Close menu"
          >
            <X size={16} />
          </button>
        </div>

        {/* Six Primary Destinations */}
        <nav className="sidebar-primary-nav" aria-label="Primary Destinations">
          <div className="nav-group-label">
            {!isSidebarCollapsed ? 'PRIMARY DESTINATIONS' : 'NAV'}
          </div>

          {PRIMARY_DESTINATIONS.map((dest) => {
            const Icon = dest.icon;
            const isActive = activeDestination.id === dest.id;

            return (
              <NavLink
                key={dest.id}
                to={dest.defaultPath}
                className={`primary-nav-item ${isActive ? 'active' : ''}`}
                title={dest.label}
                onClick={() => setIsMobileDrawerOpen(false)}
              >
                <div className="nav-item-icon-wrap">
                  <Icon size={17} className="primary-nav-icon" />
                </div>
                {!isSidebarCollapsed && (
                  <span className="primary-nav-label">{dest.label}</span>
                )}
                {!isSidebarCollapsed && dest.badge && (
                  <span className={`primary-nav-badge ${dest.badgeType || ''}`}>
                    {dest.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Sidebar Footer Status */}
        <div className="sidebar-footer">
          <div className="footer-status-pill" title={`Engine Status: ${apiStatus}`}>
            <span className={`status-dot ${apiStatus}`}></span>
            {!isSidebarCollapsed && (
              <span className="status-text">
                {apiStatus === 'healthy' ? 'FASTAPI ENGINE ACTIVE' : apiStatus === 'error' ? 'BACKEND OFFLINE' : 'SYNCHRONIZING...'}
              </span>
            )}
          </div>
        </div>
      </aside>

      {/* Main Engineering Viewport */}
      <main className="app-main">
        {/* Global Race Context Header */}
        <header className="app-topbar">
          <div className="topbar-left">
            {/* Mobile Menu Hamburger */}
            <button
              className="mobile-hamburger-btn mobile-only"
              onClick={() => setIsMobileDrawerOpen(true)}
              aria-label="Open navigation menu"
            >
              <Menu size={18} />
            </button>

            {/* Universal Search / Command Palette Trigger */}
            <button
              className="topbar-search-trigger"
              onClick={() => setIsCommandPaletteOpen(true)}
              title="Search tools, drivers, circuits, or actions (Ctrl+K or /)"
            >
              <Search size={13} className="text-cyan" />
              <span className="search-text">Search features or press</span>
              <kbd className="search-kbd">Ctrl K</kbd>
            </button>

            {/* Season Selector */}
            <div className="selector-group">
              <span className="metric-label">SEASON</span>
              <select
                value={season}
                onChange={(e) => setSeason(Number(e.target.value))}
                className="topbar-select"
                aria-label="Select season"
              >
                {availableSeasons.map((yr) => (
                  <option key={yr} value={yr}>{yr}</option>
                ))}
              </select>
            </div>

            {/* Grand Prix / Round Selector */}
            <div className="selector-group">
              <span className="metric-label">ROUND / GRAND PRIX</span>
              <select
                value={selectedRound}
                onChange={(e) => setSelectedRound(Number(e.target.value))}
                className="topbar-select gp-select"
                aria-label="Select Grand Prix event"
              >
                {rounds.map((r) => (
                  <option key={r.round_number} value={r.round_number}>
                    R{r.round_number} - {r.event_name}
                  </option>
                ))}
                {rounds.length === 0 && (
                  <option value={18}>R18 - United States Grand Prix</option>
                )}
              </select>
            </div>

            {/* Session Type */}
            <div className="selector-group">
              <span className="metric-label">SESSION</span>
              <select
                value={sessionType}
                onChange={(e) => setSessionType(e.target.value)}
                className="topbar-select"
                aria-label="Select session type"
              >
                <option value="R">Race (R)</option>
                <option value="Q">Qualifying (Q)</option>
                <option value="FP1">Practice 1</option>
                <option value="FP2">Practice 2</option>
                <option value="FP3">Practice 3</option>
                <option value="S">Sprint</option>
              </select>
            </div>

            {/* Initialize Uplink Button */}
            <button
              onClick={() => triggerUplink()}
              disabled={isUplinkSyncing}
              className={`uplink-button ${isUplinkSyncing ? 'loading' : ''}`}
              title="Synchronize session data from FastF1 / Live Timing pipeline"
            >
              <RefreshCw size={13} className={`btn-icon ${isUplinkSyncing ? 'spin' : ''}`} />
              <span>{isUplinkSyncing ? 'SYNCING...' : 'INITIALIZE UPLINK'}</span>
            </button>
          </div>

          <div className="topbar-right">
            {/* Primary Driver Selector */}
            <div className="selector-group driver-selector primary">
              <span className="metric-label">PRIMARY DRV</span>
              <select
                value={primaryDriver}
                onChange={(e) => setPrimaryDriver(e.target.value)}
                className="topbar-select driver-select primary"
                aria-label="Select primary driver"
              >
                {availableDrivers.map((d) => (
                  <option key={d.abbreviation} value={d.abbreviation}>
                    #{d.driver_number} {d.abbreviation} ({d.team_name.split(' ')[0]})
                  </option>
                ))}
                {availableDrivers.length === 0 && (
                  <>
                    <option value="VER">#1 VER (Red Bull)</option>
                    <option value="NOR">#4 NOR (McLaren)</option>
                    <option value="HAM">#44 HAM (Mercedes)</option>
                    <option value="LEC">#16 LEC (Ferrari)</option>
                  </>
                )}
              </select>
            </div>

            {/* Reference Driver Selector */}
            <div className="selector-group driver-selector comparison">
              <span className="metric-label">COMP DRV</span>
              <select
                value={referenceDriver}
                onChange={(e) => setReferenceDriver(e.target.value)}
                className="topbar-select driver-select comparison"
                aria-label="Select comparison reference driver"
              >
                {availableDrivers.map((d) => (
                  <option key={d.abbreviation} value={d.abbreviation}>
                    #{d.driver_number} {d.abbreviation} ({d.team_name.split(' ')[0]})
                  </option>
                ))}
                {availableDrivers.length === 0 && (
                  <>
                    <option value="HAM">#44 HAM (Mercedes)</option>
                    <option value="VER">#1 VER (Red Bull)</option>
                    <option value="NOR">#4 NOR (McLaren)</option>
                    <option value="LEC">#16 LEC (Ferrari)</option>
                  </>
                )}
              </select>
            </div>

            {/* Active Session Identifier Pill */}
            <div className="active-session-pill" title={`Active Session ID: ${session}`}>
              <span className="session-dot"></span>
              <span className="session-code">{session}</span>
            </div>
          </div>
        </header>

        {/* Global Uplink Notification Banner if triggered */}
        {uplinkNotice && (
          <div className={`uplink-banner ${uplinkNotice.startsWith('Notice:') ? 'notice' : 'success'}`}>
            {uplinkNotice.startsWith('Notice:') ? <AlertCircle size={15} /> : <CheckCircle2 size={15} />}
            <span>{uplinkNotice}</span>
          </div>
        )}

        {/* Secondary Sub-Navigation Tab Bar (Shown when inside any grouped hub) */}
        {activeDestination.subTabs.length > 0 && (
          <div className="subnav-tab-bar" aria-label="Tool sub-tabs">
            <div className="subnav-hub-indicator">
              <activeDestination.icon size={13} className="hub-indicator-icon" />
              <span className="hub-indicator-name">{activeDestination.label.toUpperCase()}</span>
            </div>
            <div className="subnav-tabs-list">
              {activeDestination.subTabs.map((tab) => {
                const TabIcon = tab.icon;
                const isTabActive = location.pathname === tab.path;
                return (
                  <NavLink
                    key={tab.path}
                    to={tab.path}
                    className={`subnav-tab-item ${isTabActive ? 'active' : ''}`}
                  >
                    <TabIcon size={13} className="subnav-tab-icon" />
                    <span>{tab.label}</span>
                    {tab.badge && (
                      <span className={`subnav-tab-badge ${tab.badge.toLowerCase()}`}>
                        {tab.badge}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </div>
          </div>
        )}

        {/* Content Outlet */}
        <div className="app-content">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
