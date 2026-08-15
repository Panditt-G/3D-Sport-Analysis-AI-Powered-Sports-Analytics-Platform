"""Volleyball AI Pipeline."""
from ai_engine.base.base_pipeline import BaseSportPipeline
from ai_engine.registry import SportRegistry
from typing import Any, Dict
import numpy as np

@SportRegistry.register_pipeline("volleyball")
class VolleyballPipeline(BaseSportPipeline):
    def process_frame(self, frame: np.ndarray, frame_idx: int) -> Dict[str, Any]:
        return {"frame_idx": frame_idx, "sport": "volleyball"}

    def get_summary(self) -> Dict[str, Any]:
        return {"spikes_detected": 0, "max_jump_height_cm": 0.0}
