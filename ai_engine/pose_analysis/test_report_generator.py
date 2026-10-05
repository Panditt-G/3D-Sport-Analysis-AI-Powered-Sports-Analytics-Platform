"""
Running Analysis Report Generator Test Module
==============================================
This test script:
1. Verifies required pipeline input files exist.
2. Loads precomputed JSON outputs (running_metrics, motion_phases, joint_angles, smoothed_landmarks).
3. Reads video metadata if available.
4. Generates a structured analysis report using RunningReportGenerator.
5. Saves the report to data/outputs/pose_test/running_analysis_report.json.
6. Validates the JSON schema, integrity, null handling, and limitation warnings.
7. Prints a clean, human-readable terminal summary.
"""

import json
import os
import sys
from pathlib import Path
import cv2
import pytest

# Ensure project root is in sys.path for direct script execution
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ai_engine.pose_analysis.report_generator import RunningReportGenerator


def load_json_file(file_path: str):
    """Safely load and parse a JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Required input file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_video_metadata(video_path: str):
    """Extract metadata from video file using OpenCV if it exists."""
    if not os.path.exists(video_path):
        return None
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = round(float(cap.get(cv2.CAP_PROP_FPS)), 2)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_seconds = round(total_frames / fps, 2) if fps > 0 else None
    cap.release()

    return {
        "filename": os.path.basename(video_path),
        "width": width,
        "height": height,
        "fps": fps,
        "total_frames": total_frames,
        "duration_seconds": duration_seconds,
    }


def run_report_test():
    """Main execution function for Step 10 report generation test."""
    print("\n" + "=" * 60)
    print("STEP 10: RUNNING ANALYSIS REPORT GENERATION TEST")
    print("=" * 60)

    # File paths
    base_output_dir = str(project_root / "data" / "outputs" / "pose_test")
    metrics_path = os.path.join(base_output_dir, "running_metrics.json")
    phases_path = os.path.join(base_output_dir, "motion_phases.json")
    angles_path = os.path.join(base_output_dir, "joint_angles.json")
    landmarks_path = os.path.join(base_output_dir, "smoothed_landmarks.json")
    report_output_path = os.path.join(base_output_dir, "running_analysis_report.json")

    # Candidate video paths
    video_candidates = [
        str(project_root / "data" / "raw" / "test" / "running1.avi"),
        str(project_root / "data" / "raw" / "test" / "running1.mp4"),
    ]
    video_path = None
    for cand in video_candidates:
        if os.path.exists(cand):
            video_path = cand
            break

    print(f"\n[1/4] Checking required input files...")
    for p in [metrics_path, phases_path, angles_path, landmarks_path]:
        if os.path.exists(p):
            print(f"  ✓ Found: {p} ({os.path.getsize(p):,} bytes)")
        else:
            raise FileNotFoundError(f"Missing required input file: {p}")

    # Load precomputed data
    print(f"\n[2/4] Loading precomputed pipeline outputs...")
    metrics_data = load_json_file(metrics_path)
    phases_data = load_json_file(phases_path)
    angles_data = load_json_file(angles_path)
    landmarks_data = load_json_file(landmarks_path)
    print(f"  ✓ Successfully loaded all 4 JSON files.")

    # Video metadata
    video_metadata = None
    if video_path:
        video_metadata = get_video_metadata(video_path)
        if video_metadata:
            print(f"  ✓ Extracted video metadata from {video_path}: {video_metadata['width']}x{video_metadata['height']} @ {video_metadata['fps']} FPS ({video_metadata['total_frames']} frames)")

    output_paths = {
        "annotated_video": "data/outputs/pose_test/annotated_running_analysis.mp4",
        "metrics": "data/outputs/pose_test/running_metrics.json",
        "report": "data/outputs/pose_test/running_analysis_report.json",
    }

    # Generate Report
    print(f"\n[3/4] Compiling structured running analysis report...")
    generator = RunningReportGenerator()
    report = generator.generate_report(
        running_metrics=metrics_data,
        motion_phases=phases_data,
        joint_angles=angles_data,
        smoothed_landmarks=landmarks_data,
        video_metadata=video_metadata,
        output_paths=output_paths,
    )

    # Save to disk
    generator.save_report(report, report_output_path)
    print(f"  ✓ Saved report JSON to: {report_output_path} ({os.path.getsize(report_output_path):,} bytes)")

    # Validation
    print(f"\n[4/4] Validating report structure and constraints...")
    validate_report_structure(report)
    print("  ✓ Report validation passed successfully.")

    # Print Terminal Summary
    summary_text = generator.format_terminal_summary(report)
    print("\n" + summary_text + "\n")

    return report


def validate_report_structure(report: dict):
    """Thoroughly validate the report content against requirements."""
    # Required top-level keys
    required_keys = [
        "report", "video", "data_quality", "motion_phases", "stance_time",
        "swing_time", "foot_contact_events", "toe_off_events", "step_timing",
        "cadence", "symmetry", "joint_angles", "running_cycle", "outputs", "warnings"
    ]
    for key in required_keys:
        assert key in report, f"Missing required top-level key: {key}"

    # Report metadata
    rep_meta = report["report"]
    assert rep_meta["version"] == "1.0"
    assert rep_meta["analysis_type"] == "running_analysis"
    assert rep_meta["sport"] == "running"
    assert "generated_at" in rep_meta and rep_meta["generated_at"]

    # Video info
    vid = report["video"]
    assert "filename" in vid
    assert "total_frames" in vid
    assert "fps" in vid
    assert "duration_seconds" in vid

    # Data Quality
    dq = report["data_quality"]
    assert "total_frames" in dq
    assert "valid_pose_frames" in dq
    assert "pose_coverage_percent" in dq
    assert dq["pose_coverage_percent"] == 25.41
    assert dq["quality_warning"] is True

    # Motion Phases
    mp = report["motion_phases"]
    assert "left" in mp and "right" in mp
    for side in ["left", "right"]:
        for phase in ["FOOT_CONTACT", "STANCE", "TOE_OFF", "SWING"]:
            assert phase in mp[side], f"Missing phase {phase} in motion_phases[{side}]"

    # Step Timing & Cadence null-handling (no fabricated 0s)
    step_t = report["step_timing"]
    assert step_t["valid_intervals"] == 0
    assert step_t["average_interval_seconds"] is None

    cad = report["cadence"]
    assert cad["steps_per_minute"] is None

    # Running Cycles
    rc = report["running_cycle"]
    assert rc["valid_cycles"] == 0
    assert rc["average_duration_seconds"] is None
    assert rc.get("status") == "insufficient_data"

    # Warnings (must have coverage and cadence warnings)
    warnings = report["warnings"]
    assert len(warnings) >= 3
    assert any("Low pose coverage" in w for w in warnings)
    assert any("cadence estimation" in w for w in warnings)
    assert any("Camera calibration unavailable" in w for w in warnings)

    # No forbidden medical / diagnostic words in warnings or summaries
    forbidden_terms = ["injury", "disorder", "pathology", "abnormal", "unhealthy", "poor running form"]
    report_str = json.dumps(report).lower()
    for term in forbidden_terms:
        assert term not in report_str, f"Forbidden diagnostic term '{term}' found in report!"


def test_running_report_generation():
    """Pytest entrypoint."""
    report = run_report_test()
    assert report is not None


if __name__ == "__main__":
    run_report_test()
