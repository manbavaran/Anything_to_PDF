# Anything to PDF 변환 및 병합

지원 파일을 PDF로 변환하고 하나의 PDF로 병합하는 Windows GUI 프로그램입니다. 기본 UI는 한국어로 제공됩니다.

## 인수인계 요약

- 저장소: `https://github.com/manbavaran/Anything_to_PDF`
- 실행 파일: `dist/AnythingToPDF.exe`
- 진입점: `main.py`
- 핵심 로직: `converter.py`
- 테스트: `tests/smoke_test.py`, `tests/verify_exe.ps1`
- Python: Windows Python 3.11 이상 권장

### 현재 상태

- 이미지(PNG/JPG/JPEG/WEBP) 변환 및 PDF 병합 검증 완료
- 한국어 UI 및 오류 메시지 적용 완료
- PyInstaller 단일 EXE 빌드 및 EXE self-test 통과
- HWP/HWPX, DOC/DOCX, PPT/PPTX는 설치된 Office 프로그램에 따라 변환 엔진이 선택됨

## Supported files

- Images: PNG, JPG, JPEG, WEBP
- Documents: HWP, HWPX, DOC, DOCX, PPT, PPTX
- Existing PDFs: included directly in the merge order

## Features

- Add files by button or drag and drop
- Files are sorted by name by default
- Reorder merge order by dragging list items or using Move Up/Move Down
- Convert images and documents to PDF, then merge them
- Show the selected conversion engine and fidelity level for each file
- Clean up temporary conversion files automatically
- Clear status and error messages in the GUI

## 소스에서 실행

Tested on Windows with Python 3.11.

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
```

If you are already inside an activated virtual environment, this also works:

```bash
pip install -r requirements.txt
python main.py
```

## 테스트 및 검증

Run the smoke tests before building on a new PC:

```bash
.venv\Scripts\python tests\smoke_test.py
.venv\Scripts\python main.py --self-test
.venv\Scripts\python main.py --ui-smoke-test
powershell -ExecutionPolicy Bypass -File tests\verify_exe.ps1
```

## Windows 단일 EXE 빌드

For a single-file executable, use PyInstaller:

```bash
.venv\Scripts\python -m PyInstaller --onefile --windowed --name AnythingToPDF main.py
```

The single executable is created at:

```bash
dist\AnythingToPDF.exe
```

The project also keeps a `cx_Freeze` build path for folder-style distribution:

```bash
.venv\Scripts\python setup.py build_exe
```

The built app is created under `build/AnythingToPDF/`. Run:

```bash
build\AnythingToPDF\AnythingToPDF.exe
```

## 변환 요구사항

- PNG/JPG/JPEG/WEBP image conversion and PDF merging are fully local and do not require Office apps.
- HWP/HWPX high-fidelity conversion requires Hancom Office.
- HWP/HWPX conversion without Hancom uses LibreOffice only as an experimental fallback, when available. Layout, tables, images, fonts, and page breaks are not guaranteed.
- If Hancom Office and LibreOffice are both unavailable, `rhwp-python` provides an additional experimental HWP/HWPX-to-PDF rendering fallback. It is intended for best-effort output and may differ on complex tables, fonts, and page layout.
- DOC/DOCX/PPT/PPTX conversion prefers Microsoft Office and falls back to LibreOffice when Office is unavailable.
- Existing PDFs are merged directly without conversion.

Optional external converters are detected at runtime:

- Microsoft Word: high-fidelity DOC/DOCX export, experimental HWP only when Word has an HWP import filter.
- Microsoft PowerPoint: high-fidelity PPT/PPTX export.
- Hancom Office: high-fidelity HWP/HWPX export.
- LibreOffice: fallback DOC/DOCX/PPT/PPTX export, experimental HWP/HWPX export.
- rhwp: no-Office HWP/HWPX rendering fallback, installed from `rhwp-python`.

If none of the required external converters are installed, the GUI marks that file's engine as unavailable instead of silently producing a low-quality PDF.
