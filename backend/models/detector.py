"""
Badminton Detector Integration for Backend
"""

from ultralytics import YOLO
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class BadmintonDetector:
    """Badminton object detector integrated with backend."""
    
    def __init__(self):
        model_path = Path(__file__).parent.parent.parent / "model" / "badminton_detector_v1.pt"
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        logger.info(f"Loading model: {model_path}")
        self.model = YOLO(str(model_path))
        logger.info("Model loaded successfully!")
    
    def detect(self, image_path: str, conf_threshold: float = 0.25):
        """Detect objects in image."""
        results = self.model.predict(image_path, conf=conf_threshold, verbose=False)
        
        detections = []
        for result in results:
            for box in result.boxes:
                detection = {
                    'class_id': int(box.cls[0]),
                    'class_name': ['shuttlecock', 'badminton_racket', 'player'][int(box.cls[0])],
                    'confidence': float(box.conf[0]),
                    'bbox': box.xyxy[0].tolist()
                }
                detections.append(detection)
        
        return detections

# Singleton instance
_detector = None

def get_detector():
    """Get detector instance (singleton)."""
    global _detector
    if _detector is None:
        _detector = BadmintonDetector()
    return _detector
