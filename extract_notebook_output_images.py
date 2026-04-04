from __future__ import annotations

import argparse
import base64
import html
import json
from pathlib import Path


def load_notebook(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def cell_source_text(cell: dict) -> str:
    source = cell.get("source", [])
    if isinstance(source, list):
        return "".join(source)
    return str(source)


def markdown_preview(cells: list[dict], index: int) -> str:
    previews: list[str] = []

    for offset in range(index - 1, -1, -1):
        cell = cells[offset]
        if cell.get("cell_type") != "markdown":
            continue
        text = " ".join(line.strip() for line in cell_source_text(cell).splitlines())
        text = " ".join(text.split())
        if text:
            previews.append(text[:240])
            break

    for offset in range(index + 1, len(cells)):
        cell = cells[offset]
        if cell.get("cell_type") != "markdown":
            continue
        text = " ".join(line.strip() for line in cell_source_text(cell).splitlines())
        text = " ".join(text.split())
        if text:
            previews.append(text[:240])
            break

    return " | ".join(previews)


def render_gallery(items: list[dict], notebook_name: str) -> str:
    cards: list[str] = []

    for item in items:
        code_html = html.escape(item["code_preview"])
        context_html = html.escape(item["markdown_context"])
        cards.append(
            f"""
            <article class=\"card\">
              <div class=\"meta\">
                <h2>{html.escape(item['title'])}</h2>
                <p><strong>Cell id:</strong> {html.escape(item['cell_id'])}</p>
                <p><strong>Output:</strong> {item['output_index']}</p>
                <p><strong>Image:</strong> <a href=\"{html.escape(item['image_rel'])}\">open PNG</a></p>
              </div>
              <img src=\"{html.escape(item['image_rel'])}\" alt=\"Preview for {html.escape(item['title'])}\">
              <section>
                <h3>Code preview</h3>
                <pre>{code_html}</pre>
              </section>
              <section>
                <h3>Nearby markdown context</h3>
                <p>{context_html or 'No nearby markdown context found.'}</p>
              </section>
            </article>
            """.strip()
        )

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Notebook Output Image Gallery</title>
  <style>
    :root {{
      --bg: #f6f2ea;
      --paper: #fffdf8;
      --ink: #1f1a17;
      --muted: #6b5b4f;
      --line: #dccfbe;
      --accent: #8c3b2a;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, #efe5d6 0, transparent 30%),
        linear-gradient(180deg, #fbf8f1 0%, var(--bg) 100%);
    }}

    header {{
      padding: 2rem 1.5rem 1rem;
      max-width: 1100px;
      margin: 0 auto;
    }}

    h1 {{
      margin: 0 0 0.5rem;
      font-size: clamp(2rem, 4vw, 3rem);
      line-height: 1.1;
    }}

    header p {{
      margin: 0.35rem 0;
      color: var(--muted);
      max-width: 70ch;
    }}

    main {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 1rem 1.5rem 3rem;
      display: grid;
      gap: 1rem;
    }}

    .card {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 1rem;
      box-shadow: 0 12px 30px rgba(73, 48, 31, 0.08);
      display: grid;
      gap: 1rem;
    }}

    .meta h2 {{
      margin: 0 0 0.5rem;
      color: var(--accent);
      font-size: 1.35rem;
    }}

    .meta p,
    section p {{
      margin: 0.25rem 0;
      line-height: 1.45;
    }}

    img {{
      width: 100%;
      max-height: 520px;
      object-fit: contain;
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 0.5rem;
    }}

    section h3 {{
      margin: 0 0 0.5rem;
      font-size: 1rem;
    }}

    pre {{
      margin: 0;
      padding: 0.9rem;
      overflow: auto;
      background: #f3ede3;
      border-radius: 12px;
      border: 1px solid var(--line);
      font-family: Consolas, "Courier New", monospace;
      font-size: 0.92rem;
      line-height: 1.35;
      white-space: pre-wrap;
    }}

    a {{ color: var(--accent); }}
  </style>
</head>
<body>
  <header>
    <h1>Output Image Gallery</h1>
    <p><strong>Notebook:</strong> {html.escape(notebook_name)}</p>
    <p>This gallery contains generated image outputs extracted from the notebook so they can be reviewed and described individually.</p>
    <p>Open a PNG directly if you want a larger standalone view, then send back the description you want for that figure.</p>
  </header>
  <main>
    {''.join(cards)}
  </main>
</body>
</html>
"""


def extract_images(notebook_path: Path, output_dir: Path) -> int:
    notebook = load_notebook(notebook_path)
    cells = notebook.get("cells", [])
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    items: list[dict] = []
    image_counter = 1

    for cell_index, cell in enumerate(cells):
        if cell.get("cell_type") != "code":
            continue

        outputs = cell.get("outputs", [])
        for output_index, output in enumerate(outputs, start=1):
            data = output.get("data", {})
            image_data = data.get("image/png")
            if not image_data:
                continue

            encoded = "".join(image_data) if isinstance(image_data, list) else image_data
            image_bytes = base64.b64decode(encoded)
            image_name = f"output_{image_counter:03d}.png"
            image_path = images_dir / image_name
            image_path.write_bytes(image_bytes)

            source = cell_source_text(cell).strip()
            source_lines = source.splitlines()
            code_preview = "\n".join(source_lines[:12]).strip()
            if len(source_lines) > 12:
                code_preview += "\n..."

            items.append(
                {
                    "title": f"Figure {image_counter}",
                    "cell_id": cell.get("id", f"cell-{cell_index + 1}"),
                    "output_index": output_index,
                    "image_rel": f"images/{image_name}",
                    "code_preview": code_preview or "No code source found.",
                    "markdown_context": markdown_preview(cells, cell_index),
                }
            )
            image_counter += 1

    gallery_path = output_dir / "index.html"
    gallery_path.write_text(render_gallery(items, notebook_path.name), encoding="utf-8")

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(items, indent=2), encoding="utf-8")

    return len(items)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract image/png outputs from a notebook into a review gallery.")
    parser.add_argument("notebook", help="Path to the .ipynb file")
    parser.add_argument(
        "--output-dir",
        default="extracted_notebook_output_images",
        help="Directory where images and gallery files will be written",
    )
    args = parser.parse_args()

    notebook_path = Path(args.notebook).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    count = extract_images(notebook_path, output_dir)
    print(f"Extracted {count} image output(s) to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())