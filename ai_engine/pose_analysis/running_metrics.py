"""
Running Biomechanics & Performance Metrics Module
=================================================
This module processes motion phase sequences, joint kinematics, and body landmark
trajectories to compute standardized athletic running metrics.

Computed Metrics:
1. Stance Time (Left / Right): Event counts, min/avg/max duration in frames and seconds.
2. Swing Time (Left / Right): Event counts, min/avg/max duration in frames and seconds.
3. Foot Contact Events: Transition counts per leg and total.
4. Toe-Off Events: Push-off transition counts per leg and total.
5. Step Timing: Alternating step intervals (left-to-right, right-to-left, average).
6. Cadence: Estimated steps per minute based on validated contact timing.
7. Bilateral Symmetry: Absolute stance, swing, and step-timing differences.
8. Joint Angle Statistics: Min, max, and average angles for athletic joints.
9. Running Cycle Summary: Valid gait cycle detection and cycle duration metrics.
10. Data Quality: Tracking validity percentages and event reliability indicators.

Design Principles:
- Measurement & reporting layer only (no medical diagnoses or subjective claims).
- Resolution/scale invariant calculations.
- Safe division & null-handling for missing or low-confidence data.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple


@dataclass
class PhaseEvent:
    """Represents a continuous period of a single motion phase for one leg."""
    phase: str
    side: str
    start_frame: int
    end_frame: int
    frame_count: int
    start_timestamp: float
    end_timestamp: float
    duration_seconds: Optional[float] = None


class RunningMetricsCalculator:
    """
    Computes running biomechanics and performance metrics from motion phases and joint kinematics.
    """

    def __init__(self, fps: Optional[float] = None):
        """
        Initialize the metrics calculator.

        Args:
            fps: Video frames per second. If None or <= 0, duration seconds will be null.
        """
        self.fps = fps if (fps is not None and fps > 0) else None

    def extract_phase_events(self, frames: List[Dict[str, Any]], side: str) -> List[PhaseEvent]:
        """
        Extract continuous phase periods for a specified leg side ('left' or 'right').
        Consecutive frames with the same phase form ONE continuous event.

        Args:
            frames: List of frame dictionaries containing 'frame_index', 'timestamp', and phase keys.
            side: 'left' or 'right'.

        Returns:
            List of PhaseEvent objects.
        """
        events: List[PhaseEvent] = []
        phase_key = f"{side}_phase"

        current_phase: Optional[str] = None
        current_frames: List[int] = []
        start_ts: Optional[float] = None
        end_ts: Optional[float] = None

        for f in frames:
            phase = f.get(phase_key)
            idx = f.get("frame_index", 0)
            ts = f.get("timestamp", 0.0)

            # Check for phase change or gap
            if phase != current_phase:
                if current_phase is not None and current_phase != "UNKNOWN" and current_frames:
                    dur_sec = (len(current_frames) / self.fps) if self.fps else None
                    events.append(
                        PhaseEvent(
                            phase=current_phase,
                            side=side,
                            start_frame=current_frames[0],
                            end_frame=current_frames[-1],
                            frame_count=len(current_frames),
                            start_timestamp=start_ts if start_ts is not None else 0.0,
                            end_timestamp=end_ts if end_ts is not None else 0.0,
                            duration_seconds=round(dur_sec, 3) if dur_sec is not None else None,
                        )
                    )
                current_phase = phase
                current_frames = [idx] if phase is not None else []
                start_ts = ts
                end_ts = ts
            else:
                if phase is not None:
                    current_frames.append(idx)
                    end_ts = ts

        # Close the trailing event if present
        if current_phase is not None and current_phase != "UNKNOWN" and current_frames:
            dur_sec = (len(current_frames) / self.fps) if self.fps else None
            events.append(
                PhaseEvent(
                    phase=current_phase,
                    side=side,
                    start_frame=current_frames[0],
                    end_frame=current_frames[-1],
                    frame_count=len(current_frames),
                    start_timestamp=start_ts if start_ts is not None else 0.0,
                    end_timestamp=end_ts if end_ts is not None else 0.0,
                    duration_seconds=round(dur_sec, 3) if dur_sec is not None else None,
                )
            )

        return events

    def calculate_phase_durations(self, events: List[PhaseEvent], target_phase: str) -> Dict[str, Any]:
        """
        Calculate event count, min, avg, max durations in frames and seconds for a target phase.

        Args:
            events: List of PhaseEvents for a leg.
            target_phase: Phase name (e.g. 'STANCE', 'SWING').

        Returns:
            Dictionary matching required duration metrics structure.
        """
        matching = [e for e in events if e.phase == target_phase]
        count = len(matching)

        if count == 0:
            return {
                "count": 0,
                "min_frames": None,
                "avg_frames": None,
                "max_frames": None,
                "min_seconds": None,
                "avg_seconds": None,
                "max_seconds": None,
            }

        frame_counts = [e.frame_count for e in matching]
        min_f = min(frame_counts)
        max_f = max(frame_counts)
        avg_f = round(sum(frame_counts) / count, 2)

        min_s = round(min_f / self.fps, 3) if self.fps else None
        avg_s = round(avg_f / self.fps, 3) if self.fps else None
        max_s = round(max_f / self.fps, 3) if self.fps else None

        return {
            "count": count,
            "min_frames": min_f,
            "avg_frames": avg_f,
            "max_frames": max_f,
            "min_seconds": min_s,
            "avg_seconds": avg_s,
            "max_seconds": max_s,
        }

    def count_transition_events(self, events: List[PhaseEvent], target_phase: str) -> int:
        """Count the number of distinct continuous events of a given phase."""
        return len([e for e in events if e.phase == target_phase])

    def calculate_step_timing(
        self, left_events: List[PhaseEvent], right_events: List[PhaseEvent]
    ) -> Dict[str, Any]:
        """
        Calculate step intervals using chronologically ordered alternating foot contact events.

        Args:
            left_events: List of PhaseEvents for left leg.
            right_events: List of PhaseEvents for right leg.

        Returns:
            Dictionary with average, left-to-right, right-to-left intervals and valid count.
        """
        # Gather all foot contact events (or stance if no explicit contact phase)
        contacts: List[Tuple[float, str]] = []
        for e in left_events:
            if e.phase == "FOOT_CONTACT":
                contacts.append((e.start_timestamp, "left"))
        for e in right_events:
            if e.phase == "FOOT_CONTACT":
                contacts.append((e.start_timestamp, "right"))

        # Sort chronologically by event start timestamp
        contacts.sort(key=lambda x: x[0])

        l_to_r_intervals: List[float] = []
        r_to_l_intervals: List[float] = []
        all_intervals: List[float] = []

        for i in range(len(contacts) - 1):
            t_curr, leg_curr = contacts[i]
            t_next, leg_next = contacts[i + 1]

            if leg_curr != leg_next and t_next > t_curr:
                dt = t_next - t_curr
                all_intervals.append(dt)
                if leg_curr == "left" and leg_next == "right":
                    l_to_r_intervals.append(dt)
                elif leg_curr == "right" and leg_next == "left":
                    r_to_l_intervals.append(dt)

        valid_count = len(all_intervals)
        avg_interval = round(sum(all_intervals) / valid_count, 3) if valid_count > 0 else None
        l_to_r_avg = round(sum(l_to_r_intervals) / len(l_to_r_intervals), 3) if l_to_r_intervals else None
        r_to_l_avg = round(sum(r_to_l_intervals) / len(r_to_l_intervals), 3) if r_to_l_intervals else None

        return {
            "average_interval_seconds": avg_interval,
            "left_to_right_seconds": l_to_r_avg,
            "right_to_left_seconds": r_to_l_avg,
            "valid_intervals": valid_count,
        }

    def calculate_cadence(self, step_timing: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate cadence in steps per minute using valid alternating contact intervals.

        Args:
            step_timing: Output from calculate_step_timing.

        Returns:
            Dictionary with 'steps_per_minute' (float or None).
        """
        avg_interval = step_timing.get("average_interval_seconds")
        valid_intervals = step_timing.get("valid_intervals", 0)

        if avg_interval is not None and avg_interval > 0.05 and valid_intervals >= 1:
            spm = round(60.0 / avg_interval, 1)
            # Reasonable athletic human running cadence check (50 to 300 spm)
            if 50.0 <= spm <= 300.0:
                return {"steps_per_minute": spm}

        return {"steps_per_minute": None}

    def calculate_symmetry(
        self,
        stance_time: Dict[str, Any],
        swing_time: Dict[str, Any],
        step_timing: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculate absolute differences between left and right gait parameters.

        Args:
            stance_time: Stance duration dict.
            swing_time: Swing duration dict.
            step_timing: Step interval dict.

        Returns:
            Dictionary with symmetry difference metrics (reporting layer only).
        """
        # Stance symmetry
        l_stance = stance_time.get("left", {}).get("avg_seconds")
        r_stance = stance_time.get("right", {}).get("avg_seconds")
        stance_diff = (
            round(abs(l_stance - r_stance), 3)
            if (l_stance is not None and r_stance is not None)
            else None
        )

        # Swing symmetry
        l_swing = swing_time.get("left", {}).get("avg_seconds")
        r_swing = swing_time.get("right", {}).get("avg_seconds")
        swing_diff = (
            round(abs(l_swing - r_swing), 3)
            if (l_swing is not None and r_swing is not None)
            else None
        )

        # Step timing symmetry
        l_to_r = step_timing.get("left_to_right_seconds")
        r_to_l = step_timing.get("right_to_left_seconds")
        step_diff = (
            round(abs(l_to_r - r_to_l), 3)
            if (l_to_r is not None and r_to_l is not None)
            else None
        )

        return {
            "stance_difference_seconds": stance_diff,
            "swing_difference_seconds": swing_diff,
            "step_timing_difference_seconds": step_diff,
        }

    def calculate_joint_angle_statistics(self, angles_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract min, max, and average joint angles preserving existing calculation methodology.

        Args:
            angles_payload: Payload from joint_angles.json.

        Returns:
            Dictionary mapping joint names to min/max/average angles.
        """
        target_joints = ["left_knee", "right_knee", "left_hip", "right_hip", "left_ankle", "right_ankle"]
        joint_stats: Dict[str, Any] = {}

        # First attempt to read existing precomputed joint_statistics
        precomputed = angles_payload.get("joint_statistics", {})
        frames = angles_payload.get("frames", [])

        for joint in target_joints:
            if joint in precomputed:
                stat = precomputed[joint]
                joint_stats[joint] = {
                    "min": stat.get("min"),
                    "max": stat.get("max"),
                    "average": stat.get("avg"),
                }
            else:
                # Compute directly from frame series
                vals = [
                    f["angles"][joint]
                    for f in frames
                    if f.get("angles") and f["angles"].get(joint) is not None
                ]
                if vals:
                    joint_stats[joint] = {
                        "min": round(min(vals), 2),
                        "max": round(max(vals), 2),
                        "average": round(sum(vals) / len(vals), 2),
                    }
                else:
                    joint_stats[joint] = {"min": None, "max": None, "average": None}

        return joint_stats

    def calculate_running_cycles(
        self,
        left_events: List[PhaseEvent],
        right_events: List[PhaseEvent],
    ) -> Dict[str, Any]:
        """
        Identify full gait cycles (FOOT_CONTACT/STANCE -> TOE_OFF -> SWING -> next contact/stance)
        for both legs and compute cycle durations.

        Args:
            left_events: Phase events for left leg.
            right_events: Phase events for right leg.

        Returns:
            Dictionary with cycle statistics.
        """
        cycle_durations: List[float] = []

        for leg_events in [left_events, right_events]:
            # Look for sequence of phases: (Contact/Stance) -> (Toe-off) -> (Swing) -> (Contact/Stance)
            for i in range(len(leg_events) - 3):
                e1 = leg_events[i]
                e2 = leg_events[i + 1]
                e3 = leg_events[i + 2]
                e4 = leg_events[i + 3]

                if (
                    e1.phase in ("FOOT_CONTACT", "STANCE")
                    and e2.phase == "TOE_OFF"
                    and e3.phase == "SWING"
                    and e4.phase in ("FOOT_CONTACT", "STANCE")
                ):
                    dt = e4.start_timestamp - e1.start_timestamp
                    if dt > 0.1:  # Biomechanically plausible cycle duration (> 100ms)
                        cycle_durations.append(dt)

        valid_cycles = len(cycle_durations)
        if valid_cycles == 0:
            return {
                "valid_cycles": 0,
                "average_duration_seconds": None,
                "min_duration_seconds": None,
                "max_duration_seconds": None,
            }

        return {
            "valid_cycles": valid_cycles,
            "average_duration_seconds": round(sum(cycle_durations) / valid_cycles, 3),
            "min_duration_seconds": round(min(cycle_durations), 3),
            "max_duration_seconds": round(max(cycle_durations), 3),
        }

    def compute_all_metrics(
        self,
        landmarks_payload: Dict[str, Any],
        angles_payload: Dict[str, Any],
        phases_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compute complete running performance metrics bundle from raw input JSON payloads.

        Args:
            landmarks_payload: Data from smoothed_landmarks.json.
            angles_payload: Data from joint_angles.json.
            phases_payload: Data from motion_phases.json.

        Returns:
            Standardized metrics dictionary ready for JSON export.
        """
        # Resolve FPS and total frames
        total_frames = (
            phases_payload.get("total_frames")
            or landmarks_payload.get("total_frames")
            or len(phases_payload.get("frames", []))
        )
        fps = (
            angles_payload.get("fps")
            or landmarks_payload.get("fps")
            or self.fps
        )
        if fps and fps > 0:
            self.fps = fps
            duration_seconds = round(total_frames / self.fps, 2)
        else:
            duration_seconds = None

        phase_frames = phases_payload.get("frames", [])
        valid_pose_frames = phases_payload.get(
            "valid_frames",
            len([f for f in phase_frames if f.get("left_phase") or f.get("right_phase")]),
        )

        # 1. Extract continuous phase events
        left_events = self.extract_phase_events(phase_frames, "left")
        right_events = self.extract_phase_events(phase_frames, "right")

        # 2. Stance & Swing times
        stance_time = {
            "left": self.calculate_phase_durations(left_events, "STANCE"),
            "right": self.calculate_phase_durations(right_events, "STANCE"),
        }
        swing_time = {
            "left": self.calculate_phase_durations(left_events, "SWING"),
            "right": self.calculate_phase_durations(right_events, "SWING"),
        }

        # 3. Foot contact events
        left_contacts = self.count_transition_events(left_events, "FOOT_CONTACT")
        right_contacts = self.count_transition_events(right_events, "FOOT_CONTACT")
        foot_contact_events = {
            "left": left_contacts,
            "right": right_contacts,
            "total": left_contacts + right_contacts,
        }

        # 4. Toe-off events
        left_toe_off = self.count_transition_events(left_events, "TOE_OFF")
        right_toe_off = self.count_transition_events(right_events, "TOE_OFF")
        toe_off_events = {
            "left": left_toe_off,
            "right": right_toe_off,
            "total": left_toe_off + right_toe_off,
        }

        # 5. Step timing
        step_timing = self.calculate_step_timing(left_events, right_events)

        # 6. Cadence
        cadence = self.calculate_cadence(step_timing)

        # 7. Left/Right Symmetry
        symmetry = self.calculate_symmetry(stance_time, swing_time, step_timing)

        # 8. Joint angle statistics
        joint_angles = self.calculate_joint_angle_statistics(angles_payload)

        # 9. Running cycle summary
        running_cycle = self.calculate_running_cycles(left_events, right_events)

        # 10. Data quality
        pose_validity_percent = (
            round((valid_pose_frames / total_frames) * 100, 2)
            if total_frames > 0
            else 0.0
        )
        total_phase_events_used = len(left_events) + len(right_events)

        data_quality = {
            "total_frames": total_frames,
            "valid_pose_frames": valid_pose_frames,
            "pose_validity_percent": pose_validity_percent,
            "phase_events_used": total_phase_events_used,
            "ignored_events": 0,
        }

        return {
            "video": {
                "total_frames": total_frames,
                "fps": round(self.fps, 2) if self.fps else None,
                "duration_seconds": duration_seconds,
            },
            "stance_time": stance_time,
            "swing_time": swing_time,
            "foot_contact_events": foot_contact_events,
            "toe_off_events": toe_off_events,
            "step_timing": step_timing,
            "cadence": cadence,
            "symmetry": symmetry,
            "joint_angles": joint_angles,
            "running_cycle": running_cycle,
            "data_quality": data_quality,
        }
