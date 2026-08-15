"""Abstract Base Class for Sport AI Pipelines."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import numpy as np

class BaseSportPipeline(ABC):
    """
    Standard interface that every sport pipeline must implement.
    Ensures modularity and easy integration of new sports.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    def process_frame(self, frame: np.ndarray, frame_idx: int) -> Dict[str, Any]:
        """
        Process a single video frame.
        Returns detection, pose, tracking, and telemetry for this frame.
        """
        pass

    @abstractmethod
    def get_summary(self) -> Dict[str, Any]:
        """Return final aggregated metrics for the session."""
        pass

    def reset(self) -> None:
        """Reset state between videos/streams."""
        pass
