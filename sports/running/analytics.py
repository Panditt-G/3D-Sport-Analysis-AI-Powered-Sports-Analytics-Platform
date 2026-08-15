"""Running Analytics Engine."""
from ai_engine.base.base_analytics import BaseSportAnalytics
from ai_engine.registry import SportRegistry
from typing import Any, Dict

@SportRegistry.register_analytics("running")
class RunningAnalytics(BaseSportAnalytics):
    def update(self, detection_data: Dict[str, Any], pose_data: Dict[str, Any], frame_idx: int) -> Dict[str, Any]:
        return {"instant_speed_kmh": 0.0, "current_stride_length_m": 0.0}

    def compute_summary(self) -> Dict[str, Any]:
        return {"average_speed": 0.0, "total_steps": 0, "gait_symmetry": 1.0}
