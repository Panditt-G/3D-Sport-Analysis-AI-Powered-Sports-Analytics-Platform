"""
Joint Angle Calculation Module
==============================
This module computes 2D joint angles (in degrees) from body landmark coordinates.
It provides a numerically stable 3-point angle calculation function and standard
angle definitions for athletic movement analysis (knees, hips, ankles, etc.).
"""

import math
from typing import Dict, Any, List, Optional, Tuple, Union


def calculate_2d_angle(
    a: Union[Tuple[float, float], List[float], Dict[str, float]],
    b: Union[Tuple[float, float], List[float], Dict[str, float]],
    c: Union[Tuple[float, float], List[float], Dict[str, float]],
) -> Optional[float]:
    """
    Calculate the interior angle (in degrees) formed by three points A-B-C,
    where B is the vertex / joint center.

    Args:
        a: Coordinates of first point (x, y).
        b: Coordinates of vertex/joint (x, y).
        c: Coordinates of third point (x, y).

    Returns:
        Angle in degrees [0.0, 180.0], or None if points are invalid or degenerate.
    """
    # Extract x and y from tuple, list, or dictionary
    def get_xy(pt):
        if isinstance(pt, dict):
            return pt.get("x"), pt.get("y")
        elif isinstance(pt, (list, tuple)) and len(pt) >= 2:
            return pt[0], pt[1]
        return None, None

    ax, ay = get_xy(a)
    bx, by = get_xy(b)
    cx, cy = get_xy(c)

    # Check for missing/None coordinates
    if any(coord is None for coord in (ax, ay, bx, by, cx, cy)):
        return None

    # Vector BA (B -> A) and Vector BC (B -> C)
    v_ba = (ax - bx, ay - by)
    v_bc = (cx - bx, cy - by)

    # Magnitudes
    mag_ba = math.hypot(v_ba[0], v_ba[1])
    mag_bc = math.hypot(v_bc[0], v_bc[1])

    # Avoid division by zero for coincident/degenerate points
    if mag_ba < 1e-7 or mag_bc < 1e-7:
        return None

    # Dot product
    dot = v_ba[0] * v_bc[0] + v_ba[1] * v_bc[1]

    # Cosine clamped to [-1.0, 1.0] for numerical stability
    cosine = max(-1.0, min(1.0, dot / (mag_ba * mag_bc)))
    angle_rad = math.acos(cosine)
    angle_deg = math.degrees(angle_rad)

    return round(angle_deg, 2)


# Standard running joint definitions: (joint_name: (point_A, point_B_vertex, point_C))
RUNNING_JOINT_DEFINITIONS = {
    "left_knee": ("left_hip", "left_knee", "left_ankle"),
    "right_knee": ("right_hip", "right_knee", "right_ankle"),
    "left_hip": ("left_shoulder", "left_hip", "left_knee"),
    "right_hip": ("right_shoulder", "right_hip", "right_knee"),
    "left_ankle": ("left_knee", "left_ankle", "left_foot_index"),
    "right_ankle": ("right_knee", "right_ankle", "right_foot_index"),
}


class JointAngleCalculator:
    """
    Computes biomechanical joint angles from a set of pose landmarks.
    """

    def __init__(self, joint_definitions: Optional[Dict[str, Tuple[str, str, str]]] = None):
        """
        Initialize with custom or standard joint definitions.

        Args:
            joint_definitions: Mapping of joint_name -> (landmark_a, vertex_b, landmark_c).
                               Defaults to RUNNING_JOINT_DEFINITIONS.
        """
        self.joint_definitions = joint_definitions or RUNNING_JOINT_DEFINITIONS

    def compute_angles_from_landmarks(
        self, landmarks: List[Dict[str, Any]]
    ) -> Dict[str, Optional[float]]:
        """
        Calculate all defined joint angles from a list of landmark dictionaries.

        Args:
            landmarks: List of landmark dictionaries, each containing 'name', 'x', 'y'.

        Returns:
            Dictionary mapping joint name to angle in degrees (or None if unavailable).
        """
        # Map landmark names to their coordinates for fast O(1) lookup
        lm_map = {lm["name"]: (lm["x"], lm["y"]) for lm in landmarks if "name" in lm}

        angles: Dict[str, Optional[float]] = {}

        for joint_name, (pt_a_name, vertex_name, pt_c_name) in self.joint_definitions.items():
            if (
                pt_a_name in lm_map
                and vertex_name in lm_map
                and pt_c_name in lm_map
            ):
                pt_a = lm_map[pt_a_name]
                vertex_b = lm_map[vertex_name]
                pt_c = lm_map[pt_c_name]
                angles[joint_name] = calculate_2d_angle(pt_a, vertex_b, pt_c)
            else:
                # Landmark missing
                angles[joint_name] = None

        return angles

    def process_frame(self, frame_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute joint angles for a single frame dictionary.

        Args:
            frame_data: Dictionary containing frame_index, timestamp, pose_detected, landmarks.

        Returns:
            Dictionary containing frame_index, timestamp, and calculated angles.
        """
        frame_index = frame_data["frame_index"]
        timestamp = frame_data["timestamp"]
        landmarks = frame_data.get("landmarks", [])

        if frame_data.get("pose_detected", False) and landmarks:
            angles = self.compute_angles_from_landmarks(landmarks)
        else:
            # If no pose detected, set all angles to None
            angles = {joint: None for joint in self.joint_definitions.keys()}

        return {
            "frame_index": frame_index,
            "timestamp": timestamp,
            "angles": angles,
        }

    def process_sequence(self, frames: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compute joint angles across a sequence of frames.

        Args:
            frames: Chronological list of frame dictionaries.

        Returns:
            List of frame dictionaries with joint angles.
        """
        return [self.process_frame(f) for f in frames]
