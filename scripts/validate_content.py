#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / 'reports' / 'migration-manifest.json'
PUBLIC_STORIES = sorted((ROOT / 'src' / 'content' / 'stories' / 'legacy').glob('**/*.json'))
PUBLIC_ALBUMS = sorted((ROOT / 'src' / 'content' / 'albums' / 'legacy').glob('**/*.json'))
PRIVATE_STORIES = sorted((ROOT / 'private-site' / 'content' / 'stories' / 'legacy').glob('**/*.json'))


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

for file_path in [*PUBLIC_STORIES, *PUBLIC_ALBUMS, *PRIVATE_STORIES]:
    data = load_json(file_path)
    if not isinstance(data, dict):
        raise SystemExit(f'Expected object payload in {file_path}')
    if not data.get('title') or not data.get('slug'):
        raise SystemExit(f'Missing title or slug in {file_path}')

print(
    f'Validated migration output: {len(PUBLIC_STORIES)} story files, '
    f'{len(PUBLIC_ALBUMS)} album files, {len(PRIVATE_STORIES)} private story files.'
)
