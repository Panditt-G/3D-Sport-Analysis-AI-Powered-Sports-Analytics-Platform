"""
Motion Phase Diagnostic & Signal Profiling Tool
===============================================
This script inspects and profiles the raw kinematic signals extracted from
'smoothed_landmarks.json' and 'joint_angles.json' to diagnose why phase transitions
fail or get stuck in a single phase.

Outputs:
- Saves full per-frame diagnostic time-series to 'data/outputs/pose_test/motion_phase_diagnostics.json'.
- Prints statistical summary (min, max, mean, std) for each signal.
- Prints a 20-frame tabular breakdown of actual kinematic features.
- Audits the configured thresholds in motion_phase.py against actual data distributions.
"""

from pathlib import Path
import json
import math
import sys
from typing import List, Dict, Any, Optional

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ai_engine.pose_analysis.motion_phase import PhaseDetectorConfig


def calculate_stats(values: List[float]) -> Dict[str, float]:
    """Calculate min, max, mean, and standard deviation for a list of floats."""
    if not values:
        return {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0}
    n = len(values)
    mean_val = sum(values) / n
    variance = sum((x - mean_val) ** 2 for x in values) / n
    return {
        "min": round(min(values), 5),
        "max": round(max(values), 5),
        "mean": round(mean_val, 5),
        "std": round(math.sqrt(variance), 5),
    }


def run_diagnostics():
    landmarks_path = project_root / "data" / "outputs" / "pose_test" / "smoothed_landmarks.json"
    angles_path = project_root / "data" / "outputs" / "pose_test" / "joint_angles.json"
    output_path = project_root / "data" / "outputs" / "pose_test" / "motion_phase_diagnostics.json"

    if not landmarks_path.exists():
        raise FileNotFoundError(f"Missing {landmarks_path}")
    if not angles_path.exists():
        raise FileNotFoundError(f"Missing {angles_path}")

    with open(landmarks_path, "r", encoding="utf-8") as f:
        lm_payload = json.load(f)
    with open(angles_path, "r", encoding="utf-8") as f:
        ang_payload = json.load(f)

    lm_frames = lm_payload.get("frames", [])
    ang_map = {f["frame_index"]: f.get("angles", {}) for f in ang_payload.get("frames", [])}

    diagnostics_records = []
    prev_valid_record = None

    for f in lm_frames:
        f_idx = f["frame_index"]
        t_stamp = f["timestamp"]
        pose_det = f.get("pose_detected", False)
        lms = f.get("landmarks", [])

        if not pose_det or not lms:
            continue

        lm_dict = {lm["name"]: (lm["x"], lm["y"], lm.get("z", 0.0)) for lm in lms if "name" in lm}
        angles = ang_map.get(f_idx, {})

        la = lm_dict.get("left_ankle", (None, None))
        ra = lm_dict.get("right_ankle", (None, None))
        lf = lm_dict.get("left_foot_index", la)
        rf = lm_dict.get("right_foot_index", ra)
        lh = lm_dict.get("left_hip", (None, None))
        rh = lm_dict.get("right_hip", (None, None))

        lk_angle = angles.get("left_knee")
        rk_angle = angles.get("right_knee")

        left_leg_span = (la[1] - lh[1]) if (la[1] is not None and lh[1] is not None) else None
        right_leg_span = (ra[1] - rh[1]) if (ra[1] is not None and rh[1] is not None) else None

        # Velocities and displacements
        la_vy, ra_vy = 0.0, 0.0
        lf_vy, rf_vy = 0.0, 0.0
        lf_vx, rf_vx = 0.0, 0.0
        la_disp, ra_disp = 0.0, 0.0

        if prev_valid_record is not None:
            if la[1] is not None and prev_valid_record["left_ankle_y"] is not None:
                la_vy = la[1] - prev_valid_record["left_ankle_y"]
                la_vx = la[0] - prev_valid_record["left_ankle_x"]
                la_disp = math.hypot(la_vx, la_vy)

            if ra[1] is not None and prev_valid_record["right_ankle_y"] is not None:
                ra_vy = ra[1] - prev_valid_record["right_ankle_y"]
                ra_vx = ra[0] - prev_valid_record["right_ankle_x"]
                ra_disp = math.hypot(ra_vx, ra_vy)

            if lf[1] is not None and prev_valid_record["left_foot_index_y"] is not None:
                lf_vy = lf[1] - prev_valid_record["left_foot_index_y"]
                lf_vx = lf[0] - prev_valid_record["left_foot_index_x"]

            if rf[1] is not None and prev_valid_record["right_foot_index_y"] is not None:
                rf_vy = rf[1] - prev_valid_record["right_foot_index_y"]
                rf_vx = rf[0] - prev_valid_record["right_foot_index_x"]

        rec = {
            "frame_index": f_idx,
            "timestamp": t_stamp,
            "left_ankle_x": round(la[0], 4) if la[0] is not None else None,
            "left_ankle_y": round(la[1], 4) if la[1] is not None else None,
            "right_ankle_x": round(ra[0], 4) if ra[0] is not None else None,
            "right_ankle_y": round(ra[1], 4) if ra[1] is not None else None,
            "left_foot_index_x": round(lf[0], 4) if lf[0] is not None else None,
            "left_foot_index_y": round(lf[1], 4) if lf[1] is not None else None,
            "right_foot_index_x": round(rf[0], 4) if rf[0] is not None else None,
            "right_foot_index_y": round(rf[1], 4) if rf[1] is not None else None,
            "left_knee_angle": lk_angle,
            "right_knee_angle": rk_angle,
            "left_leg_span": round(left_leg_span, 4) if left_leg_span is not None else None,
            "right_leg_span": round(right_leg_span, 4) if right_leg_span is not None else None,
            "left_ankle_vertical_velocity": round(la_vy, 5),
            "right_ankle_vertical_velocity": round(ra_vy, 5),
            "left_foot_vertical_velocity": round(lf_vy, 5),
            "right_foot_vertical_velocity": round(rf_vy, 5),
            "left_foot_horizontal_velocity": round(lf_vx, 5),
            "right_foot_horizontal_velocity": round(rf_vx, 5),
            "left_ankle_displacement": round(la_disp, 5),
            "right_ankle_displacement": round(ra_disp, 5),
        }
        diagnostics_records.append(rec)
        prev_valid_record = rec

    # Save to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "source": lm_payload.get("source_video", "running1"),
            "total_frames_analyzed": len(diagnostics_records),
            "records": diagnostics_records,
        }, f, indent=2)

    # Calculate Signal Statistics
    signals = [
        "left_ankle_y", "right_ankle_y",
        "left_knee_angle", "right_knee_angle",
        "left_leg_span", "right_leg_span",
        "left_ankle_vertical_velocity", "right_ankle_vertical_velocity",
        "left_foot_vertical_velocity", "right_foot_vertical_velocity",
        "left_foot_horizontal_velocity", "right_foot_horizontal_velocity",
        "left_ankle_displacement", "right_ankle_displacement",
    ]

    print("=" * 80)
    print("           MOTION PHASE KINEMATIC SIGNAL STATISTICAL PROFILE")
    print("=" * 80)
    print(f"{'Signal Name':<34} | {'Min':>10} | {'Max':>10} | {'Mean':>10} | {'Std Dev':>10}")
    print("-" * 80)

    for sig in signals:
        vals = [r[sig] for r in diagnostics_records if r.get(sig) is not None]
        st = calculate_stats(vals)
        print(f"{sig:<34} | {st['min']:>10.5f} | {st['max']:>10.5f} | {st['mean']:>10.5f} | {st['std']:>10.5f}")

    print("=" * 80)
    print("\n" + "=" * 90)
    print("                 FIRST 20 VALID FRAMES KINEMATIC SNAPSHOT")
    print("=" * 90)
    print(f"{'Frm':<4} | {'L_Span':>7} | {'R_Span':>7} | {'L_Ank_Vy':>9} | {'R_Ank_Vy':>9} | {'L_Disp':>8} | {'R_Disp':>8} | {'L_Knee':>7} | {'R_Knee':>7}")
    print("-" * 90)
    for r in diagnostics_records[:20]:
        l_span = f"{r['left_leg_span']:>7.3f}" if r['left_leg_span'] is not None else "   None"
        r_span = f"{r['right_leg_span']:>7.3f}" if r['right_leg_span'] is not None else "   None"
        lk = f"{r['left_knee_angle']:>7.1f}" if r['left_knee_angle'] is not None else "   None"
        rk = f"{r['right_knee_angle']:>7.1f}" if r['right_knee_angle'] is not None else "   None"
        print(
            f"{r['frame_index']:<4} | {l_span} | {r_span} | "
            f"{r['left_ankle_vertical_velocity']:>9.4f} | {r['right_ankle_vertical_velocity']:>9.4f} | "
            f"{r['left_ankle_displacement']:>8.4f} | {r['right_ankle_displacement']:>8.4f} | {lk} | {rk}"
        )
    print("=" * 90 + "\n")

    # Threshold Audit against current motion_phase.py config
    cfg = PhaseDetectorConfig()
    print("=" * 80)
    print("      CONFIGURED THRESHOLDS IN motion_phase.py VS OBSERVED REALITY")
    print("=" * 80)
    print(f"Configured leg_extension_ratio       : {cfg.leg_extension_ratio}")
    l_spans = [r['left_leg_span'] for r in diagnostics_records if r.get('left_leg_span') is not None]
    r_spans = [r['right_leg_span'] for r in diagnostics_records if r.get('right_leg_span') is not None]
    print(f"  -> Observed Left Leg Span Range    : [{min(l_spans):.4f}, {max(l_spans):.4f}]")
    print(f"  -> Observed Right Leg Span Range   : [{min(r_spans):.4f}, {max(r_spans):.4f}]")
    print(f"  -> Frames satisfying leg_span >= {cfg.leg_extension_ratio}: Left = {sum(1 for s in l_spans if s >= cfg.leg_extension_ratio)}, Right = {sum(1 for s in r_spans if s >= cfg.leg_extension_ratio)}")
    print("-" * 80)
    print(f"Configured contact_descent_vel       : {cfg.contact_descent_vel}")
    l_vys = [r['left_ankle_vertical_velocity'] for r in diagnostics_records]
    r_vys = [r['right_ankle_vertical_velocity'] for r in diagnostics_records]
    print(f"  -> Observed Left Ankle Vy Range    : [{min(l_vys):.4f}, {max(l_vys):.4f}]")
    print(f"  -> Observed Right Ankle Vy Range   : [{min(r_vys):.4f}, {max(r_vys):.4f}]")
    print(f"  -> Frames with Vy >= {cfg.contact_descent_vel} AND Span >= {cfg.leg_extension_ratio}: Left = {sum(1 for r in diagnostics_records if r['left_ankle_vertical_velocity'] >= cfg.contact_descent_vel and (r['left_leg_span'] or 0) >= cfg.leg_extension_ratio)}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_diagnostics()
