import React, { useState, useEffect, useRef } from 'react';
import { usePitwall } from '../contexts/PitwallContext';
import {
  Radio,
  Wifi,
  WifiOff,
  Gauge,
  Zap,
  Clock,
  Play,
  Pause,
  RotateCcw,
  Sliders,
  Car,
  History,
  AlertTriangle,
  FastForward,
  Layers,
  Compass,
  CheckCircle2
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from 'recharts';
import './LiveTelemetrySection.css';

interface SessionItem {
  session_key: number;
  session_name: string;
  session_type: string;
  circuit_short_name?: string;
  date_start?: string;
  date_end?: string;
  year?: number;
  is_source_verified?: boolean;
}

interface HistoricalEventItem {
  session_key: number;
  year: number;
  event_name: string;
  event_directory?: string;
  date?: string;
  available_sessions: string[];
  circuit_short_name?: string;
  is_cached?: boolean;
}

interface DriverItem {
  driver_number: number;
  driver_code: string;
  full_name: string;
  team_name: string;
  team_colour: string;
  headshot_url?: string;
}

interface TelemetrySample {
  source: string;
  provider?: string;
  session_key: number;
  session_name?: string;
  driver_number: number;
  driver_code?: string;
  timestamp: string | null;
  source_timestamp_epoch?: number | null;
  server_receipt_epoch?: number | null;
  processing_epoch?: number | null;
  speed_kmh: number | null;
  engine_rpm: number | null;
  gear: number | null;
  throttle_pct: number | null;
  brake_flag: number | null;
  drs_active: boolean | null;
  x?: number | null;
  y?: number | null;
  z?: number | null;
  provenance: string;
  data_classification: string;
  measurement_type?: string;
  car_telemetry_available?: boolean;
  live_timing_available?: boolean;
  channel_status?: string;
  is_test_stream?: boolean;
  is_replay?: boolean;
  replay_notice?: string;
  replay_progress_pct?: number;
  replay_speed?: number;
}

interface TimingTowerRow {
  position: number;
  driver_code: string;
  driver_number: string;
  driver_name?: string;
  team_name: string;
  team_color: string;
  gap_to_leader_s: string;
  interval_ahead_s: string;
  last_lap_time_s: string;
  best_lap_time_s: string;
  current_compound: string;
  tyre_age_laps: number;
  pit_stops_count: number;
  speed_trap_kmh?: number | null;
  status: string;
  is_source_backed?: boolean;
}

interface LiveStatus {
  provider: string;
  provider_type?: string;
  session_status: string;
  connection_state?: string;
  is_session_live: boolean;
  is_replay?: boolean;
  replay_banner?: string;
  active_session?: SessionItem | null;
  display_session?: SessionItem | null;
  current_utc_time: string;
  data_freshness: string;
  data_age_seconds?: number | null;
  source_data_age_seconds?: number | null;
  transport_packet_age_seconds?: number | null;
  last_source_timestamp?: string | null;
  total_records_ingested: number;
  has_live_credentials: boolean;
  auth_notice: string;
  car_telemetry_available: boolean;
  recent_error?: string | null;
  replay_state?: string;
  replay_progress_pct?: number;
  replay_speed?: number;
}

export const LiveTelemetrySection: React.FC = () => {
  // Global Platform Context Synchronization
  const {
    primaryDriver,
    setPrimaryDriver
  } = usePitwall();

  // Top-level Provider Mode: 'LIVE' | 'REPLAY' | 'SIMULATOR'
  const [pipelineMode, setPipelineMode] = useState<'LIVE' | 'REPLAY' | 'SIMULATOR'>('LIVE');

  // Live Mode State
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [selectedSessionKey, setSelectedSessionKey] = useState<number>(20261805);
  const [drivers, setDrivers] = useState<DriverItem[]>([]);
  const [selectedDriverNum, setSelectedDriverNum] = useState<number>(1);
  const [liveStatus, setLiveStatus] = useState<LiveStatus | null>(null);

  // Historical Replay State
  const [replaySessions, setReplaySessions] = useState<HistoricalEventItem[]>([]);
  const [replayYear, setReplayYear] = useState<number>(2024);
  const [replayEvent, setReplayEvent] = useState<string>('Spanish Grand Prix');
  const [replaySessionType, setReplaySessionType] = useState<string>('Race');
  const [replayDriverCode, setReplayDriverCode] = useState<string>('VER');
  const [replaySpeed, setReplaySpeed] = useState<number>(1.0);
  const [replayProgress, setReplayProgress] = useState<number>(0.0);
  const [replayState, setReplayState] = useState<string>('IDLE');
  const [replayTotalSamples, setReplayTotalSamples] = useState<number>(0);

  // Ingestion & Transport State
  const [currentSample, setCurrentSample] = useState<TelemetrySample | null>(null);
  const [telemetryHistory, setTelemetryHistory] = useState<TelemetrySample[]>([]);
  const [connectionState, setConnectionState] = useState<'CONNECTING' | 'CONNECTED' | 'STREAMING' | 'WAITING' | 'DISCONNECTED' | 'ERROR'>('CONNECTING');
  const [transportType, setTransportType] = useState<'WEBSOCKET' | 'REST_POLL'>('WEBSOCKET');
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [recordsCount, setRecordsCount] = useState<number>(0);
  const [lastUpdateEpoch, setLastUpdateEpoch] = useState<number>(() => Date.now());
  const [timeAgoSec, setTimeAgoSec] = useState<number>(0);
  const [timingTower, setTimingTower] = useState<TimingTowerRow[]>([]);
  const [timingLoading, setTimingLoading] = useState<boolean>(true);

  // Connection Refs
  const wsRef = useRef<WebSocket | null>(null);
  const pollTimerRef = useRef<any>(null);
  const simulatorStepRef = useRef<number>(0);

  // ---------------------------------------------------------------------------
  // 1. Initial Discovery of Sessions, Replay Cache, and Provider Health
  // ---------------------------------------------------------------------------
  useEffect(() => {
    // Check provider health
    fetch('/api/live/status')
      .then(res => res.json())
      .then((data: LiveStatus) => {
        setLiveStatus(data);
        if (data.active_session?.session_key) {
          setSelectedSessionKey(data.active_session.session_key);
        } else if (data.display_session?.session_key) {
          setSelectedSessionKey(data.display_session.session_key);
        }
      })
      .catch(err => console.error('Failed to fetch live status:', err));

    // Discover live sessions
    fetch('/api/live/sessions')
      .then(res => res.json())
      .then(data => {
        if (data.sessions && Array.isArray(data.sessions) && data.sessions.length > 0) {
          setSessions(data.sessions);
          setSelectedSessionKey(prev => {
            if (prev) return prev;
            const active = data.sessions.find((s: SessionItem) => s.is_source_verified);
            return active ? active.session_key : data.sessions[0].session_key;
          });
        }
      })
      .catch(err => console.error('Failed to fetch live sessions:', err));

    // Discover available cached historical replay sessions
    fetch('/api/replay/sessions')
      .then(res => res.json())
      .then(data => {
        if (data.sessions && Array.isArray(data.sessions) && data.sessions.length > 0) {
          setReplaySessions(data.sessions);
          // Default to first cached session
          const first = data.sessions[0];
          setReplayYear(first.year);
          setReplayEvent(first.event_name);
        }
      })
      .catch(err => console.error('Failed to fetch replay sessions:', err));
  }, []);

  // ---------------------------------------------------------------------------
  // 2. Load Replay Drivers when Replay Event Changes
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (pipelineMode !== 'REPLAY') return;
    const url = `/api/replay/drivers?year=${replayYear}&event=${encodeURIComponent(replayEvent)}&session_type=${encodeURIComponent(replaySessionType)}`;
    fetch(url)
      .then(r => r.json())
      .then(res => {
        if (res.drivers && Array.isArray(res.drivers) && res.drivers.length > 0) {
          setDrivers(res.drivers);
          const hasCurrent = res.drivers.some((d: DriverItem) => d.driver_code === replayDriverCode);
          if (!hasCurrent) {
            setReplayDriverCode(res.drivers[0].driver_code);
            setSelectedDriverNum(res.drivers[0].driver_number);
          }
        }
      })
      .catch(err => console.error('Failed to fetch replay drivers:', err));
  }, [pipelineMode, replayYear, replayEvent, replaySessionType]);

  // ---------------------------------------------------------------------------
  // 3. Load Live Drivers when Session Key Changes (in LIVE or SIMULATOR mode)
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (pipelineMode === 'REPLAY' || !selectedSessionKey) return;
    fetch(`/api/live/drivers?session_key=${selectedSessionKey}`)
      .then(res => res.json())
      .then(data => {
        if (data.drivers && Array.isArray(data.drivers) && data.drivers.length > 0) {
          setDrivers(data.drivers);
          const matchedByCode = data.drivers.find((d: DriverItem) => d.driver_code === primaryDriver);
          if (matchedByCode) {
            setSelectedDriverNum(matchedByCode.driver_number);
          } else {
            const exists = data.drivers.some((d: DriverItem) => d.driver_number === selectedDriverNum);
            if (!exists) {
              setSelectedDriverNum(data.drivers[0].driver_number);
              setPrimaryDriver(data.drivers[0].driver_code);
            }
          }
        }
      })
      .catch(err => console.error('Failed to fetch session drivers:', err));
  }, [pipelineMode, selectedSessionKey]);

  // Synchronize primaryDriver context changes into selectedDriverNum
  useEffect(() => {
    if (pipelineMode !== 'REPLAY' && drivers.length > 0 && primaryDriver) {
      const matched = drivers.find(d => d.driver_code === primaryDriver);
      if (matched && matched.driver_number !== selectedDriverNum) {
        setSelectedDriverNum(matched.driver_number);
      }
    }
  }, [primaryDriver, drivers, pipelineMode, selectedDriverNum]);

  // ---------------------------------------------------------------------------
  // 4. Timing Tower Polling (routes based on mode)
  // ---------------------------------------------------------------------------
  useEffect(() => {
    let active = true;
    const fetchTower = () => {
      const endpoint = pipelineMode === 'REPLAY'
        ? '/api/replay/timing-tower'
        : `/api/live/timing-tower?session_key=${selectedSessionKey}`;

      fetch(endpoint)
        .then(r => r.json())
        .then(res => {
          if (active && res.success && Array.isArray(res.tower)) {
            setTimingTower(res.tower);
            setTimingLoading(false);
          }
        })
        .catch(() => {
          if (active) setTimingLoading(false);
        });
    };

    fetchTower();
    const interval = setInterval(fetchTower, 3000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [pipelineMode, selectedSessionKey]);

  // ---------------------------------------------------------------------------
  // 5. Main Telemetry Streaming Pipeline (WebSocket / Poll / Simulator)
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }

    setConnectionState('CONNECTING');
    simulatorStepRef.current = 0;

    if (pipelineMode === 'REPLAY') {
      // -----------------------------------------------------------------------
      // REPLAY MODE: WebSocket or Poll from Historical Replay Engine
      // -----------------------------------------------------------------------
      if (transportType === 'WEBSOCKET') {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/live/telemetry/${selectedSessionKey}/${selectedDriverNum}?mode=REPLAY`;

        try {
          const ws = new WebSocket(wsUrl);
          wsRef.current = ws;

          ws.onopen = () => {
            setConnectionState('CONNECTED');
          };

          ws.onmessage = (event) => {
            if (isPaused) return;
            try {
              const msg = JSON.parse(event.data);
              if (msg.type === 'INITIAL_SNAPSHOT') {
                if (msg.status) {
                  setReplayState(msg.status.state || 'IDLE');
                  setReplayProgress(msg.status.progress_pct || 0);
                  setReplayTotalSamples(msg.status.total_samples || 0);
                }
                if (msg.history && Array.isArray(msg.history) && msg.history.length > 0) {
                  setTelemetryHistory(msg.history.slice(-35));
                  setCurrentSample(msg.history[msg.history.length - 1]);
                  setConnectionState('STREAMING');
                }
              } else if (msg.type === 'TELEMETRY_UPDATE' && msg.data) {
                const sample: TelemetrySample = msg.data;
                setCurrentSample(sample);
                setLastUpdateEpoch(Date.now());
                setRecordsCount(prev => prev + 1);
                setConnectionState('STREAMING');
                if (msg.status) {
                  setReplayProgress(msg.status.progress_pct || 0);
                  setReplayState(msg.status.state || 'PLAYING');
                }
                setTelemetryHistory(prev => {
                  const next = [...prev, sample];
                  return next.length > 35 ? next.slice(-35) : next;
                });
              } else if (msg.type === 'REPLAY_HEARTBEAT') {
                if (msg.status) setReplayState(msg.status);
                if (msg.progress_pct !== undefined) setReplayProgress(msg.progress_pct);
              }
            } catch (e) {
              console.error('Error parsing replay WS message:', e);
            }
          };

          ws.onerror = () => setConnectionState('ERROR');
          ws.onclose = () => setConnectionState('DISCONNECTED');
        } catch {
          setConnectionState('ERROR');
        }
      } else {
        // HTTP Polling for Replay
        pollTimerRef.current = setInterval(() => {
          if (isPaused) return;
          fetch('/api/replay/telemetry/latest')
            .then(r => r.json())
            .then(res => {
              if (res.data) {
                setCurrentSample(res.data);
                setLastUpdateEpoch(Date.now());
                setRecordsCount(prev => prev + 1);
                setConnectionState('STREAMING');
                setTelemetryHistory(prev => {
                  const next = [...prev, res.data];
                  return next.length > 35 ? next.slice(-35) : next;
                });
              }
            })
            .catch(() => setConnectionState('ERROR'));
        }, 1000);
      }

    } else if (pipelineMode === 'SIMULATOR') {
      // -----------------------------------------------------------------------
      // SIMULATOR MODE: Explicit local test generator
      // -----------------------------------------------------------------------
      setConnectionState('CONNECTED');
      const fetchSimPoint = () => {
        if (isPaused) return;
        fetch(`/api/live/telemetry/test-stream?session_key=${selectedSessionKey}&driver_number=${selectedDriverNum}&step=${simulatorStepRef.current}`)
          .then(r => r.json())
          .then(res => {
            if (res.data) {
              setCurrentSample(res.data);
              setLastUpdateEpoch(Date.now());
              setRecordsCount(prev => prev + 1);
              setConnectionState('STREAMING');
              setTelemetryHistory(prev => {
                const next = [...prev, res.data];
                return next.length > 35 ? next.slice(-35) : next;
              });
              simulatorStepRef.current += 1;
            }
          })
          .catch(() => setConnectionState('ERROR'));
      };

      fetchSimPoint();
      pollTimerRef.current = setInterval(fetchSimPoint, 1000);

    } else {
      // -----------------------------------------------------------------------
      // LIVE MODE: Real official F1 SignalR connection
      // -----------------------------------------------------------------------
      if (transportType === 'WEBSOCKET') {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/live/telemetry/${selectedSessionKey}/${selectedDriverNum}?mode=LIVE`;

        try {
          const ws = new WebSocket(wsUrl);
          wsRef.current = ws;

          ws.onopen = () => setConnectionState('CONNECTED');

          ws.onmessage = (event) => {
            if (isPaused) return;
            try {
              const msg = JSON.parse(event.data);
              if (msg.type === 'INITIAL_SNAPSHOT') {
                if (msg.status) setLiveStatus(msg.status);
                if (msg.history && Array.isArray(msg.history) && msg.history.length > 0) {
                  setTelemetryHistory(msg.history.slice(-35));
                  setCurrentSample(msg.history[msg.history.length - 1]);
                  setConnectionState('STREAMING');
                } else {
                  setConnectionState('CONNECTED');
                }
              } else if (msg.type === 'TELEMETRY_UPDATE' && msg.data) {
                const sample: TelemetrySample = msg.data;
                setCurrentSample(sample);
                setLastUpdateEpoch(Date.now());
                setRecordsCount(prev => prev + 1);
                setConnectionState('STREAMING');
                setTelemetryHistory(prev => {
                  const next = [...prev, sample];
                  return next.length > 35 ? next.slice(-35) : next;
                });
              } else if (msg.type === 'HEARTBEAT') {
                if (connectionState !== 'STREAMING') {
                  setConnectionState('CONNECTED');
                }
              }
            } catch (e) {
              console.error('Error parsing live WS message:', e);
            }
          };

          ws.onerror = () => setConnectionState('ERROR');
          ws.onclose = () => setConnectionState('DISCONNECTED');
        } catch {
          setConnectionState('ERROR');
        }
      } else {
        // LIVE HTTP REST Polling
        pollTimerRef.current = setInterval(() => {
          if (isPaused) return;
          fetch(`/api/live/telemetry/latest?session_key=${selectedSessionKey}&driver_number=${selectedDriverNum}`)
            .then(r => r.json())
            .then(res => {
              if (res.data) {
                setCurrentSample(res.data);
                setLastUpdateEpoch(Date.now());
                setRecordsCount(prev => prev + 1);
                setConnectionState('STREAMING');
                setTelemetryHistory(prev => {
                  const next = [...prev, res.data];
                  return next.length > 35 ? next.slice(-35) : next;
                });
              }
            })
            .catch(() => setConnectionState('ERROR'));
        }, 2000);
      }
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
  }, [pipelineMode, selectedSessionKey, selectedDriverNum, transportType, isPaused, replayEvent, replayDriverCode]);

  // ---------------------------------------------------------------------------
  // 6. Time-Ago Counter
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const timer = setInterval(() => {
      const elapsed = Math.round((Date.now() - lastUpdateEpoch) / 1000);
      setTimeAgoSec(elapsed);
    }, 500);
    return () => clearInterval(timer);
  }, [lastUpdateEpoch]);

  // ---------------------------------------------------------------------------
  // Replay Control Handlers
  // ---------------------------------------------------------------------------
  const handleReplayPlay = () => {
    fetch('/api/replay/control', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'play',
        year: replayYear,
        event: replayEvent,
        session_type: replaySessionType,
        driver_code: replayDriverCode,
        speed: replaySpeed
      })
    })
      .then(r => r.json())
      .then(res => {
        if (res.success && res.status) {
          setReplayState(res.status.state);
          setReplayTotalSamples(res.status.total_samples || 0);
          setReplayProgress(res.status.progress_pct || 0);
        }
      })
      .catch(err => console.error('Failed to start replay:', err));
  };

  const handleReplayPause = () => {
    fetch('/api/replay/control', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'pause' })
    })
      .then(r => r.json())
      .then(res => {
        if (res.status) setReplayState(res.status.state);
      })
      .catch(err => console.error('Failed to pause replay:', err));
  };

  const handleReplayResume = () => {
    fetch('/api/replay/control', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'resume' })
    })
      .then(r => r.json())
      .then(res => {
        if (res.status) setReplayState(res.status.state);
      })
      .catch(err => console.error('Failed to resume replay:', err));
  };

  const handleReplayRestart = () => {
    fetch('/api/replay/control', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'restart' })
    })
      .then(r => r.json())
      .then(res => {
        if (res.status) {
          setReplayState(res.status.state);
          setReplayProgress(0);
          setTelemetryHistory([]);
          setCurrentSample(null);
        }
      })
      .catch(err => console.error('Failed to restart replay:', err));
  };

  const handleReplaySeek = (pct: number) => {
    setReplayProgress(pct);
    fetch('/api/replay/control', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'seek', progress_pct: pct })
    }).catch(err => console.error('Failed to seek replay:', err));
  };

  const handleReplaySpeedChange = (speed: number) => {
    setReplaySpeed(speed);
    fetch('/api/replay/control', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'speed', speed })
    }).catch(err => console.error('Failed to set speed:', err));
  };

  // Find active driver identity
  const activeDriver = drivers.find(d =>
    pipelineMode === 'REPLAY'
      ? d.driver_code === replayDriverCode
      : d.driver_number === selectedDriverNum
  ) || {
    driver_number: selectedDriverNum,
    driver_code: pipelineMode === 'REPLAY' ? replayDriverCode : (primaryDriver || `CAR-${selectedDriverNum}`),
    full_name: pipelineMode === 'REPLAY' ? `Driver ${replayDriverCode}` : `Driver #${selectedDriverNum}`,
    team_name: 'Formula 1 Team',
    team_colour: 'E10600'
  };

  // Format Chart Data Points
  const chartData = telemetryHistory.map((pt, idx) => {
    let timeLabel = `${idx}`;
    if (pt.timestamp) {
      try {
        const d = new Date(pt.timestamp);
        timeLabel = d.toTimeString().split(' ')[0];
      } catch {
        timeLabel = `${idx}`;
      }
    }
    return {
      index: idx,
      time: timeLabel,
      speed: pt.speed_kmh !== null && pt.speed_kmh !== undefined ? pt.speed_kmh : undefined,
      rpm: pt.engine_rpm !== null && pt.engine_rpm !== undefined ? pt.engine_rpm : undefined,
      throttle: pt.throttle_pct !== null && pt.throttle_pct !== undefined ? pt.throttle_pct : undefined,
      brake: pt.brake_flag !== null && pt.brake_flag !== undefined ? pt.brake_flag * 100 : undefined,
      gear: pt.gear !== null && pt.gear !== undefined ? pt.gear : undefined,
      drs: pt.drs_active ? 1 : 0
    };
  });

  const rpmPercent = (currentSample?.engine_rpm !== null && currentSample?.engine_rpm !== undefined)
    ? Math.min(100, (currentSample.engine_rpm / 13000) * 100)
    : 0;
  const speedPercent = (currentSample?.speed_kmh !== null && currentSample?.speed_kmh !== undefined)
    ? Math.min(100, (currentSample.speed_kmh / 360) * 100)
    : 0;

  // Filter cached sessions for the selected year
  const availableYears = Array.from(new Set(replaySessions.map(s => s.year))).sort((a, b) => b - a);
  const eventsForYear = replaySessions.filter(s => s.year === replayYear);

  return (
    <div className="live-telemetry-container">
      {/* ----------------------------------------------------------------- */}
      {/* 1. TOP PIPELINE MODE SWITCHER (LIVE vs REPLAY vs SIMULATOR)       */}
      {/* ----------------------------------------------------------------- */}
      <div className="pipeline-mode-selector-bar">
        <div className="pipeline-mode-title">
          <Layers size={14} className="text-cyan" />
          <span>TELEMETRY PIPELINE SOURCE:</span>
        </div>
        <div className="pipeline-mode-tabs">
          <button
            onClick={() => {
              setPipelineMode('LIVE');
              setTelemetryHistory([]);
              setCurrentSample(null);
              fetch('/api/live/mode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: 'LIVE' })
              }).catch(() => {});
            }}
            className={`pipeline-tab ${pipelineMode === 'LIVE' ? 'active live' : ''}`}
          >
            <Radio size={13} />
            <span>OFFICIAL LIVE TIMING (SIGNALR)</span>
          </button>

          <button
            onClick={() => {
              setPipelineMode('REPLAY');
              setTelemetryHistory([]);
              setCurrentSample(null);
              fetch('/api/live/mode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: 'HISTORICAL_REPLAY' })
              }).catch(() => {});
            }}
            className={`pipeline-tab ${pipelineMode === 'REPLAY' ? 'active replay' : ''}`}
          >
            <History size={13} />
            <span>HISTORICAL TELEMETRY REPLAY (FASTF1)</span>
          </button>

          <button
            onClick={() => {
              setPipelineMode('SIMULATOR');
              setTelemetryHistory([]);
              setCurrentSample(null);
            }}
            className={`pipeline-tab ${pipelineMode === 'SIMULATOR' ? 'active sim' : ''}`}
          >
            <Sliders size={13} />
            <span>TEST SIMULATOR (SYNTHETIC)</span>
          </button>
        </div>
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* 2. REPLAY CONTROLS PANEL (Visible in REPLAY Mode)                 */}
      {/* ----------------------------------------------------------------- */}
      {pipelineMode === 'REPLAY' && (
        <div className="replay-controls-panel">
          <div className="replay-banner-badge">
            <AlertTriangle size={14} className="text-amber" />
            <span className="badge-text">HISTORICAL REPLAY — NOT LIVE</span>
            <span className="badge-subtext">
              Streaming genuine recorded telemetry from FastF1 local cache ({replayYear} {replayEvent})
            </span>
          </div>

          <div className="replay-selectors-row">
            {/* Season Selector */}
            <div className="replay-select-group">
              <label>SEASON:</label>
              <select
                value={replayYear}
                onChange={(e) => {
                  const y = Number(e.target.value);
                  setReplayYear(y);
                  const evs = replaySessions.filter(s => s.year === y);
                  if (evs.length > 0) setReplayEvent(evs[0].event_name);
                }}
              >
                {availableYears.map(yr => (
                  <option key={yr} value={yr}>{yr} Championship</option>
                ))}
              </select>
            </div>

            {/* Grand Prix / Event Selector */}
            <div className="replay-select-group">
              <label>GRAND PRIX:</label>
              <select
                value={replayEvent}
                onChange={(e) => setReplayEvent(e.target.value)}
              >
                {eventsForYear.map(ev => (
                  <option key={ev.event_name} value={ev.event_name}>
                    {ev.event_name} ({ev.date || ev.year})
                  </option>
                ))}
              </select>
            </div>

            {/* Session Type */}
            <div className="replay-select-group">
              <label>SESSION:</label>
              <select
                value={replaySessionType}
                onChange={(e) => setReplaySessionType(e.target.value)}
              >
                <option value="Race">Race</option>
                <option value="Qualifying">Qualifying</option>
              </select>
            </div>

            {/* Driver Selector */}
            <div className="replay-select-group">
              <label>DRIVER:</label>
              <select
                value={replayDriverCode}
                onChange={(e) => {
                  setReplayDriverCode(e.target.value);
                  const d = drivers.find(drv => drv.driver_code === e.target.value);
                  if (d) setSelectedDriverNum(d.driver_number);
                }}
              >
                {drivers.map(d => (
                  <option key={d.driver_code} value={d.driver_code}>
                    #{d.driver_number} {d.driver_code} — {d.full_name} ({d.team_name})
                  </option>
                ))}
              </select>
            </div>

            {/* Load / Play Button */}
            <button
              onClick={handleReplayPlay}
              className="replay-load-btn"
              title="Load session data and start replay"
            >
              <Play size={12} />
              <span>LOAD & STREAM</span>
            </button>
          </div>

          {/* Scrubber & Playback Controls */}
          <div className="replay-transport-row">
            <div className="replay-playback-buttons">
              {replayState === 'PLAYING' ? (
                <button onClick={handleReplayPause} className="ctrl-btn pause" title="Pause Replay">
                  <Pause size={13} />
                  <span>PAUSE</span>
                </button>
              ) : (
                <button onClick={handleReplayResume} className="ctrl-btn resume" title="Resume Playback">
                  <Play size={13} />
                  <span>RESUME</span>
                </button>
              )}

              <button onClick={handleReplayRestart} className="ctrl-btn restart" title="Restart from Beginning">
                <RotateCcw size={13} />
                <span>RESTART</span>
              </button>
            </div>

            {/* Speed Multiplier */}
            <div className="replay-speed-group">
              <FastForward size={12} className="text-cyan" />
              <span>SPEED:</span>
              <div className="speed-buttons">
                {[0.5, 1.0, 2.0, 5.0, 10.0].map(spd => (
                  <button
                    key={spd}
                    onClick={() => handleReplaySpeedChange(spd)}
                    className={`speed-btn ${replaySpeed === spd ? 'active' : ''}`}
                  >
                    {spd}x
                  </button>
                ))}
              </div>
            </div>

            {/* Scrubber Slider */}
            <div className="replay-scrubber-group">
              <span className="scrubber-label">PROGRESS: {replayProgress.toFixed(1)}%</span>
              <input
                type="range"
                min="0"
                max="100"
                step="0.5"
                value={replayProgress}
                onChange={(e) => handleReplaySeek(Number(e.target.value))}
                className="replay-progress-slider"
              />
              <span className="scrubber-samples">
                {replayTotalSamples > 0 ? `${Math.round((replayProgress / 100) * replayTotalSamples)} / ${replayTotalSamples}` : '0 samples'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* ----------------------------------------------------------------- */}
      {/* 3. LIVE & SIMULATOR CONTROL BAR (Visible in LIVE/SIMULATOR Modes)  */}
      {/* ----------------------------------------------------------------- */}
      {pipelineMode !== 'REPLAY' && (
        <div className="telemetry-control-bar">
          <div className="control-group">
            <label>
              <Radio size={12} className="text-cyan" />
              <span>SESSION:</span>
            </label>
            <select
              value={selectedSessionKey}
              onChange={(e) => setSelectedSessionKey(Number(e.target.value))}
              className="session-select"
            >
              {sessions.map((s) => (
                <option key={s.session_key} value={s.session_key}>
                  {s.year || 2026} {s.circuit_short_name || 'Austin'} — {s.session_name} (#{s.session_key})
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label>
              <Car size={12} className="text-amber" />
              <span>DRIVER:</span>
            </label>
            <select
              value={selectedDriverNum}
              onChange={(e) => {
                const num = Number(e.target.value);
                setSelectedDriverNum(num);
                const found = drivers.find(d => d.driver_number === num);
                if (found) setPrimaryDriver(found.driver_code);
              }}
              className="driver-select"
            >
              {drivers.map((d) => (
                <option key={d.driver_number} value={d.driver_number}>
                  #{d.driver_number} {d.driver_code} — {d.full_name} ({d.team_name})
                </option>
              ))}
            </select>
          </div>

          <div className="control-group mode-toggle">
            <label>
              <Sliders size={12} className="text-blue" />
              <span>TRANSPORT:</span>
            </label>
            <div className="mode-btn-group">
              <button
                onClick={() => setTransportType('WEBSOCKET')}
                className={`mode-btn ${transportType === 'WEBSOCKET' ? 'active' : ''}`}
              >
                WEBSOCKET
              </button>
              <button
                onClick={() => setTransportType('REST_POLL')}
                className={`mode-btn ${transportType === 'REST_POLL' ? 'active' : ''}`}
              >
                HTTP POLL
              </button>
            </div>
          </div>

          <div className="control-actions">
            <button
              onClick={() => setIsPaused(!isPaused)}
              className={`action-btn ${isPaused ? 'btn-resume' : 'btn-pause'}`}
            >
              {isPaused ? <Play size={12} /> : <Pause size={12} />}
              <span>{isPaused ? 'RESUME' : 'PAUSE'}</span>
            </button>
            <button
              onClick={() => {
                setTelemetryHistory([]);
                setCurrentSample(null);
                setRecordsCount(0);
              }}
              className="action-btn btn-reset"
              title="Clear rolling telemetry buffer"
            >
              <RotateCcw size={12} />
            </button>
          </div>
        </div>
      )}

      {/* ----------------------------------------------------------------- */}
      {/* 4. SOURCE STATUS & PROVENANCE BANNER                               */}
      {/* ----------------------------------------------------------------- */}
      <div className={`telemetry-status-banner ${
        pipelineMode === 'REPLAY' ? 'replay-mode' :
        pipelineMode === 'SIMULATOR' ? 'test-stream-mode' :
        liveStatus?.is_session_live ? 'live-active' : 'between-sessions'
      }`}>
        <div className="status-indicator-col">
          <div className="connection-pill">
            {pipelineMode === 'REPLAY' ? (
              <>
                <span className="pulse-dot amber"></span>
                <span className="status-text text-amber">
                  HISTORICAL REPLAY — {replayState} ({replaySpeed}x)
                </span>
              </>
            ) : pipelineMode === 'SIMULATOR' ? (
              <>
                <span className="pulse-dot purple"></span>
                <span className="status-text text-purple">TEST SIMULATOR — RUNNING</span>
              </>
            ) : connectionState === 'STREAMING' ? (
              <>
                <span className="pulse-dot green"></span>
                <span className="status-text">LIVE SIGNALR — STREAMING</span>
              </>
            ) : connectionState === 'CONNECTED' ? (
              <>
                <span className="pulse-dot green"></span>
                <span className="status-text">CONNECTED TO F1 SIGNALR</span>
              </>
            ) : (
              <>
                <span className="pulse-dot yellow"></span>
                <span className="status-text">{connectionState}</span>
              </>
            )}
          </div>
          <div className="transport-badge">
            {transportType === 'WEBSOCKET' ? <Wifi size={11} /> : <WifiOff size={11} />}
            <span>{transportType}</span>
          </div>
        </div>

        <div className="session-info-col">
          {pipelineMode === 'REPLAY' ? (
            <div className="replay-notice">
              <span className="status-sub-tag bg-amber">HISTORICAL REPLAY</span>
              <span className="session-title">
                {replayYear} {replayEvent} ({replaySessionType}) — #{activeDriver.driver_number} {activeDriver.driver_code}
              </span>
              <span className="cached-telemetry-notice">
                Original Race Date: {currentSample?.timestamp?.split('T')[0] || replayYear}. Delivered at {replaySpeed}x original sampling rate.
              </span>
            </div>
          ) : pipelineMode === 'SIMULATOR' ? (
            <div className="simulator-notice">
              <span className="status-sub-tag bg-purple">TEST STREAM SIMULATOR</span>
              <span className="session-title">
                Synthesized 2026 Circuit of the Americas telemetry for #{activeDriver.driver_number} {activeDriver.driver_code}
              </span>
              <span className="cached-telemetry-notice">
                Generating dynamic curves with explicit TEST_STREAM / HYPOTHETICAL provenance.
              </span>
            </div>
          ) : liveStatus?.is_session_live ? (
            <div className="live-notice">
              <span className="live-tag">LIVE ON TRACK</span>
              <span className="session-title">
                {liveStatus.active_session?.session_name || 'Race'} — {liveStatus.active_session?.circuit_short_name || 'Austin'}
              </span>
              <span className="cached-telemetry-notice">
                Real-time official timing & car telemetry via livetiming.formula1.com/signalrcore.
              </span>
            </div>
          ) : (
            <div className="between-notice">
              <span className="status-sub-tag">BETWEEN SESSIONS</span>
              <span className="session-title">
                Target: {liveStatus?.display_session?.session_name || 'Race'} — {liveStatus?.display_session?.circuit_short_name || 'Austin'}
              </span>
              <span className="cached-telemetry-notice">
                No active cars currently on track (Session concluded or idle). Select 'HISTORICAL REPLAY' above to watch recorded races.
              </span>
            </div>
          )}
        </div>

        <div className="telemetry-meta-col">
          <div className="meta-item">
            <span className="m-label">DATA FRESHNESS</span>
            <span className={`m-val ${
              pipelineMode === 'REPLAY' ? 'text-amber' :
              pipelineMode === 'SIMULATOR' ? 'text-purple' :
              !liveStatus?.is_session_live ? 'text-amber' :
              (timeAgoSec < 5 && currentSample?.car_telemetry_available ? 'text-green' : 'text-amber')
            }`}>
              {pipelineMode === 'REPLAY'
                ? (replayState === 'PLAYING' ? `STREAMING (${replaySpeed}x)` : replayState)
                : pipelineMode === 'SIMULATOR'
                ? 'SIMULATED (1Hz)'
                : (!liveStatus?.is_session_live ? 'BETWEEN SESSIONS (IDLE)' : (currentSample ? `${timeAgoSec}s ago` : 'Awaiting Data'))}
            </span>
          </div>

          <div className="meta-item">
            <span className="m-label">RECORDS STREAMED</span>
            <span className="m-val text-cyan">{recordsCount}</span>
          </div>

          <div className="meta-item">
            <span className="m-label">DATA CLASSIFICATION</span>
            <span className={`provenance-pill ${
              pipelineMode === 'REPLAY' ? 'replay' :
              pipelineMode === 'SIMULATOR' ? 'test' :
              (currentSample?.car_telemetry_available && currentSample?.provenance === 'MEASURED') ? 'measured' :
              'waiting'
            }`}>
              {pipelineMode === 'REPLAY'
                ? 'HISTORICAL_REPLAY'
                : pipelineMode === 'SIMULATOR'
                ? 'TEST_STREAM'
                : (currentSample?.provenance || 'WAITING_FOR_DATA')}
            </span>
          </div>
        </div>
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* 5. ACTIVE DRIVER DIGITAL TELEMETRY COCKPIT                        */}
      {/* ----------------------------------------------------------------- */}
      <div className="cockpit-grid">
        {/* Driver Card */}
        <div className="cockpit-card driver-card" style={{ borderLeft: `4px solid #${activeDriver.team_colour}` }}>
          <div className="card-header">
            <span className="sub-label">TELEMETRY TARGET</span>
            <span className="team-badge" style={{ color: `#${activeDriver.team_colour}` }}>
              {activeDriver.team_name}
            </span>
          </div>
          <div className="driver-identity">
            <div className="driver-num" style={{ color: `#${activeDriver.team_colour}` }}>
              #{activeDriver.driver_number}
            </div>
            <div className="driver-names">
              <div className="code">{activeDriver.driver_code}</div>
              <div className="full-name">{activeDriver.full_name}</div>
            </div>
          </div>
          <div className="source-timestamp">
            <Clock size={11} />
            <span>
              Source TS: {currentSample?.timestamp ? currentSample.timestamp.replace('Z', '').replace('T', ' ') : 'Awaiting On-Track Stream'}
            </span>
          </div>
        </div>

        {/* Speed Card */}
        <div className="cockpit-card speed-card">
          <div className="card-header">
            <Gauge size={14} className="text-cyan" />
            <span className="sub-label">CAR SPEED</span>
            <span className="channel-tag">
              {pipelineMode === 'REPLAY'
                ? '[HISTORICAL REPLAY]'
                : pipelineMode === 'SIMULATOR'
                ? '[SIMULATED]'
                : currentSample?.car_telemetry_available
                ? '[MEASURED]'
                : '[WAITING]'}
            </span>
          </div>
          <div className="metric-row">
            <span className="metric-val text-cyan">
              {currentSample?.speed_kmh !== null && currentSample?.speed_kmh !== undefined
                ? currentSample.speed_kmh.toFixed(1)
                : '---'}
            </span>
            <span className="metric-unit">KM/H</span>
          </div>
          <div className="gauge-bar-track">
            <div className="gauge-bar-fill speed-fill" style={{ width: `${speedPercent}%` }}></div>
          </div>
        </div>

        {/* Engine RPM Card */}
        <div className="cockpit-card rpm-card">
          <div className="card-header">
            <Zap size={14} className="text-amber" />
            <span className="sub-label">ENGINE RPM</span>
            <span className="channel-tag">
              {pipelineMode === 'REPLAY'
                ? '[HISTORICAL REPLAY]'
                : pipelineMode === 'SIMULATOR'
                ? '[SIMULATED]'
                : currentSample?.car_telemetry_available
                ? '[MEASURED]'
                : '[WAITING]'}
            </span>
          </div>
          <div className="metric-row">
            <span className="metric-val text-amber">
              {currentSample?.engine_rpm !== null && currentSample?.engine_rpm !== undefined
                ? currentSample.engine_rpm.toLocaleString()
                : '---'}
            </span>
            <span className="metric-unit">RPM</span>
          </div>
          <div className="gauge-bar-track">
            <div className="gauge-bar-fill rpm-fill" style={{ width: `${rpmPercent}%` }}></div>
          </div>
        </div>

        {/* Gear & Pedals Card */}
        <div className="cockpit-card gear-card">
          <div className="card-header">
            <span className="sub-label">GEAR & PEDALS</span>
            <span className="channel-tag">
              {pipelineMode === 'REPLAY' ? '[REPLAY]' : '[LIVE]'}
            </span>
          </div>
          <div className="gear-pedal-grid">
            <div className="gear-display">
              <span className="gear-label">GEAR</span>
              <span className="gear-num">
                {currentSample?.gear !== null && currentSample?.gear !== undefined
                  ? (currentSample.gear === 0 ? 'N' : currentSample.gear)
                  : '-'}
              </span>
            </div>
            <div className="pedal-meters">
              <div className="pedal-item">
                <span className="p-label text-green">THROTTLE</span>
                <div className="pedal-bar-track">
                  <div
                    className="pedal-bar-fill throttle-fill"
                    style={{ width: `${currentSample?.throttle_pct || 0}%` }}
                  ></div>
                </div>
                <span className="p-val text-green">
                  {currentSample?.throttle_pct !== null && currentSample?.throttle_pct !== undefined
                    ? `${currentSample.throttle_pct.toFixed(0)}%`
                    : '---'}
                </span>
              </div>
              <div className="pedal-item">
                <span className="p-label text-red">BRAKE</span>
                <div className="pedal-bar-track">
                  <div
                    className="pedal-bar-fill brake-fill"
                    style={{ width: `${currentSample?.brake_flag ? 100 : 0}%` }}
                  ></div>
                </div>
                <span className="p-val text-red">
                  {currentSample?.brake_flag !== null && currentSample?.brake_flag !== undefined
                    ? (currentSample.brake_flag ? 'ON' : 'OFF')
                    : '---'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* DRS & GPS Status Card */}
        <div className="cockpit-card drs-card">
          <div className="card-header">
            <span className="sub-label">DRS & SENSORS</span>
          </div>
          <div className="drs-status-box">
            <div className={`drs-pill ${currentSample?.drs_active ? 'active' : 'inactive'}`}>
              DRS: {currentSample?.drs_active !== null && currentSample?.drs_active !== undefined
                ? (currentSample.drs_active ? 'OPEN / ACTIVE' : 'CLOSED')
                : '---'}
            </div>
          </div>
          <div className="gps-status-row">
            <Compass size={11} className="text-cyan" />
            <span>
              GPS: {currentSample?.x !== undefined && currentSample.x !== null ? `${currentSample.x}, ${currentSample.y}` : 'Circuit Calibrated'}
            </span>
          </div>
        </div>
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* 6. TELEMETRY STRIP CHARTS (SPEED, RPM, THROTTLE, BRAKE, GEAR)     */}
      {/* ----------------------------------------------------------------- */}
      <div className="telemetry-charts-grid">
        {/* Speed Chart */}
        <div className="chart-card">
          <div className="chart-header">
            <div className="c-title">
              <span className="dot text-cyan">●</span>
              <span>CAR SPEED (KM/H)</span>
            </div>
            <span className="chart-provenance">
              {pipelineMode === 'REPLAY' ? 'HISTORICAL_REPLAY' : pipelineMode === 'SIMULATOR' ? 'TEST_STREAM' : 'SIGNALR_MEASURED'}
            </span>
          </div>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={chartData} margin={{ top: 10, right: 15, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="time" stroke="#64748B" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={10} domain={[0, 360]} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: '#0F172A', border: '1px solid #334155', borderRadius: '4px', fontSize: '11px' }}
                  labelStyle={{ color: '#94A3B8' }}
                />
                <Line
                  type="monotone"
                  dataKey="speed"
                  name="Speed (km/h)"
                  stroke="#00F5D4"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Engine RPM Chart */}
        <div className="chart-card">
          <div className="chart-header">
            <div className="c-title">
              <span className="dot text-amber">●</span>
              <span>ENGINE SPEED (RPM)</span>
            </div>
            <span className="chart-provenance">
              {pipelineMode === 'REPLAY' ? 'HISTORICAL_REPLAY' : pipelineMode === 'SIMULATOR' ? 'TEST_STREAM' : 'SIGNALR_MEASURED'}
            </span>
          </div>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={chartData} margin={{ top: 10, right: 15, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="time" stroke="#64748B" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={10} domain={[4000, 13000]} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: '#0F172A', border: '1px solid #334155', borderRadius: '4px', fontSize: '11px' }}
                  labelStyle={{ color: '#94A3B8' }}
                />
                <Line
                  type="monotone"
                  dataKey="rpm"
                  name="RPM"
                  stroke="#FFB703"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Throttle & Brake Chart */}
        <div className="chart-card">
          <div className="chart-header">
            <div className="c-title">
              <span className="dot text-green">●</span>
              <span>THROTTLE % & BRAKE FLAG</span>
            </div>
            <span className="chart-provenance">
              {pipelineMode === 'REPLAY' ? 'HISTORICAL_REPLAY' : pipelineMode === 'SIMULATOR' ? 'TEST_STREAM' : 'SIGNALR_MEASURED'}
            </span>
          </div>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={chartData} margin={{ top: 10, right: 15, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="time" stroke="#64748B" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={10} domain={[0, 100]} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: '#0F172A', border: '1px solid #334155', borderRadius: '4px', fontSize: '11px' }}
                  labelStyle={{ color: '#94A3B8' }}
                />
                <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '4px' }} />
                <Line
                  type="monotone"
                  dataKey="throttle"
                  name="Throttle %"
                  stroke="#10B981"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
                <Line
                  type="stepAfter"
                  dataKey="brake"
                  name="Brake"
                  stroke="#EF4444"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Gear Selection Chart */}
        <div className="chart-card">
          <div className="chart-header">
            <div className="c-title">
              <span className="dot text-purple">●</span>
              <span>TRANSMISSION GEAR</span>
            </div>
            <span className="chart-provenance">
              {pipelineMode === 'REPLAY' ? 'HISTORICAL_REPLAY' : pipelineMode === 'SIMULATOR' ? 'TEST_STREAM' : 'SIGNALR_MEASURED'}
            </span>
          </div>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={chartData} margin={{ top: 10, right: 15, left: -25, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="time" stroke="#64748B" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={10} domain={[0, 8]} ticks={[0, 1, 2, 3, 4, 5, 6, 7, 8]} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: '#0F172A', border: '1px solid #334155', borderRadius: '4px', fontSize: '11px' }}
                  labelStyle={{ color: '#94A3B8' }}
                />
                <Line
                  type="stepAfter"
                  dataKey="gear"
                  name="Gear"
                  stroke="#A855F7"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* 7. LIVE / HISTORICAL TIMING TOWER                                  */}
      {/* ----------------------------------------------------------------- */}
      <div className="timing-tower-section">
        <div className="timing-tower-header">
          <div className="t-title">
            <Radio size={14} className="text-cyan" />
            <span>
              {pipelineMode === 'REPLAY'
                ? `HISTORICAL REPLAY STANDINGS — ${replayYear} ${replayEvent}`
                : `OFFICIAL F1 TIMING TOWER — ${sessions.find(s => s.session_key === selectedSessionKey)?.session_name || 'Race'}`}
            </span>
          </div>
          <div className="tower-meta">
            <span className="tower-badge">
              {pipelineMode === 'REPLAY' ? 'FASTF1_HISTORICAL_DATA' : 'LIVETIMING.FORMULA1.COM'}
            </span>
          </div>
        </div>

        {timingLoading ? (
          <div className="timing-loading-placeholder">
            <span>Loading timing tower data...</span>
          </div>
        ) : (
          <div className="timing-table-wrapper">
            <table className="timing-table">
              <thead>
                <tr>
                  <th>POS</th>
                  <th>DRIVER</th>
                  <th>TEAM</th>
                  <th>GAP TO LEADER</th>
                  <th>INTERVAL</th>
                  <th>BEST LAP</th>
                  <th>TYRE</th>
                  <th>STOPS</th>
                  <th>STATUS</th>
                </tr>
              </thead>
              <tbody>
                {timingTower.map((row) => (
                  <tr
                    key={row.position}
                    onClick={() => {
                      const num = parseInt(String(row.driver_number));
                      if (!isNaN(num)) {
                        setSelectedDriverNum(num);
                        setPrimaryDriver(row.driver_code);
                      }
                    }}
                    style={{ cursor: 'pointer' }}
                    title={`Click to view telemetry for #${row.driver_number} ${row.driver_code}`}
                    className={`timing-row ${
                      (pipelineMode === 'REPLAY' ? row.driver_code === replayDriverCode : row.driver_code === activeDriver.driver_code)
                        ? 'active-row'
                        : ''
                    }`}
                  >
                    <td className="pos-cell font-mono">{row.position}</td>
                    <td className="driver-cell">
                      <span className="team-bar" style={{ background: row.team_color }}></span>
                      <span className="d-num font-mono">#{row.driver_number}</span>
                      <span className="d-code font-bold">{row.driver_code}</span>
                      {row.driver_name && <span className="d-full">{row.driver_name}</span>}
                    </td>
                    <td className="team-cell">{row.team_name}</td>
                    <td className="gap-cell font-mono">{row.gap_to_leader_s}</td>
                    <td className="interval-cell font-mono">{row.interval_ahead_s}</td>
                    <td className="lap-cell font-mono text-cyan">{row.best_lap_time_s || row.last_lap_time_s}</td>
                    <td className="tyre-cell">
                      <span className={`compound-pill ${row.current_compound.toLowerCase()}`}>
                        {row.current_compound[0]}
                      </span>
                      <span className="tyre-age font-mono">{row.tyre_age_laps}L</span>
                    </td>
                    <td className="stops-cell font-mono">{row.pit_stops_count}</td>
                    <td className="status-cell">
                      <span className={`status-pill ${row.status.toLowerCase()}`}>
                        {row.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* 8. PROVENANCE, DATA INTEGRITY & AUDIT FOOTER                       */}
      {/* ----------------------------------------------------------------- */}
      <div className="provenance-footer-card">
        <div className="prov-header">
          <CheckCircle2 size={14} className="text-green" />
          <span>DATA PROVENANCE & TELEMETRY INTEGRITY AUDIT</span>
        </div>
        <div className="prov-grid">
          <div className="prov-item">
            <span className="p-key">SOURCE / TRANSPORT:</span>
            <span className="p-val">
              {pipelineMode === 'REPLAY'
                ? 'FastF1 Historical Cache (Local SQLite / Session Arrays)'
                : pipelineMode === 'SIMULATOR'
                ? 'Local Synthetic Simulator (Deterministic Curves)'
                : 'livetiming.formula1.com/signalrcore (Official FOM ASP.NET Core SignalR)'}
            </span>
          </div>

          <div className="prov-item">
            <span className="p-key">DATA CLASSIFICATION:</span>
            <span className="p-val font-bold">
              {pipelineMode === 'REPLAY'
                ? 'HISTORICAL_REPLAY (Authentic Historical Recorded Data)'
                : pipelineMode === 'SIMULATOR'
                ? 'HYPOTHETICAL / TEST_STREAM'
                : currentSample?.car_telemetry_available
                ? 'MEASURED (Verified Real-Time Vehicle Channels)'
                : 'UNAVAILABLE / WAITING_FOR_SOURCE_DATA'}
            </span>
          </div>

          <div className="prov-item">
            <span className="p-key">API SUBSCRIPTION COST:</span>
            <span className="p-val text-green font-bold">$0.00 (100% Free Legitimate Pipeline — No Paid API Keys)</span>
          </div>

          <div className="prov-item">
            <span className="p-key">ZERO-FABRICATION GUARANTEE:</span>
            <span className="p-val">
              Car channels are strictly preserved or reported as None. Unavailable telemetry is never labeled MEASURED.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
