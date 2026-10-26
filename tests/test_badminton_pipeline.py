"""
End-to-End Integration Test for Badminton Overhead Clear AI Pipeline.
=====================================================================
Tests pose extraction, phase segmentation, rule evaluation, and artifact rendering.
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import cv2

from ai_engine.vision.pose.base_pose import PoseFrame, Keypoint
from sport_packs.badminton.plugin import BadmintonSportPack
from ai_engine.correction.rule_evaluator import RuleEvaluator
from ai_engine.rendering.video_renderer import VideoRenderer


def create_synthetic_badminton_sequence(num_frames: int = 40) -> list:
    """Generate a realistic sequence of PoseFrames simulating an overhead clear."""
    frames = []
    for i in range(num_frames):
        pct = i / float(num_frames - 1)
        # Simulate arm rising up to contact around 68% of sequence
        if pct < 0.3:
            # Preparation / cocking
            elbow_x = 0.55
            elbow_y = 0.35
            wrist_x = 0.52
            wrist_y = 0.32
        elif pct < 0.65:
            # Backswing -> upward forward swing
            elbow_x = 0.56
            elbow_y = 0.28 - (pct - 0.3) * 0.3
            wrist_x = 0.54
            wrist_y = 0.30 - (pct - 0.3) * 0.5
        elif pct <= 0.72:
            # Peak contact (insufficient extension: bent elbow test case around 152 degrees)
            elbow_x = 0.58
            elbow_y = 0.18
            wrist_x = 0.60
            wrist_y = 0.08
        else:
            # Follow through and recovery
            elbow_x = 0.48
            elbow_y = 0.40
            wrist_x = 0.42
            wrist_y = 0.52

        kpts = {
            "nose": Keypoint("nose", 0.50, 0.22, pixel_x=320, pixel_y=158),
            "left_shoulder": Keypoint("left_shoulder", 0.45, 0.32, pixel_x=288, pixel_y=230),
            "right_shoulder": Keypoint("right_shoulder", 0.54, 0.30, pixel_x=345, pixel_y=216),
            "right_elbow": Keypoint("right_elbow", elbow_x, elbow_y, pixel_x=int(elbow_x * 640), pixel_y=int(elbow_y * 720)),
            "right_wrist": Keypoint("right_wrist", wrist_x, wrist_y, pixel_x=int(wrist_x * 640), pixel_y=int(wrist_y * 720)),
            "left_elbow": Keypoint("left_elbow", 0.40, 0.42, pixel_x=256, pixel_y=302),
            "left_wrist": Keypoint("left_wrist", 0.38, 0.48, pixel_x=243, pixel_y=345),
            "left_hip": Keypoint("left_hip", 0.46, 0.55, pixel_x=294, pixel_y=396),
            "right_hip": Keypoint("right_hip", 0.53, 0.54, pixel_x=339, pixel_y=388),
            "left_knee": Keypoint("left_knee", 0.45, 0.72, pixel_x=288, pixel_y=518),
            "right_knee": Keypoint("right_knee", 0.54, 0.73, pixel_x=345, pixel_y=525),
            "left_ankle": Keypoint("left_ankle", 0.44, 0.90, pixel_x=281, pixel_y=648),
            "right_ankle": Keypoint("right_ankle", 0.55, 0.91, pixel_x=352, pixel_y=655),
        }
        pf = PoseFrame(
            frame_idx=i,
            timestamp=round(i * 0.033, 3),
            keypoints=kpts,
            bbox=[0.38, 0.08, 0.65, 0.92],
            confidence=0.92,
            is_valid=True,
            model_name="synthetic_test",
        )
        frames.append(pf)
    return frames


def test_badminton_pack_analysis():
    """Verify phase segmentation and metric calculation."""
    pack = BadmintonSportPack()
    frames = create_synthetic_badminton_sequence(40)

    result = pack.analyze_sequence(frames, movement_name="overhead_clear")

    assert result["sport"] == "badminton"
    assert result["movement"] == "overhead_clear"
    assert "phases" in result
    assert "contact" in result["phases"]
    assert "backswing" in result["phases"]

    metrics = result["metrics"]
    assert "contact_elbow_angle" in metrics
    assert "backswing_elbow_angle" in metrics
    assert "trunk_forward_tilt" in metrics


def test_rule_evaluator_generates_five_pillars():
    """Verify rule evaluator creates structured 5-element feedback and injury notes."""
    evaluator = RuleEvaluator()
    pack = BadmintonSportPack()
    frames = create_synthetic_badminton_sequence(40)
    analysis = pack.analyze_sequence(frames, movement_name="overhead_clear")

    # Force a bent elbow condition at contact
    analysis["metrics"]["contact_elbow_angle"] = 154.0

    corrections = evaluator.evaluate(
        metrics=analysis["metrics"],
        rules=analysis["rules"],
        phases=analysis["phases"],
        reference=analysis["reference"],
    )

    assert len(corrections) > 0
    c = corrections[0]
    # Check 5 Required Pillars
    assert "observed_difference" in c
    assert "reference_benchmark" in c
    assert "location_and_timing" in c
    assert "suggested_correction" in c
    assert "evidence_and_confidence" in c
    # Check Cautious Biomechanics Insights
    assert "efficiency_impact" in c
    assert "injury_caution" in c
    assert c["severity"] in ["high", "medium", "low"]


def test_video_renderer_synthetic():
    """Verify rendering engine outputs annotated video and overlays."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        raw_vid = tmp_path / "raw.mp4"
        out_vid = tmp_path / "annotated.mp4"

        # Create dummy source video with 30 blank frames
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(raw_vid), fourcc, 30.0, (640, 720))
        for _ in range(30):
            frame = np.full((720, 640, 3), 40, dtype=np.uint8)
            writer.write(frame)
        writer.release()

        frames = create_synthetic_badminton_sequence(30)
        pack = BadmintonSportPack()
        analysis = pack.analyze_sequence(frames, movement_name="overhead_clear")
        evaluator = RuleEvaluator()
        corrections = evaluator.evaluate(
            metrics=analysis["metrics"],
            rules=analysis["rules"],
            phases=analysis["phases"],
            reference=analysis["reference"],
        )

        renderer = VideoRenderer()
        meta = renderer.render_analysis_video(
            raw_video_path=str(raw_vid),
            output_video_path=str(out_vid),
            pose_frames=frames,
            phases=analysis["phases"],
            metrics=analysis["metrics"],
            corrections=corrections,
            reference=analysis["reference"],
        )

        assert Path(out_vid).exists()
        assert meta["total_frames_rendered"] == 30
