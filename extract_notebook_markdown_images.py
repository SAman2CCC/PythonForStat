from __future__ import annotations

import argparse
import base64
import html
import json
import re
from pathlib import Path


IMAGE_PATTERN = re.compile(r"!\[(?P<alt>.*?)\]\((?P<url>.*?)\)")


def load_notebook(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def markdown_text(cell: dict) -> str:
    source = cell.get("source", [])
    if isinstance(source, list):
        return "".join(source)
    return str(source)


def decode_data_url(url: str) -> bytes | None:
    if not url.startswith("data:image"):
        return None
    marker = "base64,"
    idx = url.find(marker)
    if idx == -1:
        return None
    payload = url[idx + len(marker) :]
    return base64.b64decode(payload)


def render_gallery(items: list[dict], notebook_name: str) -> str:
    cards: list[str] = []
    for item in items:
        cards.append(
            f"""
            <article class=\"card\">
              <h2>{html.escape(item['title'])}</h2>
              <p><strong>Cell id:</strong> {html.escape(item['cell_id'])}</p>
              <p><strong>Original markdown alt:</strong> {html.escape(item['markdown_alt']) or 'empty'}</p>
              <p><strong>Image:</strong> <a href=\"{html.escape(item['image_rel'])}\">open PNG</a></p>
              <img src=\"{html.escape(item['image_rel'])}\" alt=\"Preview of {html.escape(item['title'])}\">
            </article>
            """.strip()
        )

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Book Markdown Images</title>
  <style>
    body {{
      margin: 0;
      background: #f4f7f8;
      color: #162126;
      font-family: Georgia, "Times New Roman", serif;
    }}
    header, main {{
      max-width: 1000px;
      margin: 0 auto;
      padding: 1.2rem;
    }}
    .card {{
      background: #ffffff;
      border: 1px solid #d6e0e2;
      border-radius: 14px;
      padding: 1rem;
      margin-bottom: 1rem;
      box-shadow: 0 8px 18px rgba(0, 0, 0, 0.06);
    }}
    h1 {{ margin-bottom: 0.2rem; }}
    h2 {{ margin-top: 0; color: #0f4c5c; }}
    img {{
      width: 100%;
      max-height: 520px;
      object-fit: contain;
      border: 1px solid #d6e0e2;
      border-radius: 10px;
      background: #fff;
    }}
    a {{ color: #0f4c5c; }}
  </style>
</head>
<body>
  <header>
    <h1>Book Markdown Image Gallery</h1>
    <p><strong>Notebook:</strong> {html.escape(notebook_name)}</p>
    <p>This gallery only includes authored markdown images, not code output charts.</p>
  </header>
  <main>
    {''.join(cards)}
  </main>
</body>
</html>
"""


def extract_markdown_images(notebook_path: Path, output_dir: Path) -> int:
    notebook = load_notebook(notebook_path)
    cells = notebook.get("cells", [])
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    items: list[dict] = []
    counter = 1

    for cell in cells:
        if cell.get("cell_type") != "markdown":
            continue

        text = markdown_text(cell)
        for match in IMAGE_PATTERN.finditer(text):
            url = match.group("url").strip()
            alt = match.group("alt").strip()

            image_bytes = decode_data_url(url)
            image_name = f"markdown_{counter:03d}.png"
            image_path = images_dir / image_name

            if image_bytes is not None:
                image_path.write_bytes(image_bytes)
            else:
                source_path = (notebook_path.parent / url).resolve()
                if source_path.exists() and source_path.is_file():
                    image_path.write_bytes(source_path.read_bytes())
                else:
                    continue

            items.append(
                {
                    "title": f"Book Figure {counter}",
                    "cell_id": cell.get("id", "unknown"),
                    "markdown_alt": alt,
                    "image_rel": f"images/{image_name}",
                }
            )
            counter += 1

    (output_dir / "index.html").write_text(
        render_gallery(items, notebook_path.name),
        encoding="utf-8",
    )
    (output_dir / "manifest.json").write_text(json.dumps(items, indent=2), encoding="utf-8")
    return len(items)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract authored markdown images from a notebook into a gallery.")
    parser.add_argument("notebook", help="Path to .ipynb")
    parser.add_argument(
        "--output-dir",
        default="extracted_notebook_markdown_images",
        help="Output directory for gallery and image files",
    )
    args = parser.parse_args()

    notebook_path = Path(args.notebook).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    count = extract_markdown_images(notebook_path, output_dir)
    print(f"Extracted {count} markdown image(s) to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())