"""
Full End-to-End Workflow Integration Test.
==========================================
Simulates complete user flow:
1. Video upload -> POST /api/v1/analyses
2. Background job processing & status polling -> GET /api/v1/analyses/{job_id}
3. Results retrieval (phases, metrics, corrections) -> GET /api/v1/analyses/{job_id}/results
4. Video artifact streaming -> GET /api/v1/analyses/{job_id}/video
5. Pose landmarks for interactive overlay -> GET /api/v1/analyses/{job_id}/pose
"""

import time
import io
import tempfile
from pathlib import Path
import cv2
import numpy as np
from fastapi.testclient import TestClient

from backend.server import app

client = TestClient(app)


def create_test_video(path: str, num_frames: int = 30):
    """Generate a valid test MP4 video."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(path, fourcc, 30.0, (640, 480))
    for i in range(num_frames):
        # Create frame with a circle moving (to ensure real pixels)
        frame = np.full((480, 640, 3), 50, dtype=np.uint8)
        cv2.circle(frame, (200 + i * 5, 200), 30, (200, 200, 200), -1)
        writer.write(frame)
    writer.release()


def test_full_e2e_analysis_flow():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_video = Path(tmp_dir) / "input_stroke.mp4"
        create_test_video(str(tmp_video), num_frames=25)

        with open(tmp_video, "rb") as f:
            video_bytes = f.read()

        # 1. POST /api/v1/analyses
        response = client.post(
            "/api/v1/analyses?sport=badminton&movement=overhead_clear&pose_model=mediapipe",
            files={"file": ("input_stroke.mp4", video_bytes, "video/mp4")},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert "job_id" in data
        job_id = data["job_id"]
        assert data["sport"] == "badminton"
        assert data["movement"] == "overhead_clear"

        # 2. Poll job until completion
        max_wait = 50  # seconds (allows headroom for CPU inference on host)
        start_t = time.time()
        final_status = None

        while time.time() - start_t < max_wait:
            status_res = client.get(f"/api/v1/analyses/{job_id}")
            assert status_res.status_code == 200
            status_data = status_res.json()
            if status_data["status"] in ["completed", "failed"]:
                final_status = status_data["status"]
                break
            time.sleep(0.5)

        assert final_status == "completed", f"Job failed or timed out: {status_data}"

        # 3. GET /api/v1/analyses/{job_id}/results
        res = client.get(f"/api/v1/analyses/{job_id}/results")
        assert res.status_code == 200
        result_payload = res.json()
        assert result_payload["status"] == "completed"
        results = result_payload["results"]
        assert "phases" in results
        assert "metrics" in results
        assert "corrections" in results
        assert "reference" in results

        # Verify badminton overhead clear phases
        phases = results["phases"]
        assert "contact" in phases
        assert "backswing" in phases

        # 4. GET /api/v1/analyses/{job_id}/video (Annotated Video Stream)
        video_res = client.get(f"/api/v1/analyses/{job_id}/video")
        assert video_res.status_code == 200
        assert video_res.headers["content-type"] == "video/mp4"
        assert len(video_res.content) > 0

        # 5. GET /api/v1/analyses/{job_id}/pose (Frame-by-frame pose landmarks)
        pose_res = client.get(f"/api/v1/analyses/{job_id}/pose")
        assert pose_res.status_code == 200
        pose_data = pose_res.json()
        assert isinstance(pose_data, list)
        assert len(pose_data) > 0
        assert "keypoints" in pose_data[0]
