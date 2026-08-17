"""
YOLO Video Object Detection Inference Test
==========================================
This script performs a standalone inference test on a video using a lightweight
pretrained YOLO model (YOLOv8n).

It processes 'data/raw/test/running.mp4' frame-by-frame, runs object detection
using GPU (CUDA) if available with automatic CPU fallback, and writes the
annotated video output to 'data/outputs/yolo_test/annotated_running.mp4'.
"""

from pathlib import Path
import cv2
import torch
from ultralytics import YOLO


def run_yolo_video_test():
    # -------------------------------------------------------------------------
    # Step 1: Set up input and output file paths
    # -------------------------------------------------------------------------
    # Resolve the project root directory (3 levels up from ai_engine/vision/detection)
    project_root = Path(__file__).resolve().parents[3]

    input_video_path = project_root / "data" / "raw" / "test" / "running1.avi"
    output_dir = project_root / "data" / "outputs" / "yolo_test"
    output_video_path = output_dir / "annotated_running1.mp4"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Validate that the input video exists
    if not input_video_path.exists():
        raise FileNotFoundError(f"Input video not found at: {input_video_path}")

    # -------------------------------------------------------------------------
    # Step 2: Determine compute device (CUDA GPU if available, else CPU)
    # -------------------------------------------------------------------------
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # -------------------------------------------------------------------------
    # Step 3: Load lightweight pretrained YOLO detection model
    # -------------------------------------------------------------------------
    model_name = "yolov8n.pt"  # YOLOv8 nano model: fast and lightweight for testing
    model = YOLO(model_name)

    # -------------------------------------------------------------------------
    # Step 4: Open the input video stream
    # -------------------------------------------------------------------------
    cap = cv2.VideoCapture(str(input_video_path))
    if not cap.isOpened():
        raise IOError(f"Failed to open input video: {input_video_path}")

    # Retrieve video properties (resolution and frame rate)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps is None:
        fps = 30.0  # Default fallback frame rate

    # -------------------------------------------------------------------------
    # Step 5: Initialize the video writer for output
    # -------------------------------------------------------------------------
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_video_path), fourcc, fps, (width, height))

    if not out.isOpened():
        cap.release()
        raise IOError(f"Failed to create video writer at: {output_video_path}")

    # -------------------------------------------------------------------------
    # Step 6: Process video frame-by-frame
    # -------------------------------------------------------------------------
    frame_count = 0
    print(f"Starting video inference on: {input_video_path.name} ...")

    try:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break  # End of video stream reached

            # Run object detection on the current frame
            results = model(source=frame, device=device, verbose=False)

            # Get the annotated frame containing detection bounding boxes & labels
            annotated_frame = results[0].plot()

            # Write the annotated frame to the output video file
            out.write(annotated_frame)
            frame_count += 1

    finally:
        # Release all video capture and writer resources
        cap.release()
        out.release()

    # -------------------------------------------------------------------------
    # Step 7: Print test execution summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 50)
    print("       YOLO VIDEO INFERENCE TEST SUMMARY")
    print("=" * 50)
    print(f"Model Name            : {model_name}")
    print(f"Selected Device       : {device.upper()}")
    print(f"Input Video Path      : {input_video_path}")
    print(f"Output Video Path     : {output_video_path}")
    print(f"Total Processed Frames: {frame_count}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_yolo_video_test()
