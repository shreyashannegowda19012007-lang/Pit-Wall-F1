import React, { useState } from 'react';
import './MLLabPage.css';

interface MLPrediction {
  success: boolean;
  prediction_s_per_lap: number;
  feature_importance: {
    compound: number;
    fuel_load: number;
    track_temp: number;
  };
}

export const MLLabPage: React.FC = () => {
  const [compound, setCompound] = useState('MEDIUM');
  const [fuelKg, setFuelKg] = useState(100);
  const [trackTemp, setTrackTemp] = useState(35);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MLPrediction | null>(null);

  const runPrediction = async () => {
    setLoading(true);
    setError(null);
    try {
      const url = `http://localhost:8000/api/ml/predict?session_id=S-2024-SPAIN&compound=${compound}&fuel_kg=${fuelKg}&track_temp=${trackTemp}`;
      const response = await fetch(url);
      if (!response.ok) throw new Error('Prediction failed');
      const data: MLPrediction = await response.json();
      if (data.success) {
        setResult(data);
      } else {
        setError('Model error');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ml-container">
      <header className="ml-header">
        <div className="title-section">
          <h2><span className="material-icons">model_training</span> ML Model Lab</h2>
          <span className="session-badge">S-2024-SPAIN</span>
        </div>
        <p className="subtitle">Predict tyre degradation using Random Forest Regression</p>
      </header>

      <div className="ml-content">
        <div className="input-panel">
          <h3>Simulation Parameters</h3>

          <div className="form-group">
            <label>Tyre Compound</label>
            <select value={compound} onChange={e => setCompound(e.target.value)}>
              <option value="SOFT">Soft</option>
              <option value="MEDIUM">Medium</option>
              <option value="HARD">Hard</option>
            </select>
          </div>

          <div className="form-group">
            <label>Starting Fuel (kg): {fuelKg}</label>
            <input
              type="range"
              min="10" max="110" step="1"
              value={fuelKg}
              onChange={e => setFuelKg(Number(e.target.value))}
            />
          </div>

          <div className="form-group">
            <label>Track Temp (Â°C): {trackTemp}</label>
            <input
              type="range"
              min="25" max="50" step="1"
              value={trackTemp}
              onChange={e => setTrackTemp(Number(e.target.value))}
            />
          </div>

          <button className="predict-btn" onClick={runPrediction} disabled={loading}>
            {loading ? 'Running Inference...' : 'Run Prediction'}
          </button>
        </div>

        <div className="result-panel">
          {error && <div className="error-message">{error}</div>}
          {!result && !error && !loading && (
            <div className="empty-state">
              <span className="material-icons">science</span>
              <p>Configure parameters and run prediction to see results.</p>
            </div>
          )}

          {result && !loading && (
            <div className="prediction-results">
              <div className="primary-metric">
                <h4>Expected Degradation</h4>
                <div className="value">
                  {result.prediction_s_per_lap.toFixed(3)} <span>s/lap</span>
                </div>
              </div>

              <div className="feature-importance">
                <h4>Model Feature Importance</h4>
                <div className="bar-chart">
                  <div className="bar-row">
                    <label>Compound</label>
                    <div className="bar-track">
                      <div className="bar-fill" style={{width: `${result.feature_importance.compound * 100}%`}}></div>
                    </div>
                    <span>{(result.feature_importance.compound * 100).toFixed(1)}%</span>
                  </div>
                  <div className="bar-row">
                    <label>Fuel Load</label>
                    <div className="bar-track">
                      <div className="bar-fill" style={{width: `${result.feature_importance.fuel_load * 100}%`}}></div>
                    </div>
                    <span>{(result.feature_importance.fuel_load * 100).toFixed(1)}%</span>
                  </div>
                  <div className="bar-row">
                    <label>Track Temp</label>
                    <div className="bar-track">
                      <div className="bar-fill" style={{width: `${result.feature_importance.track_temp * 100}%`}}></div>
                    </div>
                    <span>{(result.feature_importance.track_temp * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
