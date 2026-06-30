from pathlib import Path
from tempfile import TemporaryDirectory
import sys

from PIL import Image
from PyPDF2 import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from converter import PDFConverterLogic


def run_smoke_test(tmp_path):
    first = tmp_path / "first.png"
    second = tmp_path / "second.jpg"
    output = tmp_path / "merged.pdf"

    Image.new("RGBA", (100, 100), (255, 0, 0, 128)).save(first)
    Image.new("RGB", (100, 100), (0, 0, 255)).save(second)

    logic = PDFConverterLogic()
    generated = []
    try:
        generated.append(logic.convert_to_pdf(first))
        generated.append(logic.convert_to_pdf(second))
        logic.merge_pdfs(generated, output)
    finally:
        logic.cleanup_temps(generated)

    assert output.exists()
    assert len(PdfReader(str(output)).pages) == 2


def test_image_conversion_and_merge(tmp_path):
    run_smoke_test(tmp_path)


if __name__ == "__main__":
    temp_root = Path(__file__).resolve().parents[1] / ".tmp"
    temp_root.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=temp_root) as temp_dir:
        run_smoke_test(Path(temp_dir))
    print("Smoke test passed.")
