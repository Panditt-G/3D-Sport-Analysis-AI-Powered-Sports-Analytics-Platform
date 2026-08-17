"""
Landmark Extraction Test Module
===============================
This test script extracts 33 standard body landmarks from 'data/raw/test/running.mp4'
frame-by-frame using the MediaPipe Pose estimator and saves the structured output
to 'data/outputs/pose_test/landmarks.json'.

Workflow:
1. Reads 'data/raw/test/running.mp4' frame-by-frame using OpenCV.
2. Performs pose estimation via MediaPipePoseEstimator.
3. Formats and extracts all 33 body landmarks via PoseLandmarkExtractor.
4. Handles frames where no pose is found safely.
5. Saves the complete landmark dataset as JSON.
6. Prints a concise execution summary.
"""

from pathlib import Path
import json
import sys
import cv2

# Ensure project root is in sys.path for direct script execution
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ai_engine.vision.pose.mediapipe_pose import MediaPipePoseEstimator
from ai_engine.pose_analysis.landmarks import PoseLandmarkExtractor


def run_landmark_extraction_test():
    # -------------------------------------------------------------------------
    # Step 1: Set up input and output file paths
    # -------------------------------------------------------------------------
    input_video_path = project_root / "data" / "raw" / "test" / "running1.avi"
    output_dir = project_root / "data" / "outputs" / "pose_test"
    output_json_path = output_dir / "landmarks.json"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Validate that input video exists
    if not input_video_path.exists():
        raise FileNotFoundError(f"Input video not found at: {input_video_path}")

    # -------------------------------------------------------------------------
    # Step 2: Open input video stream
    # -------------------------------------------------------------------------
    cap = cv2.VideoCapture(str(input_video_path))
    if not cap.isOpened():
        raise IOError(f"Failed to open video file at: {input_video_path}")

    # Retrieve video FPS to calculate frame timestamps
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps is None:
        fps = 30.0

    # -------------------------------------------------------------------------
    # Step 3: Initialize Pose Estimator and Landmark Extractor
    # -------------------------------------------------------------------------
    pose_estimator = MediaPipePoseEstimator(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    extractor = PoseLandmarkExtractor()

    video_data = []
    total_frames = 0
    detected_frames = 0
    not_detected_frames = 0

    print(f"Starting Landmark Extraction on: {input_video_path.name} ...")

    # -------------------------------------------------------------------------
    # Step 4: Process video frame-by-frame
    # -------------------------------------------------------------------------
    try:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break  # End of video stream

            timestamp = total_frames / fps

            # Run pose detection
            results = pose_estimator.process_frame(frame)

            # Extract structured frame landmark data
            frame_data = extractor.extract_frame_data(
                frame_index=total_frames,
                timestamp=timestamp,
                pose_landmarks=results.pose_landmarks,
            )

            if frame_data["pose_detected"]:
                detected_frames += 1
            else:
                not_detected_frames += 1

            video_data.append(frame_data)
            total_frames += 1

    finally:
        # Release video capture and pose estimator resources
        cap.release()
        pose_estimator.close()

    # -------------------------------------------------------------------------
    # Step 5: Save extracted landmarks to JSON file
    # -------------------------------------------------------------------------
    output_payload = {
        "source_video": str(input_video_path.name),
        "total_frames": total_frames,
        "fps": round(fps, 2),
        "landmark_count_per_pose": extractor.num_landmarks,
        "frames": video_data,
    }

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    # -------------------------------------------------------------------------
    # Step 6: Print test execution summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 55)
    print("       LANDMARK EXTRACTION TEST SUMMARY")
    print("=" * 55)
    print(f"Input Video Path              : {input_video_path}")
    print(f"JSON Output Path              : {output_json_path}")
    print(f"Total Processed Frames        : {total_frames}")
    print(f"Frames With Pose Detected     : {detected_frames}")
    print(f"Frames Without Pose Detected  : {not_detected_frames}")
    print(f"Landmarks Per Detected Frame  : {extractor.num_landmarks}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    run_landmark_extraction_test()
