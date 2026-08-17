"""
YOLO Object Detection Inference Test
====================================
This script performs an initial inference test using a lightweight pretrained YOLO model (YOLOv8n).
It detects objects in 'data/raw/test/running.jpg', leverages GPU (CUDA) if available with automatic
CPU fallback, and saves the annotated detection image to 'data/outputs/yolo_test/'.
"""

from pathlib import Path
import cv2
import numpy as np
import torch
from ultralytics import YOLO


def run_yolo_test():
    # -------------------------------------------------------------------------
    # Step 1: Set up input and output paths
    # -------------------------------------------------------------------------
    # Resolve the project root directory (3 levels up from ai_engine/vision/detection)
    project_root = Path(__file__).resolve().parents[3]
    
    input_image_path = project_root / "data" / "raw" / "test" / "running.jpg"
    output_dir = project_root / "data" / "outputs" / "yolo_test"
    output_image_path = output_dir / "annotated_running.jpg"

    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check if the input test image exists
    if not input_image_path.exists():
        raise FileNotFoundError(f"Input image not found at: {input_image_path}")

    # -------------------------------------------------------------------------
    # Step 2: Determine compute device (NVIDIA GPU via CUDA if available, else CPU)
    # -------------------------------------------------------------------------
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # -------------------------------------------------------------------------
    # Step 3: Load lightweight pretrained YOLO detection model
    # -------------------------------------------------------------------------
    model_name = "yolov8n.pt"  # YOLOv8 nano: compact, fast, and ideal for testing
    model = YOLO(model_name)

    # -------------------------------------------------------------------------
    # Step 4: Run inference on the test image
    # -------------------------------------------------------------------------
    # Read the image robustly across all platforms
    image = cv2.imdecode(np.fromfile(str(input_image_path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        image = str(input_image_path)

    results = model(source=image, device=device)

    # -------------------------------------------------------------------------
    # Step 5: Save annotated detection result
    # -------------------------------------------------------------------------
    result = results[0]
    result.save(filename=str(output_image_path))

    # Count total detected objects/boxes
    num_detections = len(result.boxes) if result.boxes is not None else 0

    # -------------------------------------------------------------------------
    # Step 6: Print test execution summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 50)
    print("       YOLO INFERENCE TEST SUMMARY")
    print("=" * 50)
    print(f"Model Name          : {model_name}")
    print(f"Selected Device     : {device.upper()}")
    print(f"Input Image Path    : {input_image_path}")
    print(f"Number of Detections: {num_detections}")
    print(f"Output Path         : {output_image_path}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_yolo_test()
