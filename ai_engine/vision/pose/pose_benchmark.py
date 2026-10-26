"""
Pose Model Benchmarking Utility.
================================
Benchmarks MediaPipe BlazePose and YOLOv8-pose on video input or synthetic frames,
comparing inference latency, FPS, landmark stability, and failure rates.
"""

import time
from typing import Dict, Any, List, Optional
import numpy as np

from ai_engine.vision.pose.base_pose import BasePoseEstimator
from ai_engine.vision.pose.mediapipe_adapter import MediaPipeAdapter
from ai_engine.vision.pose.yolo_pose import YOLOPoseEstimator


def benchmark_estimator(
    estimator: BasePoseEstimator,
    frames: List[np.ndarray],
    warmup_frames: int = 5,
) -> Dict[str, Any]:
    """
    Benchmark an individual pose estimator across a series of frames.

    Args:
        estimator: Instance of BasePoseEstimator.
        frames: List of BGR numpy image frames.
        warmup_frames: Frames to run without measuring (JIT / cache warm).

    Returns:
        Dictionary with latency metrics, FPS, and detection quality stats.
    """
    info = estimator.get_model_info()
    model_id = info.get("model_id", "unknown")

    # Warmup
    for i in range(min(warmup_frames, len(frames))):
        _ = estimator.estimate(frames[i], frame_idx=i, timestamp=i * 0.033)

    latencies_ms = []
    valid_frames = 0
    kpt_counts = []
    confidences = []

    for idx, frame in enumerate(frames):
        t0 = time.perf_counter()
        pose_frame = estimator.estimate(frame, frame_idx=idx, timestamp=idx * 0.033)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(dt_ms)

        if pose_frame.is_valid:
            valid_frames += 1

        kpt_counts.append(len(pose_frame.keypoints))
        confidences.append(pose_frame.confidence)

    total_frames = len(frames)
    avg_latency = float(np.mean(latencies_ms)) if latencies_ms else 0.0
    p95_latency = float(np.percentile(latencies_ms, 95)) if latencies_ms else 0.0
    fps = 1000.0 / avg_latency if avg_latency > 0 else 0.0

    return {
        "model_id": model_id,
        "total_frames": total_frames,
        "valid_detection_rate": round(valid_frames / max(1, total_frames), 3),
        "mean_latency_ms": round(avg_latency, 2),
        "p95_latency_ms": round(p95_latency, 2),
        "fps": round(fps, 1),
        "avg_confidence": round(float(np.mean(confidences)), 3) if confidences else 0.0,
        "avg_keypoints_detected": round(float(np.mean(kpt_counts)), 1) if kpt_counts else 0.0,
    }


def compare_estimators(
    frames: List[np.ndarray],
    models: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Run side-by-side comparison on all available pose estimators.
    """
    if models is None:
        models = ["mediapipe", "yolo"]

    results = {}
    for m in models:
        try:
            if m == "mediapipe":
                est = MediaPipeAdapter(model_complexity=1)
                results["mediapipe"] = benchmark_estimator(est, frames)
            elif m == "yolo":
                est = YOLOPoseEstimator()
                results["yolo"] = benchmark_estimator(est, frames)
        except Exception as e:
            results[m] = {"error": str(e)}

    return results
