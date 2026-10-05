"""
Running Analysis Report Generator Module
========================================
This module compiles precomputed AI analysis outputs (pose landmarks, joint angles,
motion phases, and running metrics) into a comprehensive, structured, and standardized
athletic running analysis report.

Design Principles:
- Strictly measurement-based (no medical diagnoses, subjective claims, or health assessments).
- No invented or fabricated data: missing or unmeasurable metrics are explicitly represented as `null`.
- Robust data-quality assessment and contextual limitation warnings.
- Clean JSON output ready for downstream consumers (REST APIs, visualization dashboards, storage).
- Human-readable terminal summaries for verification and CLI workflows.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional


class RunningReportGenerator:
    """
    Generates a structured running biomechanics and performance report
    from pipeline analysis results.
    """

    REPORT_VERSION = "1.0"
    ANALYSIS_TYPE = "running_analysis"
    SPORT = "running"

    def __init__(self):
        pass

    def generate_report(
        self,
        running_metrics: Dict[str, Any],
        motion_phases: Optional[Dict[str, Any]] = None,
        joint_angles: Optional[Dict[str, Any]] = None,
        smoothed_landmarks: Optional[Dict[str, Any]] = None,
        video_metadata: Optional[Dict[str, Any]] = None,
        output_paths: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Compile all analysis results into a standardized report structure.

        Args:
            running_metrics: Metrics computed by RunningMetricsCalculator.
            motion_phases: Motion phase detection output.
            joint_angles: Joint angle kinematics output.
            smoothed_landmarks: Smoothed pose landmarks output.
            video_metadata: Optional dictionary with video details (filename, width, height, etc.).
            output_paths: Optional dictionary mapping output names to relative/absolute file paths.

        Returns:
            Structured dictionary representing the complete analysis report.
        """
        now_utc = datetime.now(timezone.utc).isoformat()

        # 1. Report Metadata
        report_meta = {
            "version": self.REPORT_VERSION,
            "analysis_type": self.ANALYSIS_TYPE,
            "sport": self.SPORT,
            "generated_at": now_utc,
        }

        # 2. Video Information
        video_info = self._extract_video_info(
            running_metrics=running_metrics,
            motion_phases=motion_phases,
            joint_angles=joint_angles,
            video_metadata=video_metadata,
        )

        # 3. Data Quality
        data_quality = self._extract_data_quality(running_metrics)

        # 4. Motion Phase Summary
        phase_summary = self._extract_motion_phase_summary(motion_phases)

        # 5. Timing Metrics (Stance, Swing, Contacts, Toe-Offs)
        stance_time = running_metrics.get("stance_time", {})
        swing_time = running_metrics.get("swing_time", {})
        foot_contacts = running_metrics.get("foot_contact_events", {
            "left": 0, "right": 0, "total": 0
        })
        toe_offs = running_metrics.get("toe_off_events", {
            "left": 0, "right": 0, "total": 0
        })

        # 6. Step Timing & Cadence
        step_timing = running_metrics.get("step_timing", {
            "average_interval_seconds": None,
            "left_to_right_seconds": None,
            "right_to_left_seconds": None,
            "valid_intervals": 0,
        })
        cadence = running_metrics.get("cadence", {
            "steps_per_minute": None
        })

        # 7. Left/Right Symmetry
        symmetry = running_metrics.get("symmetry", {
            "stance_difference_seconds": None,
            "swing_difference_seconds": None,
            "step_timing_difference_seconds": None,
        })

        # 8. Joint Angle Statistics
        joint_angle_stats = running_metrics.get("joint_angles", {})
        if not joint_angle_stats and joint_angles and "joint_statistics" in joint_angles:
            joint_angle_stats = joint_angles.get("joint_statistics", {})

        # 9. Running Cycles
        running_cycle = running_metrics.get("running_cycle", {
            "valid_cycles": 0,
            "average_duration_seconds": None,
            "min_duration_seconds": None,
            "max_duration_seconds": None,
        })
        # Add status indicator if valid_cycles is 0
        if running_cycle.get("valid_cycles", 0) == 0 and "status" not in running_cycle:
            running_cycle = dict(running_cycle)
            running_cycle["status"] = "insufficient_data"

        # 10. Output References
        outputs_ref = self._format_output_references(output_paths)

        # 11. Limitations & Warnings
        warnings = self._generate_warnings(
            data_quality=data_quality,
            cadence=cadence,
            step_timing=step_timing,
            running_cycle=running_cycle,
            symmetry=symmetry,
            video_info=video_info,
        )

        report = {
            "report": report_meta,
            "video": video_info,
            "data_quality": data_quality,
            "motion_phases": phase_summary,
            "stance_time": stance_time,
            "swing_time": swing_time,
            "foot_contact_events": foot_contacts,
            "toe_off_events": toe_offs,
            "step_timing": step_timing,
            "cadence": cadence,
            "symmetry": symmetry,
            "joint_angles": joint_angle_stats,
            "running_cycle": running_cycle,
            "outputs": outputs_ref,
            "warnings": warnings,
        }

        return report

    def _extract_video_info(
        self,
        running_metrics: Dict[str, Any],
        motion_phases: Optional[Dict[str, Any]],
        joint_angles: Optional[Dict[str, Any]],
        video_metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Extract and consolidate video metadata from metrics or raw video inspection."""
        vm = video_metadata or {}
        rm_video = running_metrics.get("video", {})
        
        filename = (
            vm.get("filename")
            or (motion_phases.get("source_video") if motion_phases else None)
            or (joint_angles.get("source_video") if joint_angles else None)
            or "running1.avi"
        )
        total_frames = (
            vm.get("total_frames")
            or rm_video.get("total_frames")
            or (motion_phases.get("total_frames") if motion_phases else None)
            or (joint_angles.get("total_frames") if joint_angles else None)
        )
        fps = (
            vm.get("fps")
            or rm_video.get("fps")
            or (joint_angles.get("fps") if joint_angles else None)
        )
        duration_seconds = (
            vm.get("duration_seconds")
            or rm_video.get("duration_seconds")
            or (round(total_frames / fps, 2) if total_frames and fps and fps > 0 else None)
        )

        res = {
            "filename": filename,
            "total_frames": total_frames,
            "fps": fps,
            "duration_seconds": duration_seconds,
        }
        if "width" in vm and vm["width"] is not None:
            res["width"] = int(vm["width"])
        if "height" in vm and vm["height"] is not None:
            res["height"] = int(vm["height"])

        return res

    def _extract_data_quality(self, running_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and structure data quality metrics."""
        dq = running_metrics.get("data_quality", {})
        total_frames = dq.get("total_frames", 0)
        valid_pose_frames = dq.get("valid_pose_frames", 0)
        coverage_pct = dq.get("pose_validity_percent")
        if coverage_pct is None and total_frames > 0:
            coverage_pct = round((valid_pose_frames / total_frames) * 100.0, 2)

        quality_warning = False
        if coverage_pct is not None and coverage_pct < 60.0:
            quality_warning = True

        return {
            "total_frames": total_frames,
            "valid_pose_frames": valid_pose_frames,
            "pose_coverage_percent": coverage_pct,
            "phase_events_used": dq.get("phase_events_used", 0),
            "ignored_events": dq.get("ignored_events", 0),
            "quality_warning": quality_warning,
        }

    def _extract_motion_phase_summary(self, motion_phases: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract phase distribution counts for both left and right legs."""
        default_phases = {
            "FOOT_CONTACT": 0,
            "STANCE": 0,
            "TOE_OFF": 0,
            "SWING": 0,
        }
        if not motion_phases or "phase_distribution" not in motion_phases:
            return {"left": default_phases.copy(), "right": default_phases.copy()}

        dist = motion_phases["phase_distribution"]
        left_dist = dist.get("left_leg", {})
        right_dist = dist.get("right_leg", {})

        left_summary = {
            "FOOT_CONTACT": left_dist.get("FOOT_CONTACT", 0),
            "STANCE": left_dist.get("STANCE", 0),
            "TOE_OFF": left_dist.get("TOE_OFF", 0),
            "SWING": left_dist.get("SWING", 0),
        }
        right_summary = {
            "FOOT_CONTACT": right_dist.get("FOOT_CONTACT", 0),
            "STANCE": right_dist.get("STANCE", 0),
            "TOE_OFF": right_dist.get("TOE_OFF", 0),
            "SWING": right_dist.get("SWING", 0),
        }

        return {"left": left_summary, "right": right_summary}

    def _format_output_references(self, output_paths: Optional[Dict[str, str]]) -> Dict[str, str]:
        """Format and provide references to generated artifact paths."""
        defaults = {
            "annotated_video": "data/outputs/pose_test/annotated_running_analysis.mp4",
            "metrics": "data/outputs/pose_test/running_metrics.json",
            "report": "data/outputs/pose_test/running_analysis_report.json",
        }
        if output_paths:
            defaults.update(output_paths)
        return defaults

    def _generate_warnings(
        self,
        data_quality: Dict[str, Any],
        cadence: Dict[str, Any],
        step_timing: Dict[str, Any],
        running_cycle: Dict[str, Any],
        symmetry: Dict[str, Any],
        video_info: Dict[str, Any],
    ) -> List[str]:
        """
        Dynamically determine appropriate warnings based on data availability and quality.
        Ensures purely factual statements without medical or health claims.
        """
        warnings = []

        # Coverage warning
        cov = data_quality.get("pose_coverage_percent")
        valid_frames = data_quality.get("valid_pose_frames", 0)
        total_frames = data_quality.get("total_frames", 0)
        if cov is not None and cov < 50.0:
            warnings.append(
                f"Low pose coverage: only {cov:.2f}% of video frames ({valid_frames}/{total_frames}) "
                f"contained valid pose detections."
            )

        # Cadence warning
        if cadence.get("steps_per_minute") is None:
            warnings.append("Insufficient alternating contact events for cadence estimation.")

        # Step timing warning
        if step_timing.get("average_interval_seconds") is None:
            warnings.append("Insufficient alternating foot strike events for step interval estimation.")

        # Running cycles warning
        if running_cycle.get("valid_cycles", 0) == 0:
            warnings.append("No complete running cycles detected in the analyzed sequence.")

        # Camera calibration / spatial measurement warning
        warnings.append(
            "Camera calibration unavailable: spatial measurements (stride length, real-world distance, speed) "
            "cannot be calculated from uncalibrated 2D monocular video."
        )

        return warnings

    @staticmethod
    def save_report(report: Dict[str, Any], output_path: str) -> None:
        """Save the report dictionary to a JSON file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    @staticmethod
    def format_terminal_summary(report: Dict[str, Any]) -> str:
        """
        Format a human-readable terminal summary matching the specification.
        """
        video = report.get("video", {})
        dq = report.get("data_quality", {})
        stance = report.get("stance_time", {})
        swing = report.get("swing_time", {})
        contacts = report.get("foot_contact_events", {})
        toe_offs = report.get("toe_off_events", {})
        step_timing = report.get("step_timing", {})
        cadence = report.get("cadence", {})
        symmetry = report.get("symmetry", {})
        angles = report.get("joint_angles", {})
        cycles = report.get("running_cycle", {})
        warnings = report.get("warnings", [])
        outputs = report.get("outputs", {})

        def fmt_val(val, unit="", ndigits=2):
            if val is None:
                return "insufficient_data (null)"
            if isinstance(val, float):
                return f"{round(val, ndigits)}{unit}"
            return f"{val}{unit}"

        # Stance formatting
        left_stance = stance.get("left", {})
        right_stance = stance.get("right", {})
        left_st_str = f"avg {fmt_val(left_stance.get('avg_seconds'), 's', 3)} ({left_stance.get('count', 0)} events, range: {fmt_val(left_stance.get('min_seconds'), 's', 3)} - {fmt_val(left_stance.get('max_seconds'), 's', 3)})"
        right_st_str = f"avg {fmt_val(right_stance.get('avg_seconds'), 's', 3)} ({right_stance.get('count', 0)} events, range: {fmt_val(right_stance.get('min_seconds'), 's', 3)} - {fmt_val(right_stance.get('max_seconds'), 's', 3)})"

        # Swing formatting
        left_swing = swing.get("left", {})
        right_swing = swing.get("right", {})
        left_sw_str = f"avg {fmt_val(left_swing.get('avg_seconds'), 's', 3)} ({left_swing.get('count', 0)} events, range: {fmt_val(left_swing.get('min_seconds'), 's', 3)} - {fmt_val(left_swing.get('max_seconds'), 's', 3)})"
        right_sw_str = f"avg {fmt_val(right_swing.get('avg_seconds'), 's', 3)} ({right_swing.get('count', 0)} events, range: {fmt_val(right_swing.get('min_seconds'), 's', 3)} - {fmt_val(right_swing.get('max_seconds'), 's', 3)})"

        # Step timing formatting
        avg_step = step_timing.get("average_interval_seconds")
        step_str = fmt_val(avg_step, "s", 3)

        # Cadence formatting
        cad_spm = cadence.get("steps_per_minute")
        cad_str = fmt_val(cad_spm, " spm", 1)

        # Symmetry formatting
        st_diff = symmetry.get("stance_difference_seconds")
        sw_diff = symmetry.get("swing_difference_seconds")
        st_diff_str = fmt_val(st_diff, "s", 3)
        sw_diff_str = fmt_val(sw_diff, "s", 3)

        # Joint angle formatting helper
        def fmt_angle(j_key):
            j_data = angles.get(j_key, {})
            if not j_data or j_data.get("average") is None:
                return "N/A"
            return f"avg {j_data.get('average', 0):.1f}° (min {j_data.get('min', 0):.1f}°, max {j_data.get('max', 0):.1f}°)"

        # Warnings list formatting
        warn_lines = "\n".join(f"  - {w}" for w in warnings) if warnings else "  (None)"

        report_path = outputs.get("report", "data/outputs/pose_test/running_analysis_report.json")

        summary = f"""==================================================
        RUNNING ANALYSIS REPORT
==================================================

VIDEO
Frames            : {video.get('total_frames', 'N/A')}
FPS               : {video.get('fps', 'N/A')}
Duration          : {fmt_val(video.get('duration_seconds'), 's', 2)}
Resolution        : {video.get('width', 'N/A')}x{video.get('height', 'N/A')}

DATA QUALITY
Pose Coverage     : {fmt_val(dq.get('pose_coverage_percent'), '%', 2)} ({dq.get('valid_pose_frames', 0)}/{dq.get('total_frames', 0)} frames)
Phase Events Used : {dq.get('phase_events_used', 0)}
Quality Warning   : {'YES (Low Coverage)' if dq.get('quality_warning') else 'NO'}

STANCE TIME
Left              : {left_st_str}
Right             : {right_st_str}

SWING TIME
Left              : {left_sw_str}
Right             : {right_sw_str}

CONTACTS
Left              : {contacts.get('left', 0)}
Right             : {contacts.get('right', 0)}
Total             : {contacts.get('total', 0)}

TOE-OFFS
Left              : {toe_offs.get('left', 0)}
Right             : {toe_offs.get('right', 0)}
Total             : {toe_offs.get('total', 0)}

STEP TIMING
Average Interval  : {step_str}
Valid Intervals   : {step_timing.get('valid_intervals', 0)}

CADENCE
Cadence           : {cad_str}

SYMMETRY
Stance Difference : {st_diff_str}
Swing Difference  : {sw_diff_str}

JOINT ANGLES
Left Knee         : {fmt_angle('left_knee')}
Right Knee        : {fmt_angle('right_knee')}
Left Hip          : {fmt_angle('left_hip')}
Right Hip         : {fmt_angle('right_hip')}
Left Ankle        : {fmt_angle('left_ankle')}
Right Ankle       : {fmt_angle('right_ankle')}

RUNNING CYCLES
Valid Cycles      : {cycles.get('valid_cycles', 0)}
Average Duration  : {fmt_val(cycles.get('average_duration_seconds'), 's', 3)}
Cycle Status      : {cycles.get('status', 'complete' if cycles.get('valid_cycles', 0) > 0 else 'insufficient_data')}

WARNINGS
{warn_lines}

OUTPUTS
Report JSON       : {report_path}
Metrics JSON      : {outputs.get('metrics', 'N/A')}
Annotated Video   : {outputs.get('annotated_video', 'N/A')}
=================================================="""
        return summary
