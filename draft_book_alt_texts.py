from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


IMAGE_PATTERN = re.compile(r"!\[(?P<alt>.*?)\]\((?P<url>.*?)\)")
HEADING_PATTERN = re.compile(r"^\s{0,3}(#{1,6})\s+(.*)$")


def load_notebook(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def cell_text(cell: dict) -> str:
    source = cell.get("source", [])
    if isinstance(source, list):
        return "".join(source)
    return str(source)


def normalize_space(text: str) -> str:
    return " ".join(text.split())


def heading_from_text(text: str) -> str | None:
    for line in text.splitlines():
        match = HEADING_PATTERN.match(line.strip())
        if not match:
            continue
        heading = normalize_space(match.group(2)).strip()
        if heading.lower() in {"table of contents"}:
            continue
        return heading
    return None


def first_nonempty_nonimage_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("!["):
            continue
        if stripped.startswith("<"):
            continue
        return normalize_space(stripped)
    return ""


def infer_alt(current_alt: str, section_heading: str, nearby_text: str) -> str:
    alt = current_alt.strip()
    heading = section_heading or "this section"

    mapping = {
        "If Statement Flowchart": "Flowchart showing the decision path of a Python if statement, including true and false branches.",
        "For Loop Flowchart": "Flowchart illustrating the control flow of a Python for loop through repeated iterations.",
        "While Loop Flowchart": "Flowchart illustrating the control flow of a Python while loop with condition checks and repetition.",
        "python.png": "Introductory Python graphic used at the start of the workbook.",
        "list.png": "Illustration of Python list concepts, such as list structure and indexing.",
    }

    if alt in mapping:
        return mapping[alt]

    if alt.lower() == "workbook figure":
        if heading == "this section":
            if nearby_text:
                return f"Workbook illustration: {nearby_text[:140]}."
            return "Workbook illustration used in an introductory part of the notebook."
        if nearby_text:
            return f"Illustration for {heading}: {nearby_text[:140]}."
        return f"Illustration supporting the {heading} section."

    if alt:
        return f"Illustration for {heading}: {alt}."

    return f"Illustration supporting the {heading} section."


def build_drafts(notebook_path: Path) -> list[dict]:
    notebook = load_notebook(notebook_path)
    cells = notebook.get("cells", [])

    drafts: list[dict] = []
    current_heading = ""
    figure_number = 1

    for cell in cells:
        if cell.get("cell_type") != "markdown":
            continue

        text = cell_text(cell)
        heading = heading_from_text(text)
        if heading:
            current_heading = heading

        nearby_text = first_nonempty_nonimage_line(text)

        for match in IMAGE_PATTERN.finditer(text):
            alt = match.group("alt").strip()
            url = match.group("url").strip()
            drafts.append(
                {
                    "figure": figure_number,
                    "cell_id": cell.get("id", "unknown"),
                    "section": current_heading,
                    "current_alt": alt,
                    "suggested_alt": infer_alt(alt, current_heading, nearby_text),
                    "source": "data-url" if url.startswith("data:image") else url,
                }
            )
            figure_number += 1

    return drafts


def write_outputs(drafts: list[dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "draft_alt_texts.json"
    json_path.write_text(json.dumps(drafts, indent=2), encoding="utf-8")

    md_lines = [
        "# Draft Alt Text Suggestions (Book Markdown Images)",
        "",
        "These are auto-generated draft suggestions. Edit wording as needed.",
        "",
        "| Figure | Section | Current Alt | Suggested Alt |",
        "|---:|---|---|---|",
    ]

    for item in drafts:
        section = item["section"] or "(no heading found)"
        current_alt = item["current_alt"] or "(empty)"
        suggested = item["suggested_alt"]
        md_lines.append(
            f"| {item['figure']} | {section.replace('|', '/')} | {current_alt.replace('|', '/')} | {suggested.replace('|', '/')} |"
        )

    md_path = output_dir / "draft_alt_texts.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate draft alt text suggestions for notebook markdown images.")
    parser.add_argument("notebook", help="Path to the .ipynb file")
    parser.add_argument(
        "--output-dir",
        default="extracted_notebook_markdown_images",
        help="Directory where draft alt text files are written",
    )
    args = parser.parse_args()

    notebook_path = Path(args.notebook).resolve()
    output_dir = Path(args.output_dir).resolve()

    drafts = build_drafts(notebook_path)
    write_outputs(drafts, output_dir)
    print(f"Generated draft alt text for {len(drafts)} figure(s) in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())