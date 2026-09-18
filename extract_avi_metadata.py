"""OpenCV metadata extraction and shared validation rules for organoid videos."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2

VIDEO_DIR = Path(__file__).with_name("video")
RESULT_PATH = Path(__file__).with_name("result.txt")
ISSUE_PATH = Path(__file__).with_name("issue.txt")
VIDEO_EXTENSIONS = {".avi", ".mp4", ".mov", ".mkv", ".wmv"}

# Single source of truth for the web UI and terminal workflow.
FPS_WARNING_THRESHOLD = 30.50
DURATION_WARNING_SECONDS = 31.0


def extract_metadata(video_path: Path) -> dict[str, Any]:
    """Read video metadata using OpenCV."""
    capture = cv2.VideoCapture(str(video_path))
    try:
        if not capture.isOpened():
            raise RuntimeError("Video file could not be opened.")

        fps = capture.get(cv2.CAP_PROP_FPS)
        frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT)
        codec_value = int(capture.get(cv2.CAP_PROP_FOURCC))
        codec = "".join(
            chr((codec_value >> (8 * index)) & 0xFF)
            for index in range(4)
            if (codec_value >> (8 * index)) & 0xFF
        )
        return {
            "file": video_path.name,
            "fps": fps,
            "frame_count": int(frame_count),
            "duration_seconds": frame_count / fps if fps > 0 else None,
            "width": int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "codec": codec or "unknown",
            "backend": capture.getBackendName(),
        }
    finally:
        capture.release()


def validation_issues(metadata: dict[str, Any]) -> list[str]:
    """Return warning messages for metadata outside the project criteria."""
    issues: list[str] = []
    fps = float(metadata["fps"])
    duration = metadata.get("duration_seconds")

    if fps > FPS_WARNING_THRESHOLD:
        issues.append(f"FPS {fps:.3f} exceeds the {FPS_WARNING_THRESHOLD:.2f} limit.")
    if duration is not None and float(duration) >= DURATION_WARNING_SECONDS:
        issues.append(f"Duration {float(duration):.3f} s is at least {DURATION_WARNING_SECONDS:.0f} s.")
    return issues


def add_validation_result(metadata: dict[str, Any]) -> dict[str, Any]:
    """Attach a shared status and issue list to metadata."""
    issues = validation_issues(metadata)
    return {**metadata, "status": "issue" if issues else "normal", "issues": issues}


def analyze_directory() -> list[dict[str, Any]]:
    """Analyze all supported video files in the default video directory."""
    if not VIDEO_DIR.is_dir():
        raise FileNotFoundError(f"Video directory not found: {VIDEO_DIR}")

    results: list[dict[str, Any]] = []
    for video_path in sorted(VIDEO_DIR.iterdir()):
        if not video_path.is_file() or video_path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        try:
            results.append(add_validation_result(extract_metadata(video_path)))
        except RuntimeError as error:
            results.append({"file": video_path.name, "status": "error", "issues": [str(error)]})
    return results


def main() -> None:
    results = analyze_directory()
    if not results:
        raise FileNotFoundError(f"No supported video files found in: {VIDEO_DIR}")

    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    issue_results = [result for result in results if result["status"] != "normal"]
    ISSUE_PATH.write_text(json.dumps(issue_results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved metadata for {len(results)} video(s) to {RESULT_PATH}.")
    print(f"Saved {len(issue_results)} warning/error result(s) to {ISSUE_PATH}.")


if __name__ == "__main__":
    main()
