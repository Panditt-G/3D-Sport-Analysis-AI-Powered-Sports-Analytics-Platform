"""Template Sport Analytics."""
from ai_engine.base.base_analytics import BaseSportAnalytics
from ai_engine.registry import SportRegistry
from typing import Any, Dict

@SportRegistry.register_analytics("_template")
class TemplateSportAnalytics(BaseSportAnalytics):
    def update(self, detection_data: Dict[str, Any], pose_data: Dict[str, Any], frame_idx: int) -> Dict[str, Any]:
        return {"metric": 0.0}

    def compute_summary(self) -> Dict[str, Any]:
        return {"overall_score": 100}
