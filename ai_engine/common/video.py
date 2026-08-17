"""Video streaming, capture, and frame processing using OpenCV."""
import cv2
import os
from typing import Any, Dict, Generator, Optional, Tuple


class VideoCapture:
    """
    OpenCV-based video capture wrapper.
    Provides frame iteration with metadata (index, timestamp, fps).
    """

    def __init__(self, video_path: str):
        """
        Initialize video capture.

        Args:
            video_path: Path to the video file.

        Raises:
            FileNotFoundError: If video file doesn't exist.
            ValueError: If video cannot be opened.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        self._fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self._frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    @property
    def fps(self) -> float:
        return self._fps

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def resolution(self) -> Tuple[int, int]:
        return (self._width, self._height)

    @property
    def duration_seconds(self) -> float:
        return self._frame_count / self._fps if self._fps > 0 else 0.0

    def get_info(self) -> Dict[str, Any]:
        """Return video metadata dictionary."""
        return {
            "path": self.video_path,
            "fps": round(self._fps, 2),
            "frame_count": self._frame_count,
            "width": self._width,
            "height": self._height,
            "duration_seconds": round(self.duration_seconds, 2),
        }

    def frames(self) -> Generator[Tuple[int, float, Any], None, None]:
        """
        Iterate over video frames.

        Yields:
            (frame_index, timestamp_seconds, frame_ndarray)
        """
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        frame_idx = 0

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            timestamp = frame_idx / self._fps
            yield frame_idx, timestamp, frame
            frame_idx += 1

    def read_frame(self, frame_index: int) -> Optional[Any]:
        """Read a specific frame by index."""
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = self.cap.read()
        return frame if ret else None

    def release(self):
        """Release video capture resources."""
        if self.cap:
            self.cap.release()

    def __del__(self):
        self.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
