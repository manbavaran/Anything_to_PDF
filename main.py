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

from converter import PDFConverterLogic, SUPPORTED_EXTS


APP_TITLE = "Anything to PDF Converter & Merger"
INSTRUCTIONS = (
    "Drag files here or click Add Files.\n"
    "Files are sorted by name first. Drag or use Move Up/Down to set the final PDF order."
)
SUPPORTED_LABEL = "Supported: PDF, PNG, JPG, JPEG, WEBP, HWP, HWPX, DOC, DOCX, PPT, PPTX"
PATH_ROLE = Qt.ItemDataRole.UserRole


def run_self_test():
    from PIL import Image
    from PyPDF2 import PdfReader

    temp_root = Path.cwd() / ".tmp"
    temp_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=temp_root) as temp_dir:
        temp_path = Path(temp_dir)
        first = temp_path / "first.png"
        second = temp_path / "second.jpg"
        third = temp_path / "third.webp"
        output = temp_path / "merged.pdf"

        Image.new("RGBA", (120, 120), (37, 99, 235, 180)).save(first)
        Image.new("RGB", (120, 120), (16, 185, 129)).save(second)
        Image.new("RGB", (120, 120), (244, 114, 182)).save(third)

        logic = PDFConverterLogic()
        generated = []
        try:
            generated.append(logic.convert_to_pdf(first))
            generated.append(logic.convert_to_pdf(second))
            generated.append(logic.convert_to_pdf(third))
            logic.merge_pdfs(generated, output)
        finally:
            logic.cleanup_temps(generated)

        if not output.exists() or len(PdfReader(str(output)).pages) != 3:
            raise RuntimeError("Self-test PDF output was not created correctly.")


def run_ui_smoke_test():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()

    temp_root = Path.cwd() / ".tmp"
    temp_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=temp_root) as temp_dir:
        temp_path = Path(temp_dir)
        zeta = temp_path / "zeta.webp"
        alpha = temp_path / "alpha.png"

        from PIL import Image

        Image.new("RGB", (20, 20), (255, 0, 0)).save(zeta)
        Image.new("RGB", (20, 20), (0, 0, 255)).save(alpha)

        window.file_list.add_files([str(zeta), str(alpha)])
        window.file_list.refresh_engine_labels()

        if window.file_list.count() != 2:
            raise RuntimeError("UI smoke test did not add files.")
        if Path(window.file_list.item(0).data(PATH_ROLE)).name != "alpha.png":
            raise RuntimeError("UI smoke test did not sort files by name.")
        if "Pillow" not in window.file_list.item(0).text():
            raise RuntimeError("UI smoke test did not show the conversion engine.")

        window.file_list.item(0).setSelected(True)
        window.move_selected_down()
        if Path(window.file_list.item(1).data(PATH_ROLE)).name != "alpha.png":
            raise RuntimeError("UI smoke test did not move selected files.")

    window.close()
    app.quit()


class FileListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.supported_exts = SUPPORTED_EXTS
        self.logic = None

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
            dropped_files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    dropped_files.append(file_path)
            self.add_files(dropped_files)
        else:
            super().dropEvent(event)

    def add_files(self, file_paths):
        for file_path in sorted(file_paths, key=lambda p: Path(p).name.lower()):
            self.add_file(file_path)
        self.sortItems(Qt.SortOrder.AscendingOrder)

    def add_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext in self.supported_exts and not self._contains(file_path):
            item = QListWidgetItem(self._display_text(file_path))
            item.setData(PATH_ROLE, str(Path(file_path)))
            item.setToolTip(str(Path(file_path)))
            self.addItem(item)

    def _contains(self, file_path):
        normalized = os.path.normcase(os.path.abspath(file_path))
        for i in range(self.count()):
            current = os.path.normcase(os.path.abspath(self.item(i).data(PATH_ROLE)))
            if current == normalized:
                return True
        return False

    def refresh_engine_labels(self):
        for i in range(self.count()):
            item = self.item(i)
            item.setText(self._display_text(item.data(PATH_ROLE)))

    def _display_text(self, file_path):
        path = Path(file_path)
        if self.logic is None:
            return path.name
        engine = self.logic.engine_for(path)
        return f"{path.name}    |    {engine.label}"


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
        self.file_list.logic = self.logic
        self.file_list.setAlternatingRowColors(True)
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.file_list)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Files")
        self.btn_add.clicked.connect(self.add_files)
        self.btn_up = QPushButton("Move Up")
        self.btn_up.clicked.connect(self.move_selected_up)
        self.btn_down = QPushButton("Move Down")
        self.btn_down.clicked.connect(self.move_selected_down)
        self.btn_remove = QPushButton("Remove Selected")
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.clicked.connect(self.file_list.clear)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_up)
        btn_layout.addWidget(self.btn_down)
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
            "All Supported Files (*.hwp *.hwpx *.doc *.docx *.ppt *.pptx *.jpg *.jpeg *.png *.webp *.pdf);;"
            "Documents (*.hwp *.hwpx *.doc *.docx *.ppt *.pptx);;"
            "Images (*.jpg *.jpeg *.png *.webp);;PDF Files (*.pdf)",
        )
        self.file_list.add_files(files)
        self.file_list.refresh_engine_labels()

    def remove_selected(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def move_selected_up(self):
        rows = sorted({self.file_list.row(item) for item in self.file_list.selectedItems()})
        for row in rows:
            if row <= 0:
                continue
            item = self.file_list.takeItem(row)
            self.file_list.insertItem(row - 1, item)
            item.setSelected(True)

    def move_selected_down(self):
        rows = sorted(
            {self.file_list.row(item) for item in self.file_list.selectedItems()},
            reverse=True,
        )
        for row in rows:
            if row >= self.file_list.count() - 1:
                continue
            item = self.file_list.takeItem(row)
            self.file_list.insertItem(row + 1, item)
            item.setSelected(True)

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
        failures = []
        try:
            self.btn_convert.setEnabled(False)
            for i in range(count):
                file_path = self.file_list.item(i).data(PATH_ROLE)
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
                    else:
                        failures.append(f"{os.path.basename(file_path)}: no output PDF")

            if failures:
                raise RuntimeError("\n".join(failures))

            self.statusBar().showMessage("Merging PDFs...")
            QApplication.processEvents()
            self.logic.merge_pdfs(temp_pdfs, save_path)

            self.statusBar().showMessage("Done")
            QMessageBox.information(
                self, "PDF created", f"The merged PDF was created successfully.\n{save_path}"
            )
        except Exception as e:
            self.statusBar().showMessage("Failed")
            QMessageBox.critical(
                self,
                "Conversion failed",
                "Could not create the PDF.\n\n"
                "If this involved HWP/HWPX, install Hancom Office for layout-preserving "
                "conversion. LibreOffice fallback is experimental for those files.\n\n"
                f"Details:\n{str(e)}",
            )
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
    if "--ui-smoke-test" in sys.argv:
        run_ui_smoke_test()
        sys.exit(0)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
