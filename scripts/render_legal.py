"""Render the studio-specific legal notices, separately from archived Wix copy."""
import json
from pathlib import Path
from render_inner import esc, slug

ROOT = Path(__file__).resolve().parents[1]


def render_legal(route):
    page = json.loads((ROOT / 'reference/legal-content.json').read_text())[route]
    lead = f'<p class="intro-lead">{esc(page["introduction"])}</p>' if page.get('introduction') else ''
    opening = f'<p>{esc(page["opening"])}</p>' if page.get('opening') else ''
    sections = ''.join(
        f'<section id="{slug(section["title"])}"><h2>{esc(section["title"])}</h2>{section["body"]}</section>'
        for section in page['sections']
    )
    return f'<section class="section-shell page-intro"><h1>{esc(page["title"])}</h1>{lead}</section><div class="section-shell legal-layout"><div class="legal-copy prose">{opening}{sections}</div></div>'
