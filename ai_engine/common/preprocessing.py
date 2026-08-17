"""Frame preprocessing: letterbox resizing, normalization, color conversion."""
import cv2
import numpy as np
from typing import Tuple


def letterbox_resize(
    frame: np.ndarray,
    target_size: Tuple[int, int] = (640, 640),
    color: Tuple[int, int, int] = (114, 114, 114),
) -> np.ndarray:
    """
    Resize frame with letterbox padding to maintain aspect ratio.

    Args:
        frame: Input BGR image (H, W, C).
        target_size: Target (width, height).
        color: Padding fill color (BGR).

    Returns:
        Letterboxed image of exact target_size.
    """
    h, w = frame.shape[:2]
    tw, th = target_size
    scale = min(tw / w, th / h)
    new_w, new_h = int(w * scale), int(h * scale)

    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    # Create padded canvas
    canvas = np.full((th, tw, 3), color, dtype=np.uint8)
    x_offset = (tw - new_w) // 2
    y_offset = (th - new_h) // 2
    canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized

    return canvas


def normalize_frame(frame: np.ndarray) -> np.ndarray:
    """
    Normalize pixel values from [0, 255] to [0.0, 1.0].

    Args:
        frame: Input uint8 image.

    Returns:
        Float32 normalized image.
    """
    return frame.astype(np.float32) / 255.0


def bgr_to_rgb(frame: np.ndarray) -> np.ndarray:
    """Convert BGR (OpenCV default) to RGB color space."""
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def rgb_to_bgr(frame: np.ndarray) -> np.ndarray:
    """Convert RGB back to BGR for OpenCV display/write."""
    return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)


def resize_frame(
    frame: np.ndarray, width: int = 640, height: int = 480
) -> np.ndarray:
    """Simple resize without aspect ratio preservation."""
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)
