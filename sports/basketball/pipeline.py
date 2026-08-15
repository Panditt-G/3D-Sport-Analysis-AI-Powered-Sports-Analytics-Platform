"""Basketball AI Pipeline."""
from ai_engine.base.base_pipeline import BaseSportPipeline
from ai_engine.registry import SportRegistry
from typing import Any, Dict
import numpy as np

@SportRegistry.register_pipeline("basketball")
class BasketballPipeline(BaseSportPipeline):
    def process_frame(self, frame: np.ndarray, frame_idx: int) -> Dict[str, Any]:
        return {"frame_idx": frame_idx, "sport": "basketball", "ball_detected": True}

    def get_summary(self) -> Dict[str, Any]:
        return {"shots_attempted": 0, "shots_made": 0, "possession_time_s": 0.0}
