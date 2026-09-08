#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / 'reports' / 'migration-manifest.json'
PUBLIC_STORIES = sorted((ROOT / 'src' / 'content' / 'stories' / 'legacy').glob('**/*.json'))
PUBLIC_ALBUMS = sorted((ROOT / 'src' / 'content' / 'albums' / 'legacy').glob('**/*.json'))
PRIVATE_STORIES = sorted((ROOT / 'private-site' / 'content' / 'stories' / 'legacy').glob('**/*.json'))
PUBLIC_ASSETS = ROOT / 'src' / 'assets' / 'public'
PRIVATE_ASSETS = ROOT / 'private-site' / 'assets'
PAGES_FILE_LIMIT = 25 * 1024 * 1024


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        raise SystemExit(f'Invalid JSON in {path}: {exc}') from exc


manifest = load_json(MANIFEST_PATH)
counts = manifest.get('totals', {})

expected_story_entries = counts.get('storyEntries')
expected_album_entries = counts.get('albumEntries')
expected_public_entries = counts.get('publicEntries')
expected_private_entries = counts.get('privateEntries')

total_story_count = len(PUBLIC_STORIES) + len(PRIVATE_STORIES)
if expected_story_entries is None or total_story_count != expected_story_entries:
    raise SystemExit(
        f'Story count mismatch: expected {expected_story_entries}, found {total_story_count}.'
    )

if expected_album_entries is None or len(PUBLIC_ALBUMS) != expected_album_entries:
    raise SystemExit(
        f'Album count mismatch: expected {expected_album_entries}, found {len(PUBLIC_ALBUMS)}.'
    )

public_entry_count = len(PUBLIC_STORIES) + len(PUBLIC_ALBUMS)
if expected_public_entries is None or public_entry_count != expected_public_entries:
    raise SystemExit(
        f'Public entry mismatch: expected {expected_public_entries}, found {public_entry_count}.'
    )

if expected_private_entries is None or len(PRIVATE_STORIES) != expected_private_entries:
    raise SystemExit(
        f'Private entry mismatch: expected {expected_private_entries}, found {len(PRIVATE_STORIES)}.'
    )

slugs: set[str] = set()
gallery_image_count = 0
referenced_asset_count = 0

for file_path in [*PUBLIC_STORIES, *PUBLIC_ALBUMS, *PRIVATE_STORIES]:
    data = load_json(file_path)
    if not isinstance(data, dict):
        raise SystemExit(f'Expected object payload in {file_path}')
    if not data.get('title') or not data.get('slug'):
        raise SystemExit(f'Missing title or slug in {file_path}')

    is_private = file_path in PRIVATE_STORIES
    expected_privacy = 'private' if is_private else 'public'
    if data.get('privacy') != expected_privacy:
        raise SystemExit(f'Expected {expected_privacy} privacy classification in {file_path}')

    route_key = f"{file_path.parts[-4]}:{data['slug']}"
    if route_key in slugs:
        raise SystemExit(f'Duplicate content route slug: {route_key}')
    slugs.add(route_key)

    asset_root = PRIVATE_ASSETS if is_private else PUBLIC_ASSETS
    references = [*data.get('images', [])]
    if data.get('featuredImage'):
        references.append({'asset': data['featuredImage'], 'kind': 'featured'})
    for media in data.get('media', []):
        references.append({'asset': media.get('asset'), 'kind': media.get('type')})
        if media.get('poster'):
            references.append({'asset': media['poster'], 'kind': 'poster'})
        local_media = asset_root / media.get('asset', '')
        if local_media.exists() and local_media.stat().st_size > PAGES_FILE_LIMIT and not media.get('sourceUrl'):
            raise SystemExit(f'Large media needs an external source URL: {local_media}')

    for reference in references:
        relative_asset = reference.get('asset')
        if not relative_asset:
            raise SystemExit(f'Empty asset reference in {file_path}')
        asset_path = asset_root / relative_asset
        if not asset_path.is_file():
            raise SystemExit(f'Missing asset {relative_asset} referenced by {file_path}')
        referenced_asset_count += 1
        if reference.get('kind') == 'gallery':
            gallery_image_count += 1

if gallery_image_count != counts.get('galleryItems'):
    raise SystemExit(
        f"Gallery image mismatch: expected {counts.get('galleryItems')}, found {gallery_image_count}."
    )

print(
    f'Validated migration output: {len(PUBLIC_STORIES)} public stories, '
    f'{len(PUBLIC_ALBUMS)} public albums, {len(PRIVATE_STORIES)} private stories, '
    f'{gallery_image_count} gallery images, and {referenced_asset_count} asset references.'
)
