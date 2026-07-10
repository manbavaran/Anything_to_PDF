import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyPDF2 import PdfReader
from converter import PDFConverterLogic


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SOURCES = [
    ("hwp", Path.home() / "Desktop" / "260519 회의" / "260519_업무공유현황_보충자료1.hwp"),
    ("hwpx", Path.home() / "Desktop" / "260519 회의" / "260519_업무공유현황_보충자료2.hwpx"),
]


def main():
    RESULTS.mkdir(exist_ok=True)
    logic = PDFConverterLogic()
    # Simulate the target fallback environment: no Hancom and no LibreOffice.
    logic._hancom_available = False
    logic._word_available = False
    logic._soffice_path = None

    report = ["rhwp fallback test", "Hancom=False", "LibreOffice=False", ""]
    outputs = []
    for label, source in SOURCES:
        if not source.exists():
            raise FileNotFoundError(source)
        engine = logic.engine_for(source)
        report.append(f"ENGINE | {label} | {engine.label}")
        if engine.name != "rhwp":
            raise AssertionError(f"Expected rhwp fallback, got {engine.name}")
        output = Path(logic.convert_to_pdf(source))
        saved = RESULTS / f"converted_rhwp_fallback_{label}.pdf"
        saved.write_bytes(output.read_bytes())
        outputs.append(saved)
        report.append(f"CONVERTED | {source.name} -> {saved.name} | pages={len(PdfReader(str(saved)).pages)}")

    merged = RESULTS / "merged_rhwp_fallback_hwp_then_hwpx.pdf"
    logic.merge_pdfs(outputs, merged)
    report.append(f"MERGED | {merged.name} | order=hwp -> hwpx | pages={len(PdfReader(str(merged)).pages)}")
    (RESULTS / "rhwp_fallback_report.txt").write_text("\n".join(report), encoding="utf-8")
    logic.cleanup_temps([])
    print("\n".join(report))


if __name__ == "__main__":
    main()
