#!/usr/bin/env python3
"""Check preserved editorial copy against the captured Wix page reference."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
PAGE_PATHS = {
    "Home": "index.html",
    "Performances": "performances/index.html",
    "About": "about-1/index.html",
    "Class Schedule": "class-schedule/index.html",
    "Competition": "competition/index.html",
    "Contact": "contact/index.html",
    "Privacy Policy": "privacy-policy/index.html",
    "Accessibility Statement": "accessibility-statement/index.html",
    "Courses": "courses/index.html",
}


def normalize(text: str) -> str:
    # Layout may split paragraphs or headings into separate elements. Retain all
    # letters and punctuation; ignore only whitespace and invisible separators.
    return re.sub(r"[\s\u200b-\u200d\ufeff]+", "", text)


class MainText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_main = False
        self.ignore_depth = 0
        self.pieces: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "main":
            self.in_main = True
        if self.in_main and tag in {"script", "style"}:
            self.ignore_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "main":
            self.in_main = False
        if self.in_main and tag in {"script", "style"}:
            self.ignore_depth = max(0, self.ignore_depth - 1)

    def handle_data(self, data: str) -> None:
        if self.in_main and not self.ignore_depth:
            self.pieces.append(data)


def course_blocks(page: dict) -> list[dict]:
    """Captured dynamic pages can include a prior page after their own content."""
    blocks = page["data"]["blocks"]
    first = next(i for i, block in enumerate(blocks) if block["tag"] == "H1")
    end = next((i for i in range(first + 1, len(blocks)) if blocks[i]["tag"] == "H1"), len(blocks))
    return blocks[first:end]


def legal_extra_lines(page: dict) -> list[str]:
    """Include source list items that the original H/P block capture omitted."""
    if page["name"] not in {"Privacy Policy", "Accessibility Statement"}:
        return []
    lines = [line.strip() for line in page["data"]["text"].splitlines() if normalize(line)]
    start = lines.index("Contact Us") + 1
    footer = max(i for i, line in enumerate(lines) if line == "Dance Institute")
    block_text = normalize("".join(block["text"] for block in page["data"]["blocks"]))
    return [line for line in lines[start:footer] if normalize(line) not in block_text]


def check_copy(base: Path) -> None:
    checks = []
    for reference in sorted((ROOT / 'reference').glob('*-request.json')):
        for route, expected in json.loads(reference.read_text()).items():
            checks.append((route, base / route, expected))
    source_pages = json.loads((ROOT/'reference/wix-content.json').read_text())
    for page in source_pages:
        if page['name'] in {'Privacy Policy', 'Accessibility Statement'}:
            checks.append((page['name'], base/PAGE_PATHS[page['name']], [b['text'] for b in page['data']['blocks']] + legal_extra_lines(page)))
        elif page['name'] == 'Contact':
            checks.append(('Contact',base/'contact/index.html',[b['text'] for i,b in enumerate(page['data']['blocks']) if i != 1]))
    checks.append(('Shows & Competition',base/'shows-and-competition/index.html',['Shows & Competition']))
    missing: list[str] = []
    checked_blocks = 0
    for name, path, expected in checks:
        if not path.is_file():
            missing.append(f"{name}: page missing ({path.relative_to(base)})")
            continue
        parser = MainText()
        parser.feed(path.read_text(encoding="utf-8"))
        actual = normalize("".join(parser.pieces))
        counts = Counter(normalize(text) for text in expected if normalize(text))
        checked_blocks += sum(counts.values())
        for text, required in counts.items():
            if actual.count(text) < required:
                original = next(item for item in expected if normalize(item) == text)
                excerpt = re.sub(r"\s+", " ", original).strip()[:140]
                missing.append(f"{name}: missing/changed source copy ({required} occurrence(s)): {excerpt!r}")
    if missing:
        raise ValueError("Copy preservation check failed:\n  - " + "\n  - ".join(missing))
    print(f"Preserved {checked_blocks} source text blocks across {len(checks)} pages, including the newly supplied content.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default=str(ROOT / "dist"))
    args = parser.parse_args()
    check_copy(Path(args.directory).resolve())
