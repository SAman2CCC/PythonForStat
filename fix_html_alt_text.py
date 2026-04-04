from __future__ import annotations

import argparse
import re
from pathlib import Path


PLACEHOLDER_ALT = 'No description has been provided for this image'
FALLBACK_ALT = 'Generated output image from the preceding Python code cell.'


def replace_placeholder_alt(html: str) -> tuple[str, int]:
    pattern = re.compile(r'alt="No description has been provided for this image"')
    updated_html, count = pattern.subn(f'alt="{FALLBACK_ALT}"', html)
    return updated_html, count


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Replace exported notebook placeholder alt text in HTML files.'
    )
    parser.add_argument('paths', nargs='+', help='HTML files to update in place.')
    args = parser.parse_args()

    total_replacements = 0
    for raw_path in args.paths:
        path = Path(raw_path)
        html = path.read_text(encoding='utf-8')
        updated_html, count = replace_placeholder_alt(html)
        if count:
            path.write_text(updated_html, encoding='utf-8')
        total_replacements += count
        print(f'{path.name}: {count} replacement(s)')

    print(f'Total replacements: {total_replacements}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())