"""
MediaPipe BlazePose Adapter conforming to BasePoseEstimator.
===========================================================
Maps 33 BlazePose landmarks to standard Keypoint and PoseFrame structures.
"""

from typing import Dict, Any, Optional
import numpy as np
import cv2

from ai_engine.vision.pose.base_pose import BasePoseEstimator, PoseFrame, Keypoint
from ai_engine.vision.pose.mediapipe_pose import MediaPipePoseEstimator


# MediaPipe BlazePose 33 index mapping to standardized names
MP_INDEX_MAP = {
    0: "nose",
    2: "left_eye",
    5: "right_eye",
    7: "left_ear",
    8: "right_ear",
    11: "left_shoulder",
    12: "right_shoulder",
    13: "left_elbow",
    14: "right_elbow",
    15: "left_wrist",
    16: "right_wrist",
    23: "left_hip",
    24: "right_hip",
    25: "left_knee",
    26: "right_knee",
    27: "left_ankle",
    28: "right_ankle",
}


class MediaPipeAdapter(BasePoseEstimator):
    """Adapter for MediaPipe BlazePose returning standardized PoseFrame."""

    def __init__(
        self,
        static_image_mode: bool = False,
        model_complexity: int = 1,
        smooth_landmarks: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        self.estimator = MediaPipePoseEstimator(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            smooth_landmarks=smooth_landmarks,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.complexity = model_complexity

    def estimate(self, frame_bgr: np.ndarray, frame_idx: int = 0, timestamp: float = 0.0) -> PoseFrame:
        h, w = frame_bgr.shape[:2]
        results = self.estimator.process_frame(frame_bgr)

        keypoints: Dict[str, Keypoint] = {}
        bbox = None
        is_valid = False
        avg_confidence = 0.0

        if results and results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            xs, ys, confs = [], [], []

            for idx, lm in enumerate(landmarks):
                # Standard named landmarks
                name = MP_INDEX_MAP.get(idx, f"lm_{idx}")
                conf = float(getattr(lm, "visibility", 1.0))
                px = int(np.clip(lm.x * w, 0, w - 1))
                py = int(np.clip(lm.y * h, 0, h - 1))

                kp = Keypoint(
                    name=name,
                    x=float(lm.x),
                    y=float(lm.y),
                    z=float(lm.z),
                    confidence=conf,
                    visibility=conf,
                    pixel_x=px,
                    pixel_y=py,
                )
                keypoints[name] = kp

                if idx in MP_INDEX_MAP:
                    xs.append(lm.x)
                    ys.append(lm.y)
                    confs.append(conf)

            # Compute virtual points: chest and neck
            if "left_shoulder" in keypoints and "right_shoulder" in keypoints:
                ls = keypoints["left_shoulder"]
                rs = keypoints["right_shoulder"]
                neck_x = (ls.x + rs.x) / 2.0
                neck_y = (ls.y + rs.y) / 2.0
                keypoints["neck"] = Keypoint(
                    name="neck",
                    x=neck_x,
                    y=neck_y,
                    z=(ls.z + rs.z) / 2.0,
                    confidence=min(ls.confidence, rs.confidence),
                    pixel_x=int(neck_x * w),
                    pixel_y=int(neck_y * h),
                )

                if "left_hip" in keypoints and "right_hip" in keypoints:
                    lh = keypoints["left_hip"]
                    rh = keypoints["right_hip"]
                    mid_hip_x = (lh.x + rh.x) / 2.0
                    mid_hip_y = (lh.y + rh.y) / 2.0
                    chest_x = neck_x * 0.6 + mid_hip_x * 0.4
                    chest_y = neck_y * 0.6 + mid_hip_y * 0.4
                    keypoints["chest"] = Keypoint(
                        name="chest",
                        x=chest_x,
                        y=chest_y,
                        confidence=min(ls.confidence, rs.confidence, lh.confidence, rh.confidence),
                        pixel_x=int(chest_x * w),
                        pixel_y=int(chest_y * h),
                    )

            if xs and ys:
                bbox = [
                    float(max(0.0, min(xs) - 0.05)),
                    float(max(0.0, min(ys) - 0.05)),
                    float(min(1.0, max(xs) + 0.05)),
                    float(min(1.0, max(ys) + 0.05)),
                ]
                avg_confidence = float(np.mean(confs))
                is_valid = avg_confidence > 0.3

        return PoseFrame(
            frame_idx=frame_idx,
            timestamp=timestamp,
            keypoints=keypoints,
            bbox=bbox,
            confidence=avg_confidence,
            is_valid=is_valid,
            model_name="mediapipe_blazepose",
        )

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_id": "mediapipe_blazepose",
            "type": "pose_estimation",
            "version": "0.10.x",
            "complexity": self.complexity,
            "device": "cpu",
            "keypoint_schema": "blazepose_33_coco17_normalized",
            "status": "validated",
        }

    def close(self):
        self.estimator.close()
