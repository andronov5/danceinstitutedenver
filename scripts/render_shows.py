"""Individual show pages with supplied Nutcracker copy and authentic galleries."""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST = json.loads((ROOT / "reference/shows-request.json").read_text(encoding="utf-8"))
ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7"/></svg>'

# Add only event photographs confirmed as belonging to the named program.
NUTCRACKER_IMAGE: tuple[str, str] | None = ("nutcracker-stage.webp", "Dance Institute Nutcracker performers on stage")
NUTCRACKER_GALLERY_IMAGES = [
    ("nutcracker-stage.webp", "Dance Institute Nutcracker performers on stage"),
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


def gallery(images: list[tuple[str, str]], prefix: str, class_name: str) -> str:
    """A single looping photo frame; append photos to the data lists."""
    if not images:
        return ""
    items = [{"src": f"{prefix}assets/images/{filename}", "alt": alt} for filename, alt in images]
    data = json.dumps(items, ensure_ascii=False).replace("<", "\\u003c")
    source, alt = items[0]["src"], items[0]["alt"]
    return f'''<section class="show-gallery {esc(class_name)}" data-show-gallery aria-roledescription="carousel" aria-label="{esc(class_name.removesuffix('-gallery').capitalize())} photographs">
      <script type="application/json" data-gallery-items>{data}</script>
      <div class="show-gallery-stage" data-show-stage tabindex="0" role="group" aria-label="{esc(alt)}"><img src="{esc(source)}" alt="{esc(alt)}" data-show-stage-image loading="eager" decoding="async" draggable="false"></div>
      <div class="show-gallery-controls"><button type="button" data-gallery-prev aria-label="Previous photograph"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M19 12H5m7-7-7 7 7 7"/></svg></button><button type="button" data-gallery-next aria-label="Next photograph">{ARROW}</button></div>
      <p class="show-gallery-status" data-gallery-status aria-live="polite" aria-atomic="true"></p>
    </section>'''


def render_nutcracker(prefix: str = "../../") -> str:
    blocks = REQUEST["shows-and-competition/nutcracker/index.html"]
    shows = blocks.index("When:")
    prep = blocks.index("Nutcracker Prep Week")
    auditions = blocks.index("Nutcracker Auditions")
    rehearsals = blocks.index("Nutcracker Rehearsals")
    merch = blocks.index("Merch")
    contact = blocks.index("Interested in Learning More?")
    dates = []
    for weekday, day in [("Friday,", "18"), ("Saturday,", "19")]:
        value = next(block for block in blocks if block.startswith(weekday))
        month_day, year = value.rsplit(", ", 1)
        date_prefix, number = month_day.rsplit(" ", 1)
        dates.append(f'<li><time datetime="2026-12-{day}"><span class="nutcracker-date-prefix">{esc(date_prefix)} </span><span class="nutcracker-date-number">{esc(number)}</span><span class="nutcracker-date-year">, {esc(year)}</span></time></li>')
    opening = f'<div class="section-shell nutcracker-hero-content"><h1 id="nutcracker-title">{esc(blocks[0])}</h1><ul class="nutcracker-hero-dates">{"".join(dates)}</ul></div>'
    if NUTCRACKER_IMAGE:
        filename, alt = NUTCRACKER_IMAGE
        source = f"{prefix}assets/images/{filename}"
        hero = f'<header class="nutcracker-hero" aria-labelledby="nutcracker-title"><img src="{esc(source)}" alt="" width="1200" height="675" loading="eager" fetchpriority="high" decoding="async">{opening}</header>'
    else:
        hero = f'<header class="nutcracker-hero" aria-labelledby="nutcracker-title">{opening}</header>'
    rehearsal = esc(blocks[rehearsals + 2]).replace("Register Now!", f'<a href="{esc(prefix)}register/index.html">Register Now!</a>')
    show_rows = "".join(
        f'<p><time datetime="{datetime}">{esc(blocks[shows + offset])}</time></p>'
        for datetime, offset in [("2026-12-18T18:00", 1), ("2026-12-19T13:00", 2)]
    )
    directions = "https://www.google.com/maps/dir/?api=1&destination=Adams+City+High+School%2C+7200+Quebec+Parkway%2C+Commerce+City%2C+CO+80022"
    return f'''<div class="shows-page nutcracker-page">
      {hero}
      <div class="section-shell">
        <section class="show-detail-row nutcracker-shows" aria-labelledby="nutcracker-shows-title"><h2 id="nutcracker-shows-title">{esc(blocks[shows - 1])}</h2><div class="show-detail-copy"><dl class="nutcracker-show-details"><dt>{esc(blocks[shows])}</dt><dd>{show_rows}</dd><dt>{esc(blocks[shows + 3])}</dt><dd><a class="nutcracker-show-venue" href="{esc(directions)}" target="_blank" rel="noopener noreferrer"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/></svg><span>{esc(blocks[shows + 4])}</span></a></dd></dl><p class="nutcracker-ticket-note">{esc(blocks[shows + 5])}</p></div></section>
        <section class="show-detail-row nutcracker-prep" aria-labelledby="nutcracker-prep-title"><h2 id="nutcracker-prep-title">{esc(blocks[prep])}</h2><div class="show-detail-copy"><p>{esc(blocks[prep + 1])}</p></div></section>
        <section class="show-detail-row nutcracker-auditions" aria-labelledby="nutcracker-auditions-title">
          <h2 id="nutcracker-auditions-title">{esc(blocks[auditions])}</h2>
          <div class="nutcracker-audition-card"><p class="nutcracker-audition-time"><time datetime="2026-08-29">{esc(blocks[auditions + 1])}</time></p><p class="nutcracker-audition-status">{esc(blocks[auditions + 2])}</p></div>
        </section>
        <section class="show-detail-row nutcracker-rehearsals" aria-labelledby="nutcracker-rehearsals-title"><h2 id="nutcracker-rehearsals-title">{esc(blocks[rehearsals])}</h2><div class="show-detail-copy"><p class="show-detail-date">{esc(blocks[rehearsals + 1])}</p><p>{rehearsal}</p></div></section>
        <section class="show-detail-row nutcracker-merch" aria-labelledby="nutcracker-merch-title"><h2 id="nutcracker-merch-title">{esc(blocks[merch])}</h2><p class="show-coming-soon">{esc(blocks[merch + 1])}</p></section>
        {gallery(NUTCRACKER_GALLERY_IMAGES, prefix, 'nutcracker-gallery')}
        <section class="show-contact"><h2>{esc(blocks[contact])}</h2><a class="button" href="{esc(prefix)}contact/index.html">{esc(blocks[contact + 1])}{ARROW}</a></section>
      </div>
    </div>'''


def render_competition(prefix: str = "../../") -> str:
    blocks = REQUEST["shows-and-competition/competition/index.html"]
    return f'''<div class="shows-page competition-page">
      {title(blocks[0])}
      <div class="section-shell">{gallery(COMPETITION_IMAGES, prefix, 'competition-gallery')}
        <div class="competition-copy"><p>{esc(blocks[1])}</p></div>
      </div>
    </div>'''


def render_recital(prefix: str = "../../") -> str:
    blocks = REQUEST["shows-and-competition/recital/index.html"]
    return f'''<div class="shows-page recital-page">
      {title(blocks[0])}
      <div class="section-shell">{gallery(RECITAL_IMAGES, prefix, 'recital-gallery')}
        <div class="recital-copy-space" aria-hidden="true"></div>
        <section class="show-detail-row recital-volunteering" aria-labelledby="recital-volunteering-title"><h2 id="recital-volunteering-title">{esc(blocks[1])}</h2><div class="recital-volunteering-space" aria-hidden="true"></div></section>
      </div>
    </div>'''
