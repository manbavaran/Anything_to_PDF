# Agent Handoff: Anything_to_PDF

## Current Objective

Build a stable first Windows version of `Anything_to_PDF`: a GUI app that accepts one or more files by drag-and-drop or file browser, lets the user control merge order, converts supported files to PDF, and merges them into one output PDF.

Supported target formats:

- Images: PNG, JPG, JPEG, WEBP
- Documents: HWP, HWPX, DOC, DOCX, PPT, PPTX
- Existing PDFs: included directly in merge order

## Repository

- Local checkout used for this work: `C:\Users\sucy\Desktop\Anything_to_PDF`
- GitHub remote: `https://github.com/manbavaran/Anything_to_PDF.git`
- Branch: `main`
- Latest pushed commit at handoff time: `b0bbb89 Build stable converter fallback release`

## Important Product Decisions

1. WEBP support is required and implemented through Pillow.
2. File order matters. The app sorts newly added files by filename by default, then lets users reorder by dragging list items or using `Move Up` / `Move Down`.
3. Existing PDFs are never converted; they are appended directly in the current UI order.
4. HWP/HWPX conversion must be honest about fidelity:
   - Hancom Office is the only high-fidelity local path for HWP/HWPX.
   - LibreOffice is only an experimental fallback for HWP/HWPX.
   - Without Hancom/LibreOffice, the app marks HWP/HWPX conversion unavailable instead of pretending it can preserve layout.
5. DOC/DOCX/PPT/PPTX conversion prefers Microsoft Office COM and falls back to LibreOffice headless conversion.
6. `simple-hwp2pdf` was removed. Its package metadata claimed standalone behavior, but the inspected wheel implementation used MS Word COM and was not a reliable HWP/HWPX fallback.

## Key Files

- `main.py`
  - PyQt6 GUI.
  - Drag-and-drop and file browser.
  - Filename default sorting.
  - Manual order controls.
  - Hidden test modes:
    - `--self-test`
    - `--ui-smoke-test`
- `converter.py`
  - Conversion and merge engine.
  - Runtime engine detection.
  - Pillow image-to-PDF conversion.
  - Microsoft Office COM conversion.
  - Hancom HWP COM conversion.
  - LibreOffice headless fallback.
  - PDF merge via PyPDF2.
- `tests/smoke_test.py`
  - Basic image/WEBP conversion and PDF merge smoke test.
- `requirements.txt`
  - Pinned dependencies used during verification.
- `setup.py`
  - cx_Freeze folder-style build path.
- `README.md`
  - User/developer instructions for setup, verification, builds, and conversion limitations.

## Setup On A New Windows PC

From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Run from source:

```powershell
.venv\Scripts\python main.py
```

## Verification Commands

Run these before and after meaningful changes:

```powershell
.venv\Scripts\python tests\smoke_test.py
.venv\Scripts\python main.py --self-test
.venv\Scripts\python main.py --ui-smoke-test
.venv\Scripts\python -m py_compile main.py converter.py tests\smoke_test.py
```

Expected result: all commands exit with code `0`; `tests\smoke_test.py` prints `Smoke test passed.`

## Build Commands

Single-file EXE:

```powershell
.venv\Scripts\python -m PyInstaller --noconfirm --clean --onefile --windowed --name AnythingToPDF main.py
```

Output:

```text
dist\AnythingToPDF.exe
```

Verify the single-file EXE:

```powershell
dist\AnythingToPDF.exe --self-test
dist\AnythingToPDF.exe --ui-smoke-test
```

Folder-style cx_Freeze build:

```powershell
.venv\Scripts\python setup.py build_exe
```

Output:

```text
build\AnythingToPDF\AnythingToPDF.exe
```

Verify the cx_Freeze EXE:

```powershell
build\AnythingToPDF\AnythingToPDF.exe --self-test
build\AnythingToPDF\AnythingToPDF.exe --ui-smoke-test
```

## Git Hygiene

`.gitignore` excludes local and generated artifacts:

- `.venv/`
- `build/`
- `dist/`
- `*.spec`
- `*.egg-info/`
- `__pycache__/`
- `.tmp/`
- `.anything_to_pdf_tmp/`

Do not commit built EXE outputs unless explicitly requested.

## Verified State At Handoff

The following passed before the latest feature commit was pushed:

- Source smoke test
- Source self-test
- Source UI smoke test
- Python compile check
- PyInstaller single-file build
- Single-file EXE self-test
- Single-file EXE UI smoke test
- cx_Freeze build
- cx_Freeze EXE self-test
- cx_Freeze EXE UI smoke test

On the development PC used for verification, Microsoft Office, Hancom Office, and LibreOffice were not detected, so real DOCX/PPTX/HWP/HWPX conversion could not be live-tested there. The app did verify that those missing engines are reported as unavailable. Image, WEBP, PDF merge, ordering, and UI smoke behavior were verified.

## Suggested Next Work

1. Test real DOCX/PPTX conversion on a PC with Microsoft Office installed.
2. Test LibreOffice fallback on a PC with LibreOffice installed.
3. Test HWP/HWPX on a PC with Hancom Office installed.
4. Consider adding sample fixture files that can be legally committed for automated conversion regression tests.
5. Consider a release workflow that builds the PyInstaller EXE and attaches it to a GitHub release.
