"""Running AI Pipeline."""
from ai_engine.base.base_pipeline import BaseSportPipeline
from ai_engine.registry import SportRegistry
from typing import Any, Dict
import numpy as np

@SportRegistry.register_pipeline("running")
class RunningPipeline(BaseSportPipeline):
    def process_frame(self, frame: np.ndarray, frame_idx: int) -> Dict[str, Any]:
        return {"frame_idx": frame_idx, "sport": "running", "stride_detected": False}

    def get_summary(self) -> Dict[str, Any]:
        return {"total_distance_m": 0.0, "avg_speed_kmh": 0.0, "avg_cadence_spm": 0}
