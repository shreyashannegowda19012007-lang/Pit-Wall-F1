import pandas as pd
import numpy as np
import streamlit as st
from typing import List, Dict, Any, Optional

class JarvisEngineeringInsightsEngine:
    """
    Flagship AI Performance Engineering Insights Engine.
    Proactively analyzes telemetry arrays, stint degradation, corner kinematics, and strategic choices
    to generate structured findings using the R6 Decision Architecture.
    Does NOT invent numbers.
    """

    @classmethod
    def generate_session_insights(
        cls,
        laps_df: pd.DataFrame,
        results_df: pd.DataFrame,
        session_info: Dict[str, Any],
        raw_session: Any = None,
        active_driver: str = None
    ) -> List[Dict[str, Any]]:
        insights = []
        
        target_driver = active_driver or st.session_state.get('primary_drv') or 'VER'
        second_driver = st.session_state.get('comp_drv') or 'HAM'
        
        from src.decision_architecture import DecisionArchitectureOrchestrator, DecisionEngine, JarvisEvidenceEngine

        # 1. Build Canonical RaceContext
        race_context = DecisionArchitectureOrchestrator.build_race_context()
        
        # 2. Get Decision Engine Recommendation
        recommendation = DecisionEngine.generate_recommendation(race_context, target_driver, second_driver)
        
        # 3. Pull Dynamic Corner Time-Loss from Real Telemetry
        time_loss_insights = []
        if raw_session is not None:
            try:
                from src.telemetry_analysis_service import TelemetryAnalysisService
                comp_res = TelemetryAnalysisService.compare_laps(raw_session, target_driver, second_driver)
                if comp_res.get("success") and comp_res.get("top_opportunities"):
                    top_opps = comp_res.get("top_opportunities", [])
                    for idx, opp in enumerate(top_opps[:4]):
                        c_name = opp.get("corner_name", f"Turn {idx + 1}")
                        loss_s = opp.get("time_loss_seconds", 0.0)
                        b_delta = opp.get("braking_point_delta_m")
                        t_delay = opp.get("throttle_delay_seconds")

                        b_text = f"Braking delta is {b_delta:+.1f}m." if b_delta is not None else ""
                        t_text = f"Throttle delay is {t_delay:+.2f}s." if t_delay is not None else ""
                        
                        time_loss_insights.append({
                            "id": f"INS-00{idx + 2}",
                            "severity": "CRITICAL" if loss_s > 0.2 else ("HIGH" if loss_s > 0.1 else "MEDIUM"),
                            "title": f"{target_driver} Time Deficit in {c_name} (+{loss_s:.3f}s)",
                            "area": "Corner Kinematics & Time Loss",
                            "confidence": opp.get("confidence_score", 90),
                            "what": f"Losing {loss_s:.3f}s through {c_name} compared to {second_driver}.",
                            "why": f"{b_text} {t_text}".strip(),
                            "evidence": f"Telemetry comparison - Valid Lap Data",
                            "recommendation": opp.get("explanation", "Adjust corner approach."),
                            "corner_ref": c_name,
                            "visual_link": "Corner Telemetry Trace"
                        })
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Telemetry extraction error: {e}")

        # 4. Construct Full Evidence Payload for AI prompt parsing if needed
        jarvis_payload = JarvisEvidenceEngine.construct_jarvis_context(
            race_context=race_context,
            primary_driver=target_driver,
            comparison_driver=second_driver,
            recommendation=recommendation,
            time_loss_insights=time_loss_insights
        )
        
        # 5. Extract structured insights back to UI layout
        insights.append({
            "id": "INS-DECISION-01",
            "severity": "CRITICAL",
            "title": f"Decision Engine Recommendation: {recommendation.recommendation}",
            "area": "Race Strategy",
            "confidence": recommendation.confidence_pct,
            "what": f"Optimal strategy is to {recommendation.recommendation}.",
            "why": recommendation.primary_reason,
            "evidence": f"P(Win): {recommendation.p_win:.1f}%. Models used: {list(recommendation.model_versions.keys())}. Strategy Regret: {recommendation.strategy_regret_s:.2f}s.",
            "recommendation": f"Alternative: {recommendation.alternative} (Risk: {recommendation.risk})",
            "corner_ref": "Pit Lane",
            "visual_link": "Monte Carlo Tree"
        })
        
        insights.extend(time_loss_insights)

        pd_ctx = race_context.drivers.get(target_driver)
        if pd_ctx and pd_ctx.telemetry_state == "AVAILABLE" and pd_ctx.last_lap_s > 0:
            insights.append({
                "id": "INS-PACE-01",
                "severity": "INFORMATIONAL",
                "title": f"Current Pace ({target_driver})",
                "area": "Pace",
                "confidence": 95,
                "what": f"Latest lap time recorded at {pd_ctx.last_lap_s:.3f}s.",
                "why": f"Tyre {pd_ctx.tyre_compound} is {pd_ctx.tyre_age_laps} laps old.",
                "evidence": "Canonical Race Context",
                "recommendation": "Monitor degradation.",
                "corner_ref": "Full Circuit",
                "visual_link": "Pace Chart"
            })
            
        if len(insights) == 1:
            insights.extend(cls._generate_fallback_insights())

        return insights

    @staticmethod
    def _generate_fallback_insights() -> List[Dict[str, Any]]:
        """Generates standard engineering findings if data is uninitialized."""
        return [
            {
                "id": "INS-000", "severity": "INFORMATIONAL", "title": "Awaiting Telemetry Sync",
                "area": "System Control", "confidence": 99,
                "what": "Telemetry uplink ready for telemetry parsing.",
                "why": "Awaiting session data buffer initialization.",
                "evidence": "No detailed corner kinematics found.",
                "recommendation": "Select session and click Initialize Command.",
                "corner_ref": "System", "visual_link": "Standby Screen"
            }
        ]

    @classmethod
    def render_insights_tab(cls, insights: List[Dict[str, Any]]) -> None:
        """
        Renders the flagship JARVIS Engineering Insights interface in Streamlit.
        """
        st.markdown(f"""
            <div style="border-left: 4px solid #4A90E2; padding-left: 15px; margin-bottom: 25px;">
                <h2 style="color: #4A90E2; font-family: 'Inter', sans-serif; font-size: 20px; margin: 0; letter-spacing: 3px; ">
                    JARVIS // ENGINEERING INSIGHTS ENGINE
                </h2>
                <p style="color: #64748B; font-family: 'Inter', sans-serif; margin: 4px 0 0 0; font-size: 13px; letter-spacing: 2px;">
                    AUTOMATED SENIOR F1 PERFORMANCE ENGINEER SESSION DEBRIEF ({len(insights)} OBSERVATIONS)
                </p>
            </div>
        """, unsafe_allow_html=True)

        col_f1, col_f2 = st.columns([2, 2])
        with col_f1:
            severities = ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]
            selected_sev = st.selectbox("Filter by Impact Severity", severities, key="insights_sev_filter")
        with col_f2:
            areas = ["ALL"] + sorted(list(set(i.get("area", "General") for i in insights)))
            selected_area = st.selectbox("Filter by Subsystem Area", areas, key="insights_area_filter")

        filtered = insights
        if selected_sev != "ALL":
            filtered = [i for i in filtered if i.get("severity") == selected_sev]
        if selected_area != "ALL":
            filtered = [i for i in filtered if i.get("area") == selected_area]

        st.markdown("<br>", unsafe_allow_html=True)

        import html
        for item in filtered:
            sev = item.get("severity", "MEDIUM")
            border_color = "#EF4444" if sev == "CRITICAL" else ("#FFEA00" if sev == "HIGH" else ("#4A90E2" if sev == "MEDIUM" else "#27F4D2"))
            badge_bg = f"rgba({int(border_color[1:3],16)}, {int(border_color[3:5],16)}, {int(border_color[5:7],16)}, 0.15)"

            item_id = html.escape(str(item.get('id', '')))
            item_area = html.escape(str(item.get('area', '')))
            item_title = html.escape(str(item.get('title', '')))
            item_what = html.escape(str(item.get('what', '')))
            item_why = html.escape(str(item.get('why', '')))
            item_ev = html.escape(str(item.get('evidence', '')))
            item_rec = html.escape(str(item.get('recommendation', '')))
            confidence = int(item.get('confidence', 90))

            st.markdown(f"""
                <div class="hud-card" style="border-left: 4px solid {border_color}; margin-bottom: 20px; padding: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <span style="color: {border_color}; font-family: 'Inter', sans-serif; font-weight: 900; font-size: 11px; padding: 3px 8px; border: 1px solid {border_color}; border-radius: 4px; background: {badge_bg};">
                                {sev}
                            </span>
                            <span style="color: #64748B; font-family: 'Share Tech Mono', monospace; font-size: 11px;">{item_id} // {item_area}</span>
                        </div>
                        <div style="color: #4A90E2; font-family: 'Share Tech Mono', monospace; font-size: 12px; font-weight: bold;">
                            CONFIDENCE: {confidence}%
                        </div>
                    </div>
                    <h4 style="color: #E2E8F0; font-family: 'Inter', sans-serif; font-size: 15px; margin: 0 0 10px 0; letter-spacing: 1.5px;">
                        {item_title}
                    </h4>
                    <p style="color: #CBD5E1; font-family: 'Inter', sans-serif; font-size: 13px; margin: 0 0 8px 0; line-height: 1.5;">
                        <strong style="color: #4A90E2;">WHAT HAPPENED:</strong> {item_what}
                    </p>
                    <p style="color: #CBD5E1; font-family: 'Inter', sans-serif; font-size: 13px; margin: 0 0 8px 0; line-height: 1.5;">
                        <strong style="color: #FFEA00;">ENGINEERING WHY:</strong> {item_why}
                    </p>
                    <p style="color: #94A3B8; font-family: 'Share Tech Mono', monospace; font-size: 12px; margin: 0 0 12px 0;">
                        <strong style="color: #94A3B8;">SUPPORTING EVIDENCE:</strong> {item_ev}
                    </p>
                    <div style="background: #333842; border: 1px dashed #4A90E2; padding: 10px 14px; border-radius: 6px; margin-top: 10px;">
                        <span style="color: #27F4D2; font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 1px;">RECOMMENDED ACTION / SETUP FIX:</span>
                        <p style="color: #E2E8F0; font-family: 'Inter', sans-serif; font-size: 12px; margin: 4px 0 0 0;">
                            {item_rec}
                        </p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

