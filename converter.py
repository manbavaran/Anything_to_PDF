import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps
from PyPDF2 import PdfMerger


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
PDF_EXTS = {".pdf"}
OFFICE_EXTS = {".doc", ".docx", ".ppt", ".pptx"}
HWP_EXTS = {".hwp", ".hwpx"}
SUPPORTED_EXTS = sorted(IMAGE_EXTS | PDF_EXTS | OFFICE_EXTS | HWP_EXTS)


try:
    import winreg
except ImportError:
    winreg = None

try:
    import comtypes.client

    HAS_COMTYPES = True
except ImportError:
    comtypes = None
    HAS_COMTYPES = False

try:
    import pythoncom
    import win32com.client

    HAS_WIN32COM = True
except ImportError:
    pythoncom = None
    win32com = None
    HAS_WIN32COM = False

try:
    import rhwp

    HAS_RHWP = True
except ImportError:
    rhwp = None
    HAS_RHWP = False


@dataclass(frozen=True)
class EngineInfo:
    name: str
    quality: str
    available: bool
    note: str = ""

    @property
    def label(self):
        suffix = f" - {self.note}" if self.note else ""
        return f"{self.name} ({self.quality}){suffix}"


class PDFConverterLogic:
    def __init__(self):
        self.supported_extensions = SUPPORTED_EXTS
        self._temp_dir = None
        self._soffice_path = self._find_soffice()
        self._hancom_available = None
        self._word_available = None
        self._powerpoint_available = None

    def engine_for(self, input_path):
        input_file = Path(input_path)
        ext = input_file.suffix.lower()

        if ext in PDF_EXTS:
            return EngineInfo("PDF 직접 병합", "원본", True, "변환 없음")
        if ext in IMAGE_EXTS:
            return EngineInfo("Pillow", "안정적", True, "이미지 1개당 1페이지")
        if ext in OFFICE_EXTS:
            if ext in {".doc", ".docx"} and self._has_word():
                return EngineInfo("Microsoft Word", "high fidelity", True)
            if ext in {".ppt", ".pptx"} and self._has_powerpoint():
                return EngineInfo("Microsoft PowerPoint", "high fidelity", True)
            if self._soffice_path:
                return EngineInfo("LibreOffice", "대체 변환", True, "레이아웃이 달라질 수 있음")
            return EngineInfo(
                "Office 변환 엔진 없음",
                "사용 불가",
                False,
                "Microsoft Office 또는 LibreOffice를 설치하세요",
            )
        if ext in HWP_EXTS:
            if self._has_hancom_hwp():
                return EngineInfo("Hancom HWP", "high fidelity", True)
            if ext == ".hwp" and self._has_word():
                return EngineInfo(
                    "Microsoft Word",
                    "experimental",
                    True,
                    "requires an HWP import filter",
                )
            if self._soffice_path:
                return EngineInfo(
                    "LibreOffice",
                    "experimental",
                    True,
                    "HWP/HWPX layout is not guaranteed",
                )
            if HAS_RHWP:
                return EngineInfo(
                    "rhwp",
                    "experimental fallback",
                    True,
                    "Office 없이 렌더링하며 레이아웃 차이가 있을 수 있음",
                )
            return EngineInfo(
                "HWP 변환 엔진 없음",
                "사용 불가",
                False,
                "layout-preserving HWP/HWPX conversion needs Hancom",
            )
        return EngineInfo("지원하지 않는 형식", "사용 불가", False)

    def convert_to_pdf(self, input_path):
        """Convert a single file to PDF and return the generated PDF path."""
        input_file = Path(input_path)
        ext = input_file.suffix.lower()

        if ext == ".pdf":
            return str(input_file)

        if ext not in self.supported_extensions:
            raise ValueError(f"Unsupported file type: {ext or 'unknown'}")

        output_pdf = self._make_temp_pdf_path(input_file)

        try:
            if ext in IMAGE_EXTS:
                self._convert_image_to_pdf(input_file, output_pdf)
                return str(output_pdf)

            if ext in OFFICE_EXTS:
                return self._convert_office_document(input_file, output_pdf, ext)

            if ext in HWP_EXTS:
                return self._convert_hwp_document(input_file, output_pdf, ext)
        except Exception:
            if output_pdf.exists():
                try:
                    output_pdf.unlink()
                except OSError:
                    pass
            raise

        return None

    def _convert_office_document(self, input_file, output_pdf, ext):
        can_use_office = (
            ext in {".doc", ".docx"} and self._has_word()
        ) or (
            ext in {".ppt", ".pptx"} and self._has_powerpoint()
        )
        if can_use_office:
            try:
                return self._convert_office_to_pdf_windows(input_file, output_pdf, ext)
            except Exception as exc:
                if not self._soffice_path:
                    raise RuntimeError(
                        "Microsoft Office conversion failed, and LibreOffice fallback "
                        f"was not found: {exc}"
                    ) from exc

        if self._soffice_path:
            return self._convert_with_libreoffice(input_file, output_pdf)

        raise RuntimeError(
            "DOC/DOCX/PPT/PPTX conversion requires Microsoft Office or LibreOffice."
        )

    def _convert_hwp_document(self, input_file, output_pdf, ext):
        if self._has_hancom_hwp():
            try:
                return self._convert_hwp_with_hancom(input_file, output_pdf)
            except Exception as exc:
                if not self._soffice_path:
                    raise RuntimeError(
                        "Hancom HWP conversion failed, and no reliable local fallback "
                        f"was found: {exc}"
                    ) from exc

        if ext == ".hwp" and self._has_word():
            try:
                return self._convert_office_to_pdf_windows(input_file, output_pdf, ext)
            except Exception:
                pass

        if self._soffice_path:
            try:
                return self._convert_with_libreoffice(input_file, output_pdf)
            except Exception as exc:
                raise RuntimeError(
                    "HWP/HWPX fallback failed. Without Hancom Office, layout-preserving "
                    "conversion is not guaranteed and may be unavailable for this file: "
                    f"{exc}"
                ) from exc

        if HAS_RHWP:
            try:
                return self._convert_with_rhwp(input_file, output_pdf)
            except Exception as exc:
                raise RuntimeError(
                    "rhwp HWP/HWPX fallback conversion failed: "
                    f"{exc}"
                ) from exc

        raise RuntimeError(
            "HWP/HWPX layout-preserving conversion requires Hancom Office. "
            "Install Hancom Office, LibreOffice, or rhwp-python for an experimental fallback."
        )

    def _make_temp_pdf_path(self, input_file):
        if self._temp_dir is None:
            self._temp_dir = self._create_temp_dir()

        temp_file = tempfile.NamedTemporaryFile(
            prefix=f"{input_file.stem}_",
            suffix=".pdf",
            dir=self._temp_dir,
            delete=False,
        )
        temp_file.close()
        path = Path(temp_file.name)
        path.unlink(missing_ok=True)
        return path

    def _create_temp_dir(self):
        try:
            return Path(tempfile.mkdtemp(prefix="anything_to_pdf_"))
        except OSError:
            fallback_root = Path.cwd() / ".anything_to_pdf_tmp"
            fallback_root.mkdir(parents=True, exist_ok=True)
            return Path(tempfile.mkdtemp(prefix="run_", dir=fallback_root))

    def _convert_image_to_pdf(self, input_file, output_pdf):
        with Image.open(input_file) as image:
            image = ImageOps.exif_transpose(image)
            if image.mode in ("RGBA", "LA") or (
                image.mode == "P" and "transparency" in image.info
            ):
                alpha = image.convert("RGBA").getchannel("A")
                background = Image.new("RGB", image.size, "white")
                background.paste(image.convert("RGBA"), mask=alpha)
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")
            image.save(output_pdf, "PDF", resolution=100.0)

    def _convert_office_to_pdf_windows(self, input_path, output_pdf, ext):
        input_path = os.path.abspath(str(input_path))
        output_pdf = os.path.abspath(str(output_pdf))

        if ext in {".doc", ".docx", ".hwp"}:
            doc = None
            word = comtypes.client.CreateObject("Word.Application")
            word.Visible = False
            try:
                doc = word.Documents.Open(input_path)
                doc.ExportAsFixedFormat(output_pdf, 17)
                return output_pdf
            finally:
                if doc is not None:
                    doc.Close(False)
                word.Quit()

        if ext in {".ppt", ".pptx"}:
            presentation = None
            powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
            try:
                presentation = powerpoint.Presentations.Open(input_path, WithWindow=False)
                presentation.ExportAsFixedFormat(output_pdf, 2)
                return output_pdf
            finally:
                if presentation is not None:
                    presentation.Close()
                powerpoint.Quit()

        return None

    def _convert_hwp_with_hancom(self, input_path, output_pdf):
        input_path = os.path.abspath(str(input_path))
        output_pdf = os.path.abspath(str(output_pdf))

        pythoncom.CoInitialize()
        hwp = None
        try:
            hwp = win32com.client.gencache.EnsureDispatch("HWPFrame.HwpObject")
            try:
                hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
            except Exception:
                pass
            if not hwp.Open(input_path):
                raise RuntimeError("Hancom could not open the file.")
            if not hwp.SaveAs(output_pdf, "PDF"):
                raise RuntimeError("Hancom could not save the file as PDF.")
            return output_pdf
        finally:
            if hwp is not None:
                try:
                    hwp.Quit()
                except Exception:
                    pass
            pythoncom.CoUninitialize()

    def _convert_with_libreoffice(self, input_file, output_pdf):
        if not self._soffice_path:
            raise RuntimeError("LibreOffice soffice executable was not found.")

        input_file = Path(input_file).resolve()
        output_pdf = Path(output_pdf).resolve()
        output_pdf.parent.mkdir(parents=True, exist_ok=True)

        command = [
            self._soffice_path,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_pdf.parent),
            str(input_file),
        ]
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        generated = output_pdf.parent / f"{input_file.stem}.pdf"
        if completed.returncode != 0 or not generated.exists():
            details = (completed.stderr or completed.stdout or "no output").strip()
            raise RuntimeError(f"LibreOffice failed: {details}")

        if generated != output_pdf:
            if output_pdf.exists():
                output_pdf.unlink()
            generated.replace(output_pdf)
        return str(output_pdf)

    def _convert_with_rhwp(self, input_file, output_pdf):
        """Render HWP/HWPX directly to PDF without Office applications."""
        if not HAS_RHWP:
            raise RuntimeError("rhwp-python is not installed.")

        document = rhwp.parse(str(Path(input_file).resolve()))
        document.export_pdf(str(Path(output_pdf).resolve()))
        if not Path(output_pdf).exists() or Path(output_pdf).stat().st_size == 0:
            raise RuntimeError("rhwp did not create a PDF output.")
        return str(output_pdf)

    def _find_soffice(self):
        found = shutil.which("soffice") or shutil.which("soffice.exe")
        if found:
            return found

        candidates = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        for candidate in candidates:
            if Path(candidate).exists():
                return candidate
        return None

    def _has_hancom_hwp(self):
        if self._hancom_available is not None:
            return self._hancom_available
        self._hancom_available = HAS_WIN32COM and self._is_com_registered(
            "HWPFrame.HwpObject"
        )
        return self._hancom_available

    def _has_word(self):
        if self._word_available is None:
            self._word_available = HAS_COMTYPES and self._is_com_registered(
                "Word.Application"
            )
        return self._word_available

    def _has_powerpoint(self):
        if self._powerpoint_available is None:
            self._powerpoint_available = HAS_COMTYPES and self._is_com_registered(
                "PowerPoint.Application"
            )
        return self._powerpoint_available

    def _is_com_registered(self, prog_id):
        if os.name != "nt" or winreg is None:
            return False
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, rf"{prog_id}\CLSID"):
                return True
        except OSError:
            return False

    def merge_pdfs(self, pdf_list, output_path):
        if not pdf_list:
            raise ValueError("No PDF files to merge.")

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        merger = PdfMerger()
        try:
            for pdf in pdf_list:
                merger.append(str(pdf))
            merger.write(str(output_file))
        finally:
            merger.close()

    def cleanup_temps(self, temp_files):
        for temp_file in temp_files:
            path = Path(temp_file)
            if path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass

        if self._temp_dir and self._temp_dir.exists():
            try:
                self._temp_dir.rmdir()
                self._temp_dir = None
            except OSError:
                pass
