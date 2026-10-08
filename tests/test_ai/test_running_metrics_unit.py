"""
Unit tests for RunningMetricsCalculator
"""

import pytest
from ai_engine.pose_analysis.running_metrics import RunningMetricsCalculator, PhaseEvent


def test_phase_event_extraction():
    calc = RunningMetricsCalculator(fps=30.0)
    frames = [
        {"frame_index": 0, "timestamp": 0.0, "left_phase": "STANCE", "right_phase": "SWING"},
        {"frame_index": 1, "timestamp": 0.033, "left_phase": "STANCE", "right_phase": "SWING"},
        {"frame_index": 2, "timestamp": 0.067, "left_phase": "STANCE", "right_phase": "SWING"},
        {"frame_index": 3, "timestamp": 0.100, "left_phase": "TOE_OFF", "right_phase": "FOOT_CONTACT"},
        {"frame_index": 4, "timestamp": 0.133, "left_phase": "SWING", "right_phase": "STANCE"},
    ]

    left_events = calc.extract_phase_events(frames, "left")
    assert len(left_events) == 3
    assert left_events[0].phase == "STANCE"
    assert left_events[0].frame_count == 3
    assert left_events[1].phase == "TOE_OFF"
    assert left_events[1].frame_count == 1
    assert left_events[2].phase == "SWING"
    assert left_events[2].frame_count == 1


def test_step_timing_and_cadence():
    calc = RunningMetricsCalculator(fps=30.0)
    # Alternating contacts every 0.35s (~171 steps/min)
    left_events = [
        PhaseEvent("FOOT_CONTACT", "left", 0, 1, 2, 0.0, 0.033),
        PhaseEvent("FOOT_CONTACT", "left", 20, 21, 2, 0.70, 0.733),
    ]
    right_events = [
        PhaseEvent("FOOT_CONTACT", "right", 10, 11, 2, 0.35, 0.383),
        PhaseEvent("FOOT_CONTACT", "right", 30, 31, 2, 1.05, 1.083),
    ]

    timing = calc.calculate_step_timing(left_events, right_events)
    assert timing["valid_intervals"] == 3
    assert pytest.approx(timing["average_interval_seconds"], 0.01) == 0.35
    assert pytest.approx(timing["left_to_right_seconds"], 0.01) == 0.35
    assert pytest.approx(timing["right_to_left_seconds"], 0.01) == 0.35

    cadence = calc.calculate_cadence(timing)
    assert cadence["steps_per_minute"] is not None
    assert pytest.approx(cadence["steps_per_minute"], 1.0) == 171.4


def test_insufficient_data_safety():
    calc = RunningMetricsCalculator(fps=None)
    timing = calc.calculate_step_timing([], [])
    assert timing["valid_intervals"] == 0
    assert timing["average_interval_seconds"] is None

    cadence = calc.calculate_cadence(timing)
    assert cadence["steps_per_minute"] is None

    durations = calc.calculate_phase_durations([], "STANCE")
    assert durations["count"] == 0
    assert durations["min_frames"] is None
    assert durations["min_seconds"] is None
