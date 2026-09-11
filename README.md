# Organoid Video Inspector / VideoMetadataChecker

Flask + OpenCV 기반의 로컬 영상 메타데이터 분석 도구입니다. AVI, MP4, MOV, MKV, WMV 파일을 한 번에 여러 개 선택해 FPS, 프레임 수, 재생 시간, 해상도, 코덱, 파일 크기를 확인할 수 있습니다.

## Windows 사용자

Windows 배포본은 Python이나 OpenCV를 별도로 설치하지 않고 실행할 수 있습니다.

1. `VideoMetadataChecker.exe`를 다운로드합니다.
2. `VideoMetadataChecker.exe`를 더블클릭합니다.
3. 기본 브라우저가 자동으로 열리면 영상 파일을 선택합니다.
4. 브라우저에서 메타데이터와 검증 결과를 확인합니다.

앱은 `http://127.0.0.1:5000`에서만 실행됩니다. 영상 데이터는 외부 서버나 외부 스토리지로 전송되지 않으며, 사용자 PC의 로컬 Flask 서버와 OpenCV에서만 처리됩니다. 브라우저가 로컬 Flask 서버로 전달한 영상은 OS 임시 디렉터리에 분석용으로 잠시 저장되고 분석 직후 삭제됩니다.

- Python 설치 불필요
- Flask 설치 불필요
- OpenCV 설치 불필요
- Windows용 독립 실행 파일
- 인터넷 연결 없이 핵심 영상 분석 기능 사용 가능

> Windows SmartScreen에서 서명되지 않은 실행 파일에 대한 경고가 표시될 수 있습니다. 조직 배포 시에는 코드 서명 인증서로 EXE에 서명하는 것을 권장합니다.

## 기능

- 드래그 앤 드롭 또는 파일 선택
- 여러 영상 파일 동시 선택 및 일괄 분석
- AVI, MP4, MOV, MKV, WMV 지원
- FPS, 프레임 수, 재생 시간, 해상도, 코덱, 파일 크기 추출
- 설정된 FPS 및 재생 시간 기준 검증
- 파일별 오류 및 검증 결과 표시
- 분석용 임시 파일 자동 삭제

## 개발자용 실행 방법

Python 3.9 이상을 권장합니다.

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
pyinstaller VideoMetadataChecker.spec
```

개발 환경에서는 Flask 디버그 모드로 `http://127.0.0.1:5000`에서 실행되며 로그를 콘솔에서 확인할 수 있습니다.

프론트엔드 포맷 검사를 하려면 Node.js 설치 후 다음을 실행합니다.

```powershell
npm ci
npm run format:check
```

## Windows EXE 빌드

PyInstaller는 운영체제별로 실행 파일을 생성하므로 **Windows용 EXE는 Windows에서 빌드**해야 합니다.

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
pyinstaller VideoMetadataChecker.spec
```

빌드 결과:

```text
dist/
└── VideoMetadataChecker.exe
```

`VideoMetadataChecker.spec`에는 Flask의 `templates/`, `static/` 리소스와 OpenCV의 PyInstaller 수집 대상이 포함되어 있습니다. 실행 파일은 `windowed` 방식(`console=False`)으로 만들어져 일반 사용자가 실행할 때 별도 콘솔 창을 표시하지 않습니다.

## 의존성

런타임 의존성은 `requirements.txt`에, 빌드/개발 의존성은 `requirements-dev.txt`에 분리되어 있습니다.

```text
requirements.txt
  Flask
  opencv-python-headless

requirements-dev.txt
  requirements.txt 포함
  PyInstaller
```

## 검증 규칙

| 항목          |       기준 |
| ------------- | ---------: |
| FPS           | 30 +/- 0.1 |
| Duration 경고 |  31초 이상 |

기준값은 `extract_avi_metadata.py`와 `app.py`에 정의되어 있습니다.

## 프로젝트 구조

```text
├── app.py
├── extract_avi_metadata.py
├── VideoMetadataChecker.spec
├── requirements.txt
├── requirements-dev.txt
├── templates/
│   └── index.html
└── static/
    ├── favicon.png
    ├── css/style.css
    └── js/app.js
```

## 파일 처리 및 개인정보

영상 파일은 외부 서버로 업로드되지 않습니다. 웹 UI와 분석 서버 모두 사용자 PC의 localhost에서 실행됩니다. 현재 브라우저 기반 UI의 기존 동작을 유지하기 위해 선택한 파일은 HTTP multipart 방식으로 `127.0.0.1`의 로컬 Flask 서버에 전달되고 OS 임시 파일로 저장된 뒤 OpenCV가 읽습니다. 분석 성공 여부와 관계없이 임시 파일은 `finally`에서 삭제됩니다.

로컬 실행 및 Windows EXE에는 Flask 업로드 크기 제한을 설정하지 않으므로 4 MB 이상의 영상도 분석할 수 있습니다. 실제 처리 가능 크기는 디스크 여유 공간과 OS/브라우저 환경의 영향을 받습니다.

## Vercel 관련 동작

기존 Vercel 호환 로직은 완전히 삭제하지 않았습니다. `VERCEL` 환경 변수가 있는 경우에만 기존 4 MB Flask 요청 제한이 적용되며, `.vercel.app` 호스트에서는 프론트엔드도 기존 용량 경고를 유지합니다.

따라서:

- 로컬 개발 / Windows EXE: 4 MB 제한 없음
- Vercel 환경: 기존 업로드 제한 유지

Vercel Functions는 대용량 영상 분석에 적합하지 않으므로 실제 영상 분석 배포본은 Windows 로컬 EXE를 사용하십시오.
