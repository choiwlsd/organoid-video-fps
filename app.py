"""Local Flask server for organoid video metadata analysis."""

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
from typing import Any

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge

from extract_avi_metadata import (
    DURATION_WARNING_SECONDS,
    FPS_WARNING_THRESHOLD,
    VIDEO_EXTENSIONS,
    add_validation_result,
    extract_metadata,
)

HOST = "127.0.0.1"
PORT = 5000


def is_frozen() -> bool:
    """Return whether the application runs from a PyInstaller bundle."""
    return bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))


def resource_path(relative_path: str) -> Path:
    """Resolve resources from the bundle or project directory."""
    base_path = Path(sys._MEIPASS) if is_frozen() else Path(__file__).resolve().parent
    return base_path / relative_path


app = Flask(
    __name__,
    template_folder=str(resource_path("templates")),
    static_folder=str(resource_path("static")),
)

@app.get("/")
def index():
    return render_template(
        "index.html",
        fps_warning_threshold=FPS_WARNING_THRESHOLD,
        duration_warning_seconds=DURATION_WARNING_SECONDS,
        packaged=is_frozen(),
    )


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(_error):
    return jsonify({"error": "The selected files exceed this server's upload size limit."}), 413


@app.post("/api/analyze")
def analyze():
    uploads = [upload for upload in request.files.getlist("files") if upload.filename]
    if not uploads:
        return jsonify({"error": "Please select video files to analyse."}), 400
    return jsonify({"results": [analyze_upload(upload) for upload in uploads]})


def analyze_upload(upload) -> dict[str, Any]:
    original_name = upload.filename or "unnamed"
    suffix = Path(original_name).suffix.lower()
    if suffix not in VIDEO_EXTENSIONS:
        return error_result(original_name, "Unsupported file format.")

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, prefix="organoid_", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        upload.save(temp_path)
        if temp_path.stat().st_size == 0:
            return error_result(original_name, "The uploaded file is empty.")

        result = add_validation_result(extract_metadata(temp_path))
        result["file"] = original_name
        result["size_bytes"] = temp_path.stat().st_size
        return result
    except Exception as error:
        return error_result(original_name, f"Could not read video metadata: {error}")
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


def error_result(file_name: str, message: str) -> dict[str, Any]:
    return {"file": file_name, "status": "error", "issues": [message]}


@app.post("/api/shutdown")
def shutdown():
    """End only the packaged local application after returning a response."""
    if not is_frozen():
        return jsonify({"error": "Program shutdown is only available in the packaged application."}), 403
    threading.Thread(target=terminate_process_after_response, daemon=True).start()
    return jsonify({"ok": True})


def terminate_process_after_response(delay_seconds: float = 0.5) -> None:
    time.sleep(delay_seconds)
    os._exit(0)


def open_browser_when_ready(url: str, timeout_seconds: float = 15.0) -> None:
    """Open the default browser after the bundled server starts responding."""
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
    """Run the local server and open a browser for the packaged application."""
    url = f"http://{HOST}:{PORT}/"
    if is_frozen():
        threading.Thread(target=open_browser_when_ready, args=(url,), daemon=True).start()
    app.run(host=HOST, port=PORT, debug=not is_frozen(), use_reloader=not is_frozen())


if __name__ == "__main__":
    run_local_app()
