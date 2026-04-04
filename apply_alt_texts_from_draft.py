from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


IMAGE_PATTERN = re.compile(r"!\[(?P<alt>.*?)\]\((?P<url>.*?)\)")


def parse_suggested_alts(draft_md_path: Path) -> list[str]:
    lines = draft_md_path.read_text(encoding="utf-8").splitlines()
    suggestions: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if stripped.startswith("|---") or stripped.startswith("| Figure"):
            continue

        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if len(parts) < 4:
            continue

        suggested_alt = parts[3]
        if suggested_alt:
            suggestions.append(suggested_alt)

    return suggestions


def replace_alts_in_markdown(markdown_text: str, new_alts: list[str], start_index: int) -> tuple[str, int]:
    image_count = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal image_count
        idx = start_index + image_count
        if idx >= len(new_alts):
            image_count += 1
            return match.group(0)

        url = match.group("url")
        new_alt = new_alts[idx]
        image_count += 1
        return f"![{new_alt}]({url})"

    updated = IMAGE_PATTERN.sub(repl, markdown_text)
    return updated, image_count


def apply_alts(notebook_path: Path, draft_md_path: Path) -> tuple[int, int]:
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    cells = notebook.get("cells", [])

    new_alts = parse_suggested_alts(draft_md_path)
    total_images_seen = 0
    total_images_updated = 0

    for cell in cells:
        if cell.get("cell_type") != "markdown":
            continue

        source = cell.get("source", [])
        source_text = "".join(source) if isinstance(source, list) else str(source)
        if "![" not in source_text:
            continue

        updated_text, seen = replace_alts_in_markdown(source_text, new_alts, total_images_seen)
        if seen > 0:
            total_images_updated += min(seen, max(0, len(new_alts) - total_images_seen))
            total_images_seen += seen
            if isinstance(source, list):
                cell["source"] = updated_text.splitlines(keepends=True)
            else:
                cell["source"] = updated_text

    notebook_path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
    return total_images_updated, len(new_alts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply suggested alt text from draft markdown table to notebook markdown images.")
    parser.add_argument("notebook", help="Path to notebook .ipynb")
    parser.add_argument("draft_md", help="Path to draft_alt_texts.md")
    args = parser.parse_args()

    notebook_path = Path(args.notebook).resolve()
    draft_md_path = Path(args.draft_md).resolve()

    updated, suggested = apply_alts(notebook_path, draft_md_path)
    print(f"Applied {updated} alt text update(s) from {suggested} suggestion(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())