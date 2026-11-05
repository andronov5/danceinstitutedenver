#!/usr/bin/env python3
"""Build, check, and package the dependency-free website for static hosting."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zipfile import ZIP_DEFLATED, ZipFile

from check_copy import check_copy


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PAGE_DIRS = (
    "dance-classes", "about", "schedule", "shows-and-competition", "summer-intensive", "register", "contact",
    "privacy-policy", "accessibility-statement", "about-1", "class-schedule", "performances",
    "competition", "registration", "adult-kids-dance-classes", "courses", "nutcracker",
)
EXPECTED_PAGES = [Path("index.html"), *(Path(name) / "index.html" for name in PAGE_DIRS), Path("about/teachers/index.html"), Path("about/studio-policies/index.html"), *(Path("shows-and-competition") / route / "index.html" for route in ("nutcracker","competition","recital"))]
MAX_BYTES = 20_000_000  # Conservative decimal interpretation of Wix's 20 MB limit.
MAX_FILES = 5_000
ALLOWED_SUFFIXES = {
    ".html", ".htm", ".css", ".js", ".mjs", ".cjs", ".jsx", ".map",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".avif", ".bmp",
    ".heic", ".heif", ".tiff", ".mp4", ".webm", ".ogv", ".mp3", ".wav",
    ".ogg", ".m4a", ".woff", ".woff2", ".ttf", ".otf", ".eot", ".json",
    ".xml", ".txt", ".md", ".pdf", ".csv", ".yaml", ".geojson", ".glb",
    ".gltf", ".bin",
}
CSS_URL = re.compile(r"url\(\s*['\"]?([^)'\"]+)['\"]?\s*\)", re.I)
CSS_IMPORT = re.compile(r"@import\s+['\"]([^'\"]+)['\"]", re.I)


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.references: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)
        for key in ("href", "src", "poster"):
            if values.get(key):
                self.references.append((values[key] or "", f"{tag}[{key}]"))
        if values.get("srcset") and not (values["srcset"] or "").lstrip().startswith("data:"):
            for candidate in (values["srcset"] or "").split(","):
                parts = candidate.strip().split()
                if parts:
                    self.references.append((parts[0], f"{tag}[srcset]"))
        if values.get("style"):
            for url in CSS_URL.findall(values["style"] or ""):
                self.references.append((url.strip(), f"{tag}[style]"))

    handle_startendtag = handle_starttag


def local_target(base: Path, source: Path, url: str) -> tuple[Path, str] | None:
    parsed = urlsplit(url.strip())
    if parsed.scheme or parsed.netloc:
        return None
    decoded = unquote(parsed.path)
    if not decoded:
        target = source
    elif decoded.startswith("/"):
        target = base / decoded.lstrip("/")
    else:
        target = source.parent / decoded
    target = target.resolve()
    if not target.is_relative_to(base.resolve()):
        raise ValueError(f"reference escapes site directory: {url}")
    if target.is_dir():
        target = target / "index.html"
    return target, unquote(parsed.fragment)


def validate(base: Path) -> None:
    problems: list[str] = []
    if not base.is_dir():
        raise ValueError("No dist directory. Run npm run build first.")
    files = sorted(path for path in base.rglob("*") if path.is_file())
    total = sum(path.stat().st_size for path in files)
    if len(files) > MAX_FILES:
        problems.append(f"{len(files)} files exceeds Wix's {MAX_FILES}-file limit")
    if total > MAX_BYTES:
        problems.append(f"{total:,} bytes exceeds the {MAX_BYTES:,}-byte upload budget")
    for relative in EXPECTED_PAGES:
        if not (base / relative).is_file():
            problems.append(f"Missing required page: {relative}")
    for path in files:
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            problems.append(f"Unsupported Wix upload file type: {path.relative_to(base)}")
        if path.stat().st_size > MAX_BYTES:
            problems.append(f"File exceeds upload budget: {path.relative_to(base)}")

    pages: dict[Path, Page] = {}
    references: list[tuple[Path, str, str]] = []
    for path in files:
        if path.suffix.lower() in {".html", ".htm"}:
            page = Page()
            page.feed(path.read_text(encoding="utf-8"))
            pages[path.resolve()] = page
            for element_id in page.duplicate_ids:
                problems.append(f"{path.relative_to(base)}: duplicate id '{element_id}'")
            references.extend((path, url, context) for url, context in page.references)
        elif path.suffix.lower() == ".css":
            css = path.read_text(encoding="utf-8")
            references.extend((path, url.strip(), "CSS") for url in CSS_URL.findall(css))
            references.extend((path, url.strip(), "CSS import") for url in CSS_IMPORT.findall(css))

    for source, url, context in references:
        try:
            resolved = local_target(base, source, url)
        except ValueError as error:
            problems.append(f"{source.relative_to(base)}: {error}")
            continue
        if resolved is None:
            continue
        target, fragment = resolved
        if not target.is_file():
            problems.append(f"{source.relative_to(base)}: missing {context} target '{url}'")
        elif fragment and target in pages and fragment not in pages[target].ids:
            problems.append(f"{source.relative_to(base)}: missing anchor in '{url}'")

    if problems:
        raise ValueError("Website validation failed:\n  - " + "\n  - ".join(problems))
    print(f"Checked {len(pages)} pages, {len(files)} files, {total / 1_000_000:.2f} MB.")
    print("Local links, anchors, assets, file types, and Wix upload limits passed.")
    check_copy(base)


def build() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "render.py")], cwd=ROOT, check=True)
    if not (ROOT / "index.html").is_file():
        raise ValueError("The root index.html has not been created yet.")
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copy2(ROOT / "index.html", DIST / "index.html")
    for name in (*PAGE_DIRS, "assets"):
        source = ROOT / name
        if source.is_dir():
            shutil.copytree(source, DIST / name, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"))
    validate(DIST)


def package() -> None:
    build()
    destination = ROOT / "exports" / "dance-institute-denver-wix.zip"
    destination.parent.mkdir(exist_ok=True)
    with ZipFile(destination, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(DIST.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(DIST))
    print(f"Created {destination.relative_to(ROOT)} (index.html at the ZIP root).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check", "package"))
    args = parser.parse_args()
    try:
        {"build": build, "check": lambda: validate(DIST), "package": package}[args.command]()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
