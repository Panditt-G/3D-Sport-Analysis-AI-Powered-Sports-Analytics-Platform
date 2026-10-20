"""Analysis service: orchestrates the full AI pipeline for video analysis."""
import os
import cv2
import json
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ai_engine.registry import SportRegistry
from ai_engine.common.video import VideoCapture
from ai_engine.common.utils import ensure_directory

logger = logging.getLogger(__name__)


class AnalysisService:
    """Orchestrates: video -> frames -> pipeline -> analytics -> annotated video."""

    def __init__(self, output_dir: str):
        self.output_dir = ensure_directory(output_dir)
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def analyze_video(
        self,
        video_path: str,
        sport_name: str,
        config: Optional[Dict[str, Any]] = None,
        max_frames: int = 300,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if session_id is None:
            session_id = str(uuid.uuid4())[:8]

        pipeline = SportRegistry.get_pipeline(sport_name, config=config)
        analytics = SportRegistry.get_analytics(sport_name, config=config)

        frame_results = []
        video_info = {}
        output_video_filename = f"{session_id}_annotated.mp4"
        output_video_path = os.path.join(self.output_dir, output_video_filename)

        # ─── Open Video ──────────────────────────────────────────────────────
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Cannot open video: {video_path}")

            fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
            width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0

            video_info = {
                "fps": round(fps, 2),
                "frame_count": total_frames,
                "width": width,
                "height": height,
                "duration_seconds": round(duration, 2),
            }

            # Use XVID on Windows (most reliable), then try mp4v
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            avi_path = output_video_path.replace('.mp4', '.avi')
            writer = cv2.VideoWriter(avi_path, fourcc, fps, (width, height))

            if not writer.isOpened():
                # Fallback: try mp4v to mp4
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                avi_path = output_video_path
                writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret or frame_idx >= max_frames:
                    break

                timestamp = frame_idx / fps

                # ── Run sport pipeline ────────────────────────────────────
                detection_data = pipeline.process_frame(frame, frame_idx)
                detection_data["timestamp"] = round(timestamp, 4)
                pose_data = detection_data.get("pose_data", {})
                instant_metrics = analytics.update(detection_data, pose_data, frame_idx)

                # ── Draw Annotations ────────────────────────────────────
                annotated = frame.copy()

                # 1. Bounding boxes + labels
                for box_item in detection_data.get("boxes", []):
                    bbox     = box_item.get("bbox", [])
                    cls_name = box_item.get("class_name", "object")
                    conf     = box_item.get("confidence", 0.0)
                    if len(bbox) == 4:
                        x1, y1, x2, y2 = map(int, bbox)
                        cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 255, 255), 2)
                        label = f" {cls_name.upper()} {conf:.2f} "
                        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                        tag_y1 = max(0, y1 - th - 8)
                        cv2.rectangle(annotated, (x1, tag_y1), (x1 + tw + 4, y1), (255, 255, 255), -1)
                        cv2.putText(annotated, label, (x1 + 2, y1 - 4),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

                # 2. HUD card — top-left white card with black text
                shuttle = "YES" if detection_data.get("shuttlecock_detected") else "NO"
                racket  = "YES" if detection_data.get("racket_detected")  else "NO"
                player  = "YES" if detection_data.get("player_detected")  else "NO"

                hud_lines = [
                    f"Sport: {sport_name.upper()}   Frame: {frame_idx:04d}   Time: {timestamp:.2f}s",
                    f"Shuttlecock: {shuttle}  |  Racket: {racket}  |  Player: {player}",
                ]
                if instant_metrics:
                    m_parts = [
                        f"{k}: {v:.1f}" if isinstance(v, float) else f"{k}: {v}"
                        for k, v in list(instant_metrics.items())[:3]
                    ]
                    hud_lines.append("  |  ".join(m_parts))

                font       = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.50
                thickness  = 1
                line_h     = 22
                pad        = 10
                hx, hy     = 16, 16
                card_w     = 560
                card_h     = pad * 2 + len(hud_lines) * line_h

                # White card
                cv2.rectangle(annotated, (hx, hy), (hx + card_w, hy + card_h), (255, 255, 255), -1)
                # Thin black border
                cv2.rectangle(annotated, (hx, hy), (hx + card_w, hy + card_h), (0, 0, 0), 1)

                for i, line in enumerate(hud_lines):
                    y = hy + pad + (i + 1) * line_h - 4
                    cv2.putText(annotated, line, (hx + pad, y),
                                font, font_scale, (0, 0, 0), thickness, cv2.LINE_AA)

                writer.write(annotated)

                frame_results.append({
                    "frame_idx": frame_idx,
                    "timestamp": round(timestamp, 4),
                    "detection": detection_data,
                    "metrics": instant_metrics,
                })
                frame_idx += 1

        except Exception as e:
            logger.exception("Video analysis failed")
            try:
                cap.release()
                writer.release()
            except Exception:
                pass
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
        finally:
            try:
                cap.release()
            except Exception:
                pass
            try:
                writer.release()
            except Exception:
                pass

        # ── Summary ─────────────────────────────────────────────────────────
        pipeline_summary = pipeline.get_summary()
        analytics_summary = analytics.compute_summary()
        combined_summary = {**pipeline_summary, **analytics_summary}

        # Determine the actual output filename (could be .avi if XVID was used)
        actual_output = avi_path
        actual_filename = os.path.basename(actual_output)

        result = {
            "session_id": session_id,
            "sport": sport_name,
            "status": "completed",
            "video_info": video_info,
            "video_output_url": f"/api/outputs/{actual_filename}",
            "frames_processed": len(frame_results),
            "frame_results": frame_results,
            "summary": combined_summary,
            "timestamp": datetime.now().isoformat(),
        }

        self._save_result(session_id, result)
        self._sessions[session_id] = result
        return result

    def get_result(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis result by session ID."""
        if session_id in self._sessions:
            return self._sessions[session_id]

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
