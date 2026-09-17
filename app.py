"""Local Flask application for analysing uploaded organoid videos."""

from __future__ import annotations

import logging
import os
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from extract_avi_metadata import EXPECTED_FPS, FPS_TOLERANCE, VIDEO_EXTENSIONS, extract_metadata

HOST = "127.0.0.1"
PORT = 5000
DURATION_WARNING_SECONDS = 31.0


def is_frozen() -> bool:
    """Return whether the application is running from a PyInstaller bundle."""
    return bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))


def resource_path(relative_path: str) -> Path:
    """Resolve bundled resources in PyInstaller and source files in development."""
    base_path = Path(sys._MEIPASS) if is_frozen() else Path(__file__).resolve().parent
    return base_path / relative_path


app = Flask(
    __name__,
    template_folder=str(resource_path("templates")),
    static_folder=str(resource_path("static")),
)

# Vercel Functions impose a small request-body limit. Keep that restriction only
# on Vercel; local development and the Windows executable intentionally have no
# Flask upload-size limit so normal/large videos can be analysed locally.
if os.environ.get("VERCEL"):
    app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024


@app.get("/")
def index():
    return render_template("index.html", expected_fps=EXPECTED_FPS)


@app.post("/api/analyze")
def analyze():
    uploads = request.files.getlist("files")
    if not uploads or all(not upload.filename for upload in uploads):
        return jsonify({"error": "Please select video files to analyse."}), 400
    return jsonify(
        {
            "results": [analyze_upload(upload) for upload in uploads if upload.filename],
            "rules": validation_rules(),
        }
    )


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
            temp_path.unlink()


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

def terminate_process_after_response(delay_seconds: float = 0.5) -> None:
    """Terminate the packaged application after the HTTP response is sent."""
    time.sleep(delay_seconds)
    os._exit(0)


@app.post("/api/shutdown")
def shutdown():
    """Shut down the local packaged application."""
    if not is_frozen():
        return jsonify(
            {
                "error": "Shutdown is only available in the packaged application."
            }
        ), 403

    threading.Thread(
        target=terminate_process_after_response,
        daemon=True,
    ).start()

    return jsonify({"ok": True})


def open_browser_when_ready(url: str, timeout_seconds: float = 15.0) -> None:
    """Open the default browser only after the local Flask server responds."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                if response.status < 500:
                    webbrowser.open(url)
                    return
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.2)
    logging.error("Local server did not become ready in time: %s", url)


def run_local_app() -> None:
    """Run the application locally, opening a browser for the packaged EXE."""
    url = f"http://{HOST}:{PORT}/"
    frozen = is_frozen()
    if frozen:
        threading.Thread(target=open_browser_when_ready, args=(url,), daemon=True).start()
    app.run(host=HOST, port=PORT, debug=not frozen, use_reloader=not frozen)


if __name__ == "__main__":
    run_local_app()
