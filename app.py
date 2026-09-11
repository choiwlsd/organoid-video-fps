"""Local Flask application for analysing uploaded organoid videos."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from extract_avi_metadata import (
    DURATION_TOLERANCE_SECONDS,
    EXPECTED_DURATION_SECONDS,
    EXPECTED_FPS,
    FPS_TOLERANCE,
    VIDEO_EXTENSIONS,
    extract_metadata,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024 * 1024  # 4 GB per request


@app.get("/")
def index():
    return render_template(
        "index.html",
        expected_fps=EXPECTED_FPS,
        expected_duration=EXPECTED_DURATION_SECONDS,
    )


@app.post("/api/analyze")
def analyze():
    uploads = request.files.getlist("files")
    if not uploads or all(not upload.filename for upload in uploads):
        return jsonify({"error": "분석할 영상 파일을 선택해주세요."}), 400

    results = [analyze_upload(upload) for upload in uploads if upload.filename]
    return jsonify({"results": results, "rules": validation_rules()})


def analyze_upload(upload) -> dict[str, object]:
    original_name = upload.filename or "unnamed"
    suffix = Path(original_name).suffix.lower()
    if suffix not in VIDEO_EXTENSIONS:
        return error_result(original_name, "지원하지 않는 형식입니다.")

    safe_name = secure_filename(original_name) or f"upload{suffix}"
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, prefix="organoid_", delete=False) as temp:
            temp_path = Path(temp.name)
        upload.save(temp_path)
        if temp_path.stat().st_size == 0:
            return error_result(original_name, "빈 파일입니다.")

        metadata = extract_metadata(temp_path)
        metadata["file"] = original_name
        metadata["size_bytes"] = temp_path.stat().st_size
        metadata["status"], metadata["issues"] = validate(metadata)
        return metadata
    except Exception as error:  # OpenCV can raise several backend-specific exceptions.
        return error_result(original_name, f"메타데이터를 읽지 못했습니다: {error}")
    finally:
        if temp_path and temp_path.exists():
            os.remove(temp_path)


def validate(metadata: dict[str, object]) -> tuple[str, list[str]]:
    issues: list[str] = []
    fps = float(metadata["fps"])
    duration = metadata["duration_seconds"]
    if abs(fps - EXPECTED_FPS) > FPS_TOLERANCE:
        issues.append(f"FPS {fps:.3f} (기준 {EXPECTED_FPS:g} ± {FPS_TOLERANCE:g})")
    if duration is None:
        issues.append("재생시간을 계산할 수 없음")
    elif abs(float(duration) - EXPECTED_DURATION_SECONDS) > DURATION_TOLERANCE_SECONDS:
        issues.append(
            f"재생시간 {float(duration):.3f}초 "
            f"(기준 {EXPECTED_DURATION_SECONDS:g}초 ± {DURATION_TOLERANCE_SECONDS:g}초)"
        )
    return ("issue" if issues else "normal", issues)


def error_result(file_name: str, message: str) -> dict[str, object]:
    return {"file": file_name, "status": "error", "issues": [message]}


def validation_rules() -> dict[str, float]:
    return {
        "expected_fps": EXPECTED_FPS,
        "fps_tolerance": FPS_TOLERANCE,
        "expected_duration_seconds": EXPECTED_DURATION_SECONDS,
        "duration_tolerance_seconds": DURATION_TOLERANCE_SECONDS,
    }


if __name__ == "__main__":
    app.run(debug=True)
