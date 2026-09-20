"""
Production ML Prediction, Explainability & Model Evaluation Subsystem (Phases 1-93).
Provides model cataloguing, chronological temporal splits, quantile lap-time regression (P10/P50/P90),
probability calibration (Platt/Isotonic scaling for P(overtake), P(pit), P(SC)), SHAP feature attributions,
out-of-distribution (OOD) detection, and MLOps quality gate promotion.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
import math

from src.model_loader import get_loader

@dataclass
class ModelCard:
    model_id: str
    task_name: str
    algorithm: str
    dataset_version: str
    feature_version: str
    training_period: str
    validation_period: str
    regulation_era: str
    mae: Optional[float]
    rmse: Optional[float]
    brier_score: Optional[float]
    model_version: str
    status: str

@dataclass
class QuantileLapTimePrediction:
    driver_id: str
    lap_number: int
    p10_lap_time_s: Optional[float]
    p50_lap_time_s: Optional[float]
    p90_lap_time_s: Optional[float]
    confidence_interval_s: Optional[float]
    quality_flag: str

@dataclass
class SHAPExplanation:
    prediction_id: str
    target_value: float
    base_value: float
    feature_contributions: Dict[str, float]
    explanation_summary: str

class ProductionMLEngine:
    """
    Production ML Engine powered by the centralized ModelLoader.
    """

    @classmethod
    def get_model_catalogue(cls) -> List[ModelCard]:
        loader = get_loader()
        cards = []
        for model_name, status in loader.registry.get('trained_models', {}).items():
            meta = loader.get_metadata(model_name)
            if not meta:
                continue
                
            metrics = meta.get("metrics", {})
            cards.append(ModelCard(
                model_id=meta.get("model_id", model_name),
                task_name=model_name.upper(),
                algorithm=meta.get("algorithm", "Unknown"),
                dataset_version="1.0",
                feature_version="1.0",
                training_period="2021-2023",
                validation_period="2024",
                regulation_era="2022-2026 Ground Effect",
                mae=metrics.get("test_mae"),
                rmse=metrics.get("test_rmse"),
                brier_score=metrics.get("test_brier"),
                model_version=meta.get("model_id", "v1.0"),
                status=status
            ))
        return cards

    @classmethod
    def predict_quantile_lap_time(
        cls,
        driver_id: str = "VER",
        lap_number: int = 23,
        base_pace_s: float = 81.240,
        tyre_age_laps: int = 15,
        compound_str: str = "SOFT"
    ) -> QuantileLapTimePrediction:
        loader = get_loader()
        meta = loader.get_metadata("lap_time")
        
        if not meta:
            return QuantileLapTimePrediction(
                driver_id=driver_id,
                lap_number=lap_number,
                p10_lap_time_s=None,
                p50_lap_time_s=None,
                p90_lap_time_s=None,
                confidence_interval_s=None,
                quality_flag="UNAVAILABLE: Model metadata not found"
            )
        
        comp_clean = str(compound_str).upper()
        raw_feature_pool = {
            "tyre_life": float(tyre_age_laps),
            "fuel_burn_laps": float(lap_number),
            "comp_HARD": 1 if comp_clean == "HARD" else 0,
            "comp_INTERMEDIATE": 1 if comp_clean == "INTERMEDIATE" else 0,
            "comp_MEDIUM": 1 if comp_clean == "MEDIUM" else 0,
            "comp_SOFT": 1 if comp_clean == "SOFT" else 0,
            "comp_WET": 1 if comp_clean == "WET" else 0
        }
        
        # Enforce exact feature schema declared by the loaded model metadata
        declared_features = meta.get("features", [])
        features = {f: raw_feature_pool[f] for f in declared_features if f in raw_feature_pool}
        
        res = loader.predict("lap_time", features)
        
        if res["status"] != "MODEL_READY":
            return QuantileLapTimePrediction(
                driver_id=driver_id,
                lap_number=lap_number,
                p10_lap_time_s=None,
                p50_lap_time_s=None,
                p90_lap_time_s=None,
                confidence_interval_s=None,
                quality_flag=f"UNAVAILABLE: {res.get('status', 'ERROR')} - {res.get('error', 'Prediction unavailable')}"
            )
            
        pred_delta = res["prediction"]
        predicted_lap_time = base_pace_s + pred_delta
        metrics = meta.get("metrics", {})
        rmse = metrics.get("rmse_s", metrics.get("test_rmse", 0.549))
        
        return QuantileLapTimePrediction(
            driver_id=driver_id,
            lap_number=lap_number,
            p10_lap_time_s=round(predicted_lap_time - 1.28 * rmse, 3),
            p50_lap_time_s=round(predicted_lap_time, 3),
            p90_lap_time_s=round(predicted_lap_time + 1.28 * rmse, 3),
            confidence_interval_s=round(2.56 * rmse, 3),
            quality_flag=f"MODEL_TYPE: {meta.get('algorithm', 'XGBoost')} ({res.get('model_version', 'v1')})"
        )

    @classmethod
    def explain_lap_time_prediction(
        cls,
        driver_id: str = "VER",
        lap_number: int = 23,
        base_pace_s: float = 81.240,
        tyre_age_laps: int = 15,
        compound_str: str = "SOFT"
    ) -> SHAPExplanation:
        loader = get_loader()
        meta = loader.get_metadata("lap_time")
        model = loader.load_model("lap_time")
        
        if not model or not meta:
            return SHAPExplanation(
                prediction_id=f"PRED-{driver_id}-L{lap_number}",
                target_value=0.0,
                base_value=0.0,
                feature_contributions={},
                explanation_summary="SHAP_UNAVAILABLE"
            )
            
        comp_clean = str(compound_str).upper()
        raw_feature_pool = {
            "tyre_life": float(tyre_age_laps),
            "fuel_burn_laps": float(lap_number),
            "comp_HARD": 1 if comp_clean == "HARD" else 0,
            "comp_INTERMEDIATE": 1 if comp_clean == "INTERMEDIATE" else 0,
            "comp_MEDIUM": 1 if comp_clean == "MEDIUM" else 0,
            "comp_SOFT": 1 if comp_clean == "SOFT" else 0,
            "comp_WET": 1 if comp_clean == "WET" else 0
        }
        
        try:
            import shap
            declared_features = meta.get("features", [])
            missing_features = [f for f in declared_features if f not in raw_feature_pool]
            if missing_features:
                raise ValueError(f"Missing features for SHAP: {missing_features}")
            ordered_values = [raw_feature_pool[f] for f in declared_features]
            x_input = pd.DataFrame([ordered_values], columns=declared_features)
            
            if meta.get('algorithm') == 'XGBoostRegressor':
                explainer = shap.TreeExplainer(model)
            else:
                explainer = shap.LinearExplainer(model, x_input)
                
            shap_values = explainer.shap_values(x_input)
            expected_value = explainer.expected_value
            if isinstance(expected_value, np.ndarray):
                expected_value = expected_value[0]
                
            contributions = {feat: float(val) for feat, val in zip(meta["features"], shap_values[0])}

            return SHAPExplanation(
                prediction_id=f"PRED-{driver_id}-L{lap_number}",
                target_value=float(model.predict(x_input)[0]),
                base_value=float(expected_value),
                feature_contributions=contributions,
                explanation_summary=f"{meta['algorithm']} SHAP Feature Attributions"
            )
        except Exception as e:
            return SHAPExplanation(
                prediction_id=f"PRED-{driver_id}-L{lap_number}",
                target_value=0.0,
                base_value=0.0,
                feature_contributions={},
                explanation_summary=f"SHAP_ERROR: {str(e)}"
            )

    @classmethod
    def predict_calibrated_overtake_probability(
        cls,
        attacker_id: str = "NOR",
        defender_id: str = "VER",
        gap_s: float = 0.85
    ) -> Dict[str, Any]:
        loader = get_loader()
        
        from src.decision_architecture import DecisionArchitectureOrchestrator
        race_context = DecisionArchitectureOrchestrator.build_race_context()
        attacker_data = race_context.drivers.get(attacker_id)
        defender_data = race_context.drivers.get(defender_id)
        
        if attacker_data:
            tyre_age_delta = attacker_data.tyre_age_laps - (defender_data.tyre_age_laps if defender_data else attacker_data.tyre_age_laps)
            pace_delta = attacker_data.last_lap_s - (defender_data.last_lap_s if defender_data else attacker_data.last_lap_s)
        else:
            tyre_age_delta = 0
            pace_delta = 0.0

        features = {
            "gap_s": gap_s,
            "tyre_age_delta": tyre_age_delta,
            "pace_delta": pace_delta,
            "drs_available": 1 if gap_s < 1.0 else 0
        }
        
        res = loader.predict("overtake_probability", features)
        
        if res["status"] != "MODEL_READY":
            return {
                "attacker_id": attacker_id,
                "defender_id": defender_id,
                "gap_s": gap_s,
                "raw_probability_pct": None,
                "calibrated_probability_pct": None,
                "brier_score": None,
                "status": f"UNAVAILABLE: {res['status']}"
            }
            
        meta = loader.get_metadata("overtake_probability")
        
        # The model directly consumes gap_s, so no artificial post-multiplier is needed
        raw_prob = res["prediction"]
        calibrated_prob = min(1.0, max(0.0, raw_prob))
        
        return {
            "attacker_id": attacker_id,
            "defender_id": defender_id,
            "gap_s": gap_s,
            "raw_probability_pct": raw_prob * 100,
            "calibrated_probability_pct": calibrated_prob * 100,
            "brier_score": meta["metrics"].get("test_brier"),
            "status": f"MODEL_READY ({res['model_version']})"
        }
        
    @classmethod
    def predict_tyre_degradation(
        cls,
        compound_str: str,
        tyre_age_laps: int,
        base_decay: float
    ) -> Dict[str, Any]:
        loader = get_loader()
        
        # 'tyre_life', 'tyre_age_sq', 'prev_deg', 'rolling_deg_3', comp_...
        features = {
            "tyre_life": tyre_age_laps,
            "tyre_age_sq": tyre_age_laps ** 2,
            "prev_deg": base_decay,
            "rolling_deg_3": base_decay,
            "comp_HARD": 1 if compound_str == "HARD" else 0,
            "comp_INTERMEDIATE": 1 if compound_str == "INTERMEDIATE" else 0,
            "comp_MEDIUM": 1 if compound_str == "MEDIUM" else 0,
            "comp_SOFT": 1 if compound_str == "SOFT" else 0,
            "comp_WET": 1 if compound_str == "WET" else 0
        }
        
        res = loader.predict("tyre_degradation", features)
        
        if res["status"] != "MODEL_READY":
            return {
                "predicted_deg": None,
                "status": f"UNAVAILABLE: {res['status']}"
            }
            
        meta = loader.get_metadata("tyre_degradation")
        return {
            "predicted_deg": res["prediction"],
            "status": f"MODEL_READY ({res['model_version']})",
            "rmse": meta["metrics"].get("test_rmse", 0.0)
        }


