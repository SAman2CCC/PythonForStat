from pathlib import Path
import argparse
from pypdf import PdfReader, PdfWriter


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


def remove_blank_pages(input_pdf: Path, output_pdf: Path, text_threshold: int = 3):
    reader = PdfReader(str(input_pdf))
    writer = PdfWriter()

    removed = []
    for idx, page in enumerate(reader.pages, start=1):
        if page_is_blank(page, text_threshold=text_threshold):
            removed.append(idx)
            continue
        writer.add_page(page)

    with output_pdf.open("wb") as f:
        writer.write(f)

    return len(reader.pages), len(writer.pages), removed


def main():
    parser = argparse.ArgumentParser(description="Remove blank pages from a PDF")
    parser.add_argument("input_pdf", type=Path)
    parser.add_argument("output_pdf", type=Path)
    parser.add_argument("--text-threshold", type=int, default=3)
    args = parser.parse_args()

    if not args.input_pdf.exists():
        raise FileNotFoundError(f"Input PDF not found: {args.input_pdf}")

    args.output_pdf.parent.mkdir(parents=True, exist_ok=True)
    before, after, removed = remove_blank_pages(
        args.input_pdf, args.output_pdf, text_threshold=args.text_threshold
    )

    print(f"input={args.input_pdf}")
    print(f"output={args.output_pdf}")
    print(f"pages_before={before}")
    print(f"pages_after={after}")
    print(f"removed_pages={removed}")


if __name__ == "__main__":
    main()
