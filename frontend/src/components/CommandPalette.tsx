import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  LayoutDashboard,
  Target,
  BarChart2,
  Users,
  GitMerge,
  Radio,
  PlayCircle,
  Settings,
  Cpu,
  Sparkles,
  Map,
  Flag,
  ShieldCheck,
  Database,
  ArrowRight,
  RadioTower,
  CornerDownLeft,
  X,
  Compass
} from 'lucide-react';
import { usePitwall } from '../contexts/PitwallContext';
import './CommandPalette.css';

interface CommandItem {
  id: string;
  title: string;
  category: 'DESTINATIONS' | 'RACE WEEKEND' | 'PERFORMANCE' | 'STRATEGY' | 'AI & INTELLIGENCE' | 'DATA & HISTORY' | 'ACTIONS';
  description: string;
  path?: string;
  action?: () => void;
  icon: any;
  keywords: string[];
  badge?: string;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const { setPrimaryDriver, setReferenceDriver, triggerUplink } = usePitwall();
  const [search, setSearch] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const commandItems: CommandItem[] = [
    // Primary Destinations
    {
      id: 'home',
      title: 'Home / Mission Control',
      category: 'DESTINATIONS',
      description: 'Orientation hub with session context, KPIs, and quick actions',
      path: '/app',
      icon: Compass,
      keywords: ['home', 'dashboard', 'start', 'mission control', 'status', 'overview', 'summary']
    },
    {
      id: 'dest-race-weekend',
      title: 'Race Weekend Hub',
      category: 'DESTINATIONS',
      description: 'Live timing, tactical command center, pit-wall tools and 3D track replay',
      path: '/app/live',
      icon: RadioTower,
      badge: 'LIVE',
      keywords: ['race weekend', 'live', 'pitwall', 'timing tower', 'track map', 'ops']
    },
    {
      id: 'dest-performance',
      title: 'Performance Hub',
      category: 'DESTINATIONS',
      description: 'Driver telemetry, lap comparisons, vehicle dynamics, and ML inference',
      path: '/app/overview',
      icon: BarChart2,
      keywords: ['performance', 'telemetry', 'comparison', 'driver', 'speed', 'throttle', 'brake']
    },
    {
      id: 'dest-strategy',
      title: 'Strategy Hub',
      category: 'DESTINATIONS',
      description: 'Strategy optimizer, Monte Carlo probabilistic engine, and tyre thermal models',
      path: '/app/strategy',
      icon: GitMerge,
      badge: 'PROB',
      keywords: ['strategy', 'pit stop', 'monte carlo', 'tyres', 'stints', 'undercut', 'crossover']
    },
    {
      id: 'dest-ai',
      title: 'JARVIS AI Performance Engineer',
      category: 'DESTINATIONS',
      description: 'Autonomous conversational race engineering intelligence and evidence citations',
      path: '/app/jarvis',
      icon: Sparkles,
      badge: 'AI',
      keywords: ['jarvis', 'ai', 'engineer', 'ask', 'chat', 'intelligence', 'advice', 'recommendations']
    },
    {
      id: 'dest-data',
      title: 'Data & History Hub',
      category: 'DESTINATIONS',
      description: 'Circuits, driver career archives, model validation, and data source provenance',
      path: '/app/circuits',
      icon: Database,
      keywords: ['data', 'history', 'circuits', 'tracks', 'teams', 'drivers', 'validation', 'provenance']
    },

    // Race Weekend Tools
    {
      id: 'live-telemetry',
      title: 'Live Telemetry & Pit-Wall',
      category: 'RACE WEEKEND',
      description: 'Official F1 SignalR Core live telemetry stream, cockpit gauges, and sector times',
      path: '/app/live',
      icon: RadioTower,
      badge: 'LIVE',
      keywords: ['live', 'telemetry', 'signalr', 'openf1', 'stream', 'gauge', 'speed', 'rpm', 'gear', 'drs']
    },
    {
      id: 'command-center',
      title: 'Tactical Command Center',
      category: 'RACE WEEKEND',
      description: 'Timing tower intervals, pit stop timelines, race control incident flags, and FIA regulations',
      path: '/app/command-center',
      icon: Target,
      keywords: ['command center', 'tactical', 'timing tower', 'gaps', 'intervals', 'pit stops', 'flags', 'regulations', 'radio']
    },
    {
      id: 'replay',
      title: '3D Track Replay',
      category: 'RACE WEEKEND',
      description: 'Interactive 3D track spline mesh, 20-car spatial interpolation, and cockpit POV camera',
      path: '/app/replay',
      icon: PlayCircle,
      keywords: ['3d', 'replay', 'track mesh', 'camera', 'pov', 'spatial', 'animation', 'laps']
    },

    // Performance Tools
    {
      id: 'driver-overview',
      title: 'Driver Performance Overview',
      category: 'PERFORMANCE',
      description: 'Driver performance profile, cornering radar, braking efficiency, and sector breakdown',
      path: '/app/overview',
      icon: LayoutDashboard,
      keywords: ['driver overview', 'profile', 'radar', 'braking', 'cornering', 'metrics', 'pace']
    },
    {
      id: 'telemetry-stack',
      title: 'Telemetry Stack (Distance-Aligned)',
      category: 'PERFORMANCE',
      description: 'Multi-channel traces for speed, throttle, brake, gear, and RPM aligned by track distance',
      path: '/app/telemetry',
      icon: BarChart2,
      keywords: ['telemetry stack', 'traces', 'distance', 'speed', 'throttle', 'brake', 'corner', 'apex']
    },
    {
      id: 'lap-comparison',
      title: 'Lap Comparison (Delta Trace)',
      category: 'PERFORMANCE',
      description: 'Micro-sector delta time, speed overlays, and head-to-head lap time attribution',
      path: '/app/comparison',
      icon: Users,
      keywords: ['lap comparison', 'compare', 'delta', 'head to head', 'ver vs ham', 'reference', 'overtake']
    },
    {
      id: 'ml-lab',
      title: 'ML Inference Lab',
      category: 'PERFORMANCE',
      description: 'Quantile regression lap time predictions (P10/P50/P90) and TreeSHAP explainability',
      path: '/app/ml-lab',
      icon: Cpu,
      keywords: ['ml lab', 'machine learning', 'shap', 'feature importance', 'p10', 'p50', 'p90', 'predictions']
    },

    // Strategy Tools
    {
      id: 'strategy-optimizer',
      title: 'Strategy Optimizer',
      category: 'STRATEGY',
      description: '1-stop vs 2-stop stint planner, pit window loss, undercut calculations, and tyre crossover',
      path: '/app/strategy',
      icon: GitMerge,
      keywords: ['strategy optimizer', 'pit window', 'stints', 'undercut', 'overcut', 'crossover', 'compounds']
    },
    {
      id: 'monte-carlo',
      title: 'Monte Carlo Strategy Simulator',
      category: 'STRATEGY',
      description: '10,000+ iteration stochastic race simulation, win/podium probabilities, and safety car sensitivity',
      path: '/app/monte-carlo',
      icon: Radio,
      badge: 'PROB',
      keywords: ['monte carlo', 'simulation', 'probabilistic', 'win probability', 'podium', 'safety car', 'stochastic']
    },
    {
      id: 'tyres',
      title: 'Tyre Degradation & Thermal Physics',
      category: 'STRATEGY',
      description: '3-layer thermal PDE model (Tread, Carcass, Core) and Bayesian conjugate wear updates',
      path: '/app/tyres',
      icon: Settings,
      keywords: ['tyres', 'tyre degradation', 'thermal', 'wear', 'tread', 'carcass', 'bayesian', 'soft', 'medium', 'hard']
    },

    // AI & Intelligence
    {
      id: 'jarvis',
      title: 'JARVIS Senior AI Race Engineer',
      category: 'AI & INTELLIGENCE',
      description: 'Engineering chat with tool grounding, real-time tactical insights, and evidence citations',
      path: '/app/jarvis',
      icon: Sparkles,
      badge: 'AI',
      keywords: ['jarvis', 'ai engineer', 'chat', 'ask jarvis', 'tactics', 'engineer', 'evidence']
    },

    // Data & History
    {
      id: 'circuits',
      title: 'Championship & Circuits Database',
      category: 'DATA & HISTORY',
      description: 'Full FIA circuit maps, corner radii, elevation profiles, and historical Grand Prix records',
      path: '/app/circuits',
      icon: Map,
      keywords: ['circuits', 'track map', 'corners', 'elevation', 'length', 'drs zones', 'austin', 'monaco', 'silverstone']
    },
    {
      id: 'drivers',
      title: 'Drivers & Constructors Dossier',
      category: 'DATA & HISTORY',
      description: 'Career racing statistics, podiums, pole positions, and constructor profiles',
      path: '/app/drivers',
      icon: Flag,
      keywords: ['drivers', 'teams', 'constructors', 'career', 'podiums', 'points', 'roster']
    },
    {
      id: 'validation',
      title: 'Model Validation & Backtesting',
      category: 'DATA & HISTORY',
      description: 'Out-of-sample backtest suite, Brier probability scores, calibration curves, and ablation matrix',
      path: '/app/validation',
      icon: ShieldCheck,
      badge: 'R²',
      keywords: ['validation', 'backtest', 'brier score', 'calibration', 'accuracy', 'ablation', 'benchmarks']
    },
    {
      id: 'provenance',
      title: 'Data Provenance & System Health',
      category: 'DATA & HISTORY',
      description: 'Upstream feeds (F1 SignalR, FastF1, Jolpica), SHA-256 session integrity manifests, and cache hit rates',
      path: '/app/provenance',
      icon: Database,
      keywords: ['provenance', 'upstream', 'sources', 'cache', 'sha-256', 'manifest', 'latency', 'system health']
    },

    // Quick Driver Switch Actions
    {
      id: 'act-ver',
      title: 'Select Primary Driver: #1 Max Verstappen (VER)',
      category: 'ACTIONS',
      description: 'Switch active engineering telemetry context to Red Bull Racing #1',
      action: () => setPrimaryDriver('VER'),
      icon: ArrowRight,
      keywords: ['ver', 'verstappen', 'max', 'red bull', 'driver 1']
    },
    {
      id: 'act-nor',
      title: 'Select Primary Driver: #4 Lando Norris (NOR)',
      category: 'ACTIONS',
      description: 'Switch active engineering telemetry context to McLaren #4',
      action: () => setPrimaryDriver('NOR'),
      icon: ArrowRight,
      keywords: ['nor', 'norris', 'lando', 'mclaren', 'driver 4']
    },
    {
      id: 'act-ham',
      title: 'Select Primary Driver: #44 Lewis Hamilton (HAM)',
      category: 'ACTIONS',
      description: 'Switch active engineering telemetry context to Mercedes #44',
      action: () => setPrimaryDriver('HAM'),
      icon: ArrowRight,
      keywords: ['ham', 'hamilton', 'lewis', 'mercedes', 'driver 44']
    },
    {
      id: 'act-lec',
      title: 'Select Primary Driver: #16 Charles Leclerc (LEC)',
      category: 'ACTIONS',
      description: 'Switch active engineering telemetry context to Ferrari #16',
      action: () => setPrimaryDriver('LEC'),
      icon: ArrowRight,
      keywords: ['lec', 'leclerc', 'charles', 'ferrari', 'driver 16']
    },
    {
      id: 'act-comp-ham',
      title: 'Set Reference Driver: #44 Lewis Hamilton (HAM)',
      category: 'ACTIONS',
      description: 'Set comparison telemetry benchmark driver to Mercedes #44',
      action: () => setReferenceDriver('HAM'),
      icon: ArrowRight,
      keywords: ['ham', 'reference', 'comparison', 'compare ham']
    },
    {
      id: 'act-comp-ver',
      title: 'Set Reference Driver: #1 Max Verstappen (VER)',
      category: 'ACTIONS',
      description: 'Set comparison telemetry benchmark driver to Red Bull #1',
      action: () => setReferenceDriver('VER'),
      icon: ArrowRight,
      keywords: ['ver', 'reference', 'comparison', 'compare ver']
    },
    {
      id: 'act-sync',
      title: 'Initialize Telemetry Uplink (Synchronize Data)',
      category: 'ACTIONS',
      description: 'Fetch and cache session laps and timing data from upstream pipeline',
      action: () => triggerUplink(),
      icon: ArrowRight,
      keywords: ['sync', 'uplink', 'refresh', 'cache', 'download data']
    }
  ];

  // Filter items
  const filteredItems = commandItems.filter(item => {
    if (!search.trim()) return true;
    const query = search.toLowerCase().trim();
    return (
      item.title.toLowerCase().includes(query) ||
      item.description.toLowerCase().includes(query) ||
      item.category.toLowerCase().includes(query) ||
      item.keywords.some(k => k.toLowerCase().includes(query))
    );
  });

  // Focus input on open
  useEffect(() => {
    if (isOpen) {
      setSearch('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex(prev => (prev < filteredItems.length - 1 ? prev + 1 : 0));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex(prev => (prev > 0 ? prev - 1 : filteredItems.length - 1));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filteredItems[selectedIndex]) {
          handleSelect(filteredItems[selectedIndex]);
        }
      } else if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredItems, selectedIndex]);

  // Scroll active item into view
  useEffect(() => {
    const activeEl = listRef.current?.querySelector('.command-item.selected') as HTMLElement;
    if (activeEl) {
      activeEl.scrollIntoView({ block: 'nearest' });
    }
  }, [selectedIndex]);

  const handleSelect = (item: CommandItem) => {
    if (item.action) {
      item.action();
    } else if (item.path) {
      navigate(item.path);
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="command-palette-backdrop" onClick={onClose}>
      <div className="command-palette-modal" onClick={e => e.stopPropagation()}>
        <div className="command-search-header">
          <Search size={18} className="search-icon text-cyan" />
          <input
            ref={inputRef}
            type="text"
            className="command-search-input"
            placeholder="Type a feature, driver, tool, or action... (e.g. tyres, compare, live, jarvis)"
            value={search}
            onChange={e => {
              setSearch(e.target.value);
              setSelectedIndex(0);
            }}
          />
          <button className="command-close-btn" onClick={onClose} title="Close (Esc)">
            <X size={16} />
          </button>
        </div>

        <div className="command-results-list" ref={listRef}>
          {filteredItems.length === 0 ? (
            <div className="command-empty-state">
              <p>No tools or commands found matching "{search}"</p>
              <span>Try searching for "strategy", "telemetry", "compare", "live", "tyres", or a driver code.</span>
            </div>
          ) : (
            filteredItems.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              const Icon = item.icon;
              return (
                <div
                  key={item.id}
                  className={`command-item ${isSelected ? 'selected' : ''}`}
                  onClick={() => handleSelect(item)}
                  onMouseEnter={() => setSelectedIndex(idx)}
                >
                  <div className="command-item-icon">
                    <Icon size={16} />
                  </div>
                  <div className="command-item-content">
                    <div className="command-item-title-row">
                      <span className="command-title">{item.title}</span>
                      {item.badge && <span className={`command-badge ${item.badge.toLowerCase()}`}>{item.badge}</span>}
                      <span className="command-category">{item.category}</span>
                    </div>
                    <div className="command-desc">{item.description}</div>
                  </div>
                  <div className="command-item-action-icon">
                    <CornerDownLeft size={13} />
                  </div>
                </div>
              );
            })
          )}
        </div>

        <div className="command-palette-footer">
          <div className="keyboard-hints">
            <span className="hint-pill"><span className="key">↑</span> <span className="key">↓</span> navigate</span>
            <span className="hint-pill"><span className="key">↵</span> select</span>
            <span className="hint-pill"><span className="key">esc</span> close</span>
          </div>
          <div className="command-count">
            {filteredItems.length} {filteredItems.length === 1 ? 'item' : 'items'}
          </div>
        </div>
      </div>
    </div>
  );
};
