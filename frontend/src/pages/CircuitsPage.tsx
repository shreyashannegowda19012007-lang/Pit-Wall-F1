import React, { useState, useEffect } from 'react';
import './CircuitsPage.css';

interface Circuit {
  round: number;
  country: string;
  location: string;
  event_name: string;
  event_date: string;
  format: string;
}

interface CircuitsResponse {
  success: boolean;
  year: number;
  circuits: Circuit[];
}

export const CircuitsPage: React.FC = () => {
  const [circuits, setCircuits] = useState<Circuit[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCircuits = async () => {
      setLoading(true);
      try {
        const res = await fetch('http://localhost:8000/api/circuits?year=2024');
        const data: CircuitsResponse = await res.json();
        if (data.success) {
          setCircuits(data.circuits);
        } else {
          setError('Failed to load circuits.');
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchCircuits();
  }, []);

  return (
    <div className="circuits-container">
      <header className="circuits-header">
        <h2><span className="material-icons">flag</span> 2024 Championship Calendar</h2>
        <p className="subtitle">Interactive schedule for the current season</p>
      </header>

      <div className="circuits-content">
        {loading && <div className="loading">Loading calendar...</div>}
        {error && <div className="error">{error}</div>}

        {!loading && !error && (
          <div className="circuits-grid">
            {circuits.map(c => (
              <div key={c.round} className="circuit-card">
                <div className="circuit-round">Round {c.round}</div>
                <div className="circuit-name">{c.event_name}</div>
                <div className="circuit-details">
                  <span className="material-icons">location_on</span> {c.location}, {c.country}
                </div>
                <div className="circuit-date">
                  <span className="material-icons">event</span> {c.event_date}
                </div>
                {c.format === 'sprint' && (
                  <div className="sprint-badge">Sprint Weekend</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
