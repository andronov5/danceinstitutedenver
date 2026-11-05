"""Dance Classes presentation using the user's supplied copy verbatim."""

from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTE = "dance-classes/index.html"
CATEGORIES = ("Combo Classes", "Ballet Classes", "Hip-Hop Classes", "Additional Classes")
LEADING_NAMES = (
    "Intro to Poms",
    "3 & 4-year-old, 4 & 5-year-old and 5 & 7-year-old",
    "6-9-Year-Old:",
    "8-11-Year-Old:",
    "Advanced:",
    "Pre-Pointe",
    "Pointe",
    "Recommendation:",
    "Musical Theater",
    "Intro to Hip-Hop:",
    "Hip-Hop 1 :",
    "Hip-Hop 2:",
    "Hip-Hop 3:",
)


def row(text: str, extra_class: str = "") -> str:
    """Emphasize an existing name without inserting or changing any words."""
    leading = next((name for name in LEADING_NAMES if text.startswith(name)), "")
    content = html.escape(text)
    if leading:
        content = "<strong>" + html.escape(leading) + "</strong>" + html.escape(text[len(leading):])
    content = content.replace("\n", "<br>")
    return f'<p class="classes-row{(" " + extra_class) if extra_class else ""}">{content}</p>'


def render_classes(prefix: str = "../") -> str:
    """Return main-inner HTML; the shared shell owns navigation and assets."""
    blocks = json.loads((ROOT / "reference" / "classes-request.json").read_text(encoding="utf-8"))[ROUTE]
    title = blocks[0]
    sections: dict[str, list[str]] = {}
    current = ""
    for block in blocks[1:]:
        if block in CATEGORIES:
            current = block
            sections[current] = []
        else:
            sections[current].append(block)

    out = f'''<div class="classes-page">
      <header class="page-intro section-shell"><h1 class="intro-title">{html.escape(title)}</h1></header>
      <div class="section-shell classes-accordion">'''

    for category in CATEGORIES:
        identifier = category.lower().replace(" ", "-")
        opened = " open"
        out += f'''<details class="classes-group" id="{identifier}"{opened}>
          <summary class="classes-summary"><h2>{html.escape(category)}</h2><span class="classes-toggle" aria-hidden="true"></span></summary>
          <div class="classes-rows">'''
        for text in sections[category]:
            intro = "classes-introduction" if category == "Hip-Hop Classes" and text.startswith("Have a blast") else ""
            out += row(text, intro)
        out += "</div></details>"

    out += '</div></div>'
    return out
