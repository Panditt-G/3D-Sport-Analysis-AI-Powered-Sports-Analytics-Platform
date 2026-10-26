"""
YOLOv8 Pose Estimator Adapter conforming to BasePoseEstimator.
==============================================================
Wraps Ultralytics YOLOv8-pose (e.g. yolov8n-pose.pt) to produce
standardized Keypoint and PoseFrame objects with COCO-17 landmarks.
"""

from typing import Dict, Any, Optional, List
import numpy as np

from ai_engine.vision.pose.base_pose import BasePoseEstimator, PoseFrame, Keypoint


YOLO_COCO_KEYPOINTS = [
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
]


class YOLOPoseEstimator(BasePoseEstimator):
    """Adapter for YOLOv8-pose (COCO-17 keypoints)."""

    def __init__(self, model_weight: str = "yolov8n-pose.pt", conf_threshold: float = 0.25):
        import os
        from pathlib import Path
        if not os.path.exists(model_weight):
            # Try searching project root
            candidate = Path(__file__).resolve().parents[3] / model_weight
            if candidate.exists():
                model_weight = str(candidate)
        self.model_weight = model_weight
        self.conf_threshold = conf_threshold
        self._model = None
        self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO
            self._model = YOLO(self.model_weight)
        except Exception as e:
            # Fallback/graceful handling if weights are downloading or ultralytics is not ready
            print(f"Warning: YOLOv8-pose initialization deferred: {e}")
            self._model = None

    def estimate(self, frame_bgr: np.ndarray, frame_idx: int = 0, timestamp: float = 0.0) -> PoseFrame:
        h, w = frame_bgr.shape[:2]
        keypoints: Dict[str, Keypoint] = {}
        bbox = None
        is_valid = False
        avg_confidence = 0.0

        if self._model is not None:
            try:
                results = self._model(frame_bgr, conf=self.conf_threshold, verbose=False)
                if results and len(results) > 0 and results[0].keypoints is not None:
                    # Select person with highest detection confidence or largest bbox area
                    boxes = results[0].boxes
                    kpts_data = results[0].keypoints.data  # [N, 17, 3] or [N, 17, 2]

                    if len(kpts_data) > 0:
                        # Select first / primary detected person
                        primary_kpts = kpts_data[0].cpu().numpy()
                        confs = []

                        for idx, name in enumerate(YOLO_COCO_KEYPOINTS):
                            if idx < len(primary_kpts):
                                pt = primary_kpts[idx]
                                px, py = float(pt[0]), float(pt[1])
                                conf = float(pt[2]) if len(pt) > 2 else 0.8
                                norm_x = px / w if w > 0 else 0.0
                                norm_y = py / h if h > 0 else 0.0

                                keypoints[name] = Keypoint(
                                    name=name,
                                    x=norm_x,
                                    y=norm_y,
                                    confidence=conf,
                                    visibility=conf,
                                    pixel_x=int(np.clip(px, 0, w - 1)),
                                    pixel_y=int(np.clip(py, 0, h - 1)),
                                )
                                confs.append(conf)

                        # Virtual joints (neck, chest)
                        if "left_shoulder" in keypoints and "right_shoulder" in keypoints:
                            ls = keypoints["left_shoulder"]
                            rs = keypoints["right_shoulder"]
                            neck_x = (ls.x + rs.x) / 2.0
                            neck_y = (ls.y + rs.y) / 2.0
                            keypoints["neck"] = Keypoint(
                                name="neck",
                                x=neck_x,
                                y=neck_y,
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

                        if boxes is not None and len(boxes) > 0:
                            b = boxes[0].xyxyn[0].cpu().numpy()
                            bbox = [float(b[0]), float(b[1]), float(b[2]), float(b[3])]

                        if confs:
                            avg_confidence = float(np.mean(confs))
                            is_valid = avg_confidence > 0.25
            except Exception as ex:
                print(f"Error during YOLO pose inference: {ex}")

        return PoseFrame(
            frame_idx=frame_idx,
            timestamp=timestamp,
            keypoints=keypoints,
            bbox=bbox,
            confidence=avg_confidence,
            is_valid=is_valid,
            model_name="yolov8n-pose",
        )

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_id": "yolov8n-pose",
            "type": "pose_estimation",
            "checkpoint": self.model_weight,
            "device": "cpu/cuda",
            "keypoint_schema": "coco_17",
            "status": "validated",
        }
