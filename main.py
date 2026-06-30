import os
import sys
import tempfile
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from converter import PDFConverterLogic


APP_TITLE = "Anything to PDF Converter & Merger"
INSTRUCTIONS = (
    "Drag files here or click Add Files.\n"
    "Reorder the list by dragging items before creating the merged PDF."
)
SUPPORTED_LABEL = "Supported: PDF, PNG, JPG, JPEG, HWP, HWPX, DOC, DOCX, PPT, PPTX"
SUPPORTED_EXTS = [
    ".png",
    ".jpg",
    ".jpeg",
    ".hwp",
    ".hwpx",
    ".ppt",
    ".pptx",
    ".doc",
    ".docx",
    ".pdf",
]


def run_self_test():
    from PIL import Image
    from PyPDF2 import PdfReader

    temp_root = Path.cwd() / ".tmp"
    temp_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=temp_root) as temp_dir:
        temp_path = Path(temp_dir)
        first = temp_path / "first.png"
        second = temp_path / "second.jpg"
        output = temp_path / "merged.pdf"

        Image.new("RGBA", (120, 120), (37, 99, 235, 180)).save(first)
        Image.new("RGB", (120, 120), (16, 185, 129)).save(second)

        logic = PDFConverterLogic()
        generated = []
        try:
            generated.append(logic.convert_to_pdf(first))
            generated.append(logic.convert_to_pdf(second))
            logic.merge_pdfs(generated, output)
        finally:
            logic.cleanup_temps(generated)

        if not output.exists() or len(PdfReader(str(output)).pages) != 2:
            raise RuntimeError("Self-test PDF output was not created correctly.")


class FileListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.supported_exts = SUPPORTED_EXTS

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    self.add_file(file_path)
        else:
            super().dropEvent(event)

    def add_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext in self.supported_exts and not self._contains(file_path):
            item = QListWidgetItem(str(Path(file_path)))
            item.setToolTip(str(Path(file_path)))
            self.addItem(item)

    def _contains(self, file_path):
        normalized = os.path.normcase(os.path.abspath(file_path))
        for i in range(self.count()):
            current = os.path.normcase(os.path.abspath(self.item(i).text()))
            if current == normalized:
                return True
        return False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(600, 400)
        self.logic = PDFConverterLogic()
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        title = QLabel(APP_TITLE)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 8px 0;")
        layout.addWidget(title)

        self.label = QLabel(INSTRUCTIONS)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: #333; margin-bottom: 6px;")
        layout.addWidget(self.label)

        supported = QLabel(SUPPORTED_LABEL)
        supported.setAlignment(Qt.AlignmentFlag.AlignCenter)
        supported.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(supported)

        self.file_list = FileListWidget()
        self.file_list.setAlternatingRowColors(True)
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.file_list)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Files")
        self.btn_add.clicked.connect(self.add_files)
        self.btn_remove = QPushButton("Remove Selected")
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.clicked.connect(self.file_list.clear)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)

        self.btn_convert = QPushButton("Create Merged PDF")
        self.btn_convert.setStyleSheet(
            "background-color: #2563eb; color: white; font-weight: bold; height: 42px;"
            "border-radius: 4px;"
        )
        self.btn_convert.clicked.connect(self.process_files)
        layout.addWidget(self.btn_convert)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select files",
            "",
            "All Supported Files (*.hwp *.hwpx *.doc *.docx *.ppt *.pptx *.jpg *.jpeg *.png *.pdf);;"
            "Documents (*.hwp *.hwpx *.doc *.docx *.ppt *.pptx);;"
            "Images (*.jpg *.jpeg *.png);;PDF Files (*.pdf)",
        )
        for file_path in files:
            self.file_list.add_file(file_path)

    def remove_selected(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def process_files(self):
        count = self.file_list.count()
        if count == 0:
            QMessageBox.warning(self, "No files", "Add at least one file before creating a PDF.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save merged PDF", "", "PDF Files (*.pdf)"
        )
        if not save_path:
            return

        if not save_path.lower().endswith(".pdf"):
            save_path += ".pdf"

        temp_pdfs = []
        generated_pdfs = []
        try:
            self.btn_convert.setEnabled(False)
            for i in range(count):
                file_path = self.file_list.item(i).text()
                ext = os.path.splitext(file_path)[1].lower()

                if ext == ".pdf":
                    temp_pdfs.append(file_path)
                else:
                    self.statusBar().showMessage(f"Converting {os.path.basename(file_path)}...")
                    QApplication.processEvents()
                    pdf_path = self.logic.convert_to_pdf(file_path)
                    if pdf_path:
                        temp_pdfs.append(pdf_path)
                        generated_pdfs.append(pdf_path)

            self.statusBar().showMessage("Merging PDFs...")
            QApplication.processEvents()
            self.logic.merge_pdfs(temp_pdfs, save_path)

            self.statusBar().showMessage("Done")
            QMessageBox.information(
                self, "PDF created", f"The merged PDF was created successfully.\n{save_path}"
            )
        except Exception as e:
            self.statusBar().showMessage("Failed")
            QMessageBox.critical(self, "Conversion failed", f"Could not create the PDF:\n{str(e)}")
        finally:
            self.logic.cleanup_temps(generated_pdfs)
            self.btn_convert.setEnabled(True)
            self.label.setText(INSTRUCTIONS)
            if self.statusBar().currentMessage() != "Done":
                self.statusBar().showMessage("Ready")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        run_self_test()
        sys.exit(0)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
