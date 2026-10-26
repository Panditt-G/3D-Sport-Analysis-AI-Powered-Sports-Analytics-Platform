"""
Badminton Overhead Clear Movement Analyzer & Phase Detector.
============================================================
Segments dynamic stroke sequences into 6 biomechanical phases and
extracts joint kinematics for coach-approved comparison.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from ai_engine.vision.pose.base_pose import PoseFrame
from ai_engine.pose_analysis.joint_angles import calculate_2d_angle


class OverheadClearAnalyzer:
    """Specialized analyzer for Badminton Overhead Clear."""

    def __init__(self, dominant_hand: str = "right"):
        self.dominant_hand = dominant_hand.lower()
        self.prefix = "right_" if self.dominant_hand == "right" else "left_"
        self.opp_prefix = "left_" if self.dominant_hand == "right" else "right_"

    def _get_joint_angle(self, frame: PoseFrame, joint_a: str, joint_b: str, joint_c: str) -> Optional[float]:
        """Compute angle between 3 joints (B is vertex)."""
        pt_a = frame.get_coords(joint_a)
        pt_b = frame.get_coords(joint_b)
        pt_c = frame.get_coords(joint_c)
        if pt_a and pt_b and pt_c:
            return float(calculate_2d_angle(pt_a, pt_b, pt_c))
        return None

    def segment_phases(self, frames: List[PoseFrame]) -> Dict[str, Dict[str, Any]]:
        """
        Segment stroke sequence into 6 standard phases:
        1. preparation
        2. backswing
        3. forward_swing
        4. contact
        5. follow_through
        6. recovery
        """
        total_frames = len(frames)
        if total_frames < 6:
            # Fallback uniform segmentation for extremely short clips
            step = total_frames / 6.0
            phases = ["preparation", "backswing", "forward_swing", "contact", "follow_through", "recovery"]
            return {
                p: {"start_idx": int(i * step), "end_idx": min(total_frames - 1, int((i + 1) * step))}
                for i, p in enumerate(phases)
            }

        wrist_name = f"{self.prefix}wrist"
        elbow_name = f"{self.prefix}elbow"
        shoulder_name = f"{self.prefix}shoulder"

        # Track wrist vertical elevation (lower y in image coords = higher physically)
        wrist_heights = []
        elbow_angles = []

        for f in frames:
            w_pt = f.get_coords(wrist_name)
            s_pt = f.get_coords(shoulder_name)
            e_ang = self._get_joint_angle(f, shoulder_name, elbow_name, wrist_name)

            if w_pt and s_pt:
                # Relative vertical height: shoulder.y - wrist.y (positive when wrist is higher than shoulder)
                wrist_heights.append(s_pt[1] - w_pt[1])
            else:
                wrist_heights.append(0.0)

            elbow_angles.append(e_ang if e_ang is not None else 120.0)

        # Contact is the frame with maximum wrist vertical elevation and extended elbow
        scores = [h * 1.5 + (ang / 180.0) for h, ang in zip(wrist_heights, elbow_angles)]
        contact_idx = int(np.argmax(scores))

        # Contact frame sanity check: should not be frame 0 or last frame
        contact_idx = max(2, min(total_frames - 3, contact_idx))

        # Backswing is minimum wrist height / deepest elbow cocking prior to contact
        pre_contact_elbows = elbow_angles[:contact_idx]
        backswing_idx = int(np.argmin(pre_contact_elbows)) if pre_contact_elbows else max(0, contact_idx // 2)

        # Build clean chronological boundaries
        prep_end = max(0, backswing_idx // 2)
        forward_swing_start = backswing_idx
        contact_end = min(total_frames - 1, contact_idx + max(1, (total_frames - contact_idx) // 4))
        follow_through_end = min(total_frames - 1, contact_end + max(1, (total_frames - contact_end) // 2))

        return {
            "preparation": {
                "name": "Preparation",
                "start_idx": 0,
                "end_idx": max(0, backswing_idx - 1),
                "start_time": frames[0].timestamp,
                "end_time": frames[max(0, backswing_idx - 1)].timestamp,
            },
            "backswing": {
                "name": "Backswing & Cocking",
                "start_idx": backswing_idx,
                "end_idx": max(backswing_idx, contact_idx - 2),
                "start_time": frames[backswing_idx].timestamp,
                "end_time": frames[max(backswing_idx, contact_idx - 2)].timestamp,
            },
            "forward_swing": {
                "name": "Forward Swing Acceleration",
                "start_idx": max(backswing_idx, contact_idx - 2),
                "end_idx": max(0, contact_idx - 1),
                "start_time": frames[max(backswing_idx, contact_idx - 2)].timestamp,
                "end_time": frames[max(0, contact_idx - 1)].timestamp,
            },
            "contact": {
                "name": "Impact / Contact Point",
                "start_idx": contact_idx,
                "end_idx": contact_end,
                "start_time": frames[contact_idx].timestamp,
                "end_time": frames[contact_end].timestamp,
                "peak_frame_idx": contact_idx,
            },
            "follow_through": {
                "name": "Follow-Through",
                "start_idx": min(total_frames - 1, contact_end + 1),
                "end_idx": follow_through_end,
                "start_time": frames[min(total_frames - 1, contact_end + 1)].timestamp,
                "end_time": frames[follow_through_end].timestamp,
            },
            "recovery": {
                "name": "Recovery & Base Return",
                "start_idx": min(total_frames - 1, follow_through_end + 1),
                "end_idx": total_frames - 1,
                "start_time": frames[min(total_frames - 1, follow_through_end + 1)].timestamp,
                "end_time": frames[-1].timestamp,
            },
        }

    def compute_movement_metrics(self, frames: List[PoseFrame], phases: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Extract stroke metrics from the segmented phases."""
        contact_idx = phases.get("contact", {}).get("peak_frame_idx", len(frames) // 2)
        contact_frame = frames[min(len(frames) - 1, contact_idx)]

        backswing_idx = phases.get("backswing", {}).get("start_idx", 0)
        backswing_frame = frames[min(len(frames) - 1, backswing_idx)]

        # Contact Elbow Angle (Shoulder - Elbow - Wrist)
        contact_elbow = self._get_joint_angle(
            contact_frame,
            f"{self.prefix}shoulder",
            f"{self.prefix}elbow",
            f"{self.prefix}wrist",
        )

        # Backswing Elbow Angle
        backswing_elbow = self._get_joint_angle(
            backswing_frame,
            f"{self.prefix}shoulder",
            f"{self.prefix}elbow",
            f"{self.prefix}wrist",
        )

        # Contact Shoulder Elevation (Hip - Shoulder - Elbow)
        contact_shoulder = self._get_joint_angle(
            contact_frame,
            f"{self.prefix}hip",
            f"{self.prefix}shoulder",
            f"{self.prefix}elbow",
        )

        # Trunk forward inclination relative to vertical
        sh_pt = contact_frame.get_coords(f"{self.prefix}shoulder")
        hip_pt = contact_frame.get_coords(f"{self.prefix}hip")
        trunk_tilt = 10.0
        if sh_pt and hip_pt:
            dx = sh_pt[0] - hip_pt[0]
            dy = hip_pt[1] - sh_pt[1]  # positive up
            trunk_tilt = float(np.degrees(np.arctan2(abs(dx), max(1e-5, dy))))

        # Fallback defaults if occluded
        metrics = {
            "contact_elbow_angle": round(contact_elbow, 1) if contact_elbow is not None else 168.0,
            "backswing_elbow_angle": round(backswing_elbow, 1) if backswing_elbow is not None else 82.0,
            "contact_shoulder_elevation": round(contact_shoulder, 1) if contact_shoulder is not None else 164.0,
            "trunk_forward_tilt": round(trunk_tilt, 1),
            "contact_frame_idx": contact_idx,
            "backswing_frame_idx": backswing_idx,
            "dominant_hand": self.dominant_hand,
        }

        return metrics
