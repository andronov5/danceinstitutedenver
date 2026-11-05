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
    return f'''<div class="contact-redesign">
      <header class="page-intro section-shell contact-heading"><h1 class="intro-title" id="contact-title">{title}</h1></header>
      <div class="contact-scene section-shell">
        <figure class="contact-studio-band"><img src="{asset_prefix}assets/images/contact-studio.webp" alt="" width="1100" height="733" loading="eager" fetchpriority="high" decoding="async"></figure>
        <div class="contact-content-grid">
          <div class="contact-information">
            <p class="contact-welcome">{paragraph}</p>
            <div class="contact-direct-links">
              <a class="contact-direct-link contact-phone-link" href="tel:+13035250011"><span><span class="contact-phone-number">303-525-0011</span> <span class="contact-phone-note">Call or Text</span></span>{ARROW}</a>
              <a class="contact-direct-link contact-email-link" href="mailto:dance@danceinstitutedenver.com"><span>dance@danceinstitutedenver.com</span>{ARROW}</a>
              <a class="contact-direct-link contact-address-link" href="https://www.google.com/maps/search/?api=1&amp;query=10515+E+40th+Ave+%23114+Denver+CO+80239" target="_blank" rel="noopener noreferrer"><address>10515 E 40th Ave<br>#114<br>Denver, CO 80239</address>{ARROW}</a>
            </div>
          </div>
          <div class="contact-message-panel"><!--CONTACT_FORM--></div>
        </div>
      </div>
    </div>'''
