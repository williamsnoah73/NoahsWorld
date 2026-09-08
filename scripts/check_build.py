#!/usr/bin/env python3

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[tuple[str, str]] = []
        self.images_without_alt: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag in {'a', 'link'} and attributes.get('href'):
            self.references.append((tag, attributes['href'] or ''))
        if tag in {'img', 'script', 'source', 'video'} and attributes.get('src'):
            self.references.append((tag, attributes['src'] or ''))
        if tag == 'video' and attributes.get('poster'):
            self.references.append(('poster', attributes['poster'] or ''))
        if tag == 'img' and 'alt' not in attributes:
            self.images_without_alt.append(attributes.get('src') or 'unknown image')
        for candidate in (attributes.get('srcset') or '').split(','):
            url = candidate.strip().split(' ', 1)[0]
            if url:
                self.references.append(('srcset', url))


def local_target(page: Path, reference: str) -> Path | None:
    parsed = urlparse(reference)
    if parsed.scheme or parsed.netloc or reference.startswith(('#', 'mailto:', 'tel:', 'data:')):
        return None
    path = parsed.path
    if not path:
        return None
    target = DIST / path.lstrip('/') if path.startswith('/') else page.parent / path
    if path.endswith('/'):
        target /= 'index.html'
    elif not target.suffix and target.is_dir():
        target /= 'index.html'
    return target


if not DIST.is_dir():
    raise SystemExit('Missing dist directory; run npm run build first.')

errors: list[str] = []
html_files = sorted(DIST.rglob('*.html'))
for page in html_files:
    parser = DocumentParser()
    parser.feed(page.read_text(encoding='utf-8'))
    for image in parser.images_without_alt:
        errors.append(f'{page.relative_to(DIST)}: image missing alt attribute: {image}')
    for kind, reference in parser.references:
        target = local_target(page, reference)
        if target is not None and not target.exists():
            errors.append(f'{page.relative_to(DIST)}: missing {kind} target: {reference}')

required = [DIST / 'index.html', DIST / 'rss.xml', DIST / 'sitemap-index.xml', DIST / '404.html']
for path in required:
    if not path.is_file():
        errors.append(f'Missing required build artifact: {path.relative_to(DIST)}')

if errors:
    raise SystemExit('\n'.join(errors))

print(f'Checked {len(html_files)} HTML files: local links/assets resolve and all images declare alt text.')
