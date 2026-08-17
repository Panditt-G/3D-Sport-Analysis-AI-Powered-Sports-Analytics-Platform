"""
Multi-Object Tracking Test with ByteTrack & YOLO
================================================
This script tests multi-object tracking on a sample running video using
a pretrained YOLOv8n detector integrated with the ByteTrack algorithm.

It processes 'data/raw/test/running.mp4' frame-by-frame, tracks people across
consecutive frames, assigns persistent tracking IDs, and writes the annotated
tracked video to 'data/outputs/tracking_test/tracked_running.mp4'.
"""

from pathlib import Path
import cv2
import torch
from ultralytics import YOLO


def run_tracking_test():
    # -------------------------------------------------------------------------
    # Step 1: Set up input and output file paths
    # -------------------------------------------------------------------------
    # Resolve the project root directory (3 levels up from ai_engine/vision/tracking)
    project_root = Path(__file__).resolve().parents[3]

    input_video_path = project_root / "data" / "raw" / "test" / "running1.avi"
    output_dir = project_root / "data" / "outputs" / "tracking_test"
    output_video_path = output_dir / "tracked_running1.mp4"

    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Validate that the input video exists
    if not input_video_path.exists():
        raise FileNotFoundError(f"Input video not found at: {input_video_path}")

    # -------------------------------------------------------------------------
    # Step 2: Determine compute device (CUDA GPU if available, fallback to CPU)
    # -------------------------------------------------------------------------
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # -------------------------------------------------------------------------
    # Step 3: Load pretrained YOLO detection model and configure tracker
    # -------------------------------------------------------------------------
    model_name = "yolov8n.pt"  # Lightweight YOLOv8 nano model
    tracker_name = "bytetrack.yaml"  # ByteTrack tracker configuration
    model = YOLO(model_name)

    # -------------------------------------------------------------------------
    # Step 4: Open the input video stream
    # -------------------------------------------------------------------------
    cap = cv2.VideoCapture(str(input_video_path))
    if not cap.isOpened():
        raise IOError(f"Failed to open input video at: {input_video_path}")

    # Retrieve video dimensions and frame rate
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps is None:
        fps = 30.0  # Fallback frame rate

    # -------------------------------------------------------------------------
    # Step 5: Initialize the video writer for tracked output
    # -------------------------------------------------------------------------
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_video_path), fourcc, fps, (width, height))

    if not out.isOpened():
        cap.release()
        raise IOError(f"Failed to create video writer at: {output_video_path}")

    # -------------------------------------------------------------------------
    # Step 6: Process video frame-by-frame with ByteTrack
    # -------------------------------------------------------------------------
    frame_count = 0
    print(f"Starting tracking inference on: {input_video_path.name} ...")

    try:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break  # Reached end of video

            # Run tracking with ByteTrack, persisting IDs across consecutive frames
            # classes=[0] focuses detection and tracking specifically on people (COCO class 0)
            results = model.track(
                source=frame,
                persist=True,
                tracker=tracker_name,
                classes=[0],
                device=device,
                verbose=False,
            )

            # Draw bounding boxes with persistent tracking IDs on the frame
            annotated_frame = results[0].plot()

            # Write the annotated frame to output video
            out.write(annotated_frame)
            frame_count += 1

    finally:
        # Release capture and writer resources
        cap.release()
        out.release()

    # -------------------------------------------------------------------------
    # Step 7: Print test execution summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 50)
    print("       BYTE TRACKING INFERENCE TEST SUMMARY")
    print("=" * 50)
    print(f"Model Name            : {model_name}")
    print(f"Tracker Name          : {tracker_name}")
    print(f"Selected Device       : {device.upper()}")
    print(f"Input Path            : {input_video_path}")
    print(f"Output Path           : {output_video_path}")
    print(f"Total Processed Frames: {frame_count}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_tracking_test()
