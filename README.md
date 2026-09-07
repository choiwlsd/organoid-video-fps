# organoid-video-fps

A Python tool for automatically extracting metadata from video files and checking whether their FPS and duration match the expected values.

Place video files in the video directory and run the program. The metadata of all supported videos will be saved to `result.txt`, while videos with FPS/duration issues or metadata extraction failures will be reported in `issue.txt`.

### Supported Video Formats

The following video formats are supported: `.avi`, `.mp4`, `.mov`, `.mkv`, `.wmv`

### Requirements

- Python 3.9 or later
- OpenCV

Install OpenCV with:

```bash
pip install opencv-python
```

## Usage

### 1. Prepare the Videos

Place the videos you want to analyze in the video directory.

For example:

```
video/
├── organoid_01.avi
├── organoid_02.avi
└── organoid_03.avi
```

### 2. Run the Program

Run the following command from the project directory:

```bash
python extract_avi_metadata.py
```

After the analysis is complete, the program will display messages similar to:

```
3 videos' metadata saved to .../result.txt.
FPS/duration issues saved to .../issue.txt.
```

### 3. Check the Results

Two output files will be generated:

```
result.txt
issue.txt
```
