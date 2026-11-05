"""Contact page presentation using the existing studio copy and contact details."""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = json.loads((ROOT / "reference/wix-content.json").read_text(encoding="utf-8"))
CONTACT = next(page for page in PAGES if page["name"] == "Contact")["data"]["blocks"]
ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7"/></svg>'


def render_contact(prefix: str = "../") -> str:
    """Return the contact body; the shared renderer inserts the working form."""
    title = html.escape(CONTACT[0]["text"])
    paragraph = html.escape(CONTACT[2]["text"])
    asset_prefix = html.escape(prefix, quote=True)
    return f'''<div class="contact-page">
      <header class="page-intro section-shell contact-heading"><h1 class="intro-title" id="contact-title">{title}</h1><p class="contact-introduction">{paragraph}</p></header>
      <section class="section-shell contact-layout">
        <div class="contact-intro">
          <div class="contact-visual-panel">
            <figure class="contact-photo-frame"><img class="contact-photo" src="{asset_prefix}assets/images/contact-dancers.webp" alt="Dancers performing together on stage" width="448" height="446" loading="eager" fetchpriority="high" decoding="async"></figure>
            <div class="contact-details">
              <a class="contact-address-link" href="https://www.google.com/maps/search/?api=1&amp;query=10515+E+40th+Ave+%23114+Denver+CO+80239" target="_blank" rel="noopener noreferrer"><address>10515 E 40th Ave<br>#114<br>Denver, CO 80239</address>{ARROW}</a>
              <div class="contact-actions">
                <a href="tel:+13035250011">303-525-0011 Call or Text</a>
                <a href="mailto:dance@danceinstitutedenver.com">dance@danceinstitutedenver.com</a>
              </div>
            </div>
          </div>
        </div>
        <div class="contact-form-panel"><!--CONTACT_FORM--></div>
      </section>
    </div>'''
