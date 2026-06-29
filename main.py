import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QListWidgetItem, QFileDialog, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from converter import PDFConverterLogic

class FileListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.supported_exts = ['.png', '.jpg', '.jpeg', '.hwp', '.hwpx', '.ppt', '.pptx', '.doc', '.docx', '.pdf']

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
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext in self.supported_exts:
                        self.addItem(file_path)
        else:
            super().dropEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anything to PDF Converter & Merger")
        self.setMinimumSize(600, 400)
        self.logic = PDFConverterLogic()

        # Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Instructions
        self.label = QLabel("파일을 드래그하여 놓거나 '파일 추가' 버튼을 누르세요.\n목록에서 드래그하여 순서를 변경할 수 있습니다.")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        # List Widget
        self.file_list = FileListWidget()
        layout.addWidget(self.file_list)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("파일 추가")
        self.btn_add.clicked.connect(self.add_files)
        self.btn_remove = QPushButton("선택 삭제")
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_clear = QPushButton("전체 비우기")
        self.btn_clear.clicked.connect(self.file_list.clear)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)

        self.btn_convert = QPushButton("PDF로 변환 및 병합")
        self.btn_convert.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 40px;")
        self.btn_convert.clicked.connect(self.process_files)
        layout.addWidget(self.btn_convert)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "파일 선택", "", 
            "All Supported Files (*.hwp *.hwpx *.doc *.docx *.ppt *.pptx *.jpg *.jpeg *.png *.pdf);;"
            "Documents (*.hwp *.hwpx *.doc *.docx *.ppt *.pptx);;"
            "Images (*.jpg *.jpeg *.png);;PDF Files (*.pdf)"
        )
        for f in files:
            self.file_list.addItem(f)

    def remove_selected(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def process_files(self):
        count = self.file_list.count()
        if count == 0:
            QMessageBox.warning(self, "경고", "처리할 파일이 없습니다.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "저장할 PDF 이름 입력", "", "PDF Files (*.pdf)")
        if not save_path:
            return

        if not save_path.lower().endswith('.pdf'):
            save_path += ".pdf"

        temp_pdfs = []
        try:
            for i in range(count):
                file_path = self.file_list.item(i).text()
                ext = os.path.splitext(file_path)[1].lower()
                
                if ext == '.pdf':
                    temp_pdfs.append(file_path)
                else:
                    self.label.setText(f"변환 중: {os.path.basename(file_path)}...")
                    QApplication.processEvents()
                    pdf_path = self.logic.convert_to_pdf(file_path)
                    if pdf_path:
                        temp_pdfs.append(pdf_path)
            
            self.label.setText("PDF 병합 중...")
            QApplication.processEvents()
            self.logic.merge_pdfs(temp_pdfs, save_path)
            
            # Cleanup temp files (only those created during process)
            created_temps = [f for f in temp_pdfs if f.endswith("_temp.pdf")]
            self.logic.cleanup_temps(created_temps)
            
            self.label.setText("완료!")
            QMessageBox.information(self, "성공", f"PDF가 성공적으로 생성되었습니다:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"처리 중 오류가 발생했습니다:\n{str(e)}")
        finally:
            self.label.setText("파일을 드래그하여 놓거나 '파일 추가' 버튼을 누르세요.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
