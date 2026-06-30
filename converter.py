import os
import tempfile
from pathlib import Path

from PIL import Image, ImageOps
from PyPDF2 import PdfMerger


try:
    import comtypes.client

    HAS_COMTYPES = True
except ImportError:
    HAS_COMTYPES = False

try:
    from simple_hwp2pdf import convert_hwp_to_pdf as hwp_convert

    HAS_HWP2PDF = True
except ImportError:
    HAS_HWP2PDF = False


class PDFConverterLogic:
    def __init__(self):
        self.supported_extensions = [
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
        self._temp_dir = None

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
            if ext in [".png", ".jpg", ".jpeg"]:
                self._convert_image_to_pdf(input_file, output_pdf)
                return str(output_pdf)

            if ext in [".hwp", ".hwpx"]:
                if not HAS_HWP2PDF:
                    raise RuntimeError("simple-hwp2pdf is required for HWP/HWPX conversion.")
                try:
                    hwp_convert(str(input_file), str(output_pdf))
                    return str(output_pdf)
                except Exception as exc:
                    raise RuntimeError(f"HWP/HWPX conversion failed: {exc}") from exc

            if ext in [".doc", ".docx", ".ppt", ".pptx"]:
                if os.name != "nt" or not HAS_COMTYPES:
                    raise RuntimeError(
                        "Office conversion requires Windows, Microsoft Office, and comtypes."
                    )
                return self._convert_office_to_pdf_windows(input_file, output_pdf, ext)
        except Exception:
            if output_pdf.exists():
                try:
                    output_pdf.unlink()
                except OSError:
                    pass
            raise

        return None

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

        if ext in [".doc", ".docx"]:
            doc = None
            word = comtypes.client.CreateObject("Word.Application")
            word.Visible = False
            try:
                doc = word.Documents.Open(input_path)
                doc.SaveAs(output_pdf, FileFormat=17)
                return output_pdf
            finally:
                if doc is not None:
                    doc.Close(False)
                word.Quit()

        if ext in [".ppt", ".pptx"]:
            presentation = None
            powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
            try:
                presentation = powerpoint.Presentations.Open(input_path, WithWindow=False)
                presentation.SaveAs(output_pdf, 32)
                return output_pdf
            finally:
                if presentation is not None:
                    presentation.Close()
                powerpoint.Quit()

        return None

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
