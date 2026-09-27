import os
import json
import numpy as np
import pandas as pd
import pickle

from src import config

class ModelLoader:
    def __init__(self, models_dir=None):
        self.models_dir = models_dir or os.path.join(config.BASE_DIR, 'models')
        self.registry = self._load_registry()
        self.models = {}
        self.metadata = {}

    def _load_registry(self):
        reg_path = os.path.join(self.models_dir, 'registry.json')
        if not os.path.exists(reg_path):
            return {}
        with open(reg_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_model(self, model_name: str):
        if model_name in self.models:
            return self.models[model_name]

        trained_models = self.registry.get('trained_models', {})
        if model_name not in trained_models:
            return None

        status = trained_models.get(model_name)
        if status not in ("ACTIVE", "PRODUCTION"):
            return None

        model_dir = os.path.join(self.models_dir, model_name)
        meta_path = os.path.join(model_dir, 'metadata.json')
        model_path = os.path.join(model_dir, 'model.pkl')

        if not os.path.exists(meta_path) and not os.path.exists(os.path.join(model_dir, 'metadata_v1.json')):
            return None

        actual_meta_path = meta_path if os.path.exists(meta_path) else os.path.join(model_dir, 'metadata_v1.json')

        with open(actual_meta_path, 'r', encoding='utf-8') as f:
            self.metadata[model_name] = json.load(f)

        algorithm = self.metadata[model_name].get('algorithm', '')

        try:
            if algorithm == 'XGBoostRegressor':
                import xgboost as xgb
                # Try to load a .json model first, otherwise fallback to pickle
                xgb_json_path = os.path.join(model_dir, 'model.json')
                if not os.path.exists(xgb_json_path):
                    # Check for v1 fallback
                    xgb_json_path = os.path.join(model_dir, f'xgboost_{model_name}_v1.json')

                if os.path.exists(xgb_json_path):
                    model = xgb.XGBRegressor()
                    model.load_model(xgb_json_path)
                    self.models[model_name] = model
                else:
                    with open(model_path, 'rb') as f:
                        self.models[model_name] = pickle.load(f)
            elif algorithm == 'PPO':
                from stable_baselines3 import PPO
                zip_path = os.path.join(model_dir, 'ppo_strategy_v1.zip')
                if os.path.exists(zip_path):
                    self.models[model_name] = PPO.load(zip_path)
                else:
                    self.models[model_name] = None
            else:
                with open(model_path, 'rb') as f:
                    self.models[model_name] = pickle.load(f)
        except (pickle.UnpicklingError, ModuleNotFoundError, ImportError, AttributeError, EOFError) as e:
            print(f"[ModelLoader] Serialization/Pickle error loading {model_name}: {e}")
            self.registry['trained_models'][model_name] = "FAILED_VALIDATION"
            return None
        except Exception as e:
            print(f"[ModelLoader] Unknown error loading {model_name}: {e}")
            return None

        return self.models[model_name]

    def get_metadata(self, model_name: str):
        if model_name not in self.metadata:
            self.load_model(model_name)
        return self.metadata.get(model_name, None)

    def predict(self, model_name: str, features: dict):
        model = self.load_model(model_name)
        if model is None:
            return {"status": "MODEL_UNAVAILABLE", "error": "Model not ACTIVE or not found"}

        meta = self.get_metadata(model_name)
        if meta is None:
            return {"status": "MODEL_UNAVAILABLE", "error": "Model metadata not found"}

        # Verify feature contract
        expected_features = meta['features']

        missing = [f for f in expected_features if f not in features]
        if missing:
            return {"status": "FEATURE_ERROR", "error": f"Missing features: {missing}"}

        # Build array
        x = np.array([[features[f] for f in expected_features]])

        try:
            if meta['algorithm'] == 'LogisticRegression' or meta['algorithm'] == 'XGBoostClassifier':
                pred = model.predict_proba(x)[0, 1]
            else:
                pred = model.predict(x)[0]

            return {
                "status": "MODEL_READY",
                "prediction": float(pred),
                "model_version": meta['model_id']
            }
        except Exception as e:
            return {"status": "PREDICTION_ERROR", "error": str(e)}

# Singleton loader for production
_loader = None
def get_loader():
    global _loader
    if _loader is None:
        _loader = ModelLoader()
    return _loader
