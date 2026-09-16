# Organoid Video Inspector

A local, OpenCV-powered web application for inspecting organoid videos. Upload one or more files to extract their metadata and flag files that do not meet the expected FPS.

## Features

- Drag-and-drop or file-picker upload
- Batch analysis of AVI, MP4, MOV, MKV, and WMV files
- Metadata extraction: FPS, frame count, duration, resolution, codec, and file size
- FPS validation against the configured expected value
- Per-file validation errors and analysis error messages
- Temporary uploads are deleted immediately after analysis

## Installation and Usage

Python 3.9 or later is required.

```powershell
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Validation Rule

| Field    | Warning condition       |
| -------- | ----------------------- |
| FPS      | Greater than 30.50      |
| Duration | 31.00 seconds or longer |

Change `FPS_WARNING_THRESHOLD` and `DURATION_WARNING_SECONDS` in `app.py` to use different rules.

## Project Structure

```text
├── app.py
├── extract_avi_metadata.py
├── templates/
│   └── index.html
├── static/
│   ├── css/style.css
│   └── js/app.js
└── requirements.txt
```

## File Handling and Privacy

The application runs locally. Uploaded videos are written to a temporary file while OpenCV analyses them, then deleted whether analysis succeeds or fails. Files are not permanently stored or sent to an external server.

## Vercel Deployment Note

The project can serve its Flask UI from Vercel using `opencv-python-headless`. However, Vercel Functions limit a request body to 4.5 MB, so direct video uploads larger than approximately 4 MB cannot be analyzed there. Use the local application for ordinary video files, or add a direct-to-storage upload and a separate video-processing service for production-scale uploads.
