"""
Pose Estimation Test with MediaPipe BlazePose
=============================================
This script performs a standalone body pose estimation test on a sample running video
using MediaPipe Pose / BlazePose.

Workflow:
1. Reads 'data/raw/test/running.mp4' frame-by-frame using OpenCV.
2. Extracts 33 standard body landmarks per frame using MediaPipe BlazePose.
3. Overlays the full-body skeleton/connections on each frame.
4. Writes the annotated output video to 'data/outputs/pose_test/pose_running.mp4'.
5. Prints a summary of processed frames, detection rates, and landmark counts.
"""

from pathlib import Path
import sys
import cv2

# Ensure project root is in sys.path for direct script execution
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ai_engine.vision.pose.mediapipe_pose import MediaPipePoseEstimator


def run_pose_test():
    # -------------------------------------------------------------------------
    # Step 1: Set up input and output file paths
    # -------------------------------------------------------------------------
    input_video_path = project_root / "data" / "raw" / "test" / "running1.avi"
    output_dir = project_root / "data" / "outputs" / "pose_test"
    output_video_path = output_dir / "pose_running1.mp4"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Validate that the input video exists
    if not input_video_path.exists():
        raise FileNotFoundError(f"Input video not found at: {input_video_path}")

    # -------------------------------------------------------------------------
    # Step 2: Open the input video stream with OpenCV
    # -------------------------------------------------------------------------
    cap = cv2.VideoCapture(str(input_video_path))
    if not cap.isOpened():
        raise IOError(f"Failed to open input video at: {input_video_path}")

    # Retrieve video properties (dimensions and framerate)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps is None:
        fps = 30.0  # Default fallback frame rate

    # -------------------------------------------------------------------------
    # Step 3: Initialize VideoWriter for annotated output
    # -------------------------------------------------------------------------
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_video_path), fourcc, fps, (width, height))

    if not out.isOpened():
        cap.release()
        raise IOError(f"Failed to initialize video writer at: {output_video_path}")

    # -------------------------------------------------------------------------
    # Step 4: Initialize MediaPipe Pose Estimator
    # -------------------------------------------------------------------------
    # Uses BlazePose Full model (complexity=1) with temporal landmark smoothing
    pose_estimator = MediaPipePoseEstimator(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    # Metrics tracking counters
    total_frames = 0
    detected_frames = 0
    not_detected_frames = 0

    print(f"Starting MediaPipe Pose Estimation on: {input_video_path.name} ...")

    # -------------------------------------------------------------------------
    # Step 5: Process video frame-by-frame
    # -------------------------------------------------------------------------
    try:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break  # Reached end of video stream

            total_frames += 1

            # Run MediaPipe Pose estimation on the current frame
            results = pose_estimator.process_frame(frame)

            # Check if pose landmarks were detected in this frame
            if results.pose_landmarks is not None:
                detected_frames += 1
                # Draw the skeletal connections and landmarks onto the frame
                pose_estimator.draw_landmarks(frame, results.pose_landmarks)
            else:
                not_detected_frames += 1

            # Write the processed (annotated) frame to output video
            out.write(frame)

    finally:
        # Step 6: Release all resources cleanly
        cap.release()
        out.release()
        pose_estimator.close()

    # -------------------------------------------------------------------------
    # Step 7: Print test execution summary
    # -------------------------------------------------------------------------
    detection_rate = (detected_frames / total_frames * 100) if total_frames > 0 else 0.0

    print("\n" + "=" * 55)
    print("       MEDIAPIPE POSE ESTIMATION TEST SUMMARY")
    print("=" * 55)
    print(f"Model / System             : MediaPipe BlazePose (Pose)")
    print(f"Processing Mode            : Video Stream (Temporal Smoothing)")
    print(f"Landmark Count per Pose    : {pose_estimator.num_landmarks} 3D Body Landmarks")
    print(f"Input Video Path           : {input_video_path}")
    print(f"Output Video Path          : {output_video_path}")
    print(f"Total Processed Frames     : {total_frames}")
    print(f"Frames With Pose Detected  : {detected_frames} ({detection_rate:.1f}%)")
    print(f"Frames Without Pose        : {not_detected_frames}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    run_pose_test()
