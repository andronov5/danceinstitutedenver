"""Individual show pages with supplied Nutcracker copy and authentic galleries."""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST = json.loads((ROOT / "reference/shows-request.json").read_text(encoding="utf-8"))
ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7"/></svg>'
EXPAND = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M14 4h6v6M10 20H4v-6M20 4l-7 7M4 20l7-7"/></svg>'

# Add only event photographs confirmed as belonging to the named program.
NUTCRACKER_IMAGE: tuple[str, str] | None = ("dance-performance.webp", "Dance Institute dancers performing in the Nutcracker")
COMPETITION_IMAGES: list[tuple[str, str]] = [
    ("competition-rainbow.webp", "Five Dance Institute dancers onstage at Rainbow National Dance Competition"),
]
RECITAL_IMAGES = [
    ("dance-hero.webp", "Dance Institute dancers performing together on stage"),
    ("dance-community.webp", "Young Dance Institute dancers in pink tutus on stage"),
]


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def title(value: str) -> str:
    return f'<header class="page-intro section-shell"><h1 class="intro-title">{esc(value)}</h1></header>'


def gallery(images: list[tuple[str, str]], prefix: str, class_name: str, empty_slots: int = 0) -> str:
    if not images:
        return '<div class="show-photo-space" aria-hidden="true"></div>'
    photos = []
    for index, (filename, alt) in enumerate(images):
        source = f"{prefix}assets/images/{filename}"
        loading = 'loading="eager" fetchpriority="high"' if index == 0 else 'loading="lazy"'
        photos.append(f'''<a class="show-photo" href="{esc(source)}" data-show-image aria-label="{esc('Open ' + alt)}"><img src="{esc(source)}" alt="{esc(alt)}" {loading} decoding="async"><span class="show-photo-expand">{EXPAND}</span></a>''')
    photos.extend('<div class="show-photo-space" aria-hidden="true"></div>' for _ in range(empty_slots))
    return f'<div class="show-gallery {class_name}" data-show-gallery>{"".join(photos)}</div>'


def lightbox() -> str:
    return '''<dialog class="show-lightbox" aria-label="Show photographs" data-show-lightbox>
      <button class="show-lightbox-close" type="button" aria-label="Close image" data-show-close>×</button>
      <img alt="" data-show-full-image>
      <div class="show-lightbox-controls"><button type="button" aria-label="Previous image" data-show-previous>←</button><button type="button" aria-label="Next image" data-show-next>→</button></div>
    </dialog>'''


def render_nutcracker(prefix: str = "../../") -> str:
    blocks = REQUEST["shows-and-competition/nutcracker/index.html"]
    if NUTCRACKER_IMAGE:
        filename, alt = NUTCRACKER_IMAGE
        photo = f'<figure class="nutcracker-banner"><img src="{esc(prefix)}assets/images/{esc(filename)}" alt="{esc(alt)}" loading="eager" fetchpriority="high" decoding="async"></figure>'
    else:
        photo = '<div class="nutcracker-banner nutcracker-photo-space" aria-hidden="true"></div>'
    rehearsal = esc(blocks[9]).replace("Register Now!", f'<a href="{esc(prefix)}register/index.html">Register Now!</a>')
    return f'''<div class="shows-page nutcracker-page">
      {title(blocks[0])}
      <div class="section-shell">
        <section class="nutcracker-auditions" aria-labelledby="nutcracker-auditions-title">
          {photo}
          <div class="nutcracker-audition-card"><h2 id="nutcracker-auditions-title">{esc(blocks[2])}</h2><p class="nutcracker-audition-time">{esc(blocks[3])}</p></div>
          <div class="nutcracker-audition-copy"><p>{esc(blocks[4])}</p><p>{esc(blocks[5])}</p></div>
        </section>
        <section class="show-detail-row show-information" aria-labelledby="show-information-title"><h2 id="show-information-title">{esc(blocks[6])}</h2><div class="show-information-space" aria-hidden="true"></div></section>
        <section class="show-detail-row nutcracker-rehearsals" aria-labelledby="nutcracker-rehearsals-title"><h2 id="nutcracker-rehearsals-title">{esc(blocks[7])}</h2><div class="show-detail-copy"><p class="show-detail-date">{esc(blocks[8])}</p><p>{rehearsal}</p></div></section>
        <section class="show-detail-row nutcracker-merch" aria-labelledby="nutcracker-merch-title"><h2 id="nutcracker-merch-title">{esc(blocks[10])}</h2><p class="show-coming-soon">{esc(blocks[11])}</p></section>
        <section class="show-contact"><h2>{esc(blocks[12])}</h2><a class="button" href="{esc(prefix)}contact/index.html">{esc(blocks[13])}{ARROW}</a></section>
      </div>
    </div>'''


def render_competition(prefix: str = "../../") -> str:
    blocks = REQUEST["shows-and-competition/competition/index.html"]
    return f'''<div class="shows-page competition-page">
      {title(blocks[0])}
      <div class="section-shell">{gallery(COMPETITION_IMAGES, prefix, 'competition-gallery', empty_slots=2)}
        <div class="competition-copy"><p>{esc(blocks[1])}</p></div>
      </div>
      {lightbox() if COMPETITION_IMAGES else ''}
    </div>'''


def render_recital(prefix: str = "../../") -> str:
    blocks = REQUEST["shows-and-competition/recital/index.html"]
    return f'''<div class="shows-page recital-page">
      {title(blocks[0])}
      <div class="section-shell">{gallery(RECITAL_IMAGES, prefix, 'recital-gallery')}
        <div class="recital-copy-space" aria-hidden="true"></div>
        <section class="show-detail-row recital-volunteering" aria-labelledby="recital-volunteering-title"><h2 id="recital-volunteering-title">{esc(blocks[1])}</h2><div class="recital-volunteering-space" aria-hidden="true"></div></section>
      </div>
      {lightbox()}
    </div>'''
