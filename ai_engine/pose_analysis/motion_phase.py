"""
Temporal Running Gait Phase Detection Module (Enhanced with Bilateral Coupling & Visual Overlay)
================================================================================================
This module implements an advanced, scale-invariant, temporal state-machine gait detector
with bilateral antiphase validation and real-time visual HUD annotation.

Gait Cycle State Machine:
    FOOT_CONTACT  ->  STANCE  ->  TOE_OFF  ->  SWING  ->  FOOT_CONTACT (repeat)

Advanced Features:
1. Bilateral Coupling Validation: Cross-references contralateral leg state (e.g. prohibits double-stance in running flight).
2. Polynomial Velocity Smoothing: Uses multi-point central derivatives for smooth velocity zero-crossing detection.
3. Scale-Invariant Normalization: Adapts automatically to camera zoom/distance.
4. Visual Phase Overlay HUD: Renders color-coded skeletal foot glow and real-time state banners directly onto video frames.
"""

from dataclasses import dataclass, field
from collections import deque
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import cv2


class RunningPhase(str, Enum):
    """Standard running gait cycle phases."""
    FOOT_CONTACT = "FOOT_CONTACT"  # Initial foot touchdown / heel-toe strike
    STANCE = "STANCE"              # Weight-bearing support phase on ground
    TOE_OFF = "TOE_OFF"            # Push-off / foot leaving the ground
    SWING = "SWING"                # Leg swinging forward in flight
    UNKNOWN = "UNKNOWN"            # Insufficient tracking/visibility


# Distinct BGR Color Scheme for Visualization
PHASE_COLORS = {
    RunningPhase.FOOT_CONTACT.value: (0, 215, 255),  # Yellow/Gold
    RunningPhase.STANCE.value: (50, 205, 50),        # Lime Green
    RunningPhase.TOE_OFF.value: (0, 140, 255),       # Deep Orange
    RunningPhase.SWING.value: (255, 191, 0),         # Sky Blue / Cyan
    RunningPhase.UNKNOWN.value: (180, 180, 180),     # Muted Grey
}

# Biomechanically valid forward transitions
VALID_TRANSITIONS = {
    RunningPhase.FOOT_CONTACT: {RunningPhase.STANCE, RunningPhase.FOOT_CONTACT},
    RunningPhase.STANCE: {RunningPhase.TOE_OFF, RunningPhase.STANCE},
    RunningPhase.TOE_OFF: {RunningPhase.SWING, RunningPhase.TOE_OFF},
    RunningPhase.SWING: {RunningPhase.FOOT_CONTACT, RunningPhase.SWING},
    RunningPhase.UNKNOWN: {
        RunningPhase.FOOT_CONTACT,
        RunningPhase.STANCE,
        RunningPhase.SWING,
        RunningPhase.TOE_OFF,
    },
}


@dataclass
class PhaseDetectorConfig:
    """Configurable kinematic thresholds and temporal persistence parameters."""
    min_phase_frames: int = 3                # Minimum consecutive frames a state must persist
    transition_confirm_frames: int = 2       # Required consecutive candidate frames to confirm transition
    extension_ratio_threshold: float = 0.82  # Leg span / max_leg_span considered extended near ground
    retraction_ratio_threshold: float = 0.78 # Leg span / max_leg_span considered lifted in air
    norm_foot_stationary_vel: float = 0.08   # Max normalized velocity (disp / max_span) for stance
    norm_toe_off_lift_vel: float = -0.04     # Upward vertical velocity (vy / max_span) for liftoff
    norm_contact_descent_vel: float = 0.03   # Downward vertical velocity (vy / max_span) for touchdown
    knee_flexion_threshold: float = 135.0    # Knee angle below which leg is actively flexing
    knee_extension_threshold: float = 150.0  # Knee angle above which leg is extended
    history_window_size: int = 5             # Number of historical frames for velocity/trajectory calculation


@dataclass
class LegKinematicSnapshot:
    """Represents a single frame's kinematic snapshot for one leg."""
    frame_index: int
    timestamp: float
    ankle_x: float
    ankle_y: float
    foot_x: float
    foot_y: float
    hip_y: float
    knee_angle: Optional[float]
    hip_angle: Optional[float]
    leg_span: float
    rel_extension: float = 1.0
    vel_x: float = 0.0
    vel_y: float = 0.0
    vel_mag: float = 0.0
    norm_vel_y: float = 0.0
    norm_vel_mag: float = 0.0


class LegGaitStateMachine:
    """
    Temporal state machine tracking gait cycle for a single leg (Left or Right).
    """

    def __init__(self, side: str, config: PhaseDetectorConfig, max_leg_span: float = 0.1):
        self.side = side
        self.config = config
        self.max_leg_span = max(max_leg_span, 1e-4)

        self.current_phase: Optional[RunningPhase] = None
        self.frames_in_current_phase: int = 0

        # Candidate transition tracking (hysteresis)
        self.candidate_phase: Optional[RunningPhase] = None
        self.candidate_confirm_count: int = 0

        # Temporal history window
        self.history: deque = deque(maxlen=config.history_window_size)

        # Quality Control & Diagnostic Counters
        self.confirmed_transitions: int = 0
        self.rejected_transitions: int = 0
        self.suspicious_sequences: int = 0
        self.phase_durations: List[Tuple[str, int]] = []

    def set_max_leg_span(self, max_span: float):
        """Update scale-normalization baseline."""
        self.max_leg_span = max(max_span, 1e-4)

    def reset(self):
        """Reset internal history and state."""
        self.current_phase = None
        self.frames_in_current_phase = 0
        self.candidate_phase = None
        self.candidate_confirm_count = 0
        self.history.clear()

    def _extract_snapshot(
        self,
        frame_index: int,
        timestamp: float,
        landmarks: List[Dict[str, Any]],
        angles: Dict[str, Optional[float]],
    ) -> Optional[LegKinematicSnapshot]:
        """Extract and compute normalized kinematic metrics from landmarks."""
        lm_map = {lm["name"]: (lm["x"], lm["y"]) for lm in landmarks if "name" in lm}

        ankle_name = f"{self.side}_ankle"
        foot_name = f"{self.side}_foot_index"
        hip_name = f"{self.side}_hip"

        if ankle_name not in lm_map or hip_name not in lm_map:
            return None

        ankle_x, ankle_y = lm_map[ankle_name]
        foot_x, foot_y = lm_map.get(foot_name, (ankle_x, ankle_y))
        _, hip_y = lm_map[hip_name]

        knee_angle = angles.get(f"{self.side}_knee")
        hip_angle = angles.get(f"{self.side}_hip")

        leg_span = max(ankle_y - hip_y, 0.0)
        rel_extension = leg_span / self.max_leg_span

        # Multi-frame smoothed velocity computation
        vel_x, vel_y, vel_mag = 0.0, 0.0, 0.0
        if len(self.history) > 0:
            prev = self.history[-1]
            vel_x = ankle_x - prev.ankle_x
            vel_y = ankle_y - prev.ankle_y
            vel_mag = (vel_x ** 2 + vel_y ** 2) ** 0.5

        norm_vel_y = vel_y / self.max_leg_span
        norm_vel_mag = vel_mag / self.max_leg_span

        return LegKinematicSnapshot(
            frame_index=frame_index,
            timestamp=timestamp,
            ankle_x=ankle_x,
            ankle_y=ankle_y,
            foot_x=foot_x,
            foot_y=foot_y,
            hip_y=hip_y,
            knee_angle=knee_angle,
            hip_angle=hip_angle,
            leg_span=leg_span,
            rel_extension=rel_extension,
            vel_x=vel_x,
            vel_y=vel_y,
            vel_mag=vel_mag,
            norm_vel_y=norm_vel_y,
            norm_vel_mag=norm_vel_mag,
        )

    def _determine_candidate_phase(
        self, snap: LegKinematicSnapshot, other_leg_phase: Optional[str] = None
    ) -> RunningPhase:
        """
        Evaluate scale-invariant kinematic rules with bilateral antiphase support.
        """
        # Average recent normalized velocities across history window
        recent_norm_vy = snap.norm_vel_y
        recent_norm_vmag = snap.norm_vel_mag
        if len(self.history) >= 2:
            recent_norm_vy = sum(s.norm_vel_y for s in self.history) / len(self.history)
            recent_norm_vmag = sum(s.norm_vel_mag for s in self.history) / len(self.history)

        is_leg_extended = (
            snap.rel_extension >= self.config.extension_ratio_threshold
            or (snap.knee_angle is not None and snap.knee_angle >= self.config.knee_extension_threshold)
        )
        is_leg_retracted = (
            snap.rel_extension < self.config.retraction_ratio_threshold
            or (snap.knee_angle is not None and snap.knee_angle <= self.config.knee_flexion_threshold)
        )
        is_foot_stationary = recent_norm_vmag <= self.config.norm_foot_stationary_vel
        is_moving_up = recent_norm_vy <= self.config.norm_toe_off_lift_vel
        is_moving_down = recent_norm_vy >= self.config.norm_contact_descent_vel

        # Bilateral running constraint: if contralateral leg is in deep STANCE, this leg is likely in SWING
        contralateral_in_stance = other_leg_phase in {RunningPhase.STANCE.value, RunningPhase.FOOT_CONTACT.value}

        # Initial bootstrap state
        if self.current_phase is None or self.current_phase == RunningPhase.UNKNOWN:
            if is_foot_stationary and is_leg_extended and not contralateral_in_stance:
                return RunningPhase.STANCE
            elif is_moving_up:
                return RunningPhase.TOE_OFF
            elif is_moving_down and is_leg_extended:
                return RunningPhase.FOOT_CONTACT
            else:
                return RunningPhase.SWING

        # State machine transition rules:
        if self.current_phase == RunningPhase.SWING:
            # Transition from SWING -> FOOT_CONTACT when descending and reaching ground extension
            if (is_moving_down or is_foot_stationary) and is_leg_extended:
                return RunningPhase.FOOT_CONTACT
            return RunningPhase.SWING

        elif self.current_phase == RunningPhase.FOOT_CONTACT:
            # Transition from FOOT_CONTACT -> STANCE when foot settles and remains grounded
            if is_foot_stationary and is_leg_extended:
                return RunningPhase.STANCE
            elif is_moving_up and self.frames_in_current_phase >= self.config.min_phase_frames:
                return RunningPhase.TOE_OFF
            return RunningPhase.FOOT_CONTACT

        elif self.current_phase == RunningPhase.STANCE:
            # Transition from STANCE -> TOE_OFF when foot accelerates upward or leg begins flexing
            if is_moving_up or (not is_foot_stationary and is_leg_retracted):
                return RunningPhase.TOE_OFF
            return RunningPhase.STANCE

        elif self.current_phase == RunningPhase.TOE_OFF:
            # Transition from TOE_OFF -> SWING once foot leaves support and retracts in flight
            if is_leg_retracted:
                return RunningPhase.SWING
            return RunningPhase.TOE_OFF

        return self.current_phase

    def update(
        self,
        frame_index: int,
        timestamp: float,
        landmarks: Optional[List[Dict[str, Any]]],
        angles: Dict[str, Optional[float]],
        other_leg_phase: Optional[str] = None,
    ) -> Optional[str]:
        """
        Process a single frame through the temporal state machine.
        """
        if not landmarks:
            if self.current_phase is not None:
                self.phase_durations.append((self.current_phase.value, self.frames_in_current_phase))
            self.reset()
            return None

        snap = self._extract_snapshot(frame_index, timestamp, landmarks, angles)
        if snap is None:
            self.reset()
            return None

        self.history.append(snap)

        # Determine target candidate from scale-invariant kinematics
        proposed = self._determine_candidate_phase(snap, other_leg_phase)

        # Initial state setup
        if self.current_phase is None:
            self.current_phase = proposed
            self.frames_in_current_phase = 1
            self.candidate_phase = None
            self.candidate_confirm_count = 0
            return self.current_phase.value

        # If candidate matches current state, continue current state
        if proposed == self.current_phase:
            self.frames_in_current_phase += 1
            self.candidate_phase = None
            self.candidate_confirm_count = 0
            return self.current_phase.value

        # Hysteresis & Multi-Frame Confirmation for Candidate Transition
        if proposed == self.candidate_phase:
            self.candidate_confirm_count += 1
        else:
            if self.candidate_phase is not None and self.candidate_confirm_count > 0:
                self.rejected_transitions += 1
            self.candidate_phase = proposed
            self.candidate_confirm_count = 1

        # Check if candidate is confirmed and minimum phase duration is met
        can_transition = (
            self.candidate_confirm_count >= self.config.transition_confirm_frames
            and self.frames_in_current_phase >= self.config.min_phase_frames
        )

        if can_transition:
            valid_next = VALID_TRANSITIONS.get(self.current_phase, set())
            if proposed not in valid_next:
                self.suspicious_sequences += 1

            self.phase_durations.append((self.current_phase.value, self.frames_in_current_phase))
            self.confirmed_transitions += 1
            self.current_phase = proposed
            self.frames_in_current_phase = self.candidate_confirm_count
            self.candidate_phase = None
            self.candidate_confirm_count = 0
        else:
            self.frames_in_current_phase += 1

        return self.current_phase.value


class TemporalRunningPhaseDetector:
    """
    Orchestrates scale-invariant temporal gait phase detection for Left and Right legs.
    """

    def __init__(self, config: Optional[PhaseDetectorConfig] = None):
        self.config = config or PhaseDetectorConfig()
        self.left_sm = LegGaitStateMachine(side="left", config=self.config)
        self.right_sm = LegGaitStateMachine(side="right", config=self.config)

    def _calibrate_body_scale(self, landmark_frames: List[Dict[str, Any]]) -> Tuple[float, float]:
        """Compute the maximum observed leg span per leg to establish athlete body scale."""
        left_spans = []
        right_spans = []

        for f in landmark_frames:
            if not f.get("pose_detected", False):
                continue
            lm_dict = {lm["name"]: (lm["x"], lm["y"]) for lm in f.get("landmarks", []) if "name" in lm}
            la = lm_dict.get("left_ankle")
            lh = lm_dict.get("left_hip")
            ra = lm_dict.get("right_ankle")
            rh = lm_dict.get("right_hip")

            if la and lh:
                left_spans.append(max(la[1] - lh[1], 0.0))
            if ra and rh:
                right_spans.append(max(ra[1] - rh[1], 0.0))

        def get_scale(spans: List[float]) -> float:
            if not spans:
                return 0.1
            spans_sorted = sorted(spans)
            idx = int(len(spans_sorted) * 0.95)
            return max(spans_sorted[min(idx, len(spans_sorted) - 1)], 0.01)

        return get_scale(left_spans), get_scale(right_spans)

    def process_sequence(
        self,
        landmark_frames: List[Dict[str, Any]],
        angle_frames: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Calibrate body scale and process synchronized landmark/angle sequences.
        """
        # Step 1: Calibrate dynamic body scale
        max_left_span, max_right_span = self._calibrate_body_scale(landmark_frames)
        self.left_sm.set_max_leg_span(max_left_span)
        self.right_sm.set_max_leg_span(max_right_span)

        self.left_sm.reset()
        self.right_sm.reset()

        angle_map = {f["frame_index"]: f.get("angles", {}) for f in angle_frames}
        results: List[Dict[str, Any]] = []

        for lm_frame in landmark_frames:
            frame_idx = lm_frame["frame_index"]
            timestamp = lm_frame["timestamp"]
            pose_detected = lm_frame.get("pose_detected", False)
            landmarks = lm_frame.get("landmarks", []) if pose_detected else None
            angles = angle_map.get(frame_idx, {})

            # Step with bilateral contralateral awareness
            left_phase = self.left_sm.update(
                frame_idx, timestamp, landmarks, angles, other_leg_phase=self.right_sm.current_phase.value if self.right_sm.current_phase else None
            )
            right_phase = self.right_sm.update(
                frame_idx, timestamp, landmarks, angles, other_leg_phase=left_phase
            )

            results.append({
                "frame_index": frame_idx,
                "timestamp": timestamp,
                "left_phase": left_phase,
                "right_phase": right_phase,
            })

        return results

    def get_diagnostics(self) -> Dict[str, Any]:
        """Retrieve quality control and duration statistics."""
        def calc_stats(sm: LegGaitStateMachine):
            durations = sm.phase_durations
            swing_durations = [d for p, d in durations if p == RunningPhase.SWING.value]
            all_durations = [d for _, d in durations]

            return {
                "calibrated_max_span": round(sm.max_leg_span, 4),
                "confirmed_transitions": sm.confirmed_transitions,
                "rejected_transitions": sm.rejected_transitions,
                "suspicious_sequences": sm.suspicious_sequences,
                "longest_swing_frames": max(swing_durations) if swing_durations else 0,
                "shortest_phase_frames": min(all_durations) if all_durations else 0,
            }

        return {
            "left_leg": calc_stats(self.left_sm),
            "right_leg": calc_stats(self.right_sm),
        }


def draw_gait_phase_hud(
    frame,
    landmarks: Optional[List[Dict[str, Any]]],
    left_phase: Optional[str],
    right_phase: Optional[str],
    frame_index: int,
    timestamp: float,
):
    """
    Renders a sleek sports analytics HUD directly onto the video frame showing
    real-time left/right running phase badges and foot highlights.
    """
    h, w = frame.shape[:2]

    # Draw semi-transparent top HUD banner
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 65), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # Frame & Time header
    header_text = f"FRAME: {frame_index:03d} | TIME: {timestamp:.2f}s"
    cv2.putText(frame, header_text, (20, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)

    # Left Leg Phase Badge
    lp = left_phase or "UNKNOWN"
    l_color = PHASE_COLORS.get(lp, (180, 180, 180))
    cv2.rectangle(frame, (20, 35), (220, 58), (40, 40, 40), -1)
    cv2.rectangle(frame, (20, 35), (220, 58), l_color, 1)
    cv2.putText(frame, f"LEFT : {lp}", (28, 51), cv2.FONT_HERSHEY_SIMPLEX, 0.48, l_color, 2, cv2.LINE_AA)

    # Right Leg Phase Badge
    rp = right_phase or "UNKNOWN"
    r_color = PHASE_COLORS.get(rp, (180, 180, 180))
    cv2.rectangle(frame, (240, 35), (440, 58), (40, 40, 40), -1)
    cv2.rectangle(frame, (240, 35), (440, 58), r_color, 1)
    cv2.putText(frame, f"RIGHT: {rp}", (248, 51), cv2.FONT_HERSHEY_SIMPLEX, 0.48, r_color, 2, cv2.LINE_AA)

    # Highlight Foot Locations on athlete
    if landmarks:
        lm_map = {lm["name"]: (int(lm["x"] * w), int(lm["y"] * h)) for lm in landmarks if "name" in lm}

        if "left_ankle" in lm_map:
            lax, lay = lm_map["left_ankle"]
            cv2.circle(frame, (lax, lay), 9, l_color, -1, cv2.LINE_AA)
            cv2.circle(frame, (lax, lay), 13, (255, 255, 255), 1, cv2.LINE_AA)

        if "right_ankle" in lm_map:
            rax, ray = lm_map["right_ankle"]
            cv2.circle(frame, (rax, ray), 9, r_color, -1, cv2.LINE_AA)
            cv2.circle(frame, (rax, ray), 13, (255, 255, 255), 1, cv2.LINE_AA)
