"""Overlays, bounding boxes, pose skeletons, and telemetry HUD drawing."""
import cv2
import numpy as np
from typing import Any, Dict, List, Optional, Tuple


# MediaPipe BlazePose skeleton connections for drawing
POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),  # Shoulders to wrists
    (11, 23), (12, 24), (23, 24),                        # Torso
    (23, 25), (25, 27), (24, 26), (26, 28),              # Hips to ankles
    (27, 29), (27, 31), (28, 30), (28, 32),              # Ankles to feet
]


def draw_bounding_box(
    frame: np.ndarray,
    bbox: Tuple[int, int, int, int],
    label: str = "",
    color: Tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
) -> np.ndarray:
    """
    Draw a bounding box with optional label on the frame.

    Args:
        frame: Input BGR image.
        bbox: (x1, y1, x2, y2) bounding box coordinates.
        label: Optional text label above the box.
        color: BGR color tuple.
        thickness: Line thickness.

    Returns:
        Frame with bounding box drawn.
    """
    x1, y1, x2, y2 = bbox
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

    if label:
        font_scale = 0.5
        font_thickness = 1
        (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness)
        cv2.rectangle(frame, (x1, y1 - text_h - 8), (x1 + text_w + 4, y1), color, -1)
        cv2.putText(frame, label, (x1 + 2, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), font_thickness, cv2.LINE_AA)

    return frame


def draw_pose_skeleton(
    frame: np.ndarray,
    landmarks: List[Dict[str, Any]],
    point_color: Tuple[int, int, int] = (0, 200, 0),
    line_color: Tuple[int, int, int] = (200, 200, 200),
    point_radius: int = 4,
    line_thickness: int = 2,
    min_visibility: float = 0.5,
) -> np.ndarray:
    """
    Draw pose skeleton from landmark data on the frame.

    Args:
        frame: Input BGR image.
        landmarks: List of landmark dicts with 'index', 'x', 'y', 'visibility'.
        point_color: BGR color for joint points.
        line_color: BGR color for skeleton lines.
        point_radius: Radius of joint circles.
        line_thickness: Thickness of skeleton lines.
        min_visibility: Minimum visibility score to draw a landmark.

    Returns:
        Frame with pose skeleton drawn.
    """
    h, w = frame.shape[:2]

    # Build index-to-pixel map
    lm_pixels = {}
    for lm in landmarks:
        idx = lm.get("index", -1)
        vis = lm.get("visibility", 0.0)
        if vis >= min_visibility and idx >= 0:
            px = int(lm["x"] * w)
            py = int(lm["y"] * h)
            lm_pixels[idx] = (px, py)

    # Draw connections
    for idx_a, idx_b in POSE_CONNECTIONS:
        if idx_a in lm_pixels and idx_b in lm_pixels:
            cv2.line(frame, lm_pixels[idx_a], lm_pixels[idx_b], line_color, line_thickness, cv2.LINE_AA)

    # Draw joint points
    for idx, (px, py) in lm_pixels.items():
        cv2.circle(frame, (px, py), point_radius, point_color, -1, cv2.LINE_AA)

    return frame


def draw_text_overlay(
    frame: np.ndarray,
    text: str,
    position: Tuple[int, int] = (10, 30),
    font_scale: float = 0.6,
    color: Tuple[int, int, int] = (255, 255, 255),
    bg_color: Optional[Tuple[int, int, int]] = (0, 0, 0),
    thickness: int = 1,
) -> np.ndarray:
    """
    Draw text with optional background rectangle on the frame.

    Args:
        frame: Input BGR image.
        text: Text string to draw.
        position: (x, y) top-left position.
        font_scale: Font scale factor.
        color: Text color (BGR).
        bg_color: Background color (BGR), None for transparent.
        thickness: Text thickness.

    Returns:
        Frame with text drawn.
    """
    (text_w, text_h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
    x, y = position

    if bg_color is not None:
        cv2.rectangle(frame, (x - 2, y - text_h - 4), (x + text_w + 4, y + baseline + 2), bg_color, -1)

    cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)
    return frame


def draw_telemetry_hud(
    frame: np.ndarray,
    metrics: Dict[str, Any],
    sport_name: str = "",
    frame_idx: int = 0,
) -> np.ndarray:
    """
    Draw a simple telemetry HUD showing sport metrics on the frame.

    Args:
        frame: Input BGR image.
        metrics: Dictionary of metric_name: value pairs.
        sport_name: Name of the sport being analyzed.
        frame_idx: Current frame index.

    Returns:
        Frame with telemetry HUD.
    """
    y_pos = 30
    if sport_name:
        draw_text_overlay(frame, f"Sport: {sport_name.upper()}", (10, y_pos))
        y_pos += 25

    draw_text_overlay(frame, f"Frame: {frame_idx}", (10, y_pos))
    y_pos += 25

    for key, value in metrics.items():
        if isinstance(value, float):
            text = f"{key}: {value:.2f}"
        else:
            text = f"{key}: {value}"
        draw_text_overlay(frame, text, (10, y_pos))
        y_pos += 22

    return frame
