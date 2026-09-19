"""
MediaPipe Pose Estimation Module (Tasks API & Legacy Compatible)
================================================================
This module wraps the MediaPipe BlazePose estimation model using the modern
MediaPipe Tasks API (PoseLandmarker) while maintaining seamless backward
compatibility with both MediaPipe Tasks and legacy mp.solutions interfaces.
"""

import os
import urllib.request
from pathlib import Path
from typing import Optional, Tuple, List, Any
from dataclasses import dataclass
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core import base_options


# Standard MediaPipe 33 BlazePose landmark connections
POSE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7),
    (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10),
    (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (24, 26), (25, 27), (26, 28),
    (27, 29), (28, 30), (29, 31), (30, 32), (27, 31), (28, 32)
]

# Google Cloud Storage URL for downloading PoseLandmarker task models
MODEL_URLS = {
    0: "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task",
    1: "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task",
    2: "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task",
}


class NormalizedLandmarkList:
    """Wrapper matching legacy MediaPipe NormalizedLandmarkList interface."""

    def __init__(self, landmarks: List[Any]):
        self.landmark = landmarks

    def __iter__(self):
        return iter(self.landmark)

    def __len__(self):
        return len(self.landmark)

    def __getitem__(self, idx):
        return self.landmark[idx]


class PoseResults:
    """Container for pose estimation results matching legacy namedtuple."""

    def __init__(
        self,
        pose_landmarks: Optional[NormalizedLandmarkList] = None,
        pose_world_landmarks: Optional[NormalizedLandmarkList] = None,
    ):
        self.pose_landmarks = pose_landmarks
        self.pose_world_landmarks = pose_world_landmarks


class MediaPipePoseEstimator:
    """
    Wrapper class for MediaPipe Pose to handle frame inference
    and skeletal landmark visualization across all MediaPipe versions.
    """

    def __init__(
        self,
        static_image_mode: bool = False,
        model_complexity: int = 1,
        smooth_landmarks: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        model_path: Optional[str] = None,
    ):
        """
        Initialize the MediaPipe Pose detector using PoseLandmarker Tasks API.

        Args:
            static_image_mode: Flag preserved for API compatibility.
            model_complexity: 0: Lite, 1: Full, 2: Heavy model.
            smooth_landmarks: Whether to smooth landmarks across frames.
            min_detection_confidence: Minimum detection confidence threshold [0.0, 1.0].
            min_tracking_confidence: Minimum tracking confidence threshold [0.0, 1.0].
            model_path: Optional custom path to pose_landmarker.task file.
        """
        self.num_landmarks = 33
        self.POSE_CONNECTIONS = POSE_CONNECTIONS

        # Determine model file path
        if model_path is None:
            model_path = self._resolve_or_download_model(model_complexity)

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"MediaPipe Pose model file not found at: {model_path}")

        # Initialize Tasks API PoseLandmarker
        base_opts = base_options.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_opts,
            running_mode=vision.RunningMode.IMAGE,
            min_pose_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            num_poses=1,
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)

    def _resolve_or_download_model(self, complexity: int) -> str:
        """Find local model task file or download from Google Cloud Storage."""
        model_names = {0: "pose_landmarker_lite.task", 1: "pose_landmarker_full.task", 2: "pose_landmarker_heavy.task"}
        model_name = model_names.get(complexity, "pose_landmarker_full.task")

        # Check candidate search locations
        possible_paths = [
            Path(os.getcwd()) / model_name,
            Path(__file__).resolve().parents[3] / model_name,
            Path(__file__).resolve().parents[3] / "models" / model_name,
            Path(__file__).resolve().parent / model_name,
        ]

        for p in possible_paths:
            if p.exists():
                return str(p)

        # Download if not present
        target_path = Path(__file__).resolve().parents[3] / model_name
        url = MODEL_URLS.get(complexity, MODEL_URLS[1])
        print(f"Downloading MediaPipe model ({model_name})...")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, str(target_path))
        return str(target_path)

    def process_frame(self, frame_bgr) -> PoseResults:
        """
        Process a single BGR image/frame and extract pose landmarks.

        Args:
            frame_bgr: Input frame in BGR format (standard OpenCV format).

        Returns:
            PoseResults object with 'pose_landmarks' and 'pose_world_landmarks'.
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return PoseResults(None, None)

        # Convert OpenCV BGR frame to RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        # Run detection
        detection_result = self.detector.detect(mp_image)

        if not detection_result.pose_landmarks or len(detection_result.pose_landmarks) == 0:
            return PoseResults(None, None)

        # Extract primary person landmarks
        primary_landmarks = detection_result.pose_landmarks[0]
        wrapped_landmarks = NormalizedLandmarkList(primary_landmarks)

        world_landmarks = None
        if detection_result.pose_world_landmarks and len(detection_result.pose_world_landmarks) > 0:
            world_landmarks = NormalizedLandmarkList(detection_result.pose_world_landmarks[0])

        return PoseResults(pose_landmarks=wrapped_landmarks, pose_world_landmarks=world_landmarks)

    def draw_landmarks(self, frame_bgr, pose_landmarks) -> None:
        """
        Draw pose landmarks and skeletal connections directly on the BGR frame.

        Args:
            frame_bgr: The frame to draw on (modified in-place).
            pose_landmarks: NormalizedLandmarkList or list of landmarks.
        """
        if pose_landmarks is None:
            return

        landmarks = (
            pose_landmarks.landmark
            if hasattr(pose_landmarks, "landmark")
            else pose_landmarks
        )

        if not landmarks:
            return

        height, width = frame_bgr.shape[:2]

        # Draw skeletal connection lines
        for start_idx, end_idx in self.POSE_CONNECTIONS:
            if start_idx < len(landmarks) and end_idx < len(landmarks):
                pt1 = landmarks[start_idx]
                pt2 = landmarks[end_idx]

                # Check visibility if available
                v1 = getattr(pt1, "visibility", 1.0)
                v2 = getattr(pt2, "visibility", 1.0)
                if (v1 is None or v1 > 0.3) and (v2 is None or v2 > 0.3):
                    x1, y1 = int(pt1.x * width), int(pt1.y * height)
                    x2, y2 = int(pt2.x * width), int(pt2.y * height)
                    cv2.line(frame_bgr, (x1, y1), (x2, y2), (0, 255, 0), 2, cv2.LINE_AA)

        # Draw landmark keypoints
        for lm in landmarks:
            v = getattr(lm, "visibility", 1.0)
            if v is None or v > 0.3:
                cx, cy = int(lm.x * width), int(lm.y * height)
                cv2.circle(frame_bgr, (cx, cy), 4, (0, 0, 255), -1, cv2.LINE_AA)
                cv2.circle(frame_bgr, (cx, cy), 5, (255, 255, 255), 1, cv2.LINE_AA)

    def close(self):
        """Release MediaPipe Pose detector resources."""
        if hasattr(self, "detector") and self.detector is not None:
            try:
                self.detector.close()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
