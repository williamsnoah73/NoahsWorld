#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "Welcome_to_Noahs_World"
PUBLIC_CONTENT_ROOT = ROOT / "src" / "content"
PRIVATE_CONTENT_ROOT = ROOT / "private-site" / "content"
PUBLIC_ASSET_ROOT = ROOT / "src" / "assets" / "public"
PRIVATE_ASSET_ROOT = ROOT / "private-site" / "assets"
REPORT_PATH = ROOT / "reports" / "migration-manifest.json"

NS = {
    "x": "http://www.w3.org/1999/xhtml",
    "iphoto": "urn:iphoto:property",
    "iweb": "http://www.apple.com/iweb",
}

STORY_PAGES = {
    Path("Welcome.html"): {"section": "home", "privacy": "public"},
    Path("The_Family.html"): {"section": "family", "privacy": "private"},
    Path("Madison.html"): {"section": "family", "privacy": "private"},
    Path("Travel/Pages/Double_Musky_Express.html"): {
        "section": "travel",
        "privacy": "public",
    },
    Path("Travel/Pages/Maui_-_July_2010.html"): {
        "section": "travel",
        "privacy": "public",
    },
    Path("Travel/Pages/Park_City_-_March_2010.html"): {
        "section": "travel",
        "privacy": "public",
    },
    Path("Jeep_Stuff/Pages/Jeep_Upgrade.html"): {
        "section": "jeep-stuff",
        "privacy": "public",
    },
    Path("Jeep_Stuff/Pages/Sunflower_Mine_Excursion.html"): {
        "section": "jeep-stuff",
        "privacy": "public",
    },
    Path("The_Wedding/Pages/Wedding.html"): {
        "section": "wedding",
        "privacy": "public",
    },
}

ALBUM_PAGES = {
    Path("Albums/Pages/Maui_2010_-_4th_of_July.html"): {
        "section": "travel",
        "privacy": "public",
    },
    Path("Albums/Pages/Maui_2010_-_Cirque_Polynesia.html"): {
        "section": "travel",
        "privacy": "public",
    },
    Path("Albums/Pages/Maui_2010_-_Helicopter_Tour.html"): {
        "section": "travel",
        "privacy": "public",
    },
    Path("Albums/Pages/Maui_2010_-_Maui_Ocean_Center.html"): {
        "section": "travel",
        "privacy": "public",
    },
    Path("Albums/Pages/Maui_2010_-_Ocean_Sailing.html"): {
        "section": "travel",
        "privacy": "public",
    },
    Path("Albums/Pages/Maui_2010_-_Road_to_Hana.html"): {
        "section": "travel",
        "privacy": "public",
    },
    Path("Albums/Pages/Maui_2010_-_Sunsets.html"): {
        "section": "travel",
        "privacy": "public",
    },
    Path("Albums/Pages/Maui_2010_-_Wailele_Luau.html"): {
        "section": "travel",
        "privacy": "public",
    },
}

LANDING_PAGES = {
    Path("Travel/Travel.html"): {"section": "travel", "privacy": "public"},
    Path("Jeep_Stuff/Jeep_Stuff.html"): {"section": "jeep-stuff", "privacy": "public"},
    Path("The_Wedding/The_Wedding.html"): {"section": "wedding", "privacy": "public"},
    Path("Albums/Albums.html"): {"section": "albums", "privacy": "public"},
}

ALL_PAGES = STORY_PAGES | ALBUM_PAGES | LANDING_PAGES

GENERATED_DIRS = [
    PUBLIC_CONTENT_ROOT / "stories" / "legacy",
    PUBLIC_CONTENT_ROOT / "albums" / "legacy",
    PRIVATE_CONTENT_ROOT / "stories" / "legacy",
    PRIVATE_CONTENT_ROOT / "albums" / "legacy",
    PUBLIC_ASSET_ROOT / "legacy",
    PRIVATE_ASSET_ROOT / "legacy",
]

DECORATIVE_IMAGE_PATTERNS = (
    "darkroom_spotlight",
    "photogray_",
    "mwmac_white",
    "stroke",
    "techblack-frame",
    "spiralboook",
    "transparent",
    "canvas_",
)

EXPECTED_SUBSTANTIVE_PAGE_COUNT = 21
EXPECTED_FEED_COUNT = 17
EXPECTED_GALLERY_ITEM_COUNT = 290


class MigrationError(RuntimeError):
    pass


@dataclass
class BlockRecord:
    type: str
    text: str
    links: list[dict[str, str]]
    classes: list[str]
    position: float


@dataclass
class VideoCandidate:
    position: float
    source_url: str
    source_path: Path | None
    poster_path: Path | None
    kind: str = "video"


def local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def class_list(element: ET.Element) -> list[str]:
    raw = element.attrib.get("class", "")
    return [part for part in raw.split() if part]


def normalize_text(value: str) -> str:
    value = value.replace("\xa0", " ")
    value = value.replace("\r", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r" ?\n ?", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = ascii_value.lower()
    ascii_value = re.sub(r"[^a-z0-9]+", "-", ascii_value)
    ascii_value = re.sub(r"-{2,}", "-", ascii_value)
    return ascii_value.strip("-")


def style_number(style: str, name: str) -> float | None:
    match = re.search(rf"{re.escape(name)}:\s*(-?\d+(?:\.\d+)?)px", style)
    if not match:
        return None
    return float(match.group(1))


def element_position(element: ET.Element) -> float:
    style = element.attrib.get("style", "")
    for field in ("top", "margin-top", "bottom"):
        value = style_number(style, field)
        if value is not None:
            return value
    return 0.0


def is_parseable_date(text: str) -> bool:
    try:
        datetime.strptime(text, "%B %d, %Y")
    except ValueError:
        return False
    return True


def normalize_date(text: str | None) -> str | None:
    if not text:
        return None
    try:
        return datetime.strptime(text, "%B %d, %Y").date().isoformat()
    except ValueError:
        return None


def humanize_stem(relative_path: Path) -> str:
    return re.sub(r"\s+", " ", relative_path.stem.replace("_", " ")).strip()


def page_slug(relative_path: Path) -> str:
    return slugify(relative_path.stem)


def page_kind(relative_path: Path) -> str:
    if relative_path in STORY_PAGES:
        return "story"
    if relative_path in ALBUM_PAGES:
        return "album"
    if relative_path in LANDING_PAGES:
        return "landing"
    raise MigrationError(f"Unexpected page classification for {relative_path.as_posix()}")


def page_metadata(relative_path: Path) -> dict[str, str]:
    if relative_path not in ALL_PAGES:
        raise MigrationError(f"Unexpected substantive page {relative_path.as_posix()}")
    return ALL_PAGES[relative_path]


def resolve_legacy_path(href: str, current_relative: Path) -> Path | None:
    if not href:
        return None
    if href.startswith("#"):
        return current_relative

    parsed = urlparse(href)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return None

    if parsed.netloc:
        path = unquote(parsed.path)
        marker = "/Welcome_to_Noahs_World/"
        if marker not in path:
            return None
        rel = path.split(marker, 1)[1]
        return Path(rel)

    path = unquote(parsed.path)
    if not path:
        return current_relative
    base_parent = current_relative.parent
    if current_relative.name == "rss.xml" and current_relative.parent.name.endswith("_files"):
        base_parent = current_relative.parent.parent
    return (SOURCE_ROOT / base_parent / path).resolve().relative_to(SOURCE_ROOT)


def parse_html_tree(path: Path) -> ET.ElementTree:
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"(<video\b[^>]*?)\scontrols(?=[\s>])", r'\1 controls="controls"', raw)
    raw = re.sub(r"(<source\b[^>]*?)(?<!/)>", r"\1 />", raw)
    return ET.ElementTree(ET.fromstring(raw))


def classify_href(href: str, current_relative: Path) -> tuple[str, str]:
    parsed = urlparse(href)
    if parsed.scheme in {"http", "https"}:
        if "noahwilliams.me" in parsed.netloc:
            resolved = resolve_legacy_path(href, current_relative)
            if resolved is None:
                return ("external", href)
            return ("internal", resolved.as_posix())
        return ("external", href)
    if href.startswith("#"):
        return ("internal", f"{current_relative.as_posix()}{href}")
    if href.startswith("javascript:"):
        return ("script", href)
    resolved = resolve_legacy_path(href, current_relative)
    if resolved is None:
        return ("external", href)
    return ("internal", resolved.as_posix())


def extract_links(element: ET.Element, current_relative: Path) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for anchor in element.findall(".//x:a", NS):
        href = anchor.attrib.get("href", "").strip()
        text = normalize_text("".join(anchor.itertext()))
        kind, resolved = classify_href(href, current_relative)
        if not href or kind == "script":
            continue
        links.append(
            {
                "text": text,
                "href": href,
                "kind": kind,
                "resolved": resolved,
            }
        )
    return links


def paragraph_text(element: ET.Element) -> str:
    text = normalize_text("".join(element.itertext()))
    if text == "Your browser does not support the video tag.":
        return ""
    return text


def build_text_block(
    element: ET.Element,
    current_relative: Path,
    title_text: str,
    date_text: str | None,
    position: float,
) -> BlockRecord | None:
    text = paragraph_text(element)
    if not text:
        return None

    classes = class_list(element)
    class_set = set(classes)

    if text == title_text or text == "Noah’s World" or text == "Madison’s World":
        return None
    if is_parseable_date(text) and date_text and text == date_text:
        return None
    if text in {"Subscribe", "Back to Index", "Play Slideshow"}:
        return None

    block_type = "paragraph"
    if "Caption" in class_set:
        block_type = "caption"
    elif "Date" in class_set and not is_parseable_date(text):
        block_type = "caption"

    return BlockRecord(
        type=block_type,
        text=text,
        links=extract_links(element, current_relative),
        classes=classes,
        position=position,
    )


def build_list_block(
    element: ET.Element,
    current_relative: Path,
    position: float,
) -> BlockRecord | None:
    items = [
        normalize_text("".join(item.itertext()))
        for item in element.findall(".//x:li", NS)
    ]
    items = [item for item in items if item]
    if not items:
        return None

    text = "\n".join(f"- {item}" for item in items)
    return BlockRecord(
        type="list",
        text=text,
        links=extract_links(element, current_relative),
        classes=class_list(element),
        position=position,
    )


def harvest_text_blocks(
    container: ET.Element,
    current_relative: Path,
    title_text: str,
    date_text: str | None,
    base_position: float,
) -> list[BlockRecord]:
    blocks: list[BlockRecord] = []
    offset = 0.0

    def walk(node: ET.Element) -> None:
        nonlocal offset
        for child in list(node):
            tag = local_name(child.tag)
            if tag == "p":
                block = build_text_block(
                    child,
                    current_relative,
                    title_text,
                    date_text,
                    base_position + offset,
                )
                offset += 0.01
                if block:
                    blocks.append(block)
            elif tag in {"ol", "ul"}:
                block = build_list_block(child, current_relative, base_position + offset)
                offset += 0.01
                if block:
                    blocks.append(block)
            elif tag == "div":
                if child.find(".//x:video", NS) is not None:
                    text = paragraph_text(child)
                    if not text:
                        continue
                if "paragraph" in class_list(child):
                    block = build_text_block(
                        child,
                        current_relative,
                        title_text,
                        date_text,
                        base_position + offset,
                    )
                    offset += 0.01
                    if block:
                        blocks.append(block)
                    continue
                walk(child)

    walk(container)
    return blocks


def content_containers(body_layer: ET.Element) -> list[tuple[float, int, ET.Element]]:
    containers: list[tuple[float, int, ET.Element]] = []
    for index, child in enumerate(list(body_layer)):
        if local_name(child.tag) != "div":
            continue
        child_classes = class_list(child)
        child_id = child.attrib.get("id", "")
        if any("com-apple-iweb-widget" in class_name for class_name in child_classes):
            continue
        if child_id.startswith("widget"):
            continue
        text_container = None
        for descendant in child.findall(".//x:div", NS):
            if "text-content" in class_list(descendant):
                text_container = descendant
                break
        if text_container is None:
            continue
        containers.append((element_position(child), index, text_container))
    containers.sort(key=lambda item: (item[0], item[1]))
    return containers


def extract_body_blocks(
    body_layer: ET.Element,
    current_relative: Path,
    title_text: str,
    date_text: str | None,
) -> list[BlockRecord]:
    blocks: list[BlockRecord] = []
    for position, _, container in content_containers(body_layer):
        blocks.extend(
            harvest_text_blocks(
                container,
                current_relative,
                title_text,
                date_text,
                position,
            )
        )
    blocks.sort(key=lambda block: block.position)
    return blocks


def is_decorative_image(src: str) -> bool:
    lower = src.lower()
    return any(pattern in lower for pattern in DECORATIVE_IMAGE_PATTERNS)


def inline_image_sources(body_layer: ET.Element) -> list[Path]:
    sources: list[Path] = []
    seen: set[str] = set()
    for image in body_layer.findall(".//x:img", NS):
        src = image.attrib.get("src", "").strip()
        if not src or is_decorative_image(src):
            continue
        decoded = unquote(src)
        if decoded in seen:
            continue
        seen.add(decoded)
        sources.append(Path(decoded))
    return sources


def inline_videos(body_layer: ET.Element, current_relative: Path) -> list[VideoCandidate]:
    candidates: list[VideoCandidate] = []
    lfs_index = build_mp4_index()
    for child in list(body_layer):
        if local_name(child.tag) != "div" and local_name(child.tag) != "video":
            continue
        base_position = element_position(child)
        videos = [child] if local_name(child.tag) == "video" else child.findall(".//x:video", NS)
        for video in videos:
            source = video.find("./x:source", NS)
            if source is None:
                continue
            source_url = source.attrib.get("src", "").strip()
            if not source_url:
                continue

            poster = video.attrib.get("poster", "").strip()
            poster_path = (current_relative.parent / unquote(poster)) if poster else None

            position = element_position(video)
            if abs(position) < 1 and base_position:
                position = base_position

            source_path = resolve_local_mp4(source_url, lfs_index)
            candidates.append(
                VideoCandidate(
                    position=position,
                    source_url=source_url,
                    source_path=source_path,
                    poster_path=poster_path,
                )
            )
    candidates.sort(key=lambda candidate: candidate.position)
    return candidates


def parse_rich_title(value: str | None) -> str | None:
    if not value:
        return None
    text = normalize_text(re.sub(r"<[^>]+>", " ", unescape(value)))
    return text or None


def feed_path_from_page(doc: ET.ElementTree, page_relative: Path) -> Path | None:
    root = doc.getroot()
    for link in root.findall(".//x:link", NS):
        rel = link.attrib.get("rel", "")
        href = link.attrib.get("href", "")
        if rel == "alternate" and href.endswith("rss.xml"):
            return resolve_legacy_path(href, page_relative)
    return None


def parse_feed(feed_relative: Path) -> dict[str, Any]:
    feed_path = SOURCE_ROOT / feed_relative
    tree = ET.parse(feed_path)
    channel = tree.getroot().find("./channel")
    if channel is None:
        raise MigrationError(f"Feed missing channel: {feed_relative.as_posix()}")

    description = normalize_text(channel.findtext("description", default=""))
    items: list[dict[str, Any]] = []
    gallery_items = 0

    for index, item in enumerate(channel.findall("./item")):
        link_value = item.findtext("link", default="").strip()
        enclosure = item.find("enclosure")
        rich_title = item.findtext("{http://www.apple.com/iweb}richTitle")
        feed_item: dict[str, Any] = {
            "order": index + 1,
            "link": link_value,
        }

        if enclosure is not None:
            source_rel = resolve_legacy_path(enclosure.attrib.get("url", ""), feed_relative)
            if source_rel is None:
                raise MigrationError(
                    f"Unable to resolve enclosure for {feed_relative.as_posix()}: "
                    f"{enclosure.attrib.get('url', '')}"
                )
            gallery_items += 1
            feed_item.update(
                {
                    "kind": "gallery",
                    "sourceFile": source_rel.as_posix(),
                    "caption": parse_rich_title(rich_title),
                    "mimeType": enclosure.attrib.get("type", ""),
                }
            )
        else:
            linked_page = resolve_legacy_path(link_value, feed_relative)
            feed_item.update(
                {
                    "kind": "index",
                    "linkedPage": linked_page.as_posix() if linked_page else link_value,
                    "title": normalize_text(item.findtext("title", default="")),
                }
            )

        items.append(feed_item)

    feed_type = "gallery" if gallery_items else "index"
    return {
        "sourceFile": feed_relative.as_posix(),
        "type": feed_type,
        "title": normalize_text(channel.findtext("title", default="")),
        "description": description,
        "itemCount": len(items),
        "galleryItemCount": gallery_items,
        "items": items,
    }


def normalized_filename(name: str, index: int | None = None) -> str:
    path = Path(name)
    ext = path.suffix.lower()
    stem = slugify(path.stem)
    filename = f"{stem}{ext}" if stem else f"asset{ext}"
    if index is None:
        return filename
    return f"{index:03d}-{filename}"


def copy_file(source_relative: Path, asset_relative: Path, privacy: str) -> str:
    source_path = SOURCE_ROOT / source_relative
    if not source_path.exists():
        raise MigrationError(f"Missing source asset {source_relative.as_posix()}")

    asset_root = PUBLIC_ASSET_ROOT if privacy == "public" else PRIVATE_ASSET_ROOT
    destination = asset_root / asset_relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination)
    return asset_relative.as_posix()


def is_lfs_pointer(path: Path) -> bool:
    if not path.exists():
        return False
    with path.open("rb") as handle:
        head = handle.read(128)
    return head.startswith(b"version https://git-lfs.github.com/spec/v1")


def materialize_lfs_sources(paths: list[Path]) -> dict[str, Any]:
    source_paths = [SOURCE_ROOT / path for path in paths]
    pointer_paths = [path for path in source_paths if is_lfs_pointer(path)]
    if not pointer_paths:
        return {
            "attempted": False,
            "recovered": [],
            "blocked": [],
            "status": "already-materialized",
        }

    relative_args = [path.relative_to(ROOT).as_posix() for path in pointer_paths]
    include_value = ",".join(relative_args)
    result = subprocess.run(
        ["git", "lfs", "pull", f"--include={include_value}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    recovered: list[str] = []
    blocked: list[dict[str, str]] = []
    for path in pointer_paths:
        rel = path.relative_to(ROOT).as_posix()
        if is_lfs_pointer(path):
            blocked.append(
                {
                    "sourceFile": rel,
                    "reason": "git-lfs object could not be materialized",
                }
            )
        else:
            recovered.append(rel)

    return {
        "attempted": True,
        "status": "recovered" if not blocked else "blocked",
        "recovered": recovered,
        "blocked": blocked,
        "stdout": normalize_text(result.stdout),
        "stderr": normalize_text(result.stderr),
    }


def build_mp4_index() -> dict[str, Path]:
    index: dict[str, Path] = {}
    for path in (SOURCE_ROOT / "Media").glob("*.mp4"):
        key = re.sub(r"[^a-z0-9]", "", path.stem.lower())
        index[key] = path.relative_to(SOURCE_ROOT)
    return index


def resolve_local_mp4(source_url: str, mp4_index: dict[str, Path]) -> Path | None:
    basename = Path(unquote(urlparse(source_url).path)).name
    key = re.sub(r"[^a-z0-9]", "", Path(basename).stem.lower())
    return mp4_index.get(key)


def clear_generated_output() -> None:
    for path in GENERATED_DIRS:
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)


def discover_pages() -> list[Path]:
    pages = [
        path.relative_to(SOURCE_ROOT)
        for path in SOURCE_ROOT.rglob("*.html")
        if path.name not in {"index.html", "streamloader.html"} and "Media" not in path.parts
    ]
    pages.sort()
    if len(pages) != EXPECTED_SUBSTANTIVE_PAGE_COUNT:
        raise MigrationError(
            f"Expected {EXPECTED_SUBSTANTIVE_PAGE_COUNT} substantive pages, found {len(pages)}"
        )
    unexpected = [page for page in pages if page not in ALL_PAGES]
    missing = [page for page in ALL_PAGES if page not in pages]
    if unexpected or missing:
        raise MigrationError(
            "Substantive page set mismatch: "
            f"unexpected={[page.as_posix() for page in unexpected]} "
            f"missing={[page.as_posix() for page in missing]}"
        )
    return pages


def discover_feeds() -> list[Path]:
    feeds = [path.relative_to(SOURCE_ROOT) for path in SOURCE_ROOT.rglob("rss.xml")]
    feeds.sort()
    if len(feeds) != EXPECTED_FEED_COUNT:
        raise MigrationError(f"Expected {EXPECTED_FEED_COUNT} feeds, found {len(feeds)}")
    return feeds


def page_output_relative(kind: str, section: str, slug: str) -> Path:
    collection = "stories" if kind == "story" else "albums"
    return Path(collection) / "legacy" / section / f"{slug}.json"


def asset_prefix(kind: str, section: str, slug: str) -> Path:
    collection = "stories" if kind == "story" else "albums"
    return Path("legacy") / collection / section / slug


def serialize_blocks(blocks: list[BlockRecord]) -> list[dict[str, Any]]:
    return [
        {
            "type": block.type,
            "text": block.text,
            "links": block.links,
        }
        for block in blocks
    ]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_entry(
    page_relative: Path,
    feed_by_page: dict[Path, dict[str, Any]],
    lfs_status: dict[str, Any],
    blockers: list[dict[str, str]],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    page_path = SOURCE_ROOT / page_relative
    tree = parse_html_tree(page_path)
    body_layer = tree.getroot().find(".//x:div[@id='body_layer']", NS)
    if body_layer is None:
        raise MigrationError(f"Missing body layer in {page_relative.as_posix()}")

    metadata = page_metadata(page_relative)
    kind = page_kind(page_relative)
    slug = page_slug(page_relative)

    title_node = body_layer.find(".//x:p[@class='Title']", NS)
    if title_node is not None:
        title_text = normalize_text("".join(title_node.itertext()))
    else:
        head_title = normalize_text(tree.getroot().findtext(".//x:title", default="", namespaces=NS))
        if head_title and head_title not in {"Noah’s World", "Noah's World"}:
            title_text = head_title
        else:
            title_text = humanize_stem(page_relative)

    date_text = None
    for candidate in body_layer.findall(".//x:p[@class='Date']", NS):
        text = normalize_text("".join(candidate.itertext()))
        if is_parseable_date(text):
            date_text = text
            break

    blocks = extract_body_blocks(body_layer, page_relative, title_text, date_text)
    feed = feed_by_page.get(page_relative)

    summary = feed["description"] if feed and feed["description"] else ""
    if not summary:
        for block in blocks:
            if block.type == "paragraph":
                summary = block.text
                break

    privacy = metadata["privacy"]
    section = metadata["section"]
    output_relative = page_output_relative(kind, section, slug)
    asset_base = asset_prefix(kind, section, slug)

    images: list[dict[str, Any]] = []
    media: list[dict[str, Any]] = []
    paired_caption_positions: set[float] = set()

    if feed and feed["type"] == "gallery":
        for item in feed["items"]:
            source_relative = Path(item["sourceFile"])
            filename = normalized_filename(source_relative.name, item["order"])
            asset_relative = asset_base / filename
            asset_id = copy_file(source_relative, asset_relative, privacy)
            images.append(
                {
                    "asset": asset_id,
                    "caption": item.get("caption"),
                    "sourceFile": item["sourceFile"],
                    "order": item["order"],
                    "kind": "gallery",
                }
            )
    else:
        inline_sources = inline_image_sources(body_layer)
        for index, source_relative in enumerate(inline_sources, start=1):
            filename = normalized_filename(source_relative.name, index)
            asset_relative = asset_base / filename
            asset_id = copy_file((page_relative.parent / source_relative), asset_relative, privacy)
            images.append(
                {
                    "asset": asset_id,
                    "caption": None,
                    "sourceFile": (page_relative.parent / source_relative).as_posix(),
                    "order": index,
                    "kind": "inline",
                }
            )

    video_candidates = inline_videos(body_layer, page_relative)
    caption_blocks = [block for block in blocks if block.type == "caption"]
    for index, candidate in enumerate(video_candidates, start=1):
        caption_text = None
        for caption in caption_blocks:
            if caption.position in paired_caption_positions:
                continue
            if 150 <= (caption.position - candidate.position) <= 260:
                paired_caption_positions.add(caption.position)
                caption_text = caption.text
                break

        asset_id = None
        if candidate.source_path is not None:
            source_absolute = SOURCE_ROOT / candidate.source_path
            if is_lfs_pointer(source_absolute):
                blockers.append(
                    {
                        "sourceFile": candidate.source_path.as_posix(),
                        "reason": "git-lfs mp4 pointer remained unresolved; pointer left untouched",
                    }
                )
            else:
                filename = normalized_filename(candidate.source_path.name, index)
                asset_relative = asset_base / filename
                asset_id = copy_file(candidate.source_path, asset_relative, privacy)
        else:
            blockers.append(
                {
                    "sourceFile": candidate.source_url,
                    "reason": "could not map remote mp4 URL to a local source file",
                }
            )

        poster_id = None
        if candidate.poster_path is not None:
            poster_filename = normalized_filename(candidate.poster_path.name, index)
            poster_relative = asset_base / poster_filename
            poster_id = copy_file(candidate.poster_path, poster_relative, privacy)

        media.append(
            {
                "type": candidate.kind,
                "asset": asset_id,
                "poster": poster_id,
                "caption": caption_text,
                "sourceUrl": candidate.source_url,
                "sourceFile": candidate.source_path.as_posix() if candidate.source_path else None,
            }
        )

    filtered_blocks = [block for block in blocks if block.position not in paired_caption_positions]

    entry = {
        "title": title_text,
        "slug": slug,
        "date": normalize_date(date_text),
        "section": section,
        "summary": summary or None,
        "body": serialize_blocks(filtered_blocks),
        "images": images,
        "privacy": privacy,
        "sourceFile": page_relative.as_posix(),
        "featuredImage": images[0]["asset"] if images else None,
    }
    if feed is not None:
        entry["sourceFeed"] = feed["sourceFile"]
    if media:
        entry["media"] = media

    manifest_page = {
        "sourceFile": page_relative.as_posix(),
        "kind": kind,
        "privacy": privacy,
        "section": section,
        "title": title_text,
        "slug": slug,
        "date": normalize_date(date_text),
        "summary": summary or None,
        "sourceFeed": feed["sourceFile"] if feed else None,
        "galleryItemCount": len([image for image in images if image["kind"] == "gallery"]),
        "inlineImageCount": len([image for image in images if image["kind"] == "inline"]),
        "videoCount": len(media),
    }

    if kind == "landing":
        manifest_page["body"] = serialize_blocks(filtered_blocks)
        manifest_page["outputFile"] = None
        if feed:
            manifest_page["feedItems"] = feed["items"]
        return manifest_page, None

    content_root = PUBLIC_CONTENT_ROOT if privacy == "public" else PRIVATE_CONTENT_ROOT
    destination = content_root / output_relative
    write_json(destination, entry)
    manifest_page["outputFile"] = output_relative.as_posix()
    manifest_page["assetCount"] = len(images) + len(media)
    return manifest_page, entry


def main() -> int:
    try:
        clear_generated_output()
        pages = discover_pages()
        feeds = discover_feeds()

        mp4_sources = sorted(path.relative_to(SOURCE_ROOT) for path in (SOURCE_ROOT / "Media").glob("*.mp4"))
        lfs_status = materialize_lfs_sources(mp4_sources)
        blockers: list[dict[str, str]] = list(lfs_status.get("blocked", []))

        feed_records = [parse_feed(feed) for feed in feeds]
        feed_by_source = {Path(record["sourceFile"]): record for record in feed_records}
        feed_by_page: dict[Path, dict[str, Any]] = {}

        for page_relative in pages:
            tree = parse_html_tree(SOURCE_ROOT / page_relative)
            feed_relative = feed_path_from_page(tree, page_relative)
            if feed_relative is not None:
                record = feed_by_source.get(feed_relative)
                if record is None:
                    raise MigrationError(
                        f"Page references unknown feed {feed_relative.as_posix()} "
                        f"from {page_relative.as_posix()}"
                    )
                feed_by_page[page_relative] = record

        gallery_total = sum(record["galleryItemCount"] for record in feed_records)
        if gallery_total != EXPECTED_GALLERY_ITEM_COUNT:
            raise MigrationError(
                f"Expected {EXPECTED_GALLERY_ITEM_COUNT} gallery items, found {gallery_total}"
            )

        manifest_pages: list[dict[str, Any]] = []
        generated_entries: list[dict[str, Any]] = []
        for page_relative in pages:
            manifest_page, entry = build_entry(page_relative, feed_by_page, lfs_status, blockers)
            manifest_pages.append(manifest_page)
            if entry is not None:
                generated_entries.append(entry)

        story_count = sum(1 for page in manifest_pages if page["kind"] == "story")
        album_count = sum(1 for page in manifest_pages if page["kind"] == "album")
        landing_count = sum(1 for page in manifest_pages if page["kind"] == "landing")
        if story_count != len(STORY_PAGES) or album_count != len(ALBUM_PAGES) or landing_count != len(LANDING_PAGES):
            raise MigrationError("Generated page counts do not match the expected story/album/landing split")

        total_gallery_assets = sum(page["galleryItemCount"] for page in manifest_pages)
        total_inline_images = sum(page.get("inlineImageCount", 0) for page in manifest_pages)
        total_videos = sum(page.get("videoCount", 0) for page in manifest_pages)

        manifest = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "sourceRoot": SOURCE_ROOT.name,
            "totals": {
                "substantivePages": len(pages),
                "storyEntries": story_count,
                "albumEntries": album_count,
                "landingPages": landing_count,
                "publicEntries": sum(
                    1 for page in manifest_pages if page["kind"] != "landing" and page["privacy"] == "public"
                ),
                "privateEntries": sum(
                    1 for page in manifest_pages if page["kind"] != "landing" and page["privacy"] == "private"
                ),
                "rssFeeds": len(feed_records),
                "galleryFeeds": sum(1 for record in feed_records if record["type"] == "gallery"),
                "indexFeeds": sum(1 for record in feed_records if record["type"] == "index"),
                "galleryItems": gallery_total,
                "copiedGalleryImages": total_gallery_assets,
                "copiedInlineImages": total_inline_images,
                "copiedVideos": total_videos,
            },
            "lfs": lfs_status,
            "pages": manifest_pages,
            "feeds": feed_records,
            "blockers": blockers,
        }

        write_json(REPORT_PATH, manifest)

        print(
            json.dumps(
                {
                    "pages": len(pages),
                    "storyEntries": story_count,
                    "albumEntries": album_count,
                    "landingPages": landing_count,
                    "galleryItems": gallery_total,
                    "copiedGalleryImages": total_gallery_assets,
                    "copiedInlineImages": total_inline_images,
                    "copiedVideos": total_videos,
                    "blockers": len(blockers),
                    "manifest": REPORT_PATH.relative_to(ROOT).as_posix(),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0
    except MigrationError as error:
        print(f"migration failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
