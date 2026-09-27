import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from src.tyre_analytics import TyreAnalyticsEngine
from src.data_providers import get_provider

class MLService:
    _model_cache = {}

    @staticmethod
    def train_or_get_model(session_id: str):
        if session_id in MLService._model_cache:
            return MLService._model_cache[session_id]

        # Extract real training data directly from session telemetry
        # using TyreAnalyticsEngine logic to construct features for the ML model.

        parts = session_id.split('-')
        year = int(parts[1]) if len(parts) > 1 else 2024
        event = parts[2] if len(parts) > 2 else "SPAIN"

        provider = get_provider()
        data = provider.fetch_session_data(year, event, 'R')
        if not data.get("success"):
            raise Exception("Could not load data for ML training")

        session = data["raw_session"]

        compounds = ['SOFT', 'MEDIUM', 'HARD']
        X = []
        y = []

        weather = session.weather_data if hasattr(session, 'weather_data') else None

        total_laps = session.total_laps if hasattr(session, 'total_laps') and session.total_laps else 60

        from scipy import stats

        for driver in session.drivers:
            try:
                laps = session.laps.pick_driver(driver)
                if laps.empty: continue

                quicklaps = laps.pick_quicklaps().reset_index(drop=True)
                if quicklaps.empty: continue

                for stint, stint_laps in quicklaps.groupby('Stint'):
                    stint_laps = stint_laps.dropna(subset=['LapTime', 'TyreLife'])
                    if len(stint_laps) < 3: continue

                    compound = stint_laps['Compound'].iloc[0] if not stint_laps['Compound'].empty else "UNKNOWN"
                    if compound not in compounds: continue

                    stint_laps['LapTime_s'] = stint_laps['LapTime'].dt.total_seconds()
                    FUEL_EFFECT_S_PER_LAP = 0.065
                    stint_laps['FuelCorrected'] = stint_laps['LapTime_s'] + (stint_laps['LapNumber'] * FUEL_EFFECT_S_PER_LAP)

                    slope, intercept, r_value, p_value, std_err = stats.linregress(
                        stint_laps['TyreLife'].astype(float).values,
                        stint_laps['FuelCorrected'].astype(float).values
                    )

                    if slope < 0 or slope > 0.5: continue

                    track_temp = 30.0
                    if weather is not None and not weather.empty:
                        track_temp = weather['TrackTemp'].mean()

                    start_lap = stint_laps['LapNumber'].iloc[0]
                    fuel = max(0.0, 110.0 - (start_lap / total_laps) * 110.0)

                    X.append([compounds.index(compound), fuel, track_temp])
                    y.append(slope)
            except Exception:
                continue

        if len(X) < 10:
            MLService._model_cache[session_id] = {"error": "Insufficient real training data (need at least 10 valid stints)"}
            return MLService._model_cache[session_id]

        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X, y)

        MLService._model_cache[session_id] = {
            "model": model,
            "feature_importance": model.feature_importances_.tolist()
        }

        return MLService._model_cache[session_id]

    @staticmethod
    def predict_degradation(session_id: str, compound: str, fuel_kg: float, track_temp: float):
        model_data = MLService.train_or_get_model(session_id)
        if "error" in model_data:
            return {
                "success": False,
                "error": model_data["error"]
            }
        model = model_data["model"]

        compounds = ['SOFT', 'MEDIUM', 'HARD']
        if compound not in compounds:
            compound = 'MEDIUM'

        X_test = [[compounds.index(compound), fuel_kg, track_temp]]
        pred = model.predict(X_test)[0]

        return {
            "success": True,
            "prediction_s_per_lap": round(pred, 4),
            "feature_importance": {
                "compound": round(model_data["feature_importance"][0], 3),
                "fuel_load": round(model_data["feature_importance"][1], 3),
                "track_temp": round(model_data["feature_importance"][2], 3)
            }
        }
