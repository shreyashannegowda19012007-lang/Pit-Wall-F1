import React, { useState, useEffect } from 'react';
import { usePitwall } from '../contexts/PitwallContext';
import './DriversPage.css';

interface DriverInfo {
  driver_number: string;
  broadcast_name: string;
  abbreviation: string;
  team_name: string;
  team_color: string;
  position: number;
  points: number;
}

interface DriversResponse {
  success: boolean;
  session_id: string;
  drivers: DriverInfo[];
}

export const DriversPage: React.FC = () => {
  const { session } = usePitwall();
  const [drivers, setDrivers] = useState<DriverInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDrivers = async () => {
      setLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/api/drivers?session_id=${session}`);
        const data: DriversResponse = await res.json();
        if (data.success) {
          setDrivers(data.drivers);
        } else {
          setError('Failed to load drivers.');
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchDrivers();
  }, [session]);

  return (
    <div className="drivers-container">
      <header className="drivers-header">
        <div className="title-section">
          <h2><span className="material-icons">sports_motorsports</span> Drivers & Teams</h2>
          <span className="session-badge">{session}</span>
        </div>
        <p className="subtitle">Race results and entry list</p>
      </header>

      <div className="drivers-content">
        {loading && <div className="loading">Loading drivers...</div>}
        {error && <div className="error">{error}</div>}

        {!loading && !error && (
          <div className="drivers-grid">
            {drivers.map(d => (
              <div key={d.abbreviation} className="driver-card" style={{borderLeftColor: d.team_color}}>
                <div className="driver-pos">P{d.position}</div>
                <div className="driver-info">
                  <div className="driver-name">{d.broadcast_name} <span className="driver-abbr">({d.abbreviation})</span></div>
                  <div className="team-name" style={{color: d.team_color}}>{d.team_name}</div>
                </div>
                <div className="driver-num">
                  #{d.driver_number}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
