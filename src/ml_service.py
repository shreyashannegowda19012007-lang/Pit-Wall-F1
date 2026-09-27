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

        # Generate some synthetic training data based on real session parameters
        # We use our TyreAnalyticsEngine to get baseline degradations, then perturb them
        # to create a dataset for the ML model to learn from.

        parts = session_id.split('-')
        year = int(parts[1]) if len(parts) > 1 else 2024
        event = parts[2] if len(parts) > 2 else "SPAIN"

        provider = get_provider()
        data = provider.fetch_session_data(year, event, 'R')
        if not data.get("success"):
            raise Exception("Could not load data for ML training")

        session = data["raw_session"]

        # We will train the model to predict 'lap_time_degradation_per_lap' (seconds)
        # Features: [compound_idx, starting_fuel_kg, track_temp_c]

        compounds = ['SOFT', 'MEDIUM', 'HARD']
        X = []
        y = []

        # Base degradation values (seconds per lap)
        base_deg = {'SOFT': 0.12, 'MEDIUM': 0.08, 'HARD': 0.05}

        # Generate 500 synthetic samples
        np.random.seed(42)
        for _ in range(500):
            c = np.random.choice(compounds)
            fuel = np.random.uniform(10.0, 110.0)
            temp = np.random.uniform(25.0, 50.0)

            # True target calculation
            # Higher fuel = more degradation
            # Higher temp = more degradation for softs, less for hards (optimal temp)
            c_idx = compounds.index(c)
            deg = base_deg[c]

            # Fuel penalty: +0.0005s/lap per kg
            deg += (fuel * 0.0005)

            # Temp penalty
            if c == 'SOFT' and temp > 40:
                deg += 0.02
            elif c == 'HARD' and temp < 30:
                deg += 0.03

            # Add noise
            deg += np.random.normal(0, 0.01)

            X.append([c_idx, fuel, temp])
            y.append(deg)

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
