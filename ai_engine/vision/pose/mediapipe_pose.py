"""
MediaPipe Pose Estimation Module
================================
This module wraps the MediaPipe BlazePose estimation model to provide an easy,
beginner-friendly interface for detecting 33 full-body 3D landmarks and drawing
skeletal connections on video frames.
"""

from typing import Optional, Tuple
import cv2
import mediapipe as mp


class MediaPipePoseEstimator:
    """
    A wrapper class for MediaPipe Pose (BlazePose) to handle frame inference
    and skeletal landmark visualization.
    """

    def __init__(
        self,
        static_image_mode: bool = False,
        model_complexity: int = 1,
        smooth_landmarks: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        """
        Initialize the MediaPipe Pose detector.

        Args:
            static_image_mode: Set to False for video streams to enable temporal tracking.
            model_complexity: Model complexity (0: Lite, 1: Full, 2: Heavy).
            smooth_landmarks: Whether to filter landmarks across frames to reduce jitter.
            min_detection_confidence: Minimum confidence threshold [0.0, 1.0] for detection.
            min_tracking_confidence: Minimum confidence threshold [0.0, 1.0] for tracking.
        """
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        # Initialize the underlying MediaPipe Pose model
        self.pose = self.mp_pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            smooth_landmarks=smooth_landmarks,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

        # Standard landmark count provided by BlazePose
        self.num_landmarks = 33

    def process_frame(self, frame_bgr):
        """
        Process a single BGR image/frame and extract pose landmarks.

        Args:
            frame_bgr: Input image/frame in BGR format (standard OpenCV format).

        Returns:
            NamedTuple with 'pose_landmarks' and 'pose_world_landmarks'.
        """
        # OpenCV frames are BGR by default, but MediaPipe expects RGB format
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        # MediaPipe optimizes processing by marking the image as non-writeable
        frame_rgb.flags.writeable = False
        results = self.pose.process(frame_rgb)
        frame_rgb.flags.writeable = True

        return results

    def draw_landmarks(self, frame_bgr, pose_landmarks) -> None:
        """
        Draw pose landmarks and skeletal connections directly on the BGR frame.

        Args:
            frame_bgr: The frame to draw on (modified in-place).
            pose_landmarks: MediaPipe NormalizedLandmarkList from inference results.
        """
        if pose_landmarks is not None:
            self.mp_drawing.draw_landmarks(
                image=frame_bgr,
                landmark_list=pose_landmarks,
                connections=self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style(),
            )

    def close(self):
        """Release MediaPipe Pose resources."""
        if hasattr(self, "pose") and self.pose is not None:
            self.pose.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
