from cx_Freeze import Executable, setup


build_exe_options = {
    "build_exe": "build/AnythingToPDF",
    "includes": [
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
    ],
    "packages": [
        "PIL",
        "PyPDF2",
        "comtypes",
        "pythoncom",
        "win32com",
    ],
    "excludes": [
        "PyQt6.QtBluetooth",
        "PyQt6.QtDesigner",
        "PyQt6.QtHelp",
        "PyQt6.QtMultimedia",
        "PyQt6.QtMultimediaWidgets",
        "PyQt6.QtNetwork",
        "PyQt6.QtNfc",
        "PyQt6.QtOpenGL",
        "PyQt6.QtOpenGLWidgets",
        "PyQt6.QtPdf",
        "PyQt6.QtPdfWidgets",
        "PyQt6.QtPositioning",
        "PyQt6.QtPrintSupport",
        "PyQt6.QtQml",
        "PyQt6.QtQuick",
        "PyQt6.QtQuick3D",
        "PyQt6.QtRemoteObjects",
        "PyQt6.QtSensors",
        "PyQt6.QtSerialPort",
        "PyQt6.QtSql",
        "PyQt6.QtSvg",
        "PyQt6.QtTest",
        "PyQt6.QtTextToSpeech",
        "PyQt6.QtWebChannel",
        "PyQt6.QtWebSockets",
        "tkinter",
        "unittest",
        "pytest",
    ],
    "include_msvcr": True,
}


setup(
    name="AnythingToPDF",
    version="1.0.0",
    description="Convert supported files to PDF and merge them in order.",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "main.py",
            base="gui",
            target_name="AnythingToPDF.exe",
        )
    ],
)
