"""
Pose Landmark Extraction Module
===============================
This module extracts, formats, and standardizes 33 full-body landmarks from
MediaPipe BlazePose inference results.

Each landmark contains:
- landmark name (e.g. 'left_shoulder', 'right_knee')
- landmark index (0-32)
- normalized coordinates (x, y, z)
- visibility score (0.0 - 1.0)
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import mediapipe as mp


# Standard MediaPipe 33 BlazePose landmark mapping
BLAZEPOSE_LANDMARK_NAMES = [
    "nose",                   # 0
    "left_eye_inner",         # 1
    "left_eye",               # 2
    "left_eye_outer",         # 3
    "right_eye_inner",        # 4
    "right_eye",              # 5
    "right_eye_outer",        # 6
    "left_ear",               # 7
    "right_ear",              # 8
    "mouth_left",             # 9
    "mouth_right",            # 10
    "left_shoulder",          # 11
    "right_shoulder",         # 12
    "left_elbow",             # 13
    "right_elbow",            # 14
    "left_wrist",             # 15
    "right_wrist",            # 16
    "left_pinky",             # 17
    "right_pinky",            # 18
    "left_index",             # 19
    "right_index",            # 20
    "left_thumb",             # 21
    "right_thumb",            # 22
    "left_hip",               # 23
    "right_hip",              # 24
    "left_knee",              # 25
    "right_knee",             # 26
    "left_ankle",             # 27
    "right_ankle",            # 28
    "left_heel",              # 29
    "right_heel",             # 30
    "left_foot_index",        # 31
    "right_foot_index",       # 32
]


@dataclass
class LandmarkPoint:
    """Represents a single body landmark point."""
    name: str
    index: int
    x: float
    y: float
    z: float
    visibility: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert landmark data to standard dictionary format."""
        return asdict(self)


class PoseLandmarkExtractor:
    """
    Extracts structured landmark data from MediaPipe Pose detection results.
    """

    def __init__(self):
        self.landmark_names = BLAZEPOSE_LANDMARK_NAMES
        self.num_landmarks = len(self.landmark_names)

    def extract_landmarks(self, pose_landmarks) -> List[Dict[str, Any]]:
        """
        Extract all 33 body landmarks from MediaPipe pose_landmarks object.

        Args:
            pose_landmarks: MediaPipe NormalizedLandmarkList object.

        Returns:
            List of dictionaries containing landmark name, index, coordinates, and visibility.
        """
        if pose_landmarks is None or not hasattr(pose_landmarks, "landmark"):
            return []

        extracted = []
        for idx, lm in enumerate(pose_landmarks.landmark):
            name = (
                self.landmark_names[idx]
                if idx < len(self.landmark_names)
                else f"landmark_{idx}"
            )
            landmark_point = LandmarkPoint(
                name=name,
                index=idx,
                x=float(lm.x),
                y=float(lm.y),
                z=float(lm.z),
                visibility=float(getattr(lm, "visibility", 1.0)),
            )
            extracted.append(landmark_point.to_dict())

        return extracted

    def extract_frame_data(
        self,
        frame_index: int,
        timestamp: float,
        pose_landmarks: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Extract structured frame metadata and landmark list for a video frame.

        Args:
            frame_index: Sequential integer index of the frame (0, 1, 2, ...).
            timestamp: Video timestamp in seconds (e.g. 0.033).
            pose_landmarks: MediaPipe pose landmarks if detected, else None.

        Returns:
            Dictionary containing frame index, timestamp, detection status, and landmarks list.
        """
        landmarks = self.extract_landmarks(pose_landmarks)
        pose_detected = len(landmarks) > 0

        return {
            "frame_index": frame_index,
            "timestamp": round(float(timestamp), 4),
            "pose_detected": pose_detected,
            "landmarks": landmarks,
        }
