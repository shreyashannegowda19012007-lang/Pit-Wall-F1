import logging
import uuid
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# =============================================================================
# STRUCTURED EVIDENCE MODELS (R6-B CONTRACT)
# =============================================================================

@dataclass
class EvidenceItem:
    """Individual structured piece of evidence."""
    metric: str
    value: Any
    source: str                 # "FASTF1", "TELEMETRY_DERIVED", "MONTE_CARLO", "DECISION_ENGINE", "SOURCE_UNAVAILABLE"
    driver: Optional[str] = None
    lap: Optional[int] = None
    distance: Optional[float] = None
    comparison: Optional[str] = None
    uncertainty: Optional[float] = None
    provenance: str = "SOURCE_UNAVAILABLE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric,
            "value": self.value,
            "source": self.source,
            "driver": self.driver,
            "lap": self.lap,
            "distance": self.distance,
            "comparison": self.comparison,
            "uncertainty": self.uncertainty,
            "provenance": self.provenance
        }


@dataclass
class StructuredEvidenceResponse:
    """Canonical Evidence Engine Output (R6-B)."""
    question: str
    answerable: bool
    session: str
    evidence_items: List[EvidenceItem] = field(default_factory=list)
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "answerable": self.answerable,
            "session": self.session,
            "reason": self.reason,
            "evidence_items": [item.to_dict() for item in self.evidence_items]
        }


class EvidenceEngine:
    """
    Retrieves evidence from actual underlying data.
    Does NOT manufacture explanations.
    """

    @classmethod
    def resolve_evidence(
        cls,
        question: str,
        session: Any = None,
        laps_df: pd.DataFrame = pd.DataFrame(),
        target_driver: str = "UNK",
        ref_driver: str = "UNK",
        current_race_lap: int = 1,
        mode: str = "LIVE",
        decision_context: Optional[Dict[str, Any]] = None
    ) -> StructuredEvidenceResponse:
        """
        Routes the question to the appropriate underlying analysis engine.
        Enforces future-data protection during LIVE replay.
        """
        session_name = "Session"
        if session and hasattr(session, 'session_info'):
            session_name = str(session.session_info.get('Meeting', {}).get('Name', 'Unknown Session'))

        # Future-Data Protection Guard
        valid_laps_df = laps_df
        if mode != "POST_RACE" and not laps_df.empty and 'LapNumber' in laps_df.columns:
            valid_laps_df = laps_df[laps_df['LapNumber'] <= current_race_lap].copy()

        q_lower = question.lower()
        
        # 1. Telemetry Corner Question
        if "losing time" in q_lower or "turn" in q_lower:
            return cls._gather_telemetry_evidence(
                question=question,
                session=session,
                valid_laps_df=valid_laps_df,
                target_driver=target_driver,
                ref_driver=ref_driver,
                session_name=session_name
            )
            
        # 2. Strategy Question
        if "strategy" in q_lower or "preferred" in q_lower or "pit" in q_lower:
            return cls._gather_strategy_evidence(
                question=question,
                decision_context=decision_context,
                session_name=session_name
            )
            
        # 3. ML Model Question
        if "ml model" in q_lower or "machine learning" in q_lower:
            # Simple heuristic: try to extract model name
            model_name = "lap_time"
            if "tyre" in q_lower or "degradation" in q_lower:
                model_name = "tyre_degradation"
            elif "overtake" in q_lower:
                model_name = "overtake_probability"
            return cls.get_ml_evidence(model_name)

        # Fallback for unsupported questions
        return StructuredEvidenceResponse(
            question=question,
            answerable=False,
            session=session_name,
            reason="INSUFFICIENT_EVIDENCE: Unsupported question type or lack of underlying data."
        )

    @classmethod
    def _gather_telemetry_evidence(
        cls,
        question: str,
        session: Any,
        valid_laps_df: pd.DataFrame,
        target_driver: str,
        ref_driver: str,
        session_name: str
    ) -> StructuredEvidenceResponse:
        
        if session is None or valid_laps_df.empty:
            return StructuredEvidenceResponse(
                question=question, answerable=False, session=session_name,
                reason="INSUFFICIENT_EVIDENCE: Session telemetry unavailable."
            )

        try:
            from src.telemetry_analysis_service import TelemetryAnalysisService
            comp_res = TelemetryAnalysisService.compare_laps(session, target_driver, ref_driver)
            
            if not comp_res.get("success"):
                return StructuredEvidenceResponse(
                    question=question, answerable=False, session=session_name,
                    reason="INSUFFICIENT_EVIDENCE: Telemetry alignment or distance matching failed."
                )

            evidence_items = []
            tgt_lap = comp_res.get("meta_a", {}).get("lap_number")
            ref_lap = comp_res.get("meta_b", {}).get("lap_number")
            
            # Overall lap delta
            lap_delta = comp_res.get("lap_time_delta_s")
            if lap_delta is not None:
                evidence_items.append(EvidenceItem(
                    metric="lap_time_delta_s", value=lap_delta,
                    source="TELEMETRY_DERIVED", driver=target_driver, lap=tgt_lap,
                    comparison=f"vs {ref_driver} Lap {ref_lap}",
                    provenance=f"TelemetryAnalysisService.compare_laps (FastF1 Session Data)"
                ))

            # Corner components
            top_opps = comp_res.get("top_opportunities", [])
            for opp in top_opps:
                c_name = opp.get("corner_name")
                c_entry = opp.get("entry_m")
                
                # Total loss
                t_loss = opp.get("time_loss_seconds")
                if t_loss is not None:
                    evidence_items.append(EvidenceItem(
                        metric=f"time_loss_{c_name}", value=t_loss,
                        source="TELEMETRY_DERIVED", driver=target_driver, lap=tgt_lap,
                        distance=c_entry, comparison=ref_driver,
                        provenance="CornerPerformanceAnalysis (Integrated dt=dx/v)"
                    ))
                
                # Minimum speed delta
                v_min = opp.get("minimum_speed_delta_kmh")
                if v_min is not None:
                    evidence_items.append(EvidenceItem(
                        metric=f"min_speed_delta_kmh_{c_name}", value=v_min,
                        source="TELEMETRY_DERIVED", driver=target_driver, lap=tgt_lap,
                        distance=c_entry, comparison=ref_driver,
                        provenance="CornerPerformanceAnalysis"
                    ))
                
                # Braking point delta
                b_delta = opp.get("braking_point_delta_m")
                if b_delta is not None:
                    evidence_items.append(EvidenceItem(
                        metric=f"braking_point_delta_m_{c_name}", value=b_delta,
                        source="TELEMETRY_DERIVED", driver=target_driver, lap=tgt_lap,
                        distance=c_entry, comparison=ref_driver,
                        provenance="CornerPerformanceAnalysis"
                    ))
                    
                # We do NOT invent specific component losses (braking_loss_s, throttle_loss_s)
                # because they are not strictly calculated by time_loss_attribution.py.

            return StructuredEvidenceResponse(
                question=question,
                answerable=True,
                session=session_name,
                evidence_items=evidence_items
            )
            
        except Exception as e:
            logger.error(f"Error in telemetry evidence gathering: {e}")
            return StructuredEvidenceResponse(
                question=question, answerable=False, session=session_name,
                reason=f"INSUFFICIENT_EVIDENCE: Telemetry processing crashed: {str(e)}"
            )

    @classmethod
    def _gather_strategy_evidence(
        cls,
        question: str,
        decision_context: Optional[Dict[str, Any]],
        session_name: str
    ) -> StructuredEvidenceResponse:
        
        if not decision_context:
            return StructuredEvidenceResponse(
                question=question, answerable=False, session=session_name,
                reason="INSUFFICIENT_EVIDENCE: No strategy/decision context provided."
            )

        evidence_items = []
        
        rec_action = decision_context.get("recommended_action")
        if rec_action:
            evidence_items.append(EvidenceItem(
                metric="recommended_action", value=rec_action,
                source="DECISION_ENGINE",
                provenance="DecisionEngine.evaluate"
            ))
            
        win_prob = decision_context.get("win_probability_pct")
        if win_prob is not None:
            evidence_items.append(EvidenceItem(
                metric="win_probability_pct", value=win_prob,
                source="MONTE_CARLO", uncertainty=decision_context.get("position_std_dev"),
                provenance="MonteCarloRaceEngine.simulate_strategy_vectorized"
            ))
            
        expected_finish = decision_context.get("expected_finish")
        if expected_finish is not None:
            evidence_items.append(EvidenceItem(
                metric="expected_finish", value=expected_finish,
                source="MONTE_CARLO",
                provenance="MonteCarloRaceEngine"
            ))
            
        downside_risk = decision_context.get("downside_risk_pct")
        if downside_risk is not None:
            evidence_items.append(EvidenceItem(
                metric="downside_risk_pct", value=downside_risk,
                source="MONTE_CARLO",
                provenance="MonteCarloRaceEngine"
            ))

        return StructuredEvidenceResponse(
            question=question,
            answerable=True,
            session=session_name,
            evidence_items=evidence_items
        )


    @classmethod
    def get_ml_evidence(cls, model_name: str):
        """Returns metadata and validation info about an ML model used in prediction."""
        from src.model_loader import get_loader
        loader = get_loader()
        meta = loader.get_metadata(model_name)
        
        if not meta:
            return StructuredEvidenceResponse(
                question=f"ML Model Evidence: {model_name}",
                answerable=False,
                session="ANY",
                reason=f"Model {model_name} is UNAVAILABLE or NOT ACTIVE."
            )
            
        metrics = meta.get("metrics", {})
        
        evidence_items = [
            EvidenceItem(
                metric="model_status", value=meta.get("status"),
                source="ML_MODEL", provenance=f"Registry ({meta.get('model_id')})"
            ),
            EvidenceItem(
                metric="algorithm", value=meta.get("algorithm"),
                source="ML_MODEL", provenance=f"Registry ({meta.get('model_id')})"
            ),
            EvidenceItem(
                metric="test_mae" if "test_mae" in metrics else "test_roc_auc", 
                value=metrics.get("test_mae", metrics.get("test_roc_auc")),
                source="ML_MODEL", provenance="ML-3 Validation"
            )
        ]
        
        uncertainty = meta.get("uncertainty", "UNAVAILABLE")
        evidence_items.append(EvidenceItem(
            metric="uncertainty", value=uncertainty,
            source="ML_MODEL", provenance="ML-3 Validation"
        ))
        
        return StructuredEvidenceResponse(
            question=f"ML Model Evidence: {model_name}",
            answerable=True,
            session="ANY",
            evidence_items=evidence_items
        )

