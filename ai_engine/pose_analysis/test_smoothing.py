"""
Landmark Smoothing Test Module
==============================
This script tests temporal landmark smoothing using Exponential Moving Average (EMA).
It loads raw extracted landmarks from 'data/outputs/pose_test/landmarks.json', applies
coordinate smoothing frame-by-frame with a configurable alpha factor (default: 0.4),
and saves the result to 'data/outputs/pose_test/smoothed_landmarks.json'.

Workflow:
1. Load raw landmark data from 'landmarks.json'.
2. Initialize EMALandmarkSmoother with alpha = 0.4.
3. Smooth landmarks across all sequential frames.
4. Save the resulting smoothed dataset to 'smoothed_landmarks.json'.
5. Print an execution summary.
"""

from pathlib import Path
import json
import sys

# Ensure project root is in sys.path for direct script execution
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ai_engine.pose_analysis.smoothing import EMALandmarkSmoother


def run_smoothing_test(alpha: float = 0.4):
    # -------------------------------------------------------------------------
    # Step 1: Set up input and output paths
    # -------------------------------------------------------------------------
    input_json_path = project_root / "data" / "outputs" / "pose_test" / "landmarks.json"
    output_dir = project_root / "data" / "outputs" / "pose_test"
    output_json_path = output_dir / "smoothed_landmarks.json"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Validate that raw landmarks JSON exists
    if not input_json_path.exists():
        raise FileNotFoundError(
            f"Raw landmarks JSON not found at: {input_json_path}. "
            f"Please run 'test_landmarks.py' first."
        )

    # -------------------------------------------------------------------------
    # Step 2: Load raw landmark data
    # -------------------------------------------------------------------------
    print(f"Loading raw landmark data from: {input_json_path.name} ...")
    with open(input_json_path, "r", encoding="utf-8") as f:
        raw_payload = json.load(f)

    raw_frames = raw_payload.get("frames", [])
    total_frames = len(raw_frames)

    # -------------------------------------------------------------------------
    # Step 3: Apply EMA smoothing sequentially
    # -------------------------------------------------------------------------
    smoother = EMALandmarkSmoother(alpha=alpha)
    smoothed_frames = smoother.smooth_sequence(raw_frames)

    # Count frames and individual landmarks processed
    frames_with_pose = sum(1 for f in smoothed_frames if f.get("pose_detected", False))
    total_landmarks_smoothed = sum(len(f.get("landmarks", [])) for f in smoothed_frames)

    # -------------------------------------------------------------------------
    # Step 4: Save smoothed dataset to JSON
    # -------------------------------------------------------------------------
    output_payload = {
        "source_video": raw_payload.get("source_video", "unknown"),
        "total_frames": total_frames,
        "fps": raw_payload.get("fps", 30.0),
        "landmark_count_per_pose": raw_payload.get("landmark_count_per_pose", 33),
        "smoothing": {
            "method": smoother.smoothing_method,
            "alpha": smoother.alpha,
        },
        "frames": smoothed_frames,
    }

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    # -------------------------------------------------------------------------
    # Step 5: Print execution summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 55)
    print("       LANDMARK SMOOTHING TEST SUMMARY")
    print("=" * 55)
    print(f"Input JSON Path           : {input_json_path}")
    print(f"Output JSON Path          : {output_json_path}")
    print(f"Smoothing Method          : {smoother.smoothing_method}")
    print(f"Smoothing Factor (Alpha)  : {smoother.alpha}")
    print(f"Total Video Frames        : {total_frames}")
    print(f"Frames Processed with Pose: {frames_with_pose}")
    print(f"Total Landmarks Smoothed  : {total_landmarks_smoothed}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    run_smoothing_test(alpha=0.4)
