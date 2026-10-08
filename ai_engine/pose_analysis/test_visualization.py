"""
Running Analysis Visualization Test Module
===========================================
This test script:
1. Verifies all required input files exist.
2. Loads precomputed JSON outputs from the pipeline (landmarks, angles, phases, metrics).
3. Runs the visualization overlay onto the original video.
4. Saves: data/outputs/pose_test/annotated_running_analysis.mp4
5. Prints a comprehensive summary of processing results.
"""

from pathlib import Path
import json
import sys

# Ensure project root is in sys.path for direct script execution
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ai_engine.pose_analysis.visualization import load_json, create_annotated_video


def run_visualization_test():
    # -------------------------------------------------------------------------
    # Step 1: Define input and output paths
    # -------------------------------------------------------------------------
    # Try .avi first (existing test file), then .mp4 fallback
    video_path = project_root / "data" / "raw" / "test" / "running1.avi"
    if not video_path.exists():
        video_path = project_root / "data" / "raw" / "test" / "running1.mp4"

    landmarks_json_path = project_root / "data" / "outputs" / "pose_test" / "smoothed_landmarks.json"
    angles_json_path = project_root / "data" / "outputs" / "pose_test" / "joint_angles.json"
    phases_json_path = project_root / "data" / "outputs" / "pose_test" / "motion_phases.json"
    metrics_json_path = project_root / "data" / "outputs" / "pose_test" / "running_metrics.json"

    output_dir = project_root / "data" / "outputs" / "pose_test"
    output_video_path = output_dir / "annotated_running_analysis.mp4"

    # -------------------------------------------------------------------------
    # Step 2: Print input file paths and verify existence
    # -------------------------------------------------------------------------
    print("=" * 65)
    print("       RUNNING ANALYSIS VISUALIZATION — INPUT VERIFICATION")
    print("=" * 65)

    inputs = {
        "Video": video_path,
        "Landmarks": landmarks_json_path,
        "Joint Angles": angles_json_path,
        "Motion Phases": phases_json_path,
        "Running Metrics": metrics_json_path,
    }

    all_found = True
    for label, path in inputs.items():
        exists = path.exists()
        status = "FOUND" if exists else "MISSING"
        print(f"  {label:<16}: {path.name:<35} [{status}]")
        if not exists and label == "Video":
            all_found = False

    if not all_found:
        raise FileNotFoundError(
            f"Required input video not found: {video_path}. "
            f"Cannot proceed with visualization."
        )

    # -------------------------------------------------------------------------
    # Step 3: Load JSON data (each load handles missing files safely)
    # -------------------------------------------------------------------------
    print("\nLoading analysis data ...")
    landmarks_payload = load_json(landmarks_json_path)
    angles_payload = load_json(angles_json_path)
    phases_payload = load_json(phases_json_path)
    metrics_payload = load_json(metrics_json_path)

    loaded_count = sum(1 for d in [landmarks_payload, angles_payload, phases_payload, metrics_payload] if d)
    print(f"  Loaded {loaded_count}/4 JSON data files successfully.")

    # -------------------------------------------------------------------------
    # Step 4: Run visualization
    # -------------------------------------------------------------------------
    print(f"\nGenerating annotated video from: {video_path.name} ...")
    output_dir.mkdir(parents=True, exist_ok=True)

    result = create_annotated_video(
        video_path=video_path,
        output_path=output_video_path,
        landmarks_payload=landmarks_payload,
        angles_payload=angles_payload,
        phases_payload=phases_payload,
        metrics_payload=metrics_payload,
    )

    # -------------------------------------------------------------------------
    # Step 5: Print summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 65)
    print("       VISUALIZATION TEST SUMMARY")
    print("=" * 65)
    print(f"Total Frames Processed    : {result['total_frames_processed']}")
    print(f"Valid Pose Frames         : {result['valid_pose_frames']}")
    print(f"Missing Pose Frames       : {result['missing_pose_frames']}")
    print(f"Output FPS                : {result['fps']}")
    print(f"Output Resolution         : {result['resolution']}")
    print(f"Output Video Path         : {result['output_path']}")
    print(f"Status                    : COMPLETED SUCCESSFULLY")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_visualization_test()
