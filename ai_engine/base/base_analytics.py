"""Abstract Base Class for Sport Analytics."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseSportAnalytics(ABC):
    """
    Standard interface for sport-specific metrics computation.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.history: List[Dict[str, Any]] = []

    @abstractmethod
    def update(self, detection_data: Dict[str, Any], pose_data: Dict[str, Any], frame_idx: int) -> Dict[str, Any]:
        """Update metrics with new frame data and return instantaneous statistics."""
        pass

    @abstractmethod
    def compute_summary(self) -> Dict[str, Any]:
        """Compute aggregate performance metrics across the entire session."""
        pass
