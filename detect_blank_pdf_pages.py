from pathlib import Path
import argparse
from pypdf import PdfReader


def _deref(obj):
    try:
        return obj.get_object()
    except Exception:
        return obj


def page_is_blank(page, text_threshold: int = 3) -> bool:
    text = (page.extract_text() or "").strip()
    if len(text) > text_threshold:
        return False

    resources = _deref(page.get("/Resources"))
    if not resources:
        return True

    xobj = _deref(resources.get("/XObject")) if hasattr(resources, "get") else None
    if xobj:
        try:
            if len(list(xobj.keys())) > 0:
                return False
        except Exception:
            return False

    annots = _deref(page.get("/Annots"))
    if annots:
        return False

    return True


def analyze_pdf(path: Path):
    reader = PdfReader(str(path))
    blank = []
    for i, p in enumerate(reader.pages, start=1):
        if page_is_blank(p):
            blank.append(i)
    return len(reader.pages), blank


def main():
    parser = argparse.ArgumentParser(description="Detect blank pages in PDFs")
    parser.add_argument("pdfs", nargs="*", help="Optional list of PDF files")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    if args.pdfs:
        targets = [Path(p) if Path(p).is_absolute() else (root / p) for p in args.pdfs]
    else:
        targets = sorted(root.glob("*.pdf"))

    for pdf in targets:
        try:
            total, blank = analyze_pdf(pdf)
            print(f"{pdf.name}: total={total}, blank_pages={blank}")
        except Exception as exc:
            print(f"{pdf.name}: ERROR -> {exc}")


if __name__ == "__main__":
    main()
