import shutil
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from converter import PDFConverterLogic
from PyPDF2 import PdfReader

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
MCP_OUTPUT = Path.home() / "Documents" / "Anything to PDF" / "results" / "generated_by_hwpx_mcp_table_image_caption.hwpx"
SOURCES = [
    ("01_mcp_generated", MCP_OUTPUT),
    ("02_real_hwp", Path.home() / "Desktop" / "260519 회의" / "260519_업무공유현황_보충자료1.hwp"),
    ("03_real_hwpx", Path.home() / "Desktop" / "260519 회의" / "260519_업무공유현황_보충자료2.hwpx"),
]


def main():
    RESULTS.mkdir(exist_ok=True)
    logic = PDFConverterLogic()
    report = ["HWP/HWPX conversion test", f"Hancom available={logic._has_hancom_hwp()}", ""]
    outputs = []
    for label, source in SOURCES:
        if not source.exists():
            report.append(f"MISSING | {label} | {source}")
            continue
        engine = logic.engine_for(source)
        report.append(f"SOURCE | {label} | {source.name} | ENGINE | {engine.label} | AVAILABLE | {engine.available}")
        if not engine.available:
            report.append(f"SKIP | {label} | {engine.note}")
            continue
        try:
            temp = Path(logic.convert_to_pdf(source))
            output = RESULTS / f"converted_{label}_{engine.name.replace(' ', '_')}.pdf"
            shutil.copy2(temp, output)
            outputs.append((label, output))
            report.append(f"CONVERTED | {label} | {output.name} | pages={len(PdfReader(str(output)).pages)}")
        except Exception as exc:
            report.append(f"ERROR | {label} | {type(exc).__name__}: {exc}")

    if outputs:
        merged = RESULTS / "merged_hwp_hwpx_order_01_mcp_02_hwp_03_hwpx.pdf"
        logic.merge_pdfs([path for _, path in outputs], merged)
        report.append("")
        report.append(f"MERGED | {merged.name} | pages={len(PdfReader(str(merged)).pages)}")
        report.append("ORDER | " + " -> ".join(label for label, _ in outputs))
    (RESULTS / "hwp_hwpx_conversion_report.txt").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
