"""Analysis service: orchestrates the full AI pipeline for video analysis."""
import os
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ai_engine.registry import SportRegistry
from ai_engine.common.video import VideoCapture
from ai_engine.common.utils import ensure_directory


class AnalysisService:
    """Orchestrates: video -> frames -> pipeline -> analytics -> results."""

    def __init__(self, output_dir: str):
        self.output_dir = ensure_directory(output_dir)
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def analyze_video(
        self,
        video_path: str,
        sport_name: str,
        config: Optional[Dict[str, Any]] = None,
        max_frames: int = 300,
    ) -> Dict[str, Any]:
        """
        Run full analysis pipeline on a video file.

        Args:
            video_path: Path to the video file.
            sport_name: Registered sport name.
            config: Optional config overrides.
            max_frames: Max frames to process (for performance).

        Returns:
            Complete analysis result dict.
        """
        session_id = str(uuid.uuid4())[:8]

        # Get pipeline and analytics from registry
        pipeline = SportRegistry.get_pipeline(sport_name, config=config)
        analytics = SportRegistry.get_analytics(sport_name, config=config)

        # Process video frames
        frame_results = []
        video_info = {}

        try:
            with VideoCapture(video_path) as vc:
                video_info = vc.get_info()

                for frame_idx, timestamp, frame in vc.frames():
                    if frame_idx >= max_frames:
                        break

                    # Run pipeline on frame
                    detection_data = pipeline.process_frame(frame, frame_idx)
                    detection_data["timestamp"] = round(timestamp, 4)

                    # Update analytics
                    pose_data = detection_data.get("pose_data", {})
                    instant_metrics = analytics.update(detection_data, pose_data, frame_idx)

                    frame_results.append({
                        "frame_idx": frame_idx,
                        "timestamp": round(timestamp, 4),
                        "detection": detection_data,
                        "metrics": instant_metrics,
                    })

        except Exception as e:
            return {
                "session_id": session_id,
                "sport": sport_name,
                "status": "error",
                "error": str(e),
                "video_info": video_info,
                "frame_results": [],
                "summary": {},
                "timestamp": datetime.now().isoformat(),
            }

        # Get final summary
        pipeline_summary = pipeline.get_summary()
        analytics_summary = analytics.compute_summary()
        combined_summary = {**pipeline_summary, **analytics_summary}

        result = {
            "session_id": session_id,
            "sport": sport_name,
            "status": "completed",
            "video_info": video_info,
            "frames_processed": len(frame_results),
            "frame_results": frame_results,
            "summary": combined_summary,
            "timestamp": datetime.now().isoformat(),
        }

        # Save results to file
        self._save_result(session_id, result)
        self._sessions[session_id] = result

        return result

    def get_result(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis result by session ID."""
        # Check memory cache first
        if session_id in self._sessions:
            return self._sessions[session_id]

        # Check saved file
        result_path = os.path.join(self.output_dir, f"{session_id}.json")
        if os.path.exists(result_path):
            with open(result_path, "r", encoding="utf-8") as f:
                result = json.load(f)
            self._sessions[session_id] = result
            return result

        return None

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all analysis sessions (summary only)."""
        sessions = []
        for filename in os.listdir(self.output_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.output_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    sessions.append({
                        "session_id": data.get("session_id", ""),
                        "sport": data.get("sport", ""),
                        "status": data.get("status", ""),
                        "frames_processed": data.get("frames_processed", 0),
                        "timestamp": data.get("timestamp", ""),
                    })
                except (json.JSONDecodeError, KeyError):
                    continue
        return sessions

    def _save_result(self, session_id: str, result: Dict[str, Any]):
        """Save analysis result to JSON file."""
        result_path = os.path.join(self.output_dir, f"{session_id}.json")
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
