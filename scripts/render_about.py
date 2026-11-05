"""About pages using the user's exact supplied copy and existing studio copy."""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST = json.loads((ROOT / "reference/about-request.json").read_text(encoding="utf-8"))
ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7"/></svg>'


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def paragraph(value: str) -> str:
    return f"<p>{esc(value)}</p>"


def title(value: str) -> str:
    return f'<header class="page-intro section-shell"><h1 class="intro-title">{esc(value)}</h1></header>'


def render_about(prefix: str = "../") -> str:
    """Return the About hub's main content, without the shared site shell."""
    blocks = REQUEST["about/index.html"]
    return f'''<div class="about-hub">
      {title(blocks[0])}
      <section class="section-shell about-hub-layout">
        <figure class="about-hub-photo"><img src="{esc(prefix)}assets/images/dance-community.webp" alt="Young Dance Institute dancers in pink tutus on stage" width="1100" height="1566" loading="eager" fetchpriority="high" decoding="async"></figure>
        <div class="about-hub-copy">{paragraph(blocks[1])}
          <nav class="about-hub-links" aria-label="About">
            <a href="{esc(prefix)}about/teachers/index.html"><span>{esc(blocks[2])}</span>{ARROW}</a>
            <a href="{esc(prefix)}about/studio-policies/index.html"><span>{esc(blocks[3])}</span>{ARROW}</a>
          </nav>
        </div>
      </section>
    </div>'''


def render_teachers(prefix: str = "../../") -> str:
    """Return Michele's supplied biography and the requested blank teacher spaces."""
    blocks = REQUEST["about/teachers/index.html"]
    biography = "".join(paragraph(value) for value in blocks[2:6])
    additional = "".join(
        f'''<article class="teacher-space" aria-labelledby="teacher-{index}">
          <div class="teacher-empty-photo" aria-hidden="true"></div>
          <h2 id="teacher-{index}">{esc(name)}</h2>
          <div class="teacher-empty-bio" aria-hidden="true"></div>
        </article>'''
        for index, name in enumerate(blocks[6:], start=1)
    )
    return f'''<div class="teachers-page">
      {title(blocks[0])}
      <section class="section-shell teacher-feature" aria-labelledby="miss-michele">
        <figure class="teacher-portrait"><img src="{esc(prefix)}assets/images/miss-michele.webp" alt="{esc(blocks[1])}" loading="eager" fetchpriority="high" decoding="async"></figure>
        <div class="teacher-biography"><h2 id="miss-michele">{esc(blocks[1])}</h2>{biography}</div>
      </section>
      <section class="section-shell teacher-spaces">{additional}</section>
    </div>'''


def render_policies(prefix: str = "../../") -> str:
    """Return only the supplied mission and announcements."""
    blocks = REQUEST["about/studio-policies/index.html"]
    announcements = "".join(f"<li>{esc(value)}</li>" for value in blocks[5:])
    return f'''<div class="policies-page">
      {title(blocks[0])}
      <div class="section-shell policies-content">
        <section class="policy-section" aria-labelledby="policy-mission">
          <h2 id="policy-mission">{esc(blocks[1])}</h2>
          <div class="policy-copy"><p class="mission-opening">{esc(blocks[2])}</p>{paragraph(blocks[3])}</div>
        </section>
        <section class="policy-section" aria-labelledby="policy-announcements">
          <h2 id="policy-announcements">{esc(blocks[4])}</h2>
          <ul class="policy-announcements">{announcements}</ul>
        </section>
      </div>
    </div>'''
