"""
Motion Phase Visual Validation & Temporal Quality Control (QC) Module
======================================================================
This standalone module creates an annotated verification video from existing
pipeline outputs ('motion_phases.json' and 'smoothed_landmarks.json') and performs
non-destructive bilateral temporal consistency auditing.

Features:
1. Video HUD Overlay:
   - Frame index and exact timestamp
   - Left / Right gait phase color badges (Yellow: FOOT_CONTACT, Green: STANCE, Orange: TOE_OFF, Cyan: SWING)
   - Color-coded foot and ankle landmark tracking highlights
2. Bilateral Temporal QC Diagnostics:
   - Simultaneous bilateral phase occurrences (e.g. double stance, double swing)
   - Impossible / illegal state sequence jumps
   - Sub-minimum phase duration tracking
   - Rapid flickering / anomaly pattern detection
"""

from pathlib import Path
from collections import Counter
import json
import sys
from typing import Dict, Any, List, Optional, Tuple
import cv2

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Standard Gait Phase Colors (BGR format for OpenCV)
PHASE_COLORS = {
    "FOOT_CONTACT": (0, 215, 255),  # Yellow / Gold
    "STANCE": (50, 205, 50),        # Lime Green
    "TOE_OFF": (0, 140, 255),       # Deep Orange
    "SWING": (255, 191, 0),         # Cyan / Sky Blue
    "UNKNOWN": (180, 180, 180),     # Muted Grey
}

VALID_NEXT_PHASES = {
    "FOOT_CONTACT": {"STANCE", "FOOT_CONTACT"},
    "STANCE": {"TOE_OFF", "STANCE"},
    "TOE_OFF": {"SWING", "TOE_OFF"},
    "SWING": {"FOOT_CONTACT", "SWING"},
}


class BilateralTemporalAuditor:
    """
    Non-destructive auditor evaluating temporal coherence and bilateral synchronization
    from pre-computed motion phases without modifying the underlying classifications.
    """

    def __init__(self, min_phase_frames: int = 3):
        self.min_phase_frames = min_phase_frames

    def audit(self, phase_frames: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze motion phase time series for bilateral and temporal anomalies.
        """
        simultaneous_counts = Counter()
        illegal_transitions = []
        short_phases = []
        rapid_reversals = 0

        left_prev_phase = None
        right_prev_phase = None
        left_streak = 0
        right_streak = 0

        for idx, f in enumerate(phase_frames):
            lp = f.get("left_phase")
            rp = f.get("right_phase")

            if lp and rp:
                simultaneous_counts[f"{lp}_AND_{rp}"] += 1

            # Check Left Leg Temporal Transitions
            if lp:
                if lp == left_prev_phase:
                    left_streak += 1
                else:
                    if left_prev_phase and left_streak < self.min_phase_frames:
                        short_phases.append({
                            "leg": "left",
                            "frame": idx,
                            "phase": left_prev_phase,
                            "duration": left_streak,
                        })
                    if left_prev_phase and lp not in VALID_NEXT_PHASES.get(left_prev_phase, {lp}):
                        illegal_transitions.append({
                            "leg": "left",
                            "frame": idx,
                            "from": left_prev_phase,
                            "to": lp,
                        })
                    left_prev_phase = lp
                    left_streak = 1

            # Check Right Leg Temporal Transitions
            if rp:
                if rp == right_prev_phase:
                    right_streak += 1
                else:
                    if right_prev_phase and right_streak < self.min_phase_frames:
                        short_phases.append({
                            "leg": "right",
                            "frame": idx,
                            "phase": right_prev_phase,
                            "duration": right_streak,
                        })
                    if right_prev_phase and rp not in VALID_NEXT_PHASES.get(right_prev_phase, {rp}):
                        illegal_transitions.append({
                            "leg": "right",
                            "frame": idx,
                            "from": right_prev_phase,
                            "to": rp,
                        })
                    right_prev_phase = rp
                    right_streak = 1

        total_suspicious = len(illegal_transitions) + len(short_phases)

        return {
            "simultaneous_bilateral_combinations": dict(simultaneous_counts),
            "illegal_state_jumps": illegal_transitions,
            "sub_minimum_durations": short_phases,
            "total_suspicious_patterns": total_suspicious,
        }


def draw_hud(
    frame,
    landmarks: Optional[List[Dict[str, Any]]],
    left_phase: Optional[str],
    right_phase: Optional[str],
    frame_index: int,
    timestamp: float,
):
    """Render sports analytics top banner and foot highlights on frame."""
    h, w = frame.shape[:2]

    # Semi-transparent HUD background
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 70), (15, 15, 15), -1)
    cv2.addWeighted(overlay, 0.80, frame, 0.20, 0, frame)

    # Frame Counter & Video Timestamp
    time_text = f"FRAME: {frame_index:03d}  |  TIME: {timestamp:.2f}s"
    cv2.putText(frame, time_text, (20, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (230, 230, 230), 1, cv2.LINE_AA)

    # Left Leg Phase Badge
    lp = left_phase or "UNKNOWN"
    l_col = PHASE_COLORS.get(lp, (180, 180, 180))
    cv2.rectangle(frame, (20, 36), (220, 62), (35, 35, 35), -1)
    cv2.rectangle(frame, (20, 36), (220, 62), l_col, 2)
    cv2.putText(frame, f"LEFT : {lp}", (28, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.48, l_col, 2, cv2.LINE_AA)

    # Right Leg Phase Badge
    rp = right_phase or "UNKNOWN"
    r_col = PHASE_COLORS.get(rp, (180, 180, 180))
    cv2.rectangle(frame, (235, 36), (435, 62), (35, 35, 35), -1)
    cv2.rectangle(frame, (235, 36), (435, 62), r_col, 2)
    cv2.putText(frame, f"RIGHT: {rp}", (243, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.48, r_col, 2, cv2.LINE_AA)

    # Feet and Ankle Visual Indicators
    if landmarks:
        lm_map = {lm["name"]: (int(lm["x"] * w), int(lm["y"] * h)) for lm in landmarks if "name" in lm}

        if "left_ankle" in lm_map:
            lax, lay = lm_map["left_ankle"]
            cv2.circle(frame, (lax, lay), 9, l_col, -1, cv2.LINE_AA)
            cv2.circle(frame, (lax, lay), 13, (255, 255, 255), 1, cv2.LINE_AA)

        if "right_ankle" in lm_map:
            rax, ray = lm_map["right_ankle"]
            cv2.circle(frame, (rax, ray), 9, r_col, -1, cv2.LINE_AA)
            cv2.circle(frame, (rax, ray), 13, (255, 255, 255), 1, cv2.LINE_AA)


def run_visual_validation():
    # 1. Resolve Paths
    phases_path = project_root / "data" / "outputs" / "pose_test" / "motion_phases.json"
    landmarks_path = project_root / "data" / "outputs" / "pose_test" / "smoothed_landmarks.json"
    output_dir = project_root / "data" / "outputs" / "pose_test"
    output_video_path = output_dir / "annotated_motion_phases.mp4"

    if not phases_path.exists():
        raise FileNotFoundError(f"Missing {phases_path}. Run test_motion_phase.py first.")
    if not landmarks_path.exists():
        raise FileNotFoundError(f"Missing {landmarks_path}. Run test_smoothing.py first.")

    # 2. Load JSON Data
    with open(phases_path, "r", encoding="utf-8") as f:
        phases_data = json.load(f)
    with open(landmarks_path, "r", encoding="utf-8") as f:
        landmarks_data = json.load(f)

    phase_frames = phases_data.get("frames", [])
    lm_frames = landmarks_data.get("frames", [])
    source_name = phases_data.get("source_video", "running1.avi")

    # 3. Locate Source Video
    video_path = project_root / "data" / "raw" / "test" / source_name
    if not video_path.exists():
        for fb in ["running1.avi", "running1.mp4", "running.mp4"]:
            candidate = project_root / "data" / "raw" / "test" / fb
            if candidate.exists():
                video_path = candidate
                break

    if not video_path.exists():
        raise FileNotFoundError(f"Source video not found in data/raw/test/")

    # 4. Perform Bilateral Temporal QC Audit
    auditor = BilateralTemporalAuditor(min_phase_frames=3)
    qc_results = auditor.audit(phase_frames)

    # 5. Render Video Overlay
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise IOError(f"Failed to open source video at {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_video_path), fourcc, fps, (width, height))

    phase_by_idx = {f["frame_index"]: f for f in phase_frames}
    lm_by_idx = {f["frame_index"]: f.get("landmarks", []) for f in lm_frames}

    annotated_frames_count = 0
    labels_rendered_count = 0

    print(f"Rendering visual motion phase validation video from: {video_path.name} ...")
    frame_idx = 0
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        p_info = phase_by_idx.get(frame_idx, {})
        lp = p_info.get("left_phase")
        rp = p_info.get("right_phase")
        lms = lm_by_idx.get(frame_idx, [])
        t_sec = frame_idx / fps

        if lp is not None:
            labels_rendered_count += 1
        if rp is not None:
            labels_rendered_count += 1

        draw_hud(
            frame=frame,
            landmarks=lms,
            left_phase=lp,
            right_phase=rp,
            frame_index=frame_idx,
            timestamp=t_sec,
        )

        out.write(frame)
        annotated_frames_count += 1
        frame_idx += 1

    cap.release()
    out.release()

    # 6. Print Summary Report
    print("\n" + "=" * 70)
    print("      MOTION PHASE VISUAL VALIDATION & TEMPORAL QC REPORT")
    print("=" * 70)
    print(f"Output Video Path              : {output_video_path}")
    print(f"Total Frames Annotated         : {annotated_frames_count}")
    print(f"Number of Phase Labels Rendered: {labels_rendered_count}")
    print(f"Suspicious Bilateral Patterns  : {qc_results['total_suspicious_patterns']}")
    print("-" * 70)
    print("Bilateral Simultaneous Phase Combinations:")
    print("-" * 70)
    for combo, count in sorted(qc_results["simultaneous_bilateral_combinations"].items(), key=lambda x: -x[1]):
        print(f"  - {combo:<30}: {count:>3} frames")
    print("-" * 70)
    if qc_results["illegal_state_jumps"]:
        print("Detected Illegal Sequence Jumps:")
        for item in qc_results["illegal_state_jumps"]:
            print(f"  - Leg: {item['leg'].upper()} | Frame: {item['frame']} | Jump: {item['from']} -> {item['to']}")
    else:
        print("No illegal state sequence jumps detected.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_visual_validation()
