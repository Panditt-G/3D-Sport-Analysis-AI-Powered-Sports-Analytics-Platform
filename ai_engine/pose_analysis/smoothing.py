"""
Pose Landmark Smoothing Module
==============================
This module applies temporal filtering to reduce jitter in sequential pose
landmark coordinates (x, y, z) across video frames while preserving athletic movement.

Uses Exponential Moving Average (EMA):
    S_t = alpha * X_t + (1 - alpha) * S_{t-1}
where:
    - X_t: raw landmark coordinate at frame t
    - S_{t-1}: smoothed landmark coordinate from previous frame
    - S_t: updated smoothed coordinate
    - alpha: smoothing factor in range (0, 1] (higher = more responsive, lower = smoother)
"""

from typing import List, Dict, Any, Optional
import copy


class EMALandmarkSmoother:
    """
    Exponential Moving Average (EMA) smoother for 3D body pose landmarks.
    """

    def __init__(self, alpha: float = 0.4):
        """
        Initialize the EMA smoother.

        Args:
            alpha: Smoothing weight factor between 0.0 and 1.0 (default: 0.4).
                   - alpha = 1.0: no smoothing (raw values).
                   - alpha < 0.5: heavier smoothing for jitter reduction.
        """
        if not (0.0 < alpha <= 1.0):
            raise ValueError(f"Alpha must be in range (0.0, 1.0], got {alpha}")

        self.alpha = float(alpha)
        self.smoothing_method = "Exponential Moving Average (EMA)"
        # Stores previous smoothed coordinates by landmark index: {index: (x, y, z)}
        self._prev_landmarks: Dict[int, Dict[str, float]] = {}

    def reset(self) -> None:
        """Reset the internal history state of the smoother."""
        self._prev_landmarks.clear()

    def smooth_landmarks(self, raw_landmarks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Smooth landmark coordinates for a single frame.

        Args:
            raw_landmarks: List of landmark dictionaries from MediaPipe extraction.

        Returns:
            List of new landmark dictionaries with smoothed x, y, z coordinates.
        """
        if not raw_landmarks:
            return []

        smoothed_landmarks: List[Dict[str, Any]] = []

        for lm in raw_landmarks:
            idx = lm["index"]
            name = lm["name"]
            curr_x = float(lm["x"])
            curr_y = float(lm["y"])
            curr_z = float(lm["z"])
            visibility = float(lm.get("visibility", 1.0))

            if idx in self._prev_landmarks:
                # Apply EMA formula: S_t = alpha * X_t + (1 - alpha) * S_{t-1}
                prev = self._prev_landmarks[idx]
                smooth_x = self.alpha * curr_x + (1.0 - self.alpha) * prev["x"]
                smooth_y = self.alpha * curr_y + (1.0 - self.alpha) * prev["y"]
                smooth_z = self.alpha * curr_z + (1.0 - self.alpha) * prev["z"]
            else:
                # First appearance of this landmark initializes the state
                smooth_x = curr_x
                smooth_y = curr_y
                smooth_z = curr_z

            # Update stored state for next frame
            self._prev_landmarks[idx] = {
                "x": smooth_x,
                "y": smooth_y,
                "z": smooth_z,
            }

            smoothed_landmarks.append({
                "name": name,
                "index": idx,
                "x": round(smooth_x, 6),
                "y": round(smooth_y, 6),
                "z": round(smooth_z, 6),
                "visibility": round(visibility, 6),
            })

        return smoothed_landmarks

    def smooth_frame(self, frame_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Smooth a single structured frame dictionary.

        Args:
            frame_data: Dictionary containing frame_index, timestamp, pose_detected, landmarks.

        Returns:
            New frame dictionary with smoothed landmark list.
        """
        smoothed_frame = {
            "frame_index": frame_data["frame_index"],
            "timestamp": frame_data["timestamp"],
            "pose_detected": frame_data["pose_detected"],
            "landmarks": [],
        }

        if frame_data.get("pose_detected", False) and frame_data.get("landmarks"):
            smoothed_frame["landmarks"] = self.smooth_landmarks(frame_data["landmarks"])

        return smoothed_frame

    def smooth_sequence(self, frames: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sequentially smooth a full list of video frames.

        Args:
            frames: Chronological list of frame dictionaries.

        Returns:
            List of smoothed frame dictionaries.
        """
        self.reset()
        smoothed_frames = []
        for frame in frames:
            smoothed_frames.append(self.smooth_frame(frame))
        return smoothed_frames
