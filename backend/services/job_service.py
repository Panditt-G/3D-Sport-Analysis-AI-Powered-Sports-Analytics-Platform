"""
Asynchronous Job Management Service.
===================================
Manages analysis job lifecycles, background execution, progress state updates,
and result persistence.
"""

import uuid
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import cv2

from ai_engine.vision.pose.mediapipe_adapter import MediaPipeAdapter
from ai_engine.vision.pose.yolo_pose import YOLOPoseEstimator
from sport_packs.badminton.plugin import BadmintonSportPack
from ai_engine.correction.rule_evaluator import RuleEvaluator
from ai_engine.rendering.video_renderer import VideoRenderer


class JobStatus:
    QUEUED = "queued"
    EXTRACTING_POSE = "extracting_pose"
    SEGMENTING_PHASES = "segmenting_phases"
    EVALUATING_RULES = "evaluating_rules"
    RENDERING_VIDEO = "rendering_video"
    COMPLETED = "completed"
    FAILED = "failed"


class JobService:
    """In-memory & file-persisted asynchronous job coordinator."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self.sport_packs = {
            "badminton": BadmintonSportPack(),
        }
        self.rule_evaluator = RuleEvaluator()
        self.video_renderer = VideoRenderer()

    def create_job(
        self,
        video_path: str,
        sport_name: str = "badminton",
        movement_name: str = "overhead_clear",
        pose_model: str = "mediapipe",
    ) -> Dict[str, Any]:
        """Initialize and enqueue an analysis job."""
        job_id = f"job_{uuid.uuid4().hex[:10]}"
        job_record = {
            "id": job_id,
            "status": JobStatus.QUEUED,
            "progress_pct": 0,
            "stage": "Job queued for processing",
            "sport": sport_name,
            "movement": movement_name,
            "pose_model": pose_model,
            "video_path": video_path,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
            "artifacts": {},
            "results": None,
        }
        self._jobs[job_id] = job_record

        # Launch background processing thread
        thread = threading.Thread(target=self._process_job, args=(job_id,), daemon=True)
        thread.start()

        return job_record

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve job status record."""
        return self._jobs.get(job_id)

    def _update_progress(self, job_id: str, status: str, pct: int, stage_desc: str):
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = status
            self._jobs[job_id]["progress_pct"] = pct
            self._jobs[job_id]["stage"] = stage_desc
            self._jobs[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

    def _process_job(self, job_id: str):
        """Worker executing end-to-end multi-sport AI pipeline."""
        job = self._jobs[job_id]
        video_path = job["video_path"]
        sport_name = job["sport"]
        movement_name = job["movement"]
        model_choice = job["pose_model"]

        job_dir = self.output_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Pose Model Initialization
            self._update_progress(job_id, JobStatus.EXTRACTING_POSE, 10, "Initializing human pose estimator")
            if model_choice == "yolo":
                pose_estimator = YOLOPoseEstimator()
            else:
                try:
                    pose_estimator = MediaPipeAdapter()
                except Exception as mp_err:
                    print(f"Notice: MediaPipe initialization fell back to YOLOv8-pose: {mp_err}")
                    pose_estimator = YOLOPoseEstimator()

            # 2. Extract pose landmarks from video frames
            self._update_progress(job_id, JobStatus.EXTRACTING_POSE, 20, "Extracting body landmarks from video")
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise IOError(f"Unable to read video from {video_path}")

            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 100
            max_process_frames = min(total_video_frames, 300)

            pose_frames = []
            frame_idx = 0
            while cap.isOpened() and frame_idx < max_process_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                timestamp = frame_idx / fps
                p_frame = pose_estimator.estimate(frame, frame_idx=frame_idx, timestamp=timestamp)
                pose_frames.append(p_frame)
                frame_idx += 1

                if frame_idx % 15 == 0:
                    pct = 20 + int((frame_idx / max_process_frames) * 30)
                    self._update_progress(job_id, JobStatus.EXTRACTING_POSE, pct, f"Tracking athlete landmarks ({frame_idx}/{max_process_frames} frames)")

            cap.release()

            # 3. Sport Pack Analysis (Phase Detection & Metrics)
            self._update_progress(job_id, JobStatus.SEGMENTING_PHASES, 55, "Detecting movement phases and calculating kinematics")
            sport_pack = self.sport_packs.get(sport_name, self.sport_packs["badminton"])
            analysis_output = sport_pack.analyze_sequence(pose_frames, movement_name=movement_name)

            phases = analysis_output.get("phases", {})
            metrics = analysis_output.get("metrics", {})
            reference = analysis_output.get("reference", {})
            rules = analysis_output.get("rules", [])

            # 4. Correction Engine Evaluation
            self._update_progress(job_id, JobStatus.EVALUATING_RULES, 70, "Evaluating technique rules against coach references")
            corrections = self.rule_evaluator.evaluate(
                metrics=metrics,
                rules=rules,
                phases=phases,
                reference=reference,
            )

            # 5. Video Rendering Engine
            self._update_progress(job_id, JobStatus.RENDERING_VIDEO, 80, "Rendering annotated video with ghost reference overlay")
            annotated_video_path = str(job_dir / "annotated.mp4")
            render_meta = self.video_renderer.render_analysis_video(
                raw_video_path=video_path,
                output_video_path=annotated_video_path,
                pose_frames=pose_frames,
                phases=phases,
                metrics=metrics,
                corrections=corrections,
                reference=reference,
                sport_name=sport_name,
                movement_name=movement_name,
            )

            # 6. Save JSON artifacts
            pose_json_path = job_dir / "pose.json"
            with open(pose_json_path, "w", encoding="utf-8") as f:
                json.dump([pf.to_dict() for pf in pose_frames], f)

            metrics_json_path = job_dir / "metrics.json"
            with open(metrics_json_path, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)

            analysis_json_path = job_dir / "analysis.json"
            analysis_payload = {
                "job_id": job_id,
                "sport": sport_name,
                "movement": movement_name,
                "phases": phases,
                "metrics": metrics,
                "corrections": corrections,
                "reference": reference,
                "render_meta": render_meta,
            }
            with open(analysis_json_path, "w", encoding="utf-8") as f:
                json.dump(analysis_payload, f, indent=2)

            # Mark completed
            self._jobs[job_id]["status"] = JobStatus.COMPLETED
            self._jobs[job_id]["progress_pct"] = 100
            self._jobs[job_id]["stage"] = "Analysis complete"
            self._jobs[job_id]["results"] = analysis_payload
            self._jobs[job_id]["artifacts"] = {
                "annotated_video": annotated_video_path,
                "pose_json": str(pose_json_path),
                "metrics_json": str(metrics_json_path),
                "analysis_json": str(analysis_json_path),
            }
            self._jobs[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

        except Exception as e:
            print(f"Error processing job {job_id}: {e}")
            self._jobs[job_id]["status"] = JobStatus.FAILED
            self._jobs[job_id]["error"] = str(e)
            self._jobs[job_id]["stage"] = f"Failed: {str(e)}"
            self._jobs[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
