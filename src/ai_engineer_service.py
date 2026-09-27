from typing import Dict, List, Optional, Any
import pandas as pd
import time

from evidence_engine import EvidenceEngine, StructuredEvidenceResponse
from ai_tools import AIToolRegistry

import re

class IntentParser:
    @staticmethod
    def extract_intent(query: str) -> str:
        q = query.lower()

        # Weighted regex patterns for structured intent routing
        patterns = {
            "STRATEGY": [
                (r'\b(strategy|plan|undercut|overcut)\b', 2.0),
                (r'\b(pit\s*stop|pit|box)\b', 1.5),
                (r'\b(when|should)\s+(i|we)\s+(pit|box)\b', 3.0),
                (r'\bwhat\s+if\b', 2.0)
            ],
            "PERFORMANCE": [
                (r'\b(pace|delta|time\s*loss|lose|losing)\b', 2.0),
                (r'\b(corner|turn|sector)\b', 1.5),
                (r'\b(faster|slower)\b', 1.5),
                (r'\bwhere\s+am\s+i\s+losing\b', 3.0)
            ],
            "TYRE": [
                (r'\b(tyre|tyres|tire|tires)\b', 2.0),
                (r'\b(wear|degradation|deg|life|cliff)\b', 1.5),
                (r'\b(soft|medium|hard|compound)\b', 1.0)
            ],
            "ML": [
                (r'\b(ml|model|predict|prediction|probability)\b', 2.0),
                (r'\bmachine\s+learning\b', 2.0),
                (r'\bovertake\s+probability\b', 3.0)
            ],
            "RL": [
                (r'\b(rl|agent|reinforcement\s+learning)\b', 3.0),
                (r'\bpolicy\b', 1.5)
            ],
            "EVENT": [
                (r'\b(safety\s*car|vsc|flag|incident|yellow|red|crash)\b', 2.0),
                (r'\bhappened\b', 1.0)
            ]
        }

        scores = {intent: 0.0 for intent in patterns.keys()}

        for intent, rules in patterns.items():
            for pattern, weight in rules:
                if re.search(pattern, q):
                    scores[intent] += weight

        max_intent = max(scores, key=scores.get)
        if scores[max_intent] >= 1.5:
            return max_intent

        return "UNKNOWN"

class AIEngineerService:
    """
    Authoritative JARVIS AI Engineer Orchestration & Grounded Interface Layer.
    Orchestrates: Intent -> Evidence/Decision Tools -> Grounded Markdown Response.
    """

    def process_query(
        self,
        query: str,
        primary_driver: str = "VER",
        ref_driver: str = "HAM",
        session: Any = None,
        laps_df: Optional[pd.DataFrame] = None,
        race_state: Any = None,
        mc_outcomes: Optional[List[Any]] = None,
        current_lap: int = 1,
        mode: str = "LIVE"
    ) -> Dict[str, Any]:
        resp = self._process_query_internal(
            query=query,
            primary_driver=primary_driver,
            ref_driver=ref_driver,
            session=session,
            laps_df=laps_df,
            race_state=race_state,
            mc_outcomes=mc_outcomes,
            current_lap=current_lap,
            mode=mode
        )
        if "answer_markdown" in resp and "answer" not in resp:
            resp["answer"] = resp["answer_markdown"]
        elif "answer" in resp and "answer_markdown" not in resp:
            resp["answer_markdown"] = resp["answer"]
        return resp

    def _process_query_internal(
        self,
        query: str,
        primary_driver: str = "VER",
        ref_driver: str = "HAM",
        session: Any = None,
        laps_df: Optional[pd.DataFrame] = None,
        race_state: Any = None,
        mc_outcomes: Optional[List[Any]] = None,
        current_lap: int = 1,
        mode: str = "LIVE"
    ) -> Dict[str, Any]:
        """
        Processes a natural language query strictly by executing authoritative tools
        and producing a grounded markdown explanation.
        """
        if laps_df is None:
            laps_df = pd.DataFrame()
        q_lower = query.lower()

        # 1. Temporal Guardrails (Future-Data Protection)
        if "lap " in q_lower:
            import re
            match = re.search(r'lap\s+(\d+)', q_lower)
            if match:
                requested_lap = int(match.group(1))
                if mode == "REPLAY" and requested_lap > current_lap:
                    return {
                        "query_text": query,
                        "answer_markdown": f"Future replay information (Lap {requested_lap}) is unavailable in the current temporal context (Lap {current_lap}).",
                        "data_status": "TEMPORAL_VIOLATION",
                        "evidence_citations": []
                    }

        # 2. Unsupported Claim / Hallucination Protection
        if "invent" in q_lower or "guess" in q_lower or "make up" in q_lower:
            return {
                "query_text": query,
                "answer_markdown": "I cannot manufacture data. All claims must be grounded in the authoritative simulation and telemetry models.",
                "data_status": "UNSUPPORTED_CLAIM",
                "evidence_citations": []
            }

        intent = IntentParser.extract_intent(query)

        # 3. Strategy / What-If Questions
        if intent == "STRATEGY":
            # Check availability
            if not race_state or not mc_outcomes:
                return {
                    "query_text": query,
                    "answer_markdown": "The strategy engine cannot currently provide a recommendation. (Models or Data Unavailable)",
                    "data_status": "MODEL_UNAVAILABLE",
                    "evidence_citations": []
                }

            # Decision Engine integration
            try:
                dec = AIToolRegistry.get_current_decision(race_state, mc_outcomes)
                action = dec.get("recommended_action")

                # Fetch Evidence
                bundle = EvidenceEngine.resolve_evidence(
                    question=query,
                    session=session,
                    laps_df=laps_df,
                    target_driver=primary_driver,
                    ref_driver=ref_driver,
                    current_race_lap=current_lap,
                    mode=mode,
                    decision_context=dec
                )

                ans_parts = [f"**ANSWER**\n{action} (Compound: {dec.get('recommended_compound')}, Lap: {dec.get('recommended_pit_lap')})"]

                ans_parts.append("\n**EVIDENCE**")
                for ev in bundle.evidence_items:
                    unc_str = f" ± {ev.uncertainty}" if ev.uncertainty is not None else ""
                    ans_parts.append(f"- {ev.metric}: {ev.value}{unc_str} (Source: {ev.source} / {ev.provenance})")

                ans_parts.append(f"\n**WHY**\n{dec.get('primary_reason', 'Decision based on Monte Carlo simulations.')}")

                if "what if" in q_lower or "earlier" in q_lower:
                    ans_parts.append("\n**WHAT-IF SIMULATION**\nBased on Monte Carlo variations.")

                ans_parts.append(f"\n**SESSION CONTEXT**\nSession: {bundle.session}")

                return {
                    "query_text": query,
                    "answer_markdown": "\n".join(ans_parts),
                    "data_status": "SUCCESS",
                    "evidence_citations": [e.to_dict() for e in bundle.evidence_items]
                }
            except Exception as e:
                return {
                    "query_text": query,
                    "answer_markdown": f"The strategy model encountered an error: {e}",
                    "data_status": "MODEL_ERROR",
                    "evidence_citations": []
                }

        # 4. Telemetry / Driver Performance Questions
        if intent == "PERFORMANCE":
            bundle = EvidenceEngine.resolve_evidence(
                question=query,
                session=session,
                laps_df=laps_df,
                target_driver=primary_driver,
                ref_driver=ref_driver,
                current_race_lap=current_lap,
                mode=mode
            )

            if not bundle.answerable or not bundle.evidence_items:
                return {
                    "query_text": query,
                    "answer_markdown": "Insufficient telemetry evidence available to answer this question.",
                    "data_status": "INSUFFICIENT_EVIDENCE",
                    "evidence_citations": []
                }

            ans_parts = ["**ANSWER**"]
            t_loss = next((e for e in bundle.evidence_items if e.metric.startswith("time_loss")), None)
            if t_loss:
                corner = t_loss.metric.replace("time_loss_", "")
                ans_parts.append(f"The primary loss is at {corner}.")
            else:
                ans_parts.append("Time loss analysis completed.")

            ans_parts.append("\n**EVIDENCE**")
            for ev in bundle.evidence_items:
                unc = f" ± {ev.uncertainty}" if ev.uncertainty else ""
                driver_meta = f" [Driver: {ev.driver}, Lap: {ev.lap}]" if ev.driver else ""
                comp_meta = f" [Ref: {ev.comparison}]" if ev.comparison else ""
                ans_parts.append(f"- {ev.metric}: {ev.value}{unc}{driver_meta}{comp_meta} (Source: {ev.source} / Provenance: {ev.provenance})")

            ans_parts.append("\n**WHY**\nObserved in kinematic telemetry integration.")

            source = t_loss.source if t_loss else "TELEMETRY_DERIVED"
            ans_parts.append(f"\n**SESSION CONTEXT**\nSession: {bundle.session}")

            return {
                "query_text": query,
                "answer_markdown": "\n".join(ans_parts),
                "data_status": "SUCCESS",
                "evidence_citations": [e.to_dict() for e in bundle.evidence_items]
            }

        # 5. Tyre Intelligence Questions
        if intent == "TYRE":
            if primary_driver == "UNK" or laps_df.empty:
                return {
                    "query_text": query,
                    "answer_markdown": "REMAINING TYRE LIFE UNAVAILABLE",
                    "data_status": "MODEL_UNAVAILABLE",
                    "evidence_citations": []
                }

            try:
                from src.trend_analysis import TimeSeriesTrendEngine
                deg = TimeSeriesTrendEngine.calculate_stint_pace_degradation(laps_df, primary_driver)
                if not deg.get("valid"):
                    return {
                        "query_text": query,
                        "answer_markdown": "REMAINING TYRE LIFE UNAVAILABLE",
                        "data_status": "MODEL_UNAVAILABLE",
                        "evidence_citations": []
                    }
                return {
                    "query_text": query,
                    "answer_markdown": f"Current pace degradation is {deg.get('degradation_rate_s_per_lap'):+.3f}s/lap based on the physics/trend model.",
                    "data_status": "SUCCESS",
                    "evidence_citations": []
                }
            except Exception:
                return {
                    "query_text": query,
                    "answer_markdown": "REMAINING TYRE LIFE UNAVAILABLE",
                    "data_status": "MODEL_ERROR",
                    "evidence_citations": []
                }

        # 6. ML / RL Model Availability
        if intent == "ML":
            ml_bundle = EvidenceEngine.get_ml_evidence("overtake_probability")
            if not ml_bundle.answerable:
                return {
                    "query_text": query,
                    "answer_markdown": "The ML models are not currently available.",
                    "data_status": "ML_MODEL_NOT_TRAINED",
                    "evidence_citations": []
                }
            ans_parts = ["**ANSWER**\nML Model Status Report:"]
            ans_parts.append("\n**EVIDENCE**")
            for ev in ml_bundle.evidence_items:
                ans_parts.append(f"- {ev.metric}: {ev.value} (Source: {ev.source})")
            return {
                "query_text": query,
                "answer_markdown": "\n".join(ans_parts),
                "data_status": "SUCCESS",
                "evidence_citations": [e.to_dict() for e in ml_bundle.evidence_items]
            }

        if intent == "RL":
            rl_bundle = EvidenceEngine.get_ml_evidence("rl_strategy")
            if not rl_bundle.answerable:
                return {
                    "query_text": query,
                    "answer_markdown": "The RL models are not currently trained/available for this session.",
                    "data_status": "RL_MODEL_NOT_TRAINED",
                    "evidence_citations": []
                }
            ans_parts = ["**ANSWER**\nRL Agent Status Report:"]
            ans_parts.append("\n**EVIDENCE**")
            for ev in rl_bundle.evidence_items:
                ans_parts.append(f"- {ev.metric}: {ev.value} (Source: {ev.source})")
            return {
                "query_text": query,
                "answer_markdown": "\n".join(ans_parts),
                "data_status": "SUCCESS",
                "evidence_citations": [e.to_dict() for e in rl_bundle.evidence_items]
            }

        # 7. Historical/Race Control Questions
        if intent == "EVENT":
            return {
                "query_text": query,
                "answer_markdown": "Race control event telemetry (Safety Cars, Flags, Incidents) is currently unavailable in the Evidence Engine.",
                "data_status": "MODEL_UNAVAILABLE",
                "evidence_citations": []
            }

        # Fallback
        return {
            "query_text": query,
            "answer_markdown": "I cannot answer this query based on the current authoritative data contexts.",
            "data_status": "UNSUPPORTED",
            "evidence_citations": []
        }

    # Alias for backward compatibility
    handle_query = process_query
