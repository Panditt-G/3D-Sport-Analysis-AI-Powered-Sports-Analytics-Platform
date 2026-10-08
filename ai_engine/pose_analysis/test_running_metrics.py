"""
Running Performance & Biomechanics Metrics Test Module
======================================================
This script:
1. Loads precomputed motion phases, joint angles, and smoothed landmark time series.
2. Computes comprehensive athletic running performance metrics (stance/swing times,
   step intervals, cadence, bilateral symmetry, joint angle ranges, and cycle stats).
3. Exports structured results to 'data/outputs/pose_test/running_metrics.json'.
4. Prints a concise, formatted human-readable summary of all performance metrics.
"""

from pathlib import Path
import json
import sys

# Ensure project root is in sys.path for direct script execution
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ai_engine.pose_analysis.running_metrics import RunningMetricsCalculator


def run_running_metrics_test():
    # -------------------------------------------------------------------------
    # Step 1: Set up input and output paths
    # -------------------------------------------------------------------------
    landmarks_json_path = project_root / "data" / "outputs" / "pose_test" / "smoothed_landmarks.json"
    angles_json_path = project_root / "data" / "outputs" / "pose_test" / "joint_angles.json"
    phases_json_path = project_root / "data" / "outputs" / "pose_test" / "motion_phases.json"
    output_dir = project_root / "data" / "outputs" / "pose_test"
    output_json_path = output_dir / "running_metrics.json"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Validate prerequisite files
    if not landmarks_json_path.exists():
        raise FileNotFoundError(
            f"Smoothed landmarks JSON not found at: {landmarks_json_path}. "
            f"Please run 'test_smoothing.py' first."
        )
    if not angles_json_path.exists():
        raise FileNotFoundError(
            f"Joint angles JSON not found at: {angles_json_path}. "
            f"Please run 'test_joint_angles.py' first."
        )
    if not phases_json_path.exists():
        raise FileNotFoundError(
            f"Motion phases JSON not found at: {phases_json_path}. "
            f"Please run 'test_motion_phase.py' first."
        )

    # -------------------------------------------------------------------------
    # Step 2: Load input time-series data
    # -------------------------------------------------------------------------
    print(f"Loading smoothed landmarks from : {landmarks_json_path.name}")
    with open(landmarks_json_path, "r", encoding="utf-8") as f:
        landmarks_payload = json.load(f)

    print(f"Loading joint angles from       : {angles_json_path.name}")
    with open(angles_json_path, "r", encoding="utf-8") as f:
        angles_payload = json.load(f)

    print(f"Loading motion phases from      : {phases_json_path.name}")
    with open(phases_json_path, "r", encoding="utf-8") as f:
        phases_payload = json.load(f)

    # -------------------------------------------------------------------------
    # Step 3: Compute Running Biomechanics & Performance Metrics
    # -------------------------------------------------------------------------
    calculator = RunningMetricsCalculator()
    metrics = calculator.compute_all_metrics(
        landmarks_payload=landmarks_payload,
        angles_payload=angles_payload,
        phases_payload=phases_payload,
    )

    # -------------------------------------------------------------------------
    # Step 4: Export standardized metrics JSON
    # -------------------------------------------------------------------------
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # -------------------------------------------------------------------------
    # Step 5: Print concise human-readable summary
    # -------------------------------------------------------------------------
    video_meta = metrics["video"]
    stance = metrics["stance_time"]
    swing = metrics["swing_time"]
    contacts = metrics["foot_contact_events"]
    toe_offs = metrics["toe_off_events"]
    timing = metrics["step_timing"]
    cadence = metrics["cadence"]
    symmetry = metrics["symmetry"]
    joint_angles = metrics["joint_angles"]
    cycle = metrics["running_cycle"]
    quality = metrics["data_quality"]

    print("\n" + "=" * 65)
    print("           ATHLETIC RUNNING PERFORMANCE METRICS SUMMARY")
    print("=" * 65)
    print(f"Input Files           : {landmarks_json_path.name}, {angles_json_path.name}, {phases_json_path.name}")
    print(f"Total Video Frames    : {video_meta['total_frames']}")
    print(f"Video FPS             : {video_meta['fps']}")
    print(f"Video Duration        : {video_meta['duration_seconds']}s")
    print("-" * 65)

    print("STANCE TIME (GROUND SUPPORT):")
    l_st = stance["left"]
    r_st = stance["right"]
    print(f"  - Left Leg  : {l_st['count']} events | Avg: {l_st['avg_frames']} frames ({l_st['avg_seconds']}s) | Range: [{l_st['min_frames']}, {l_st['max_frames']}] frames")
    print(f"  - Right Leg : {r_st['count']} events | Avg: {r_st['avg_frames']} frames ({r_st['avg_seconds']}s) | Range: [{r_st['min_frames']}, {r_st['max_frames']}] frames")

    print("\nSWING TIME (FLIGHT / RECOVERY):")
    l_sw = swing["left"]
    r_sw = swing["right"]
    print(f"  - Left Leg  : {l_sw['count']} events | Avg: {l_sw['avg_frames']} frames ({l_sw['avg_seconds']}s) | Range: [{l_sw['min_frames']}, {l_sw['max_frames']}] frames")
    print(f"  - Right Leg : {r_sw['count']} events | Avg: {r_sw['avg_frames']} frames ({r_sw['avg_seconds']}s) | Range: [{r_sw['min_frames']}, {r_sw['max_frames']}] frames")

    print("\nFOOT CONTACT & TOE-OFF TRANSITIONS:")
    print(f"  - Foot Contacts : Left = {contacts['left']}, Right = {contacts['right']}, Total = {contacts['total']}")
    print(f"  - Toe-Offs      : Left = {toe_offs['left']}, Right = {toe_offs['right']}, Total = {toe_offs['total']}")

    print("\nSTEP TIMING & CADENCE:")
    print(f"  - Valid Step Intervals  : {timing['valid_intervals']}")
    print(f"  - Average Step Interval : {timing['average_interval_seconds']}s" if timing['average_interval_seconds'] else "  - Average Step Interval : N/A (Insufficient alternating contacts)")
    print(f"  - Left-to-Right Step    : {timing['left_to_right_seconds']}s" if timing['left_to_right_seconds'] else "  - Left-to-Right Step    : N/A")
    print(f"  - Right-to-Left Step    : {timing['right_to_left_seconds']}s" if timing['right_to_left_seconds'] else "  - Right-to-Left Step    : N/A")
    print(f"  - Estimated Cadence     : {cadence['steps_per_minute']} steps/min" if cadence['steps_per_minute'] else "  - Estimated Cadence     : N/A (Insufficient alternating contacts)")

    print("\nBILATERAL SYMMETRY (ABSOLUTE DIFFERENCE):")
    print(f"  - Stance Difference     : {symmetry['stance_difference_seconds']}s" if symmetry['stance_difference_seconds'] is not None else "  - Stance Difference     : N/A")
    print(f"  - Swing Difference      : {symmetry['swing_difference_seconds']}s" if symmetry['swing_difference_seconds'] is not None else "  - Swing Difference      : N/A")
    print(f"  - Step Timing Difference: {symmetry['step_timing_difference_seconds']}s" if symmetry['step_timing_difference_seconds'] is not None else "  - Step Timing Difference: N/A")

    print("\nJOINT ANGLE KINEMATICS (MIN / MAX / AVG):")
    for j_name, stats in joint_angles.items():
        if stats.get("min") is not None:
            print(f"  - {j_name:<12}: Min = {stats['min']:>6.1f}° | Max = {stats['max']:>6.1f}° | Avg = {stats['average']:>6.1f}°")
        else:
            print(f"  - {j_name:<12}: N/A")

    print("\nRUNNING GAIT CYCLE SUMMARY:")
    print(f"  - Valid Cycles Detected : {cycle['valid_cycles']}")
    print(f"  - Average Cycle Duration: {cycle['average_duration_seconds']}s" if cycle['average_duration_seconds'] else "  - Average Cycle Duration: N/A")

    print("\nDATA QUALITY & COVERAGE:")
    print(f"  - Valid Pose Frames     : {quality['valid_pose_frames']} / {quality['total_frames']} ({quality['pose_validity_percent']}%)")
    print(f"  - Phase Events Used     : {quality['phase_events_used']}")
    print(f"  - Output JSON Saved To  : {output_json_path}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_running_metrics_test()
