"""Presentation-only templates for the original Wix site's secondary pages.

All editorial text comes from reference/wix-content.json. Existing template
placeholders deliberately remain unchanged; review them before production.
The owning renderer supplies the shared header/footer and contact form.
"""

from __future__ import annotations

import html
import json
import re
from urllib.parse import quote, unquote, urlsplit


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def paragraphs(text: str, cls: str = "") -> str:
    """Retain words and punctuation while honoring source paragraph breaks."""
    attr = f' class="{esc(cls)}"' if cls else ""
    return "".join(f"<p{attr}>{esc(part)}</p>" for part in re.split(r"\n\s*\n", text) if part.strip(" \n\t\u200b\xa0"))


def image_uri(image: dict) -> str:
    match = re.search(r'data-image-info="([^"]+)"', image.get("parent", ""))
    if match:
        try:
            return json.loads(html.unescape(match.group(1)))["imageData"]["uri"]
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
    return image.get("src", "").split("/v1/")[0]


def image_source(image: dict, assets: dict | list | None, prefix: str) -> str:
    uri = image_uri(image)
    keys = [uri, uri.rsplit("/", 1)[-1], image.get("src", "")]
    source = None
    if isinstance(assets, dict):
        for key in keys:
            value = assets.get(key)
            if isinstance(value, str):
                source = value
                break
            if isinstance(value, dict):
                source = value.get("path") or value.get("file") or value.get("local")
                if source:
                    break
    elif isinstance(assets, list):
        for item in assets:
            if isinstance(item, dict) and any(item.get(key) in keys for key in ("original", "uri", "source", "url", "filename", "source_url", "original_filename")):
                source = item.get("path") or item.get("file") or item.get("local")
                if source:
                    break
    if source:
        if source.startswith(("https://", "http://", "data:")):
            return source
        return prefix + source.lstrip("/")
    return uri if uri.startswith("https://") else "https://static.wixstatic.com/media/" + uri


def img(image: dict, assets: dict | list | None, prefix: str, cls: str = "", alt: str | None = None, eager: bool = False) -> str:
    if not image_uri(image):
        return ""
    loading = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    return f'<img class="{esc(cls)}" src="{esc(image_source(image, assets, prefix))}" alt="{esc(image.get("alt", "") if alt is None else alt)}" {loading} decoding="async">'


def intro(name: str, title: str, lead: str = "") -> str:
    return f'<header class="page-intro section-shell"><h1 class="intro-title">{esc(title)}</h1>{paragraphs(lead, "intro-lead")}</header>'


def heading(number: int, title: str) -> str:
    return f'<div class="section-heading"><h2>{esc(title)}</h2></div>'


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def blocks_to_sections(blocks: list[dict], heading_tag: str = "H2") -> list[dict]:
    groups: list[dict] = []
    for block in blocks:
        if block["tag"] == heading_tag:
            groups.append({"title": block["text"], "blocks": []})
        elif groups:
            groups[-1]["blocks"].append(block)
    return groups


def performances(page: dict, assets: dict | list | None, prefix: str) -> str:
    data = page["data"]
    blocks = data["blocks"]
    photo = next((i for i in data["images"] if i.get("alt") == "Ballet at the Barre"), data["images"][-1])
    return intro(page["name"], blocks[0]["text"]) + f'''<section class="section-shell split-story performance-story">
      <div class="editorial-image reveal">{img(photo, assets, prefix, alt="Ballet at the Barre", eager=True)}</div>
      <div class="prose story-copy reveal">{paragraphs(blocks[1]["text"])}</div>
    </section>'''


def about(page: dict, assets: dict | list | None, prefix: str) -> str:
    data, b = page["data"], page["data"]["blocks"]
    images = [image for image in data["images"] if image.get("alt") not in ("Facebook", "Twitter", "LinkedIn")]
    out = intro(page["name"], b[0]["text"], b[1]["text"])
    out += f'<section class="section-shell about-opening"><div class="wide-editorial reveal">{img(images[0], assets, prefix, eager=True)}</div><div class="prose about-description reveal">{paragraphs(b[2]["text"])}</div></section>'
    out += f'<section class="section-shell story-section">{heading(1, b[3]["text"])}<div class="prose reveal">{paragraphs(b[4]["text"])}</div></section>'
    out += f'<section class="section-shell team-section">{heading(2, b[5]["text"])}<div class="team-grid">'
    for i in range(6):
        name, role = b[6 + i * 2]["text"], b[7 + i * 2]["text"]
        photo = img(images[i + 1], assets, prefix, alt=name)
        out += f'<article class="team-card reveal"><div class="team-photo">{photo}</div><h3>{esc(name)}</h3><p>{esc(role)}</p></article>'
    out += '</div></section>'
    out += f'<section class="section-shell clients-section">{heading(3, b[18]["text"])}<div class="client-grid">'
    out += ''.join(f'<div class="client-logo">{img(image, assets, prefix)}</div>' for image in images[7:])
    return out + '</div></section>'


def schedule(page: dict, assets: dict | list | None, prefix: str) -> str:
    data = page["data"]
    out = intro(page["name"], data["blocks"][0]["text"])
    out += '<section class="section-shell program-accordion">'
    for i, group in enumerate(blocks_to_sections(data["blocks"])):
        subtitle, copy = group["blocks"]
        opened = " open" if i == 0 else ""
        out += f'''<details class="program-detail reveal" id="{slug(group['title'])}"{opened}>
        <summary class="program-summary"><h2>{esc(group['title'])}</h2><span class="accordion-icon" aria-hidden="true">+</span></summary>
        <div class="program-copy"><h3>{esc(subtitle['text'])}</h3>{paragraphs(copy['text'])}</div>
        </details>'''
    return out + '</section>'


def competition(page: dict, assets: dict | list | None, prefix: str) -> str:
    b = page["data"]["blocks"]
    out = intro(page["name"], b[0]["text"], b[1]["text"])
    out += '<section class="section-shell program-stack">'
    for i, group in enumerate(blocks_to_sections(b)):
        subtitle, copy = group["blocks"]
        out += f'''<article class="program-panel reveal" id="{slug(group['title'])}">
        <div class="program-panel-heading"><h2>{esc(group['title'])}</h2><p class="program-subtitle">{esc(subtitle['text'])}</p></div>
        <div class="prose">{paragraphs(copy['text'])}</div>
        </article>'''
    return out + '</section>'


def contact(page: dict, assets: dict | list | None, prefix: str) -> str:
    b = page["data"]["blocks"]
    out = intro(page["name"], b[0]["text"], b[1]["text"])
    photo = img(page["data"]["images"][0], assets, prefix, "contact-photo") if page["data"]["images"] else ""
    return out + f'''<section class="section-shell contact-layout">
      <div class="contact-intro reveal"><div class="prose">{paragraphs(b[2]['text'])}</div>{photo}</div>
      <div class="contact-form-panel reveal"><!--CONTACT_FORM--></div>
    </section>'''


def legal(page: dict, assets: dict | list | None, prefix: str) -> str:
    b, name = page["data"]["blocks"], page["name"]
    title = next(x["text"] for x in b if x["tag"] == "H1")
    before_h1 = []
    after_h1 = []
    seen_h1 = False
    for item in b:
        if item["tag"] == "H1":
            seen_h1 = True
            continue
        (after_h1 if seen_h1 else before_h1).append(item)
    intro_text = "\n\n".join(x["text"] for x in before_h1)
    out = intro(name, title, intro_text)
    sections = blocks_to_sections(after_h1)
    out += '<div class="section-shell legal-layout"><div class="legal-copy prose">'
    for item in after_h1:
        if item["tag"] == "H2":
            break
        out += paragraphs(item["text"])
    for group in sections:
        out += f'<section id="{slug(group["title"])}"><h2>{esc(group["title"])}</h2>'
        for block in group["blocks"]:
            text = block["text"]
            if name == "Accessibility Statement" and "[Name of the accessibility coordinator]" in text:
                description = text.split("[Name of the accessibility coordinator]")[0]
                items = re.findall(r"\[[^\]]+\]", text)
                out += paragraphs(description) + '<ul>' + ''.join(f'<li>{esc(item)}</li>' for item in items) + '</ul>'
            elif name == "Privacy Policy" and "Creating a Privacy Policy" in text:
                out += paragraphs(text).replace('Creating a Privacy Policy', '<a href="https://support.wix.com/en/article/creating-a-privacy-policy" target="_blank" rel="noopener noreferrer">Creating a Privacy Policy</a>')
            else:
                out += paragraphs(text)
        if name == "Accessibility Statement" and group["title"] == "Accessibility adjustments on this site":
            full_text = page["data"]["text"]
            start = full_text.find("Utilized accessibility tools")
            end = full_text.find("We acknowledge partial compliance", start)
            items = [text.strip() for text in re.split(r"\n+", full_text[start:end]) if text.strip()]
            out += '<ul>' + ''.join(f'<li>{esc(item)}</li>' for item in items) + '</ul>'
        out += '</section>'
    return out + '</div></div>'


def courses(page: dict, assets: dict | list | None, prefix: str) -> str:
    data = page["data"]
    out = intro(page["name"], data["blocks"][0]["text"])
    out += '<section class="section-shell course-grid">'
    links = [link for link in data["links"] if link.get("text") == "Read More"]
    for i, group in enumerate(blocks_to_sections(data["blocks"])):
        copy, price_label, duration_label, price, duration = group["blocks"]
        link_slug = urlsplit(links[i]["href"]).path.rstrip('/').rsplit('/', 1)[-1]
        href = link_slug + "/index.html"
        out += f'''<article class="course-card reveal">
        <a class="course-image" href="{esc(href)}" aria-label="{esc(group['title'].strip())}">{img(data['images'][i], assets, prefix, alt=group['title'].strip())}<span class="course-image-arrow" aria-hidden="true">↗</span></a>
        <div class="course-body"><h2><a href="{esc(href)}">{esc(group['title'])}</a></h2>{paragraphs(copy['text'])}
        <dl class="course-meta"><div><dt>{esc(price_label['text'])}</dt><dd>{esc(price['text'])}</dd></div><div><dt>{esc(duration_label['text'])}</dt><dd>{esc(duration['text'])}</dd></div></dl>
        <a class="text-link" href="{esc(href)}">Read More <span aria-hidden="true">↗</span></a></div></article>'''
    return out + '</section>'


def render_page_content(page: dict, assets: dict | list | None = None, prefix: str = "../") -> str:
    """Return semantic HTML inside the shared main element (no outer layout)."""
    renderers = {
        "Performances": performances,
        "About": about,
        "Class Schedule": schedule,
        "Competition": competition,
        "Contact": contact,
        "Privacy Policy": legal,
        "Accessibility Statement": legal,
        "Courses": courses,
    }
    try:
        renderer = renderers[page["name"]]
    except KeyError as error:
        raise ValueError(f"No secondary-page template for {page.get('name')!r}") from error
    return renderer(page, assets, prefix)


def course_detail_blocks(page: dict) -> list[dict]:
    """Discard only the previous page DOM retained during a Wix transition."""
    blocks: list[dict] = []
    started = False
    for block in page["data"]["blocks"]:
        if block["tag"] == "H1":
            if started:
                break
            started = True
        if started:
            blocks.append(block)
    return blocks


def render_course_detail(page: dict, assets: dict | list | None = None, prefix: str = "../../") -> str:
    """Return course detail main-inner HTML; source content remains unchanged.

    The original Enroll button targeted a Wix template example URL. Its replacement
    opens an explicitly described email inquiry without submitting registration.
    """
    b = course_detail_blocks(page)
    if len(b) < 11:
        raise ValueError(f"Incomplete course detail capture: {page.get('name')}")
    name = b[0]["text"]
    price_label, price, duration_label, duration = [x["text"] for x in b[1:5]]
    sections = blocks_to_sections(b[5:])
    about_section, instructor_section = sections
    instructor_name = instructor_section["blocks"][0]["text"]
    email = "mailto:dance@danceinstitutedenver.com?subject=" + quote(name.strip(), safe="")
    image = img(page["data"]["images"][0], assets, prefix, "course-detail-photo", alt=name.strip(), eager=True)
    instructor_image = img(page["data"]["images"][1], assets, prefix, "instructor-photo", alt=instructor_name.strip())
    out = f'''<header class="section-shell page-intro course-detail-heading"><div class="course-detail-title">
      <a class="text-link course-back" href="../index.html">&lt; Back</a>
      <h1 class="intro-title">{esc(name)}</h1></div>
      <div class="course-detail-booking"><dl class="course-meta"><div><dt>{esc(price_label)}</dt><dd>{esc(price)}</dd></div><div><dt>{esc(duration_label)}</dt><dd>{esc(duration)}</dd></div></dl>
      <div class="enroll-action"><a class="button button-dark" href="{esc(email)}" aria-describedby="enroll-description">Enroll <span aria-hidden="true">↗</span></a><p class="form-note" id="enroll-description">Opens an email inquiry. No registration or payment is submitted.</p></div></div>
    </header>
    <div class="section-shell course-detail-hero reveal">{image}</div>
    <div class="section-shell course-detail-layout">
      <section class="course-detail-copy prose reveal"><h2>{esc(about_section['title'])}</h2>{''.join(paragraphs(block['text']) for block in about_section['blocks'])}</section>
      <aside class="instructor-card reveal"><p class="eyebrow">{esc(instructor_section['title'])}</p>{instructor_image}<h2>{esc(instructor_name)}</h2>{''.join(paragraphs(block['text']) for block in instructor_section['blocks'][1:])}</aside>
    </div>'''
    course_order = [
        ("Trumpet Basics", "trumpet-basics"),
        ("Modern Ballet", "modern-ballet"),
        ("Arts & Crafts", "arts-%26-crafts"),
        ("Tennis", "tennis"),
        ("Baking for Beginners", "baking-for-beginners"),
        ("Pottery Workshop", "pottery-workshop"),
    ]
    position = next(i for i, item in enumerate(course_order) if item[0] == name.strip())
    out += '<nav class="section-shell course-detail-nav" aria-label="Course navigation">'
    for offset, label, relation, arrow in [(-1, "Previous", "prev", "←"), (1, "Next", "next", "→")]:
        target = position + offset
        text = f'<span aria-hidden="true">{arrow}</span> {label}' if offset < 0 else f'{label} <span aria-hidden="true">{arrow}</span>'
        if 0 <= target < len(course_order):
            target_name, target_slug = course_order[target]
            out += f'<a href="../{target_slug}/index.html" rel="{relation}" aria-label="{label} course: {esc(target_name)}">{text}</a>'
        else:
            out += f'<span aria-disabled="true">{text}</span>'
    return out + '</nav>'

