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
NUTCRACKER_IMAGE: tuple[str, str] | None = ("nutcracker-stage.webp", "Dance Institute Nutcracker performers on stage")
NUTCRACKER_GALLERY_IMAGES = [
    ("dance-performance.webp", "Dance Institute dancers performing in the Nutcracker"),
]
COMPETITION_IMAGES: list[tuple[str, str]] = [
    ('competition-legacy-lift.webp', 'Dancers in white shirts lift a teammate with her arms reaching upward.'),
    ('competition-legacy-red-costumes.webp', 'Dancers in sparkling red costumes perform a synchronized kneeling pose.'),
    ('competition-legacy-floorwork.webp', 'Dancers in brown dresses perform expressive floorwork at Legacy Dance Championships.'),
    ('competition-rainbow.webp', 'Five Dance Institute dancers onstage at Rainbow National Dance Competition'),
    ('competition-legacy-reach.webp', 'A dancer in a mauve dress reaches upward as her teammates gather around her on the floor.'),
    ('competition-legacy-acro-lift.webp', 'Dancers in brown costumes support a teammate in an overhead acrobatic lift.'),
    ('competition-legacy-quartet.webp', 'Four dancers in white costumes balance with one hand on the floor and the other reaching upward.'),
    ('competition-legacy-ensemble.webp', 'Dancers in black costumes hold a group pose at Legacy Dance Championships.'),
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
        dimensions = ' width="1668" height="1112"' if filename.startswith('competition-legacy-') else (' width="1200" height="571"' if filename == 'competition-rainbow.webp' else '')
        photos.append(f'''<a class="show-photo" href="{esc(source)}" data-show-image aria-label="{esc('Open ' + alt)}"><img src="{esc(source)}" alt="{esc(alt)}"{dimensions} {loading} decoding="async"><span class="show-photo-expand">{EXPAND}</span></a>''')
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
        source = f"{prefix}assets/images/{filename}"
        photo = f'<a class="show-photo nutcracker-banner" href="{esc(source)}" data-show-image aria-label="{esc("Open " + alt)}"><img src="{esc(source)}" alt="{esc(alt)}" width="1200" height="675" loading="eager" fetchpriority="high" decoding="async"><span class="show-photo-expand">{EXPAND}</span></a>'
    else:
        photo = '<div class="nutcracker-banner nutcracker-photo-space" aria-hidden="true"></div>'
    rehearsal = esc(blocks[13]).replace("Register Now!", f'<a href="{esc(prefix)}register/index.html">Register Now!</a>')
    return f'''<div class="shows-page nutcracker-page">
      {title(blocks[0])}
      <div class="section-shell">
        {photo}
        <section class="show-detail-row nutcracker-prep" aria-labelledby="nutcracker-prep-title"><h2 id="nutcracker-prep-title">{esc(blocks[1])}</h2><div class="show-detail-copy"><p>{esc(blocks[2])}</p></div></section>
        <section class="show-detail-row nutcracker-auditions" aria-labelledby="nutcracker-auditions-title">
          <h2 id="nutcracker-auditions-title">{esc(blocks[3])}</h2>
          <div class="nutcracker-audition-card"><p class="nutcracker-audition-time"><time datetime="2026-08-29">{esc(blocks[4])}</time></p><p class="nutcracker-audition-status">{esc(blocks[5])}</p></div>
        </section>
        <section class="show-detail-row show-information" aria-labelledby="show-information-title"><h2 id="show-information-title">{esc(blocks[6])}</h2><div class="show-detail-copy"><ul class="nutcracker-show-dates"><li><time datetime="2026-12-18">{esc(blocks[7])}</time></li><li><time datetime="2026-12-19">{esc(blocks[8])}</time></li></ul><p>{esc(blocks[9])}</p><p class="nutcracker-ticket-note">{esc(blocks[10])}</p></div></section>
        <section class="show-detail-row nutcracker-rehearsals" aria-labelledby="nutcracker-rehearsals-title"><h2 id="nutcracker-rehearsals-title">{esc(blocks[11])}</h2><div class="show-detail-copy"><p class="show-detail-date">{esc(blocks[12])}</p><p>{rehearsal}</p></div></section>
        <section class="show-detail-row nutcracker-merch" aria-labelledby="nutcracker-merch-title"><h2 id="nutcracker-merch-title">{esc(blocks[14])}</h2><p class="show-coming-soon">{esc(blocks[15])}</p></section>
        {gallery(NUTCRACKER_GALLERY_IMAGES, prefix, 'nutcracker-gallery', empty_slots=3)}
        <section class="show-contact"><h2>{esc(blocks[16])}</h2><a class="button" href="{esc(prefix)}contact/index.html">{esc(blocks[17])}{ARROW}</a></section>
      </div>
      {lightbox()}
    </div>'''


def render_competition(prefix: str = "../../") -> str:
    blocks = REQUEST["shows-and-competition/competition/index.html"]
    return f'''<div class="shows-page competition-page">
      {title(blocks[0])}
      <div class="section-shell">{gallery(COMPETITION_IMAGES, prefix, 'competition-gallery')}
        <div class="competition-copy"><p>{esc(blocks[1])}</p></div>
      </div>
      {lightbox() if COMPETITION_IMAGES else ''}
    </div>'''


def render_recital(prefix: str = "../../") -> str:
    blocks = REQUEST["shows-and-competition/recital/index.html"]
    return f'''<div class="shows-page recital-page">
      {title(blocks[0])}
      <div class="section-shell">{gallery(RECITAL_IMAGES, prefix, 'recital-gallery', empty_slots=4)}
        <div class="recital-copy-space" aria-hidden="true"></div>
        <section class="show-detail-row recital-volunteering" aria-labelledby="recital-volunteering-title"><h2 id="recital-volunteering-title">{esc(blocks[1])}</h2><div class="recital-volunteering-space" aria-hidden="true"></div></section>
      </div>
      {lightbox()}
    </div>'''
