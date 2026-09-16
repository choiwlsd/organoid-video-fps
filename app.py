"""Local Flask application for analysing uploaded organoid videos."""

from __future__ import annotations

import os
import tempfile
import threading
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from extract_avi_metadata import EXPECTED_FPS, FPS_TOLERANCE, VIDEO_EXTENSIONS, extract_metadata

app = Flask(__name__)
# Vercel Functions cap request bodies at 4.5 MB; retain a small multipart safety margin.
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024
DURATION_WARNING_SECONDS = 31.0


@app.get("/")
def index():
    return render_template("index.html", expected_fps=EXPECTED_FPS)


@app.post("/api/analyze")
def analyze():
    uploads = request.files.getlist("files")
    if not uploads or all(not upload.filename for upload in uploads):
        return jsonify({"error": "Please select video files to analyse."}), 400
    return jsonify({"results": [analyze_upload(upload) for upload in uploads if upload.filename], "rules": validation_rules()})


@app.post("/api/shutdown")
def shutdown():
    """Stop only a locally run development server after sending its response."""
    if request.remote_addr not in {"127.0.0.1", "::1"}:
        return jsonify({"error": "Program shutdown is only available locally."}), 403
    threading.Timer(0.25, os._exit, args=(0,)).start()
    return jsonify({"message": "The local server is shutting down."})


def analyze_upload(upload) -> dict[str, object]:
    original_name = upload.filename or "unnamed"
    suffix = Path(original_name).suffix.lower()
    if suffix not in VIDEO_EXTENSIONS:
        return error_result(original_name, "Unsupported file format.")

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, prefix="organoid_", delete=False) as temp:
            temp_path = Path(temp.name)
        upload.save(temp_path)
        if temp_path.stat().st_size == 0:
            return error_result(original_name, "The uploaded file is empty.")
        metadata = extract_metadata(temp_path)
        metadata["file"] = original_name
        metadata["size_bytes"] = temp_path.stat().st_size
        metadata["status"], metadata["issues"] = validate(metadata)
        return metadata
    except Exception as error:
        return error_result(original_name, f"Could not read video metadata: {error}")
    finally:
        if temp_path and temp_path.exists():
            os.remove(temp_path)


def validate(metadata: dict[str, object]) -> tuple[str, list[str]]:
    """Flag incorrect FPS and durations of 31 seconds or more."""
    fps = float(metadata["fps"])
    duration = metadata.get("duration_seconds")
    issues: list[str] = []
    if abs(fps - EXPECTED_FPS) > FPS_TOLERANCE:
        issues.append(f"FPS {fps:.3f} (expected {EXPECTED_FPS:g} +/- {FPS_TOLERANCE:g})")
    if duration is not None and float(duration) >= DURATION_WARNING_SECONDS:
        issues.append(f"Duration {float(duration):.3f} s (limit {DURATION_WARNING_SECONDS:g} s)")
    return ("issue", issues) if issues else ("normal", [])


def error_result(file_name: str, message: str) -> dict[str, object]:
    return {"file": file_name, "status": "error", "issues": [message]}


def validation_rules() -> dict[str, float]:
    return {
        "expected_fps": EXPECTED_FPS,
        "fps_tolerance": FPS_TOLERANCE,
        "duration_warning_seconds": DURATION_WARNING_SECONDS,
    }


if __name__ == "__main__":
    app.run(debug=False)
