"""Extract metadata from every video in the video directory."""

import json
from pathlib import Path

import cv2


VIDEO_DIR = Path(__file__).with_name("video")
RESULT_PATH = Path(__file__).with_name("result.txt")
ISSUE_PATH = Path(__file__).with_name("issue.txt")
VIDEO_EXTENSIONS = {".avi", ".mp4", ".mov", ".mkv", ".wmv"}
EXPECTED_FPS = 30.0
EXPECTED_DURATION_SECONDS = 30.0
FPS_TOLERANCE = 0.1
DURATION_TOLERANCE_SECONDS = 0.1


def extract_metadata(video_path: Path) -> dict[str, object]:
    """Read video metadata using OpenCV."""
    capture = cv2.VideoCapture(str(video_path))
    try:
        if not capture.isOpened():
            raise RuntimeError(f"동영상 파일을 열 수 없습니다: {video_path}")

        fps = capture.get(cv2.CAP_PROP_FPS)
        frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT)
        width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        codec_value = int(capture.get(cv2.CAP_PROP_FOURCC))
        codec = "".join(
            chr((codec_value >> (8 * index)) & 0xFF)
            for index in range(4)
            if (codec_value >> (8 * index)) & 0xFF
        )

        metadata: dict[str, object] = {
            "file": video_path.name,
            "fps": fps,
            "frame_count": int(frame_count),
            "duration_seconds": frame_count / fps if fps > 0 else None,
            "width": int(width),
            "height": int(height),
            "codec": codec or "unknown",
            "backend": capture.getBackendName(),
        }
        return metadata
    finally:
        capture.release()


def create_issue_report(results: list[dict[str, object]]) -> str:
    """Create a report for videos outside the expected FPS or duration."""
    issue_lines = [
        "영상 이슈 목록",
        f"기준 FPS: {EXPECTED_FPS:g} (허용 오차: ±{FPS_TOLERANCE:g})",
        f"기준 duration: {EXPECTED_DURATION_SECONDS:g}초 "
        f"(허용 오차: ±{DURATION_TOLERANCE_SECONDS:g}초)",
        "",
    ]

    for metadata in results:
        file_name = metadata["file"]
        if "error" in metadata:
            issue_lines.append(f"- {file_name}: 메타데이터 추출 실패")
            issue_lines.append(f"  이유: {metadata['error']}")
            continue

        issues: list[str] = []
        fps = float(metadata["fps"])
        duration = float(metadata["duration_seconds"])
        if abs(fps - EXPECTED_FPS) > FPS_TOLERANCE:
            issues.append(f"fps (실제 {fps:.3f})")
        if abs(duration - EXPECTED_DURATION_SECONDS) > DURATION_TOLERANCE_SECONDS:
            issues.append(f"duration (실제 {duration:.3f}초)")

        if issues:
            issue_lines.append(f"- {file_name}: {', '.join(issues)}")

    if len(issue_lines) == 4:
        issue_lines.append("이슈가 있는 영상이 없습니다.")

    return "\n".join(issue_lines) + "\n"


def main() -> None:
    if not VIDEO_DIR.is_dir():
        raise FileNotFoundError(f"video 폴더를 찾을 수 없습니다: {VIDEO_DIR}")

    video_paths = sorted(
        path
        for path in VIDEO_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    )
    if not video_paths:
        raise FileNotFoundError(f"video 폴더에 영상 파일이 없습니다: {VIDEO_DIR}")

    results: list[dict[str, object]] = []
    for video_path in video_paths:
        try:
            results.append(extract_metadata(video_path))
        except RuntimeError as error:
            results.append({"file": video_path.name, "error": str(error)})

    RESULT_PATH.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    ISSUE_PATH.write_text(create_issue_report(results), encoding="utf-8")
    print(f"{len(video_paths)}개 영상의 메타데이터를 {RESULT_PATH}에 저장했습니다.")
    print(f"FPS/duration 이슈 목록을 {ISSUE_PATH}에 저장했습니다.")


if __name__ == "__main__":
    main()