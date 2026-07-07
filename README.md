# Anything to PDF Converter & Merger

Anything to PDF Converter & Merger is a Windows GUI app for converting supported files to PDF and merging them into one output file.

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

## Run from source

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

## Verify

Run the smoke tests before building on a new PC:

```bash
.venv\Scripts\python tests\smoke_test.py
.venv\Scripts\python main.py --self-test
.venv\Scripts\python main.py --ui-smoke-test
```

## Build a Windows EXE

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

## Conversion requirements

- PNG/JPG/JPEG/WEBP image conversion and PDF merging are fully local and do not require Office apps.
- HWP/HWPX high-fidelity conversion requires Hancom Office.
- HWP/HWPX conversion without Hancom uses LibreOffice only as an experimental fallback, when available. Layout, tables, images, fonts, and page breaks are not guaranteed.
- DOC/DOCX/PPT/PPTX conversion prefers Microsoft Office and falls back to LibreOffice when Office is unavailable.
- Existing PDFs are merged directly without conversion.

Optional external converters are detected at runtime:

- Microsoft Word: high-fidelity DOC/DOCX export, experimental HWP only when Word has an HWP import filter.
- Microsoft PowerPoint: high-fidelity PPT/PPTX export.
- Hancom Office: high-fidelity HWP/HWPX export.
- LibreOffice: fallback DOC/DOCX/PPT/PPTX export, experimental HWP/HWPX export.

If none of the required external converters are installed, the GUI marks that file's engine as unavailable instead of silently producing a low-quality PDF.
