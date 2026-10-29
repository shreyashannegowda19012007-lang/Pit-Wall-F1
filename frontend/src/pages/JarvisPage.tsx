import React, { useState, useEffect } from 'react';
import { usePitwall } from '../contexts/PitwallContext';
import { Gauge, GitBranch, Disc, Info, Sparkles, AlertCircle } from 'lucide-react';
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
        const response = await fetch(`/api/jarvis/insights?session_id=${session}&primary_driver=${primaryDriver}&ref_driver=${referenceDriver}`);
        if (!response.ok) throw new Error('Failed to fetch tactical insights');
        const data: JarvisResponse = await response.json();
        if (data.success) {
          setInsights(data.insights);
        } else {
          setError('Failed to generate insights for current telemetry frame');
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchInsights();
  }, [session, primaryDriver, referenceDriver]);

  const renderIconForCategory = (cat: string) => {
    switch (cat) {
      case 'pace': return <Gauge size={18} />;
      case 'strategy': return <GitBranch size={18} />;
      case 'tyres': return <Disc size={18} />;
      default: return <Info size={18} />;
    }
  };

  return (
    <div className="jarvis-container">
      <header className="jarvis-header">
        <div className="title-section">
          <h2><Sparkles size={24} style={{ color: '#E10600', marginRight: '8px', verticalAlign: 'middle' }} /> JARVIS Tactical Engine</h2>
        </div>
        <p className="subtitle">Automated telemetry intelligence, delta calculations, and strategy advisories.</p>
      </header>

      <div className="jarvis-content">
        {loading && (
          <div className="insights-feed">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="insight-card" style={{ opacity: 0.7 }}>
                <div className="skeleton" style={{ width: '38px', height: '38px', borderRadius: '6px' }}></div>
                <div className="insight-body flex-1 flex-col gap-xs">
                  <div className="skeleton" style={{ width: '80px', height: '12px', marginBottom: '4px' }}></div>
                  <div className="skeleton" style={{ width: '100%', height: '16px' }}></div>
                </div>
              </div>
            ))}
          </div>
        )}
        {error && (
          <div className="jarvis-error">
            <AlertCircle size={18} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            {error}
          </div>
        )}

        {!loading && !error && insights.length > 0 && (
          <div className="insights-feed">
            {insights.map((insight, idx) => (
              <div key={idx} className={`insight-card ${insight.category}`}>
                <div className="insight-icon">
                  {renderIconForCategory(insight.category)}
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
          <div className="jarvis-loading">No active tactical warnings for {primaryDriver} vs {referenceDriver}. Telemetry normal.</div>
        )}
      </div>
    </div>
  );
};

export default JarvisPage;
