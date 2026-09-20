"""
Numerical Grounding Validation & Conflict Resolution Guardrail Engine.
Strictly validates that every numerical claim in AI responses matches authoritative Decision Engine outputs.
Detects and resolves contradictions between LLM explanations and StructuredDecision payloads.
"""

from typing import Dict, List, Optional, Any, Tuple
import re

from decision_engine import StructuredDecision


class DecisionValidationEngine:
    """
    Validates LLM text outputs against authoritative StructuredDecision payloads.
    """

    @classmethod
    def validate_and_correct_explanation(
        cls,
        explanation_text: str,
        decision: StructuredDecision
    ) -> Tuple[bool, str, List[str]]:
        """
        Scans explanation_text for percentages and strategy rankings.
        Returns (is_valid, corrected_text, list_of_violations).
        """
        violations = []
        corrected_text = explanation_text

        # 1. Strategy Name Conflict Check
        # If explanation claims a different strategy is recommended, correct it
        rec_strat = decision.selected_strategy_name.lower()
        if "recommend" in explanation_text.lower() or "best strategy" in explanation_text.lower():
            # Check if text contains a strategy name that is NOT the selected strategy
            for alt in decision.alternatives:
                alt_name = alt.strategy_name.lower()
                if alt_name in explanation_text.lower() and rec_strat not in explanation_text.lower():
                    violations.append(f"Contradiction: Explanation recommended '{alt.strategy_name}' instead of selected '{decision.selected_strategy_name}'.")
                    # Correct strategy recommendation text
                    corrected_text = f"**Decision Engine Recommendation ({decision.selected_strategy_name}):** {decision.primary_reason}\n\n*Original LLM explanation corrected to prevent contradiction.*"
                    return False, corrected_text, violations

        # 2. Percentage Numerical Grounding Check
        pct_matches = re.findall(r'(\d+\.?\d*)\s*%', explanation_text)
        grounded_pcts = {
            round(decision.win_probability_pct, 1),
            round(decision.podium_probability_pct, 1),
            round(decision.downside_risk_pct, 1)
        }
        for alt in decision.alternatives:
            grounded_pcts.add(round(alt.win_probability_pct, 1))
            grounded_pcts.add(round(alt.podium_probability_pct, 1))
            grounded_pcts.add(round(alt.downside_risk_pct, 1))

        for pct_str in pct_matches:
            val = round(float(pct_str), 1)
            # Allow minor rounding differences of +/- 0.5%
            if not any(abs(val - g) <= 0.5 for g in grounded_pcts):
                violations.append(f"Ungrounded numerical probability cited: {val}% not found in decision payload.")

        is_valid = len(violations) == 0
        return is_valid, corrected_text, violations

