# Organoid Video Inspector

A local, OpenCV-powered web application for inspecting organoid video files. Upload one or more videos to extract metadata and flag files that do not meet the expected FPS or duration.

## Features

- Drag-and-drop or file-picker video upload
- Batch analysis of AVI, MP4, MOV, MKV, and WMV files
- Metadata extraction: FPS, frame count, duration, resolution, codec, and file size
- Automatic validation against expected FPS and duration values
- Per-file analysis errors and validation issue messages
- Temporary uploads are deleted immediately after analysis

## Requirements

- Python 3.9 or later
- A local OpenCV-compatible video backend

## Installation and Usage

From the project directory, install the dependencies and start the application:

```powershell
pip install -r requirements.txt
python app.py
```

Then open the following URL in a browser:

```text
http://127.0.0.1:5000
```

## How to Use

1. Drag video files into the upload area, or click **Select files**.
2. You can submit multiple files in one request.
3. Review each file's FPS, frame count, duration, resolution, codec, file size, and validation result in the results table.

Supported formats: `.avi`, `.mp4`, `.mov`, `.mkv`, `.wmv`

## Validation Rules

| Field | Expected value | Tolerance |
| --- | ---: | ---: |
| FPS | 30 | ±0.1 |
| Duration | 30 seconds | ±0.1 seconds |

You can change these values in `extract_avi_metadata.py`:

- `EXPECTED_FPS`
- `FPS_TOLERANCE`
- `EXPECTED_DURATION_SECONDS`
- `DURATION_TOLERANCE_SECONDS`

## Project Structure

```text
├── app.py                         # Flask application and analysis API
├── extract_avi_metadata.py        # OpenCV metadata extraction logic
├── templates/
│   └── index.html                 # User interface
├── static/
│   ├── css/style.css
│   └── js/app.js
└── requirements.txt
```

## File Handling and Privacy

The application runs locally. Uploaded videos are written to a temporary file only while OpenCV analyses them, then deleted whether analysis succeeds or fails. Files are not permanently stored or sent to an external server.
