import argparse
import asyncio
from pathlib import Path

from pyppeteer import launch


async def render_pdf(input_html: Path, output_pdf: Path, timeout_ms: int, browser_path: str = "") -> None:
    launch_kwargs = {
        "headless": True,
        "args": [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--allow-file-access-from-files",
        ],
    }
    if browser_path:
        launch_kwargs["executablePath"] = browser_path

    browser = await launch(**launch_kwargs)
    try:
        page = await browser.newPage()
        await page.goto(input_html.resolve().as_uri(), {"waitUntil": "networkidle2", "timeout": timeout_ms})

        # Wait for MathJax v2 typesetting when available.
        await page.evaluate(
            """
            () => new Promise((resolve) => {
              if (window.MathJax && window.MathJax.Hub && window.MathJax.Hub.Queue) {
                window.MathJax.Hub.Queue(resolve);
              } else {
                resolve();
              }
            })
            """
        )

        # Give dynamic content a short stabilization window.
        await page.waitFor(1200)

        await page.pdf(
            {
                "path": str(output_pdf),
                "printBackground": True,
                "preferCSSPageSize": True,
                "margin": {"top": "12mm", "right": "10mm", "bottom": "12mm", "left": "10mm"},
            }
        )
    finally:
        await browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Render HTML to PDF after MathJax typesetting.")
    parser.add_argument("input_html", type=Path, help="Path to input HTML file")
    parser.add_argument("output_pdf", type=Path, help="Path to output PDF file")
    parser.add_argument("--timeout-ms", type=int, default=120000, help="Navigation timeout in milliseconds")
    parser.add_argument("--browser-path", type=str, default="", help="Path to existing browser executable")
    args = parser.parse_args()

    if not args.input_html.exists():
        raise FileNotFoundError(f"Input HTML not found: {args.input_html}")

    args.output_pdf.parent.mkdir(parents=True, exist_ok=True)
    asyncio.get_event_loop().run_until_complete(
        render_pdf(args.input_html, args.output_pdf, args.timeout_ms, args.browser_path)
    )


if __name__ == "__main__":
    main()
