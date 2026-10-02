#!/usr/bin/env python3
"""Build a single portable HTML page from editable source and validated JSON."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from validate import ROOT, load_site

PORTABLE_NAME = 'Planning-Knowledge-Hub-Self-Contained.html'


def build(root: Path = ROOT, output: Path | None = None) -> Path:
    site = load_site(root)
    template = (root / 'src/index.template.html').read_text(encoding='utf-8')
    style = (root / 'src/styles.css').read_text(encoding='utf-8')
    app = (root / 'src/app.js').read_text(encoding='utf-8')
    # Never allow data to close an HTML script block, even when a record contains markup.
    embedded = json.dumps(site, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    for marker in ['/*__STYLES__*/', '/*__DATA__*/', '/*__APP__*/']:
        if template.count(marker) != 1:
            raise ValueError(f'Expected exactly one build marker: {marker}')
    if '</script' in app.lower() or '</style' in style.lower():
        raise ValueError('Source contains an unsafe closing tag for inline embedding.')
    html = template.replace('/*__STYLES__*/', style).replace('/*__DATA__*/', embedded).replace('/*__APP__*/', app)
    out = output or (root / '_site')
    out.mkdir(parents=True, exist_ok=True)
    for target in [root / 'index.html', root / PORTABLE_NAME, out / 'index.html', out / PORTABLE_NAME]:
        target.write_text(html, encoding='utf-8')
    (root / '.nojekyll').touch()
    (out / '.nojekyll').touch()
    # No source code, docs, private workspace files, or credentials are deployed here.
    print(f'Built {out / "index.html"} and portable HTML ({len(html.encode("utf-8")):,} bytes).')
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Deployment output directory; default: _site')
    args = parser.parse_args()
    build(output=args.output)


if __name__ == '__main__':
    main()
