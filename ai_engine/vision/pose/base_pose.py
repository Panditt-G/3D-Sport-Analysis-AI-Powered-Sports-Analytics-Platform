"""
Base Pose Estimator Contract & Unified Landmark Specification.
==============================================================
Provides standard landmark definitions, keypoint dataclasses, and
abstract BasePoseEstimator class for plug-and-play pose estimators
(MediaPipe, YOLOv8-pose, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
import numpy as np


# Standard 17 COCO Keypoints + Common Extension Points
STANDARD_KEYPOINTS = [
    "nose",
    "left_eye",
    "right_eye",
    "left_ear",
    "right_ear",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
    # Extended points for sport biomechanics
    "chest",
    "neck",
]

# Standard Skeletal Connections for Rendering (pair names)
SKELETAL_CONNECTIONS = [
    # Head
    ("nose", "left_eye"),
    ("nose", "right_eye"),
    ("left_eye", "left_ear"),
    ("right_eye", "right_ear"),
    # Upper Body
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"),
    ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"),
    ("right_elbow", "right_wrist"),
    # Torso
    ("left_shoulder", "left_hip"),
    ("right_shoulder", "right_hip"),
    ("left_hip", "right_hip"),
    # Lower Body
    ("left_hip", "left_knee"),
    ("left_knee", "left_ankle"),
    ("right_hip", "right_knee"),
    ("right_knee", "right_ankle"),
]


@dataclass
class Keypoint:
    """Represents a single body landmark."""
    name: str
    x: float  # Normalized [0, 1] or pixel coord
    y: float  # Normalized [0, 1] or pixel coord
    z: float = 0.0  # Depth or relative elevation
    confidence: float = 1.0  # Detection confidence [0, 1]
    visibility: float = 1.0  # Visibility factor [0, 1]
    pixel_x: int = 0
    pixel_y: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PoseFrame:
    """Standardized pose estimation result for a single video frame."""
    frame_idx: int
    timestamp: float
    keypoints: Dict[str, Keypoint] = field(default_factory=dict)
    bbox: Optional[List[float]] = None  # [x_min, y_min, x_max, y_max] normalized
    confidence: float = 0.0
    is_valid: bool = False
    model_name: str = "generic"

    def get_point(self, name: str) -> Optional[Keypoint]:
        """Get a keypoint by name if present and sufficiently confident."""
        kp = self.keypoints.get(name)
        if kp and kp.confidence > 0.15:
            return kp
        return None

    def get_coords(self, name: str) -> Optional[Tuple[float, float]]:
        """Return (x, y) coordinates for a keypoint."""
        kp = self.get_point(name)
        if kp:
            return (kp.x, kp.y)
        return None

    def get_pixel_coords(self, name: str) -> Optional[Tuple[int, int]]:
        """Return (pixel_x, pixel_y) integer coordinates."""
        kp = self.get_point(name)
        if kp:
            return (kp.pixel_x, kp.pixel_y)
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame_idx": self.frame_idx,
            "timestamp": self.timestamp,
            "bbox": self.bbox,
            "confidence": self.confidence,
            "is_valid": self.is_valid,
            "model_name": self.model_name,
            "keypoints": {k: v.to_dict() for k, v in self.keypoints.items()},
        }


class BasePoseEstimator(ABC):
    """Abstract interface that all pose estimators (MediaPipe, YOLO, etc.) must implement."""

    @abstractmethod
    def estimate(self, frame_bgr: np.ndarray, frame_idx: int = 0, timestamp: float = 0.0) -> PoseFrame:
        """
        Extract pose keypoints from a single video frame.

        Args:
            frame_bgr: Input BGR frame.
            frame_idx: Index of current frame.
            timestamp: Frame timestamp in seconds.

        Returns:
            PoseFrame with normalized and pixel keypoints.
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Return model metadata, version, and device requirements."""
        pass
