"""Template Sport Pipeline.
Copy this folder to sports/<your_new_sport> and implement the methods.
"""
from ai_engine.base.base_pipeline import BaseSportPipeline
from ai_engine.registry import SportRegistry
from typing import Any, Dict
import numpy as np

# Change _template to your sport name, e.g. @SportRegistry.register_pipeline("tennis")
@SportRegistry.register_pipeline("_template")
class TemplateSportPipeline(BaseSportPipeline):
    def process_frame(self, frame: np.ndarray, frame_idx: int) -> Dict[str, Any]:
        return {"frame_idx": frame_idx, "sport": "_template", "status": "active"}

    def get_summary(self) -> Dict[str, Any]:
        return {"summary": "Template sport session complete"}
