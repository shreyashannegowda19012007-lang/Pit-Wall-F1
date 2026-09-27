import React, { useState, useEffect } from 'react';
import { usePitwall } from '../contexts/PitwallContext';
import './JarvisPage.css';

interface JarvisInsight {
  category: 'session' | 'pace' | 'strategy' | 'tyres';
  message: string;
}

interface JarvisResponse {
  success: boolean;
  primary_driver: string;
  reference_driver: string;
  insights: JarvisInsight[];
}

export const JarvisPage: React.FC = () => {
  const { session, primaryDriver, referenceDriver } = usePitwall();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [insights, setInsights] = useState<JarvisInsight[]>([]);

  useEffect(() => {
    const fetchInsights = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`http://localhost:8000/api/jarvis/insights?session_id=${session}&primary_driver=${primaryDriver}&ref_driver=${referenceDriver}`);
        if (!response.ok) throw new Error('Failed to fetch insights');
        const data: JarvisResponse = await response.json();
        if (data.success) {
          setInsights(data.insights);
        } else {
          setError('Failed to generate insights');
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchInsights();
  }, [session, primaryDriver, referenceDriver]);

  const getIconForCategory = (cat: string) => {
    switch (cat) {
      case 'pace': return 'speed';
      case 'strategy': return 'route';
      case 'tyres': return 'radio_button_unchecked';
      default: return 'info';
    }
  };

  return (
    <div className="jarvis-container">
      <header className="jarvis-header">
        <div className="title-section">
          <h2><span className="material-icons">psychology</span> JARVIS Tactical Engine</h2>
        </div>
        <p className="subtitle">Automated strategy and performance insights.</p>
      </header>

      <div className="jarvis-content">
        {loading && <div className="jarvis-loading">Analyzing telemetry data...</div>}
        {error && <div className="jarvis-error">{error}</div>}

        {!loading && !error && insights.length > 0 && (
          <div className="insights-feed">
            {insights.map((insight, idx) => (
              <div key={idx} className={`insight-card ${insight.category}`}>
                <div className="insight-icon">
                  <span className="material-icons">{getIconForCategory(insight.category)}</span>
                </div>
                <div className="insight-body">
                  <span className="insight-category">{insight.category.toUpperCase()}</span>
                  <p>{insight.message}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && !error && insights.length === 0 && (
          <div className="jarvis-loading">No insights generated for this combination.</div>
        )}
      </div>
    </div>
  );
};
