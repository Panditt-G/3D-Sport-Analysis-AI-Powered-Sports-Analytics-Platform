"""
Temporal Motion Phase Detection & Video Annotation Test Module
==============================================================
This test script:
1. Executes the bilateral, scale-invariant temporal state-machine gait detector.
2. Exports phase classifications to 'data/outputs/pose_test/motion_phases.json'.
3. Generates a video overlay with real-time HUD and color-coded foot states:
   'data/outputs/pose_test/annotated_motion_phases.mp4'.
4. Prints quality control, transition diagnostics, and phase distributions.
"""

from pathlib import Path
from collections import Counter
import json
import sys
import cv2

# Ensure project root is in sys.path for direct script execution
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ai_engine.pose_analysis.motion_phase import (
    TemporalRunningPhaseDetector,
    PhaseDetectorConfig,
    RunningPhase,
    draw_gait_phase_hud,
)


def run_temporal_motion_phase_test():
    # -------------------------------------------------------------------------
    # Step 1: Set up input and output paths
    # -------------------------------------------------------------------------
    landmarks_json_path = project_root / "data" / "outputs" / "pose_test" / "smoothed_landmarks.json"
    angles_json_path = project_root / "data" / "outputs" / "pose_test" / "joint_angles.json"
    output_dir = project_root / "data" / "outputs" / "pose_test"
    output_json_path = output_dir / "motion_phases.json"
    output_video_path = output_dir / "annotated_motion_phases.mp4"

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

    # -------------------------------------------------------------------------
    # Step 2: Load input time-series data
    # -------------------------------------------------------------------------
    print(f"Loading smoothed landmarks from: {landmarks_json_path.name} ...")
    with open(landmarks_json_path, "r", encoding="utf-8") as f:
        landmarks_payload = json.load(f)

    print(f"Loading joint angles from: {angles_json_path.name} ...")
    with open(angles_json_path, "r", encoding="utf-8") as f:
        angles_payload = json.load(f)

    landmark_frames = landmarks_payload.get("frames", [])
    angle_frames = angles_payload.get("frames", [])
    total_frames = len(landmark_frames)
    source_video_name = landmarks_payload.get("source_video", "running1.avi")

    # -------------------------------------------------------------------------
    # Step 3: Run Scale-Invariant Temporal State Machine Detector
    # -------------------------------------------------------------------------
    config = PhaseDetectorConfig(
        min_phase_frames=3,
        transition_confirm_frames=2,
        extension_ratio_threshold=0.82,
        retraction_ratio_threshold=0.78,
        norm_foot_stationary_vel=0.08,
        norm_toe_off_lift_vel=-0.04,
        norm_contact_descent_vel=0.03,
        knee_flexion_threshold=135.0,
        knee_extension_threshold=150.0,
        history_window_size=5,
    )
    detector = TemporalRunningPhaseDetector(config=config)
    phase_frames = detector.process_sequence(landmark_frames, angle_frames)
    diagnostics = detector.get_diagnostics()

    # -------------------------------------------------------------------------
    # Step 4: Render Visual Phase HUD Video Overlay (if video exists)
    # -------------------------------------------------------------------------
    input_video_path = project_root / "data" / "raw" / "test" / source_video_name
    if not input_video_path.exists():
        # Fallback check for running1.avi or running.mp4
        for fallback in ["running1.avi", "running.mp4"]:
            fb_path = project_root / "data" / "raw" / "test" / fallback
            if fb_path.exists():
                input_video_path = fb_path
                break

    if input_video_path.exists():
        print(f"Generating visual phase HUD video from: {input_video_path.name} ...")
        cap = cv2.VideoCapture(str(input_video_path))
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(str(output_video_path), fourcc, fps, (w, h))

            lm_map_by_frame = {f["frame_index"]: f.get("landmarks", []) for f in landmark_frames}
            phase_map_by_frame = {f["frame_index"]: f for f in phase_frames}

            frm_idx = 0
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    break

                pf = phase_map_by_frame.get(frm_idx, {})
                lp = pf.get("left_phase")
                rp = pf.get("right_phase")
                lms = lm_map_by_frame.get(frm_idx, [])
                t_val = frm_idx / fps

                draw_gait_phase_hud(
                    frame=frame,
                    landmarks=lms,
                    left_phase=lp,
                    right_phase=rp,
                    frame_index=frm_idx,
                    timestamp=t_val,
                )

                out.write(frame)
                frm_idx += 1

            cap.release()
            out.release()
            print(f"Annotated video saved successfully to: {output_video_path.name}")

    # -------------------------------------------------------------------------
    # Step 5: Aggregate phase counts and valid frame metrics
    # -------------------------------------------------------------------------
    left_counts = Counter()
    right_counts = Counter()
    valid_frames = 0

    for f in phase_frames:
        lp = f.get("left_phase")
        rp = f.get("right_phase")
        if lp is not None or rp is not None:
            valid_frames += 1
        if lp:
            left_counts[lp] += 1
        if rp:
            right_counts[rp] += 1

    left_diag = diagnostics["left_leg"]
    right_diag = diagnostics["right_leg"]

    total_confirmed = left_diag["confirmed_transitions"] + right_diag["confirmed_transitions"]
    total_rejected = left_diag["rejected_transitions"] + right_diag["rejected_transitions"]
    total_suspicious = left_diag["suspicious_sequences"] + right_diag["suspicious_sequences"]
    max_swing = max(left_diag["longest_swing_frames"], right_diag["longest_swing_frames"])
    min_phase = min(
        filter(lambda x: x > 0, [left_diag["shortest_phase_frames"], right_diag["shortest_phase_frames"]]),
        default=0,
    )

    # -------------------------------------------------------------------------
    # Step 6: Save results to JSON
    # -------------------------------------------------------------------------
    output_payload = {
        "source_video": source_video_name,
        "total_frames": total_frames,
        "valid_frames": valid_frames,
        "detector_configuration": {
            "min_phase_frames": config.min_phase_frames,
            "transition_confirm_frames": config.transition_confirm_frames,
            "extension_ratio_threshold": config.extension_ratio_threshold,
            "retraction_ratio_threshold": config.retraction_ratio_threshold,
            "norm_foot_stationary_vel": config.norm_foot_stationary_vel,
            "norm_toe_off_lift_vel": config.norm_toe_off_lift_vel,
            "norm_contact_descent_vel": config.norm_contact_descent_vel,
            "knee_flexion_threshold": config.knee_flexion_threshold,
            "knee_extension_threshold": config.knee_extension_threshold,
        },
        "phase_distribution": {
            "left_leg": dict(left_counts),
            "right_leg": dict(right_counts),
        },
        "quality_control_diagnostics": diagnostics,
        "frames": phase_frames,
    }

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    # -------------------------------------------------------------------------
    # Step 7: Print detailed execution summary
    # -------------------------------------------------------------------------
    phases = [
        RunningPhase.FOOT_CONTACT.value,
        RunningPhase.STANCE.value,
        RunningPhase.TOE_OFF.value,
        RunningPhase.SWING.value,
    ]

    print("\n" + "=" * 65)
    print("      TEMPORAL MOTION PHASE DETECTION TEST SUMMARY")
    print("=" * 65)
    print(f"Total Video Frames           : {total_frames}")
    print(f"Frames with Valid Phase Info : {valid_frames}")
    print(f"Output JSON Path             : {output_json_path}")
    print(f"Output Video Path            : {output_video_path}")
    print("-" * 65)
    print("PHASE DISTRIBUTION:")
    print("-" * 65)
    print(f"{'Phase Name':<16} | {'Left Leg Frames':<16} | {'Right Leg Frames':<16}")
    print("-" * 65)
    for p in phases:
        print(f"{p:<16} | {left_counts.get(p, 0):>15} | {right_counts.get(p, 0):>16}")
    print("-" * 65)
    print("QUALITY CONTROL & BODY SCALE DIAGNOSTICS:")
    print("-" * 65)
    print(f"  - Calibrated Max Leg Span        : Left = {left_diag['calibrated_max_span']}, Right = {right_diag['calibrated_max_span']}")
    print(f"  - Confirmed Transitions          : {total_confirmed} (Left: {left_diag['confirmed_transitions']}, Right: {right_diag['confirmed_transitions']})")
    print(f"  - Rejected Noisy Transitions     : {total_rejected} (Left: {left_diag['rejected_transitions']}, Right: {right_diag['rejected_transitions']})")
    print(f"  - Suspicious / Unnatural Jumps   : {total_suspicious} (Left: {left_diag['suspicious_sequences']}, Right: {right_diag['suspicious_sequences']})")
    print(f"  - Longest Continuous SWING       : {max_swing} frames")
    print(f"  - Shortest Phase Duration        : {min_phase} frames (Enforced min: {config.min_phase_frames})")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_temporal_motion_phase_test()
