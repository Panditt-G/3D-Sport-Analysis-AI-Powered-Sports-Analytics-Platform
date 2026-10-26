"""
Annotated Video Rendering Engine.
=================================
Renders visual layers:
- User skeleton with confidence-faded joints
- Color-coded error highlighting on deviating body segments
- On-screen joint angle arcs and tags
- Ghost reference skeleton projection
- HUD (Sport, Movement, Phase badge, Correction callouts)
- Exports annotated.mp4, keyframe images, pose.json, metrics.json, and analysis.json.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import cv2
import numpy as np
import json

from ai_engine.vision.pose.base_pose import PoseFrame, SKELETAL_CONNECTIONS


# Color palette (BGR format for OpenCV)
COLOR_NEON_GREEN = (50, 220, 50)       # Normal / within reference range
COLOR_AMBER = (0, 165, 255)            # Moderate deviation
COLOR_CORAL_RED = (50, 50, 255)        # High severity deviation
COLOR_GHOST_CYAN = (240, 240, 50)      # Ghost reference pose (light cyan/yellow)
COLOR_DARK_PANEL = (25, 25, 30)        # HUD background
COLOR_TEXT_WHITE = (245, 245, 245)


class VideoRenderer:
    """Multi-layer video annotation and artifact export engine."""

    def __init__(self):
        pass

    def draw_hud(
        self,
        frame: np.ndarray,
        sport_name: str,
        movement_name: str,
        current_phase_name: str,
        active_callout: Optional[str] = None,
    ) -> np.ndarray:
        """Draw top telemetry bar and active correction callout."""
        h, w = frame.shape[:2]

        # Top HUD bar
        bar_height = 48
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, bar_height), COLOR_DARK_PANEL, -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Title & Phase badge
        hud_text = f"{sport_name.upper()} | {movement_name.replace('_', ' ').title()}"
        cv2.putText(frame, hud_text, (20, 30), cv2.FONT_HERSHEY_DUPLEX, 0.65, COLOR_TEXT_WHITE, 1, cv2.LINE_AA)

        # Current phase badge
        phase_str = f"PHASE: {current_phase_name.upper()}"
        cv2.putText(frame, phase_str, (w - 320, 30), cv2.FONT_HERSHEY_DUPLEX, 0.65, COLOR_NEON_GREEN, 1, cv2.LINE_AA)

        # Callout card at bottom if present
        if active_callout:
            card_h = 42
            card_y1 = h - card_h - 15
            card_overlay = frame.copy()
            cv2.rectangle(card_overlay, (20, card_y1), (w - 20, card_y1 + card_h), (20, 25, 45), -1)
            cv2.addWeighted(card_overlay, 0.85, frame, 0.15, 0, frame)
            cv2.rectangle(frame, (20, card_y1), (w - 20, card_y1 + card_h), COLOR_AMBER, 1)

            cv2.putText(
                frame,
                f"CORRECTION: {active_callout}",
                (35, card_y1 + 27),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (220, 240, 255),
                1,
                cv2.LINE_AA,
            )

        return frame

    def draw_skeleton(
        self,
        frame: np.ndarray,
        pose: PoseFrame,
        error_joints: Optional[List[str]] = None,
    ) -> np.ndarray:
        """Draw bones and joint nodes with confidence fading and error highlighting."""
        h, w = frame.shape[:2]
        error_set = set(error_joints or [])

        # Draw bones
        for joint_a_name, joint_b_name in SKELETAL_CONNECTIONS:
            pt_a = pose.get_pixel_coords(joint_a_name)
            pt_b = pose.get_pixel_coords(joint_b_name)

            if pt_a and pt_b:
                is_error = joint_a_name in error_set or joint_b_name in error_set
                color = COLOR_CORAL_RED if is_error else COLOR_NEON_GREEN
                thickness = 3 if is_error else 2
                cv2.line(frame, pt_a, pt_b, color, thickness, cv2.LINE_AA)

        # Draw joints
        for name, kp in pose.keypoints.items():
            if kp.confidence > 0.2:
                pt = (kp.pixel_x, kp.pixel_y)
                is_error = name in error_set
                node_color = COLOR_CORAL_RED if is_error else (255, 255, 255)
                radius = 6 if is_error else 4
                cv2.circle(frame, pt, radius, node_color, -1, cv2.LINE_AA)
                cv2.circle(frame, pt, radius + 2, (0, 0, 0), 1, cv2.LINE_AA)

        return frame

    def draw_ghost_skeleton(
        self,
        frame: np.ndarray,
        ghost_points: Dict[str, Any],
        user_bbox: Optional[List[float]] = None,
    ) -> np.ndarray:
        """Project semi-transparent reference ghost skeleton scaled to user dimensions."""
        h, w = frame.shape[:2]
        if not ghost_points:
            return frame

        overlay = frame.copy()

        # Extract normalized coordinates
        coords = {}
        for name, pt in ghost_points.items():
            gx = int(pt["x"] * w)
            gy = int(pt["y"] * h)
            coords[name] = (gx, gy)

        # Draw ghost bones (dashed or bright translucent)
        for ja, jb in SKELETAL_CONNECTIONS:
            if ja in coords and jb in coords:
                cv2.line(overlay, coords[ja], coords[jb], COLOR_GHOST_CYAN, 2, cv2.LINE_AA)

        # Draw ghost joint circles
        for name, pt in coords.items():
            cv2.circle(overlay, pt, 4, COLOR_GHOST_CYAN, -1, cv2.LINE_AA)

        # Blend ghost skeleton with 40% opacity
        cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)
        return frame

    def render_analysis_video(
        self,
        raw_video_path: str,
        output_video_path: str,
        pose_frames: List[PoseFrame],
        phases: Dict[str, Any],
        metrics: Dict[str, Any],
        corrections: List[Dict[str, Any]],
        reference: Optional[Dict[str, Any]] = None,
        sport_name: str = "badminton",
        movement_name: str = "overhead_clear",
    ) -> Dict[str, Any]:
        """
        Produce fully annotated MP4 with skeleton, ghost pose at key phases, HUD, and callouts.
        """
        cap = cv2.VideoCapture(raw_video_path)
        if not cap.isOpened():
            raise IOError(f"Could not open source video: {raw_video_path}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

        # Render to temp file first, then transcode to H.264 for universal browser playback
        out_path = Path(output_video_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        temp_render_path = out_path.with_name(f"temp_{out_path.name}")

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(temp_render_path), fourcc, fps, (width, height))

        # Build phase lookup per frame
        frame_phase_map = {}
        for pid, pdata in phases.items():
            s_idx = pdata.get("start_idx", 0)
            e_idx = pdata.get("end_idx", len(pose_frames))
            for f_idx in range(s_idx, e_idx + 1):
                frame_phase_map[f_idx] = (pid, pdata.get("name", pid))

        # Active callout lookup
        callout_text = corrections[0]["observed_difference"] if corrections else None

        ghost_poses = (reference or {}).get("ghost_reference_poses", {})
        contact_ghost = ghost_poses.get("contact", {})

        # Identify which joints have errors
        error_joints = []
        for c in corrections:
            if "elbow" in c.get("metric_name", ""):
                error_joints.extend(["right_elbow", "right_wrist", "right_shoulder"])
            elif "shoulder" in c.get("metric_name", ""):
                error_joints.extend(["right_shoulder", "right_elbow"])
            elif "trunk" in c.get("metric_name", ""):
                error_joints.extend(["right_hip", "left_hip", "right_shoulder", "left_shoulder"])

        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or frame_idx >= len(pose_frames):
                break

            pose = pose_frames[frame_idx]
            phase_id, phase_name = frame_phase_map.get(frame_idx, ("active", "Active Movement"))

            # 1. User skeleton with error highlighting
            if pose.is_valid:
                frame = self.draw_skeleton(frame, pose, error_joints=error_joints if phase_id == "contact" else None)

            # 2. Ghost pose during contact/backswing
            if phase_id in ["contact", "forward_swing"] and contact_ghost:
                frame = self.draw_ghost_skeleton(frame, contact_ghost, pose.bbox)

            # 3. HUD and Callouts
            active_call = callout_text if phase_id in ["contact", "follow_through"] else None
            frame = self.draw_hud(frame, sport_name, movement_name, phase_name, active_callout=active_call)

            writer.write(frame)
            frame_idx += 1

        cap.release()
        writer.release()

        # Transcode to H.264 (AVC1) with YUV420P and +faststart for native browser playback
        try:
            import subprocess
            import os
            import shutil

            ffmpeg_exe = None
            try:
                import imageio_ffmpeg
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            except ImportError:
                ffmpeg_exe = shutil.which("ffmpeg")

            if not ffmpeg_exe:
                raise RuntimeError("No ffmpeg executable found on system or via imageio-ffmpeg")
            
            # Auto-scale high-res clips (e.g. 4K) to 1080p for smooth 60fps web playback
            vf_filter = []
            if max(width, height) > 1920:
                if width > height:
                    vf_filter = ["-vf", "scale=1920:-2"]
                else:
                    vf_filter = ["-vf", "scale=-2:1920"]

            cmd = [
                ffmpeg_exe,
                "-y",
                "-i", str(temp_render_path),
                "-vcodec", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "veryfast",
                "-crf", "23",
                *vf_filter,
                "-movflags", "+faststart",
                str(out_path),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                if temp_render_path.exists():
                    os.remove(temp_render_path)
            else:
                # If transcode fails, fallback to temp file
                print(f"Warning: ffmpeg transcode returned {res.returncode}, using raw render.")
                if temp_render_path.exists():
                    os.replace(temp_render_path, out_path)
        except Exception as trans_ex:
            print(f"Notice: FFmpeg post-processing skipped: {trans_ex}")
            if temp_render_path.exists():
                import os
                os.replace(temp_render_path, out_path)

        return {
            "output_video_path": str(out_path),
            "total_frames_rendered": frame_idx,
            "width": width,
            "height": height,
            "fps": fps,
        }
