# Anything to PDF Converter & Merger

Anything to PDF Converter & Merger is a Windows GUI app for converting supported files to PDF and merging them into one output file.

## Supported files

- Images: PNG, JPG, JPEG
- Documents: HWP, HWPX, DOC, DOCX, PPT, PPTX
- Existing PDFs: included directly in the merge order

## Features

- Add files by button or drag and drop
- Reorder merge order by dragging list items
- Convert images and documents to PDF, then merge them
- Clean up temporary conversion files automatically
- Clear status and error messages in the GUI

## Run from source

```bash
pip install -r requirements.txt
python main.py
```

## Build a Windows EXE

This project uses `cx_Freeze` instead of PyInstaller because some antivirus products flag PyInstaller one-file bootloaders.

```bash
python setup.py build_exe
```

The built app is created under `build/AnythingToPDF/`. Run:

```bash
build\AnythingToPDF\AnythingToPDF.exe
```

## Conversion requirements

- HWP/HWPX conversion depends on `simple-hwp2pdf` and local HWP support.
- DOC/DOCX/PPT/PPTX conversion requires Windows, Microsoft Office, and `comtypes`.
- Image conversion and PDF merging work without Microsoft Office.
