"""Cricket AI Pipeline."""
from ai_engine.base.base_pipeline import BaseSportPipeline
from ai_engine.registry import SportRegistry
from typing import Any, Dict
import numpy as np

@SportRegistry.register_pipeline("cricket")
class CricketPipeline(BaseSportPipeline):
    def process_frame(self, frame: np.ndarray, frame_idx: int) -> Dict[str, Any]:
        return {"frame_idx": frame_idx, "sport": "cricket", "bowler_action": None, "batsman_pose": None}

    def get_summary(self) -> Dict[str, Any]:
        return {"bowling_speed_kmh": 0.0, "shot_direction_deg": 0.0, "crease_occupancy": 0.0}
