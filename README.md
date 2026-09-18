# Organoid Video Inspector

Local OpenCV video metadata analysis for organoid recordings. It supports batch uploads and reports FPS, frame count, duration, resolution, codec, file size, and validation warnings.

## Branch Guide

| Branch         | Purpose                                                                  |
| -------------- | ------------------------------------------------------------------------ |
| `main`         | Shared project baseline and documentation entry point.                   |
| `terminal`     | Original command-line workflow that reads files from `video/`.           |
| `exe`          | Windows standalone executable (`VideoMetadataChecker.exe`) distribution. |
| `local-server` | Flask browser UI for local drag-and-drop analysis.                       |

## Recommended Usage

Use the local application or Windows executable for real video files. Videos are processed on the same computer, stored only as temporary files during analysis, and deleted afterward.

```powershell
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in a browser.

## Validation Rules

| Field    | Warning condition         |
| -------- | ------------------------- |
| FPS      | Greater than `30.50`      |
| Duration | `31.00` seconds or longer |

The rules are defined once in `extract_avi_metadata.py` and are used by both the Flask UI and terminal workflow.

## Terminal Workflow

Place supported files in `video/`, then run:

```powershell
python extract_avi_metadata.py
```

The script writes all results to `result.txt` and warning/error entries to `issue.txt`.

## Windows Executable

Build the executable on Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pyinstaller VideoMetadataChecker.spec
```

The output is `dist/VideoMetadataChecker.exe`.

## Formatting

```powershell
npm ci
npm run format:check
```

`requirements.txt` contains both the runtime packages and PyInstaller. This branch builds and runs locally, so a separate development requirements file is unnecessary.
