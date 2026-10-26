"""
Correction & Biomechanics Rule Evaluation Engine.
=================================================
Evaluates observed metrics against coach-approved references and rules,
generating explainable 5-point coaching feedback and cautious injury/efficiency notes.
"""

from typing import List, Dict, Any, Optional
import numpy as np


class RuleEvaluator:
    """Evaluates biomechanical rules against extracted movement metrics."""

    def evaluate(
        self,
        metrics: Dict[str, Any],
        rules: List[Dict[str, Any]],
        phases: Dict[str, Any],
        reference: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Evaluate all active rules and return ranked correction feedback items.

        Returns list of structured feedback dictionaries explaining:
        1. observed_difference
        2. reference_benchmark
        3. location_and_timing
        4. suggested_correction
        5. evidence_and_confidence
        + efficiency_impact
        + injury_caution
        """
        corrections = []
        benchmarks = (reference or {}).get("benchmark_metrics", {})

        for rule in rules:
            metric_key = rule.get("metric")
            if metric_key not in metrics:
                continue

            observed_val = metrics[metric_key]
            phase_id = rule.get("phase", "general")
            phase_info = phases.get(phase_id, {})
            condition_expr = rule.get("condition", "")

            # Safely evaluate condition string (e.g., 'value < 162.0')
            triggered = False
            try:
                env = {"value": observed_val}
                triggered = bool(eval(condition_expr, {"__builtins__": {}}, env))
            except Exception as e:
                print(f"Error evaluating condition '{condition_expr}': {e}")
                triggered = False

            if triggered:
                # Retrieve benchmark info
                bench = benchmarks.get(metric_key, {})
                target_range = bench.get("target_range", [165.0, 180.0])
                optimal_val = bench.get("optimal", 175.0)
                deviation = abs(observed_val - optimal_val)

                # Format 5-element explanation
                template = rule.get(
                    "observed_difference_template",
                    f"Measured {metric_key} was {observed_val} (target: {target_range}).",
                )
                observed_diff = template.format(observed_val=observed_val)

                timing_desc = f"Phase: {phase_info.get('name', phase_id.title())}"
                if "start_time" in phase_info and "end_time" in phase_info:
                    timing_desc += f" ({phase_info['start_time']:.2f}s - {phase_info['end_time']:.2f}s)"

                correction_item = {
                    "rule_id": rule.get("id"),
                    "title": rule.get("title", "Technique Deviation"),
                    "severity": rule.get("severity", "medium"),
                    "category": rule.get("category", "technique"),
                    "phase": phase_id,
                    "metric_name": metric_key,
                    "observed_value": observed_val,
                    "reference_range": target_range,
                    "optimal_value": optimal_val,
                    "deviation_magnitude": round(deviation, 1),
                    # The 5 Core Pillars
                    "observed_difference": observed_diff,
                    "reference_benchmark": f"Coach-approved baseline range: {target_range[0]} - {target_range[1]} deg (optimal: {optimal_val} deg)",
                    "location_and_timing": timing_desc,
                    "suggested_correction": rule.get("suggested_correction", ""),
                    "evidence_and_confidence": {
                        "confidence_score": rule.get("min_confidence", 0.75),
                        "evidence_level": rule.get("evidence_level", "Coach Consensus"),
                        "limitations": "2D video angle estimation subject to camera perspective and single-plane projection.",
                    },
                    # Additional contextual insights
                    "efficiency_impact": rule.get("efficiency_impact", ""),
                    "injury_caution": rule.get("injury_caution", ""),
                }
                corrections.append(correction_item)

        # Prioritize corrections: High severity first, then largest deviation
        severity_rank = {"high": 3, "medium": 2, "low": 1}
        corrections.sort(
            key=lambda x: (severity_rank.get(x["severity"], 1), x["deviation_magnitude"]),
            reverse=True,
        )

        return corrections
