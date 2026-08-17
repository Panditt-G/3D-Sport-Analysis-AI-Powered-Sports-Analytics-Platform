"""
Joint Angle Calculation Test Module
===================================
This script computes running joint angles (knees, hips, ankles) from smoothed
pose landmarks stored in 'data/outputs/pose_test/smoothed_landmarks.json' and saves
the resulting angle time series to 'data/outputs/pose_test/joint_angles.json'.

Workflow:
1. Load smoothed landmark data from 'smoothed_landmarks.json'.
2. Initialize JointAngleCalculator with standard running joint definitions.
3. Compute angles frame-by-frame (left/right knee, hip, ankle).
4. Calculate min/max range for each joint across all valid frames.
5. Save results to 'joint_angles.json'.
6. Print execution and range summary.
"""

from pathlib import Path
import json
import sys

# Ensure project root is in sys.path for direct script execution
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ai_engine.pose_analysis.joint_angles import (
    JointAngleCalculator,
    RUNNING_JOINT_DEFINITIONS,
)


def run_joint_angles_test():
    # -------------------------------------------------------------------------
    # Step 1: Set up input and output file paths
    # -------------------------------------------------------------------------
    input_json_path = project_root / "data" / "outputs" / "pose_test" / "smoothed_landmarks.json"
    output_dir = project_root / "data" / "outputs" / "pose_test"
    output_json_path = output_dir / "joint_angles.json"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Validate that smoothed landmarks JSON exists
    if not input_json_path.exists():
        raise FileNotFoundError(
            f"Smoothed landmarks JSON not found at: {input_json_path}. "
            f"Please run 'test_smoothing.py' first."
        )

    # -------------------------------------------------------------------------
    # Step 2: Load smoothed landmark data
    # -------------------------------------------------------------------------
    print(f"Loading smoothed landmarks from: {input_json_path.name} ...")
    with open(input_json_path, "r", encoding="utf-8") as f:
        smoothed_payload = json.load(f)

    raw_frames = smoothed_payload.get("frames", [])
    total_frames = len(raw_frames)

    # -------------------------------------------------------------------------
    # Step 3: Compute joint angles across all frames
    # -------------------------------------------------------------------------
    calculator = JointAngleCalculator(joint_definitions=RUNNING_JOINT_DEFINITIONS)
    angle_frames = calculator.process_sequence(raw_frames)

    # -------------------------------------------------------------------------
    # Step 4: Calculate min, max, and average statistics for each joint
    # -------------------------------------------------------------------------
    joint_stats = {}
    for joint_name in RUNNING_JOINT_DEFINITIONS.keys():
        valid_angles = [
            f["angles"][joint_name]
            for f in angle_frames
            if f.get("angles", {}).get(joint_name) is not None
        ]
        if valid_angles:
            joint_stats[joint_name] = {
                "min": round(min(valid_angles), 2),
                "max": round(max(valid_angles), 2),
                "avg": round(sum(valid_angles) / len(valid_angles), 2),
                "valid_frame_count": len(valid_angles),
            }
        else:
            joint_stats[joint_name] = {
                "min": None,
                "max": None,
                "avg": None,
                "valid_frame_count": 0,
            }

    # Count frames with valid angle data
    frames_processed_with_pose = sum(
        1 for f in angle_frames if any(v is not None for v in f["angles"].values())
    )

    # -------------------------------------------------------------------------
    # Step 5: Save joint angles to JSON
    # -------------------------------------------------------------------------
    output_payload = {
        "source_video": smoothed_payload.get("source_video", "unknown"),
        "total_frames": total_frames,
        "fps": smoothed_payload.get("fps", 30.0),
        "joint_definitions": {
            k: list(v) for k, v in RUNNING_JOINT_DEFINITIONS.items()
        },
        "joint_statistics": joint_stats,
        "frames": angle_frames,
    }

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    # -------------------------------------------------------------------------
    # Step 6: Print execution summary and joint angle ranges
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("         JOINT ANGLE CALCULATION TEST SUMMARY")
    print("=" * 60)
    print(f"Input JSON Path           : {input_json_path}")
    print(f"Output JSON Path          : {output_json_path}")
    print(f"Total Video Frames        : {total_frames}")
    print(f"Frames with Angle Data    : {frames_processed_with_pose}")
    print("-" * 60)
    print("Calculated Joints & Min / Max Angle Ranges:")
    print("-" * 60)
    for joint, stats in joint_stats.items():
        if stats["min"] is not None:
            print(
                f"  - {joint:<14}: Min = {stats['min']:>6.1f}° | "
                f"Max = {stats['max']:>6.1f}° | Avg = {stats['avg']:>6.1f}°"
            )
        else:
            print(f"  - {joint:<14}: No valid detections")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_joint_angles_test()
