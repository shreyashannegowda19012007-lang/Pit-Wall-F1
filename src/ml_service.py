import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from src.tyre_analytics import TyreAnalyticsEngine
from src.data_providers import get_provider
from src.session_utils import parse_session_id, pick_driver_laps
import logging

logger = logging.getLogger(__name__)

class MLService:
    _model_cache = {}

    @staticmethod
    def _build_baseline_model():
        """Constructs a calibrated motorsport Random Forest baseline trained across canonical degradation envelopes."""
        compounds = ['SOFT', 'MEDIUM', 'HARD']
        X = []
        y = []
        # Generate representative grid: compound (0, 1, 2), fuel (10 to 110kg), track_temp (25 to 50 C)
        base_degs = {'SOFT': 0.115, 'MEDIUM': 0.078, 'HARD': 0.048}
        np.random.seed(42)
        for comp_idx, comp in enumerate(compounds):
            base = base_degs[comp]
            for fuel in np.linspace(10, 110, 12):
                for temp in np.linspace(25, 50, 12):
                    # Physical deg sensitivity: +0.0018s/lap per deg C, +0.00035s/lap per kg fuel
                    deg = base + (temp - 30.0) * 0.0018 + (fuel - 50.0) * 0.00035
                    deg += np.random.normal(0, 0.003)
                    deg = max(0.015, min(0.35, deg))
                    X.append([comp_idx, fuel, temp])
                    y.append(deg)

        model = RandomForestRegressor(n_estimators=50, max_depth=6, random_state=42)
        model.fit(X, y)
        return {
            "model": model,
            "feature_importance": model.feature_importances_.tolist()
        }

    @staticmethod
    def train_or_get_model(session_id: str):
        if session_id in MLService._model_cache:
            return MLService._model_cache[session_id]

        year, event, session_type = parse_session_id(session_id)

        compounds = ['SOFT', 'MEDIUM', 'HARD']
        X = []
        y = []

        try:
            provider = get_provider()
            data = provider.fetch_session_data(year, event, session_type)
            if data.get("success"):
                session = data.get("raw_session")
                weather = session.weather_data if hasattr(session, 'weather_data') else None
                total_laps = session.total_laps if hasattr(session, 'total_laps') and session.total_laps else 60
                from scipy import stats

                if hasattr(session, 'drivers') and hasattr(session, 'laps'):
                    for driver in session.drivers:
                        try:
                            laps = pick_driver_laps(session.laps, driver)
                            if laps.empty:
                                continue

                            quicklaps = laps.pick_quicklaps().reset_index(drop=True)
                            if quicklaps.empty:
                                continue

                            for stint, stint_laps in quicklaps.groupby('Stint'):
                                stint_laps = stint_laps.dropna(subset=['LapTime', 'TyreLife'])
                                if len(stint_laps) < 3:
                                    continue

                                compound = stint_laps['Compound'].iloc[0] if not stint_laps['Compound'].empty else "UNKNOWN"
                                if compound not in compounds:
                                    continue

                                stint_laps = stint_laps.copy()
                                stint_laps['LapTime_s'] = stint_laps['LapTime'].dt.total_seconds()
                                FUEL_EFFECT_S_PER_LAP = 0.065
                                stint_laps['FuelCorrected'] = stint_laps['LapTime_s'] + (stint_laps['LapNumber'] * FUEL_EFFECT_S_PER_LAP)

                                slope, intercept, r_value, p_value, std_err = stats.linregress(
                                    stint_laps['TyreLife'].astype(float).values,
                                    stint_laps['FuelCorrected'].astype(float).values
                                )

                                if slope < 0 or slope > 0.5:
                                    continue

                                track_temp = 32.0
                                if weather is not None and not weather.empty and 'TrackTemp' in weather.columns:
                                    track_temp = float(weather['TrackTemp'].mean())

                                start_lap = float(stint_laps['LapNumber'].iloc[0])
                                fuel = max(0.0, 110.0 - (start_lap / total_laps) * 110.0)

                                X.append([compounds.index(compound), fuel, track_temp])
                                y.append(float(slope))
                        except Exception:
                            continue
        except Exception as e:
            logger.debug(f"Session data extraction notice for ML model: {e}")

        # If session data provides >= 10 valid stints, train session-specific random forest
        if len(X) >= 10:
            model = RandomForestRegressor(n_estimators=50, random_state=42)
            model.fit(X, y)
            MLService._model_cache[session_id] = {
                "model": model,
                "feature_importance": model.feature_importances_.tolist(),
                "stints_trained": len(X),
                "is_baseline": False
            }
        else:
            # Fallback to calibrated motorsport ensemble baseline
            baseline = MLService._build_baseline_model()
            baseline["stints_trained"] = len(X)
            baseline["is_baseline"] = True
            MLService._model_cache[session_id] = baseline

        return MLService._model_cache[session_id]

    @staticmethod
    def predict_degradation(session_id: str, compound: str, fuel_kg: float, track_temp: float):
        model_data = MLService.train_or_get_model(session_id)
        model = model_data["model"]

        compounds = ['SOFT', 'MEDIUM', 'HARD']
        if str(compound).upper() not in compounds:
            clean_compound = 'MEDIUM'
        else:
            clean_compound = str(compound).upper()

        X_test = [[compounds.index(clean_compound), float(fuel_kg), float(track_temp)]]
        pred = float(model.predict(X_test)[0])

        feat_imp = model_data.get("feature_importance", [0.55, 0.20, 0.25])
        # Ensure sum to 1.0
        total_imp = sum(feat_imp) if sum(feat_imp) > 0 else 1.0
        norm_imp = [round(x / total_imp, 3) for x in feat_imp]

        return {
            "success": True,
            "prediction_s_per_lap": round(max(0.01, pred), 4),
            "feature_importance": {
                "compound": norm_imp[0],
                "fuel_load": norm_imp[1],
                "track_temp": norm_imp[2]
            },
            "is_calibrated_baseline": model_data.get("is_baseline", False)
        }
