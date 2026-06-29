# Anything to PDF Converter & Merger

다양한 형식의 파일을 PDF로 변환하고 하나로 병합하는 GUI 프로그램입니다.

## 지원 형식
- **이미지**: PNG, JPG, JPEG
- **문서**: HWP, HWPX, DOC, DOCX, PPT, PPTX
- **기존 PDF**: 병합 가능

## 주요 기능
- **드래그 앤 드롭**: 파일을 앱으로 직접 끌어다 놓을 수 있습니다.
- **순서 변경**: 목록에서 파일을 드래그하여 병합 순서를 자유롭게 조정할 수 있습니다.
- **자동 변환**: 지원되는 모든 형식을 임시 PDF로 변환 후 최종적으로 하나의 파일로 병합합니다.

## 설치 및 실행 방법 (Python)

1. 필요한 라이브러리 설치:
   ```bash
   pip install -r requirements.txt
   ```

2. 프로그램 실행:
   ```bash
   python main.py
   ```

## EXE 빌드 방법 (Windows 전용)

`PyInstaller`를 사용하여 단일 실행 파일을 만들 수 있습니다.

```bash
pyinstaller --noconfirm --onefile --windowed --name "AnythingToPDF" main.py
```

빌드가 완료되면 `dist` 폴더 안에 `AnythingToPDF.exe` 파일이 생성됩니다.

## 주의 사항
- **HWP/HWPX 변환**: 한컴오피스가 설치되어 있지 않아도 `simple-hwp2pdf`를 통해 변환을 시도하지만, 완벽한 레이아웃을 위해서는 한컴오피스가 설치된 환경을 권장합니다.
- **Office 문서 (DOC/PPT)**: Windows 환경에서 Microsoft Office가 설치되어 있어야 정상적으로 변환됩니다.
