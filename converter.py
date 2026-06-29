import os
import sys
from PyPDF2 import PdfMerger
from PIL import Image
import img2pdf

# Optional imports for document conversion
try:
    import comtypes.client
    HAS_COMTYPES = True
except ImportError:
    HAS_COMTYPES = False

try:
    from simple_hwp2pdf import convert as hwp_convert
    HAS_HWP2PDF = True
except ImportError:
    HAS_HWP2PDF = False

class PDFConverterLogic:
    def __init__(self):
        self.supported_extensions = ['.png', '.jpg', '.jpeg', '.hwp', '.hwpx', '.ppt', '.pptx', '.doc', '.docx']

    def convert_to_pdf(self, input_path):
        """Converts a single file to PDF and returns the path of the generated PDF."""
        ext = os.path.splitext(input_path)[1].lower()
        output_pdf = os.path.splitext(input_path)[0] + "_temp.pdf"

        if ext in ['.png', '.jpg', '.jpeg']:
            with open(output_pdf, "wb") as f:
                f.write(img2pdf.convert(input_path))
            return output_pdf

        elif ext in ['.hwp', '.hwpx']:
            if HAS_HWP2PDF:
                try:
                    hwp_convert(input_path, output_pdf)
                    return output_pdf
                except Exception as e:
                    raise Exception(f"HWP conversion failed: {str(e)}")
            else:
                raise Exception("simple-hwp2pdf library is required for HWP conversion.")

        elif ext in ['.doc', '.docx', '.ppt', '.pptx']:
            if os.name == 'nt' and HAS_COMTYPES:
                return self._convert_office_to_pdf_windows(input_path, output_pdf, ext)
            else:
                raise Exception("Office conversion requires Windows and comtypes library.")
        
        return None

    def _convert_office_to_pdf_windows(self, input_path, output_pdf, ext):
        input_path = os.path.abspath(input_path)
        output_pdf = os.path.abspath(output_pdf)
        
        if ext in ['.doc', '.docx']:
            word = comtypes.client.CreateObject('Word.Application')
            word.Visible = False
            try:
                doc = word.Documents.Open(input_path)
                doc.SaveAs(output_pdf, FileFormat=17) # 17 is wdFormatPDF
                doc.Close()
                return output_pdf
            finally:
                word.Quit()
        
        elif ext in ['.ppt', '.pptx']:
            powerpoint = comtypes.client.CreateObject('PowerPoint.Application')
            try:
                presentation = powerpoint.Presentations.Open(input_path, WithWindow=False)
                presentation.SaveAs(output_pdf, 32) # 32 is ppSaveAsPDF
                presentation.Close()
                return output_pdf
            finally:
                powerpoint.Quit()
        return None

    def merge_pdfs(self, pdf_list, output_path):
        merger = PdfMerger()
        for pdf in pdf_list:
            merger.append(pdf)
        merger.write(output_path)
        merger.close()

    def cleanup_temps(self, temp_files):
        for f in temp_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass
