import React, { useEffect, useState, useRef, useMemo } from 'react';
import { usePitwall } from '../contexts/PitwallContext';
import { PlayCircle, Play, Pause, RefreshCw, AlertCircle } from 'lucide-react';
import './ReplayPage.css';

interface DriverData {
  t: number[];
  x: number[];
  y: number[];
  z: number[];
}

interface ReplayResponse {
  success: boolean;
  min_time_ms: number;
  max_time_ms: number;
  interval_ms: number;
  drivers: Record<string, DriverData>;
}

export const ReplayPage: React.FC = () => {
  const { session } = usePitwall();
  const [data, setData] = useState<ReplayResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progressMsg, setProgressMsg] = useState('Connecting...');

  const [currentTime, setCurrentTime] = useState<number>(0);
  const [playing, setPlaying] = useState(false);

  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    fetchReplayData();
  }, [session]);

  const fetchReplayData = async () => {
    setLoading(true);
    setError(null);
    setProgressMsg('Connecting...');

    const progressInterval = setInterval(() => {
      setProgressMsg(prev => {
        if (prev === 'Connecting...') return 'Loading telemetry coordinates (This takes a moment)...';
        if (prev === 'Loading telemetry coordinates (This takes a moment)...') return 'Parsing positional data...';
        return prev;
      });
    }, 10000);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    try {
      const activeSession = session || 'S-2024-SPAIN';
      const response = await fetch(`/api/replay/track?session_id=${activeSession}&frequency_hz=2`, { signal: controller.signal });
      if (!response.ok) throw new Error('Failed to fetch replay data');
      const json: ReplayResponse = await response.json();
      if (json.success) {
        setData(json);
        setCurrentTime(json.min_time_ms);
      } else {
        setError("Error loading positional data");
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        setError('Request Timed Out. The server took too long to load FastF1 data.');
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
      clearTimeout(timeoutId);
      clearInterval(progressInterval);
    }
  };

  // Find min/max bounds to scale the track
  const bounds = useMemo(() => {
    if (!data) return null;
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

    Object.values(data.drivers).forEach(d => {
      d.x.forEach(x => { if (x < minX) minX = x; if (x > maxX) maxX = x; });
      d.y.forEach(y => { if (y < minY) minY = y; if (y > maxY) maxY = y; });
    });

    return { minX, maxX, minY, maxY };
  }, [data]);

  const drawTrack = (ctx: CanvasRenderingContext2D, width: number, height: number) => {
    if (!data || !bounds) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#0a0a0f'; // Matches app background
    ctx.fillRect(0, 0, width, height);

    // Padding
    const pad = 40;
    const drawW = width - pad * 2;
    const drawH = height - pad * 2;

    const trackW = bounds.maxX - bounds.minX;
    const trackH = bounds.maxY - bounds.minY;

    // Maintain aspect ratio
    const scale = Math.min(drawW / trackW, drawH / trackH);

    // Center offset
    const cx = (width - trackW * scale) / 2;
    const cy = (height - trackH * scale) / 2;

    const transformX = (x: number) => cx + (x - bounds.minX) * scale;
    const transformY = (y: number) => cy + (bounds.maxY - y) * scale; // Invert Y

    // Draw the track outline (using the first driver's path as an approximation of the track)
    ctx.beginPath();
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 15;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    const refDriver = Object.values(data.drivers)[0];
    if (refDriver) {
      for (let i = 0; i < refDriver.x.length; i++) {
        const tx = transformX(refDriver.x[i]);
        const ty = transformY(refDriver.y[i]);
        if (i === 0) ctx.moveTo(tx, ty);
        else ctx.lineTo(tx, ty);
      }
    }
    ctx.stroke();

    // Draw driver dots at current time
    Object.entries(data.drivers).forEach(([num, driverData]) => {
      // Find index closest to currentTime
      let idx = Math.floor((currentTime - data.min_time_ms) / data.interval_ms);
      if (idx < 0) idx = 0;
      if (idx >= driverData.x.length) idx = driverData.x.length - 1;

      const x = transformX(driverData.x[idx]);
      const y = transformY(driverData.y[idx]);

      ctx.beginPath();
      ctx.fillStyle = num === '1' ? '#3671C6' : num === '4' ? '#FF8000' : num === '44' ? '#27F4D2' : '#ffffff';
      ctx.arc(x, y, 6, 0, 2 * Math.PI);
      ctx.fill();

      // Driver label
      ctx.fillStyle = '#fff';
      ctx.font = '10px monospace';
      ctx.fillText(num, x + 8, y + 3);
    });
  };

  useEffect(() => {
    if (!canvasRef.current || !data) return;
    const ctx = canvasRef.current.getContext('2d');
    if (ctx) {
      drawTrack(ctx, canvasRef.current.width, canvasRef.current.height);
    }
  }, [data, currentTime, bounds]);

  // Animation Loop
  const animate = () => {
    if (!data) return;
    setCurrentTime(prev => {
      let next = prev + data.interval_ms * 10; // Speed multiplier
      if (next > data.max_time_ms) {
        setPlaying(false);
        return data.min_time_ms; // loop or stop
      }
      return next;
    });
  };

  useEffect(() => {
    if (playing) {
      // Run every ~50ms
      const interval = setInterval(animate, 50);
      return () => clearInterval(interval);
    }
  }, [playing, data]);

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCurrentTime(Number(e.target.value));
  };

  return (
    <div className="replay-container">
      <header className="replay-header">
        <div className="title-section">
          <h2><PlayCircle size={24} style={{ color: '#E10600', marginRight: '8px', verticalAlign: 'middle' }} /> 3D Track Replay</h2>
          <span className="session-badge">{session || 'S-2024-SPAIN'}</span>
        </div>
      </header>

      {loading && (
        <div className="replay-loading">
          <RefreshCw size={18} className="spin-icon" style={{ marginRight: '8px', verticalAlign: 'middle' }} />
          {progressMsg}
        </div>
      )}
      {error && (
        <div className="replay-error">
          <AlertCircle size={18} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
          {error}
        </div>
      )}

      {!loading && !error && data && (
        <div className="replay-content">
          <div className="canvas-wrapper">
            <canvas
              ref={canvasRef}
              width={1000}
              height={600}
              className="track-canvas"
            />
          </div>

          <div className="replay-controls">
            <button className="play-btn" onClick={() => setPlaying(!playing)} aria-label={playing ? 'Pause' : 'Play'}>
              {playing ? <Pause size={20} /> : <Play size={20} />}
            </button>
            <input
              type="range"
              min={data.min_time_ms}
              max={data.max_time_ms}
              step={data.interval_ms}
              value={currentTime}
              onChange={handleSeek}
              className="time-slider"
            />
            <div className="time-display">
               {Math.floor((currentTime - data.min_time_ms) / 60000)}m {Math.floor(((currentTime - data.min_time_ms) % 60000) / 1000)}s
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReplayPage;

