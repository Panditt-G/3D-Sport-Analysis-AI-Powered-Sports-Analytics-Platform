"""
Running Analysis Visualization Module
======================================
This module provides a reusable overlay/debugging layer that draws precomputed
AI analysis results (pose landmarks, joint angles, motion phases, running metrics)
onto original video frames. It does NOT run any AI inference itself — it strictly
consumes JSON outputs from the existing pipeline stages.

Overlay Components:
1. 33-point BlazePose skeleton with bilateral leg emphasis.
2. Motion phase labels (FOOT_CONTACT / STANCE / TOE_OFF / SWING / N/A).
3. Joint angle readouts (knee, hip, ankle).
4. Frame counter, timestamp, and FPS display.
5. Pose validity indicator (VALID / MISSING).
6. Data quality panel (total frames, valid frames, coverage %).
7. Running metrics summary panel (cadence, contacts, toe-offs).
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import cv2


# ============================================================================
# CENTRALIZED VISUALIZATION CONFIGURATION
# ============================================================================
# All colors, font sizes, and thickness values are defined here so they can be
# modified in a single place without scattering hardcoded constants.

class VisConfig:
    """Centralized visualization configuration."""

    # --- COLORS (BGR format for OpenCV) ---
    # Skeleton
    LEFT_BODY_COLOR = (255, 160, 50)     # Blue-cyan for left side
    RIGHT_BODY_COLOR = (50, 160, 255)    # Orange for right side
    TORSO_COLOR = (200, 200, 200)        # Light grey for torso/spine

    # Leg emphasis (thicker, brighter)
    LEFT_LEG_COLOR = (255, 200, 80)      # Bright cyan for left leg
    RIGHT_LEG_COLOR = (50, 120, 255)     # Bright orange for right leg
    LEFT_LEG_THICKNESS = 3
    RIGHT_LEG_THICKNESS = 3

    # Landmark keypoints
    LANDMARK_COLOR = (0, 255, 200)       # Mint green
    LANDMARK_RADIUS = 4
    LANDMARK_OUTLINE_COLOR = (255, 255, 255)
    LANDMARK_OUTLINE_RADIUS = 5

    # General skeleton
    SKELETON_THICKNESS = 2

    # Panel backgrounds
    PANEL_BG_COLOR = (30, 30, 30)        # Dark charcoal
    PANEL_BG_ALPHA = 0.70
    PANEL_BORDER_COLOR = (80, 80, 80)

    # Phase label colors
    PHASE_COLORS = {
        "FOOT_CONTACT": (0, 215, 255),   # Gold/Yellow
        "STANCE": (50, 205, 50),         # Lime green
        "TOE_OFF": (0, 140, 255),        # Deep orange
        "SWING": (255, 191, 0),          # Sky blue/cyan
    }
    PHASE_DEFAULT_COLOR = (180, 180, 180)  # Grey

    # Pose validity
    POSE_VALID_COLOR = (50, 205, 50)     # Green
    POSE_MISSING_COLOR = (0, 0, 255)     # Red

    # Text
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE_TITLE = 0.55
    FONT_SCALE_BODY = 0.45
    FONT_SCALE_SMALL = 0.40
    FONT_COLOR = (255, 255, 255)         # White
    FONT_DIM_COLOR = (180, 180, 180)     # Dim grey
    FONT_THICKNESS = 1
    LINE_HEIGHT = 20
    LINE_HEIGHT_SMALL = 17

    # Visibility threshold
    VISIBILITY_THRESHOLD = 0.3


# ============================================================================
# BLAZEPOSE SKELETON CONNECTION DEFINITIONS
# ============================================================================
# Using the standard landmark naming convention from landmarks.py (BLAZEPOSE_LANDMARK_NAMES).
# Connections defined by landmark name pairs for reliable mapping.

# Torso & upper body connections
UPPER_BODY_CONNECTIONS = [
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"),
    ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"),
    ("right_elbow", "right_wrist"),
    ("left_shoulder", "left_hip"),
    ("right_shoulder", "right_hip"),
    ("left_hip", "right_hip"),
]

# Left leg (emphasized)
LEFT_LEG_CONNECTIONS = [
    ("left_hip", "left_knee"),
    ("left_knee", "left_ankle"),
    ("left_ankle", "left_heel"),
    ("left_ankle", "left_foot_index"),
    ("left_heel", "left_foot_index"),
]

# Right leg (emphasized)
RIGHT_LEG_CONNECTIONS = [
    ("right_hip", "right_knee"),
    ("right_knee", "right_ankle"),
    ("right_ankle", "right_heel"),
    ("right_ankle", "right_foot_index"),
    ("right_heel", "right_foot_index"),
]

# Key body landmarks to draw keypoints for
KEY_LANDMARKS = [
    "left_shoulder", "right_shoulder",
    "left_elbow", "right_elbow",
    "left_wrist", "right_wrist",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
    "left_foot_index", "right_foot_index",
    "left_heel", "right_heel",
]


# ============================================================================
# JSON LOADING UTILITIES
# ============================================================================

def load_json(filepath: Path) -> Optional[Dict[str, Any]]:
    """
    Safely load a JSON file. Returns None if the file is missing or malformed.

    Args:
        filepath: Path to the JSON file.

    Returns:
        Parsed dictionary or None.
    """
    if not filepath.exists():
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def build_frame_index_map(frames_list: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """
    Build a dictionary mapping frame_index -> frame data for O(1) lookup.
    Uses the 'frame_index' field from each record.

    Args:
        frames_list: List of frame dictionaries containing 'frame_index' key.

    Returns:
        Dictionary of {frame_index: frame_data}.
    """
    return {f["frame_index"]: f for f in frames_list if "frame_index" in f}


# ============================================================================
# DRAWING FUNCTIONS
# ============================================================================

def _draw_semi_transparent_rect(
    frame, x1: int, y1: int, x2: int, y2: int,
    bg_color: Tuple[int, int, int] = VisConfig.PANEL_BG_COLOR,
    alpha: float = VisConfig.PANEL_BG_ALPHA,
) -> None:
    """Draw a semi-transparent filled rectangle onto the frame (in-place)."""
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), bg_color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, frame)


def draw_skeleton(
    frame, landmarks: List[Dict[str, Any]], width: int, height: int,
) -> None:
    """
    Draw the 33-point BlazePose skeleton with bilateral leg emphasis.

    Args:
        frame: BGR image to draw on (modified in-place).
        landmarks: List of landmark dictionaries with 'name', 'x', 'y', 'visibility'.
        width: Frame width in pixels.
        height: Frame height in pixels.
    """
    if not landmarks:
        return

    # Build name -> (px, py, visibility) lookup
    lm_map: Dict[str, Tuple[int, int, float]] = {}
    for lm in landmarks:
        name = lm.get("name")
        if name is None:
            continue
        x = lm.get("x", 0.0)
        y = lm.get("y", 0.0)
        vis = lm.get("visibility", 1.0)
        px = int(x * width)
        py = int(y * height)
        lm_map[name] = (px, py, vis if vis is not None else 1.0)

    def _draw_connection(name_a, name_b, color, thickness):
        if name_a in lm_map and name_b in lm_map:
            pa = lm_map[name_a]
            pb = lm_map[name_b]
            if pa[2] > VisConfig.VISIBILITY_THRESHOLD and pb[2] > VisConfig.VISIBILITY_THRESHOLD:
                cv2.line(frame, (pa[0], pa[1]), (pb[0], pb[1]), color, thickness, cv2.LINE_AA)

    # Draw torso / upper body
    for a, b in UPPER_BODY_CONNECTIONS:
        side_color = VisConfig.TORSO_COLOR
        if "left" in a and "left" in b:
            side_color = VisConfig.LEFT_BODY_COLOR
        elif "right" in a and "right" in b:
            side_color = VisConfig.RIGHT_BODY_COLOR
        _draw_connection(a, b, side_color, VisConfig.SKELETON_THICKNESS)

    # Draw left leg (emphasized)
    for a, b in LEFT_LEG_CONNECTIONS:
        _draw_connection(a, b, VisConfig.LEFT_LEG_COLOR, VisConfig.LEFT_LEG_THICKNESS)

    # Draw right leg (emphasized)
    for a, b in RIGHT_LEG_CONNECTIONS:
        _draw_connection(a, b, VisConfig.RIGHT_LEG_COLOR, VisConfig.RIGHT_LEG_THICKNESS)

    # Draw keypoints
    for name in KEY_LANDMARKS:
        if name in lm_map:
            px, py, vis = lm_map[name]
            if vis > VisConfig.VISIBILITY_THRESHOLD:
                cv2.circle(frame, (px, py), VisConfig.LANDMARK_OUTLINE_RADIUS,
                           VisConfig.LANDMARK_OUTLINE_COLOR, 1, cv2.LINE_AA)
                kp_color = VisConfig.LEFT_LEG_COLOR if "left" in name else (
                    VisConfig.RIGHT_LEG_COLOR if "right" in name else VisConfig.LANDMARK_COLOR
                )
                cv2.circle(frame, (px, py), VisConfig.LANDMARK_RADIUS,
                           kp_color, -1, cv2.LINE_AA)


def draw_frame_info_panel(
    frame, frame_idx: int, total_frames: int,
    timestamp: float, fps: float,
    width: int, height: int,
) -> None:
    """
    Draw frame counter, timestamp, and FPS in the top-left corner.

    Args:
        frame: BGR image (modified in-place).
        frame_idx: Current frame index (0-based).
        total_frames: Total number of video frames.
        timestamp: Current timestamp in seconds.
        fps: Video framerate.
        width: Frame width in pixels.
        height: Frame height in pixels.
    """
    panel_w = 220
    panel_h = 65
    _draw_semi_transparent_rect(frame, 0, 0, panel_w, panel_h)

    y = 18
    cv2.putText(frame, f"Frame: {frame_idx} / {total_frames}",
                (8, y), VisConfig.FONT, VisConfig.FONT_SCALE_BODY,
                VisConfig.FONT_COLOR, VisConfig.FONT_THICKNESS, cv2.LINE_AA)
    y += VisConfig.LINE_HEIGHT
    cv2.putText(frame, f"Time: {timestamp:.2f} s",
                (8, y), VisConfig.FONT, VisConfig.FONT_SCALE_BODY,
                VisConfig.FONT_COLOR, VisConfig.FONT_THICKNESS, cv2.LINE_AA)
    y += VisConfig.LINE_HEIGHT
    cv2.putText(frame, f"FPS: {fps:.2f}",
                (8, y), VisConfig.FONT, VisConfig.FONT_SCALE_BODY,
                VisConfig.FONT_DIM_COLOR, VisConfig.FONT_THICKNESS, cv2.LINE_AA)


def draw_pose_validity(
    frame, pose_detected: bool, width: int,
) -> None:
    """
    Draw POSE: VALID or POSE: MISSING indicator at top-right.

    Args:
        frame: BGR image (modified in-place).
        pose_detected: Whether pose landmarks exist for this frame.
        width: Frame width in pixels.
    """
    label = "POSE: VALID" if pose_detected else "POSE: MISSING"
    color = VisConfig.POSE_VALID_COLOR if pose_detected else VisConfig.POSE_MISSING_COLOR

    panel_w = 155
    panel_h = 28
    x_start = width - panel_w
    _draw_semi_transparent_rect(frame, x_start, 0, width, panel_h)

    cv2.putText(frame, label, (x_start + 8, 19),
                VisConfig.FONT, VisConfig.FONT_SCALE_BODY,
                color, VisConfig.FONT_THICKNESS, cv2.LINE_AA)


def draw_phase_panel(
    frame, left_phase: Optional[str], right_phase: Optional[str],
    width: int, height: int,
) -> None:
    """
    Draw motion phase labels for left and right legs.

    Args:
        frame: BGR image (modified in-place).
        left_phase: Left leg phase string or None.
        right_phase: Right leg phase string or None.
        width: Frame width in pixels.
        height: Frame height in pixels.
    """
    l_label = left_phase if left_phase else "N/A"
    r_label = right_phase if right_phase else "N/A"
    l_color = VisConfig.PHASE_COLORS.get(l_label, VisConfig.PHASE_DEFAULT_COLOR)
    r_color = VisConfig.PHASE_COLORS.get(r_label, VisConfig.PHASE_DEFAULT_COLOR)

    panel_w = 230
    panel_h = 65
    x_start = 0
    y_start = height - panel_h
    _draw_semi_transparent_rect(frame, x_start, y_start, panel_w, height)

    y = y_start + 18
    cv2.putText(frame, "MOTION PHASE", (8, y),
                VisConfig.FONT, VisConfig.FONT_SCALE_SMALL,
                VisConfig.FONT_DIM_COLOR, VisConfig.FONT_THICKNESS, cv2.LINE_AA)
    y += VisConfig.LINE_HEIGHT
    cv2.putText(frame, f"LEFT : {l_label}", (8, y),
                VisConfig.FONT, VisConfig.FONT_SCALE_BODY,
                l_color, VisConfig.FONT_THICKNESS, cv2.LINE_AA)
    y += VisConfig.LINE_HEIGHT
    cv2.putText(frame, f"RIGHT: {r_label}", (8, y),
                VisConfig.FONT, VisConfig.FONT_SCALE_BODY,
                r_color, VisConfig.FONT_THICKNESS, cv2.LINE_AA)


def draw_angle_panel(
    frame, angles: Optional[Dict[str, Any]], width: int, height: int,
) -> None:
    """
    Draw joint angle readouts panel on the right side.

    Args:
        frame: BGR image (modified in-place).
        angles: Dictionary of joint_name -> angle_value (degrees) or None.
        width: Frame width in pixels.
        height: Frame height in pixels.
    """
    display_joints = ["left_knee", "right_knee", "left_hip", "right_hip", "left_ankle", "right_ankle"]
    display_labels = {
        "left_knee": "L Knee",
        "right_knee": "R Knee",
        "left_hip": "L Hip",
        "right_hip": "R Hip",
        "left_ankle": "L Ankle",
        "right_ankle": "R Ankle",
    }

    panel_w = 170
    panel_h = 15 + len(display_joints) * VisConfig.LINE_HEIGHT_SMALL + 8
    x_start = width - panel_w
    y_start = 35
    _draw_semi_transparent_rect(frame, x_start, y_start, width, y_start + panel_h)

    y = y_start + 15
    cv2.putText(frame, "JOINT ANGLES", (x_start + 8, y),
                VisConfig.FONT, VisConfig.FONT_SCALE_SMALL,
                VisConfig.FONT_DIM_COLOR, VisConfig.FONT_THICKNESS, cv2.LINE_AA)

    for joint in display_joints:
        y += VisConfig.LINE_HEIGHT_SMALL
        label = display_labels.get(joint, joint)
        if angles and angles.get(joint) is not None:
            val = angles[joint]
            text = f"{label:<9}: {val:>6.1f}\xb0"
            color = VisConfig.FONT_COLOR
        else:
            text = f"{label:<9}:    ---"
            color = VisConfig.FONT_DIM_COLOR
        cv2.putText(frame, text, (x_start + 8, y),
                    VisConfig.FONT, VisConfig.FONT_SCALE_SMALL,
                    color, VisConfig.FONT_THICKNESS, cv2.LINE_AA)


def draw_metrics_panel(
    frame, metrics: Optional[Dict[str, Any]], width: int, height: int,
) -> None:
    """
    Draw compact running metrics summary panel at bottom-right.

    Args:
        frame: BGR image (modified in-place).
        metrics: Running metrics dictionary or None.
        width: Frame width in pixels.
        height: Frame height in pixels.
    """
    panel_w = 200
    panel_h = 85
    x_start = width - panel_w
    y_start = height - panel_h
    _draw_semi_transparent_rect(frame, x_start, y_start, width, height)

    y = y_start + 15
    cv2.putText(frame, "RUNNING METRICS", (x_start + 8, y),
                VisConfig.FONT, VisConfig.FONT_SCALE_SMALL,
                VisConfig.FONT_DIM_COLOR, VisConfig.FONT_THICKNESS, cv2.LINE_AA)

    if metrics:
        cadence_val = metrics.get("cadence", {}).get("steps_per_minute")
        cadence_str = f"{cadence_val:.0f} spm" if cadence_val else "N/A"
        contacts = metrics.get("foot_contact_events", {})
        toe_offs = metrics.get("toe_off_events", {})

        y += VisConfig.LINE_HEIGHT_SMALL
        cv2.putText(frame, f"Cadence  : {cadence_str}", (x_start + 8, y),
                    VisConfig.FONT, VisConfig.FONT_SCALE_SMALL,
                    VisConfig.FONT_COLOR, VisConfig.FONT_THICKNESS, cv2.LINE_AA)
        y += VisConfig.LINE_HEIGHT_SMALL
        cv2.putText(frame, f"Contacts : L {contacts.get('left', 0)} | R {contacts.get('right', 0)}",
                    (x_start + 8, y), VisConfig.FONT, VisConfig.FONT_SCALE_SMALL,
                    VisConfig.FONT_COLOR, VisConfig.FONT_THICKNESS, cv2.LINE_AA)
        y += VisConfig.LINE_HEIGHT_SMALL
        cv2.putText(frame, f"Toe-offs : L {toe_offs.get('left', 0)} | R {toe_offs.get('right', 0)}",
                    (x_start + 8, y), VisConfig.FONT, VisConfig.FONT_SCALE_SMALL,
                    VisConfig.FONT_COLOR, VisConfig.FONT_THICKNESS, cv2.LINE_AA)
    else:
        y += VisConfig.LINE_HEIGHT_SMALL
        cv2.putText(frame, "No metrics data", (x_start + 8, y),
                    VisConfig.FONT, VisConfig.FONT_SCALE_SMALL,
                    VisConfig.FONT_DIM_COLOR, VisConfig.FONT_THICKNESS, cv2.LINE_AA)


def draw_data_quality_panel(
    frame, quality: Optional[Dict[str, Any]], width: int, height: int,
) -> None:
    """
    Draw data quality diagnostic panel (top area, below frame info).

    Args:
        frame: BGR image (modified in-place).
        quality: Data quality dictionary from running_metrics.json or None.
        width: Frame width in pixels.
        height: Frame height in pixels.
    """
    panel_w = 220
    panel_h = 72
    y_start = 70
    _draw_semi_transparent_rect(frame, 0, y_start, panel_w, y_start + panel_h)

    y = y_start + 15
    cv2.putText(frame, "DATA QUALITY", (8, y),
                VisConfig.FONT, VisConfig.FONT_SCALE_SMALL,
                VisConfig.FONT_DIM_COLOR, VisConfig.FONT_THICKNESS, cv2.LINE_AA)

    if quality:
        total = quality.get("total_frames", "?")
        valid = quality.get("valid_pose_frames", "?")
        pct = quality.get("pose_validity_percent", "?")
        events = quality.get("phase_events_used", "?")

        y += VisConfig.LINE_HEIGHT_SMALL
        cv2.putText(frame, f"Pose: {valid}/{total} ({pct}%)", (8, y),
                    VisConfig.FONT, VisConfig.FONT_SCALE_SMALL,
                    VisConfig.FONT_COLOR, VisConfig.FONT_THICKNESS, cv2.LINE_AA)
        y += VisConfig.LINE_HEIGHT_SMALL
        cv2.putText(frame, f"Phase Events: {events}", (8, y),
                    VisConfig.FONT, VisConfig.FONT_SCALE_SMALL,
                    VisConfig.FONT_COLOR, VisConfig.FONT_THICKNESS, cv2.LINE_AA)
    else:
        y += VisConfig.LINE_HEIGHT_SMALL
        cv2.putText(frame, "Quality data unavailable", (8, y),
                    VisConfig.FONT, VisConfig.FONT_SCALE_SMALL,
                    VisConfig.FONT_DIM_COLOR, VisConfig.FONT_THICKNESS, cv2.LINE_AA)


# ============================================================================
# MAIN VIDEO ANNOTATION FUNCTION
# ============================================================================

def create_annotated_video(
    video_path: Path,
    output_path: Path,
    landmarks_payload: Optional[Dict[str, Any]] = None,
    angles_payload: Optional[Dict[str, Any]] = None,
    phases_payload: Optional[Dict[str, Any]] = None,
    metrics_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create an annotated analysis video by overlaying precomputed AI results
    onto original video frames. Does NOT run any AI inference.

    Args:
        video_path: Path to the original video file.
        output_path: Path for the output annotated video.
        landmarks_payload: Data from smoothed_landmarks.json (or None).
        angles_payload: Data from joint_angles.json (or None).
        phases_payload: Data from motion_phases.json (or None).
        metrics_payload: Data from running_metrics.json (or None).

    Returns:
        Summary dictionary with processing statistics.
    """
    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise IOError(f"Failed to open video: {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if fps <= 0:
        fps = 29.97  # Fallback

    # Initialize video writer
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    if not writer.isOpened():
        cap.release()
        raise IOError(f"Failed to initialize video writer: {output_path}")

    # Build frame-indexed lookup tables from JSON payloads
    landmark_frames_map: Dict[int, Dict[str, Any]] = {}
    if landmarks_payload and "frames" in landmarks_payload:
        landmark_frames_map = build_frame_index_map(landmarks_payload["frames"])

    angle_frames_map: Dict[int, Dict[str, Any]] = {}
    if angles_payload and "frames" in angles_payload:
        angle_frames_map = build_frame_index_map(angles_payload["frames"])

    phase_frames_map: Dict[int, Dict[str, Any]] = {}
    if phases_payload and "frames" in phases_payload:
        phase_frames_map = build_frame_index_map(phases_payload["frames"])

    # Extract data quality and metrics from precomputed running_metrics.json
    data_quality = metrics_payload.get("data_quality") if metrics_payload else None

    # Counters
    valid_pose_count = 0
    missing_pose_count = 0
    frame_idx = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # --- Resolve per-frame data using frame_index alignment ---
        lm_frame = landmark_frames_map.get(frame_idx)
        ang_frame = angle_frames_map.get(frame_idx)
        ph_frame = phase_frames_map.get(frame_idx)

        # Determine pose validity
        pose_detected = False
        landmarks = []
        if lm_frame:
            pose_detected = lm_frame.get("pose_detected", False)
            landmarks = lm_frame.get("landmarks", [])
        if pose_detected and landmarks:
            valid_pose_count += 1
        else:
            missing_pose_count += 1

        # Determine timestamp
        timestamp = frame_idx / fps

        # Resolve angles
        angles = None
        if ang_frame:
            angles = ang_frame.get("angles")

        # Resolve phases
        left_phase = None
        right_phase = None
        if ph_frame:
            left_phase = ph_frame.get("left_phase")
            right_phase = ph_frame.get("right_phase")

        # --- Draw overlays ---

        # 1. Skeleton (only if pose detected)
        if pose_detected and landmarks:
            draw_skeleton(frame, landmarks, width, height)

        # 2. Frame info (top-left)
        draw_frame_info_panel(frame, frame_idx, total_frames, timestamp, fps, width, height)

        # 3. Pose validity (top-right)
        draw_pose_validity(frame, pose_detected, width)

        # 4. Joint angles (right side, below pose validity)
        draw_angle_panel(frame, angles, width, height)

        # 5. Data quality (left side, below frame info)
        draw_data_quality_panel(frame, data_quality, width, height)

        # 6. Motion phase (bottom-left)
        draw_phase_panel(frame, left_phase, right_phase, width, height)

        # 7. Running metrics (bottom-right)
        draw_metrics_panel(frame, metrics_payload, width, height)

        # Write annotated frame
        writer.write(frame)
        frame_idx += 1

    # Cleanup
    cap.release()
    writer.release()

    return {
        "total_frames_processed": frame_idx,
        "valid_pose_frames": valid_pose_count,
        "missing_pose_frames": missing_pose_count,
        "fps": fps,
        "resolution": f"{width}x{height}",
        "output_path": str(output_path),
    }
