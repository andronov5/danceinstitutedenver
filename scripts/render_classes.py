"""Concise class descriptions aligned with the supplied 2026–2027 timetable."""

from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTE = "dance-classes/index.html"
CATEGORIES = ("Combo Classes", "Advanced Classes", "Ballet Classes", "Hip-Hop Classes", "Additional Classes")
PLACEMENT_NOTE = "Class placement is determined by Dance Institute Instructors."


def row(text: str) -> str:
    """Keep each supplied class name beside its description in one readable row."""
    name, separator, description = text.partition("\n")
    content = f"<h3>{html.escape(name)}</h3>"
    if separator:
        content += f"<p>{html.escape(description)}</p>"
    return f'<article class="classes-row">{content}</article>'


def render_classes(prefix: str = "../") -> str:
    """Return main-inner HTML; the shared shell owns navigation and assets."""
    blocks = json.loads((ROOT / "reference" / "classes-request.json").read_text(encoding="utf-8"))[ROUTE]
    title = blocks[0]
    sections: dict[str, list[str]] = {}
    current = ""
    for block in blocks[1:]:
        if block == PLACEMENT_NOTE:
            continue
        if block in CATEGORIES:
            current = block
            sections[current] = []
        else:
            sections[current].append(block)

    out = f'''<div class="classes-page">
      <header class="page-intro section-shell"><h1 class="intro-title">{html.escape(title)}</h1></header>
      <nav class="section-shell classes-jump" aria-label="Class categories">'''
    for category in CATEGORIES:
        identifier = category.lower().replace(" ", "-")
        out += f'<a href="#{identifier}">{html.escape(category)}</a>'
    out += '</nav><div class="section-shell classes-accordion">'

    for category in CATEGORIES:
        identifier = category.lower().replace(" ", "-")
        out += f'''<details class="classes-group" id="{identifier}" open>
          <summary class="classes-summary"><h2>{html.escape(category)}</h2><span class="classes-toggle" aria-hidden="true"></span></summary>
          <div class="classes-rows">'''
        for text in sections[category]:
            out += row(text)
        out += "</div></details>"

    out += f'</div><div class="section-shell"><p class="classes-placement">{html.escape(PLACEMENT_NOTE)}</p></div></div>'
    return out
