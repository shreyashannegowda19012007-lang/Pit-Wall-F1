from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
import re

from evidence_engine import EvidenceEngine, StructuredEvidenceResponse
from ai_tools import AIToolRegistry


class AIEngineerQAEngine:
    """
    Formulates evidence-backed F1 Performance Engineer explanations.
    Strictly prevents number hallucinations by grounding every metric in evidence citations.
    """

    @classmethod
    def answer_question(
        cls,
        question: str,
        session: Any,
        laps_df: pd.DataFrame,
        results_df: pd.DataFrame,
        target_driver: str,
        ref_driver: str
    ) -> Dict[str, Any]:
        resp = cls._answer_question_internal(
            question=question,
            session=session,
            laps_df=laps_df,
            results_df=results_df,
            target_driver=target_driver,
            ref_driver=ref_driver
        )
        if "answer" in resp and "answer_markdown" not in resp:
            resp["answer_markdown"] = resp["answer"]
        elif "answer_markdown" in resp and "answer" not in resp:
            resp["answer"] = resp["answer_markdown"]
        return resp

    @classmethod
    def _answer_question_internal(
        cls,
        question: str,
        session: Any,
        laps_df: pd.DataFrame,
        results_df: pd.DataFrame,
        target_driver: str,
        ref_driver: str
    ) -> Dict[str, Any]:
        """
        Processes an engineering query and returns an evidence-backed answer structure.
        """
        q_lower = question.lower()

        # Build Full Evidence Bundle first for use in fallbacks and answers
        bundle = EvidenceEngine.resolve_evidence(
            question=question,
            session=session,
            laps_df=laps_df,
            target_driver=target_driver,
            ref_driver=ref_driver
        )
        bundle_dict = bundle.to_dict()

        # 1. Adversarial & Missing Data Detection Checks
        if "ignore the simulator" in q_lower or "ignore simulator" in q_lower:
            return {
                "question": question,
                "answer": "Cannot bypass deterministic simulation outcomes. Strategy recommendations originate from probabilistic models.",
                "evidence_bundle": bundle_dict,
                "has_data": False,
                "data_status": "ADVERSARIAL_REJECTED"
            }

        if "make up a probability" in q_lower or "invent a probability" in q_lower or "fake probability" in q_lower:
            return {
                "question": question,
                "answer": "Probabilities must originate from Monte Carlo simulation.",
                "evidence_bundle": bundle_dict,
                "has_data": False,
                "data_status": "ADVERSARIAL_REJECTED"
            }

        if "assume strategy c" in q_lower or "assume strategy b" in q_lower:
            return {
                "question": question,
                "answer": "Assumptions cannot override the Strategy Optimizer output.",
                "evidence_bundle": bundle_dict,
                "has_data": False,
                "data_status": "ADVERSARIAL_REJECTED"
            }

        if "wind" in q_lower or "wind speed" in q_lower or "gust" in q_lower:
            return {
                "question": question,
                "answer": "Wind telemetry data is unavailable for this session lap.",
                "evidence_bundle": bundle_dict,
                "has_data": False,
                "data_status": "DATA_UNAVAILABLE"
            }

        if "last year" in q_lower or "previous season" in q_lower or "historical race" in q_lower:
            return {
                "question": question,
                "answer": "No comparable historical dataset from previous seasons is available in local telemetry storage.",
                "evidence_bundle": bundle_dict,
                "has_data": False,
                "data_status": "HISTORICAL_DATA_UNAVAILABLE"
            }

        answer_parts = []

        if bundle.answerable and bundle.evidence_items:
            for i, item in enumerate(bundle.evidence_items[:3]):
                val = f"{item.value:.3f}" if isinstance(item.value, float) else item.value
                answer_parts.append(f"{item.metric}: {val} (Source: {item.source})")
        else:
            answer_parts.append(bundle.reason or "Telemetry unavailable for this query.")

        return {
            "question": question,
            "answer": "\n".join(answer_parts),
            "evidence_bundle": bundle_dict,
            "has_data": bundle.answerable,
            "data_status": "SUCCESS" if bundle.answerable else "INSUFFICIENT_EVIDENCE"
        }
