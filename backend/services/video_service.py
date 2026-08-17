"""Video service: handles upload validation, storage, and frame extraction."""
import os
import uuid
import shutil
from typing import Any, Dict, Tuple
from ai_engine.common.video import VideoCapture
from ai_engine.common.utils import ensure_directory


class VideoService:
    """Handles video file operations: validate, save, extract info."""

    def __init__(self, upload_dir: str, allowed_extensions: list, max_size_mb: int):
        self.upload_dir = ensure_directory(upload_dir)
        self.allowed_extensions = allowed_extensions
        self.max_size_bytes = max_size_mb * 1024 * 1024

    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, str]:
        """
        Validate uploaded file.

        Returns:
            (is_valid, error_message)
        """
        ext = os.path.splitext(filename)[1].lower()
        if ext not in self.allowed_extensions:
            return False, f"File type '{ext}' not allowed. Allowed: {self.allowed_extensions}"

        if file_size > self.max_size_bytes:
            max_mb = self.max_size_bytes / (1024 * 1024)
            return False, f"File too large. Max size: {max_mb}MB"

        return True, ""

    def save_upload(self, file_content: bytes, original_filename: str) -> Dict[str, Any]:
        """
        Save uploaded video file to disk.

        Returns:
            Dict with file_id, saved_path, file_size_mb, original_filename.
        """
        file_id = str(uuid.uuid4())[:8]
        ext = os.path.splitext(original_filename)[1].lower()
        saved_filename = f"{file_id}{ext}"
        saved_path = os.path.join(self.upload_dir, saved_filename)

        with open(saved_path, "wb") as f:
            f.write(file_content)

        file_size_mb = round(len(file_content) / (1024 * 1024), 2)

        return {
            "file_id": file_id,
            "saved_path": saved_path,
            "saved_filename": saved_filename,
            "original_filename": original_filename,
            "file_size_mb": file_size_mb,
        }

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video metadata using VideoCapture."""
        try:
            with VideoCapture(video_path) as vc:
                return vc.get_info()
        except Exception as e:
            return {"error": str(e)}
