"""Bind the existing About and show layouts to editable Wix CMS records.

The default records are read from the rendered page, so this pass does not
rewrite the studio's copy or replace its galleries with sample content.
"""

from copy import deepcopy
import json
import re

from lxml import html

from cms_model import field, inner, outer, plain


def _class(name):
    return "contains(concat(' ', normalize-space(@class), ' '), ' " + name + " ')"


def _one(node, expression):
    matches = node.xpath(expression)
    if not matches:
        raise ValueError("Missing About/show CMS target: " + expression)
    return matches[0]


def _slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _source(value):
    while value.startswith("../"):
        value = value[3:]
    return value


def _heading(builder, doc, page, expression, key, label):
    builder.text(_one(doc, expression), key, label, page)


def _optional_link(builder, container, key, label, page):
    """An empty link stays invisible until Michele supplies its URL and label."""
    link = html.Element("a", {"class": "text-link", "hidden": "hidden"})
    link.set("data-cms-optional-link", "")
    link.set("style", "margin-left: 1ch")
    container.append(link)
    builder.singleton(
        link, "DiLinks", key,
        {"title": label, "page": page, "label": "", "url": ""},
        [field(":scope", "url", "link", hideIfEmpty=True),
         field(":scope", "label")],
    )


def _status_and_link(builder, node, prefix, label, page):
    # A span lets editing the status retain the optional ticket/merch anchor.
    status = html.Element("span")
    status.text = node.text
    node.text = None
    for child in list(node):
        node.remove(child)
        status.append(child)
    node.append(status)
    builder.text(status, prefix + "-status", label + " status", page)
    _optional_link(builder, node, prefix + "-link", label + " link", page)


def _teachers(builder, route, doc):
    _heading(builder, doc, route, "//main//h1", "teachers-title", "Teachers page title")
    container = _one(doc, "//*[" + _class("teacher-rows") + "]")
    rows = container.xpath("./article[" + _class("teacher-row") + "]")
    records = []
    for order, row in enumerate(rows):
        biography = _one(row, ".//*[" + _class("teacher-biography") + "]")
        title = _one(biography, "./h2")
        name = plain(title)
        body = "".join(outer(child) for child in biography if child is not title
                       and not child.xpath("self::*[" + _class("teacher-empty-bio") + "]"))
        images = row.xpath(".//*[" + _class("teacher-portrait") + "]/img")
        image = images[0] if images else None
        records.append({
            "key": _slug(name), "name": name, "bio": body,
            "image": _source(image.get("src", "")) if image is not None else "",
            "alt": image.get("alt", "") if image is not None else name,
            "focalX": 50, "focalY": 50, "sortOrder": order, "isVisible": True,
        })

    template = deepcopy(rows[0])
    # Repeated rows must not duplicate the original teacher's DOM id.
    template.attrib.pop("aria-labelledby", None)
    heading = _one(template, ".//h2")
    heading.attrib.pop("id", None)
    biography = _one(template, ".//*[" + _class("teacher-biography") + "]")
    body = html.Element("div", {"class": "teacher-bio-copy"})
    for child in list(biography):
        if child is not heading:
            biography.remove(child)
            body.append(child)
    biography.append(body)
    image = _one(template, ".//*[" + _class("teacher-portrait") + "]/img")
    image.set("loading", "lazy")
    image.attrib.pop("fetchpriority", None)
    builder.listing(container, "DiTeachers", records, outer(template), [
        field("h2", "name"),
        field(".teacher-bio-copy", "bio", "rich", emptyClass="teacher-empty-bio"),
        field(".teacher-portrait img", "image", "image", altField="alt", xField="focalX", yField="focalY",
              hideIfEmpty=True, emptyClass="teacher-empty-photo", emptyTarget=".teacher-portrait"),
    ])


def _policies(builder, route, doc):
    _heading(builder, doc, route, "//main//h1", "policies-title", "Studio Policies page title")
    builder.image(_one(doc, "//*[" + _class("policy-portrait") + "]/img"),
                  "policies-ballet-photo", "Studio Policies photograph", route)
    container = _one(doc, "//*[" + _class("policies-list") + "]")
    rows = container.xpath("./section[" + _class("policy-section") + "]")
    records = []
    for order, row in enumerate(rows):
        title = plain(_one(row, "./h2"))
        records.append({"key": _slug(title), "title": title,
                        "body": inner(_one(row, "./div[" + _class("policy-copy") + "]")),
                        "sortOrder": order, "isVisible": True})
    template = deepcopy(rows[0])
    template.attrib.pop("aria-labelledby", None)
    _one(template, "./h2").attrib.pop("id", None)
    builder.listing(container, "DiPolicies", records, outer(template),
                    [field("h2", "title"), field(".policy-copy", "body", "rich")])


def _galleries(builder, doc, group):
    for node in doc.xpath("//*[" + _class(group + "-gallery") + "][@data-show-gallery]"):
        data = json.loads(_one(node, "./script[@data-gallery-items]").text)
        photos = []
        for item in data:
            position = re.findall(r"(-?\d+(?:\.\d+)?)%", item.get("position", "50% 50%"))
            x, y = (float(position[0]), float(position[1])) if len(position) == 2 else (50, 50)
            photos.append({"image": _source(item["src"]), "alt": item.get("alt", ""),
                           "focalX": x, "focalY": y})
        builder.gallery(node, group, photos)


def _show_dates(builder, doc):
    hero = _one(doc, "//*[" + _class("nutcracker-hero-dates") + "]")
    detail = _one(doc, "//*[" + _class("nutcracker-show-details") + "]/dd[1]")
    hero_rows = hero.xpath("./li")
    show_times = detail.xpath("./p/time")
    if len(hero_rows) != len(show_times):
        raise ValueError("Nutcracker hero and show-information dates are inconsistent")
    records = []
    for order, (row, show_time) in enumerate(zip(hero_rows, show_times)):
        time = _one(row, "./time")
        prefix = _one(time, "./span[" + _class("nutcracker-date-prefix") + "]")
        records.append({
            "key": "nutcracker-show-" + str(order + 1),
            "dateLabel": plain(time), "datePrefix": prefix.text or "",
            "dayNumber": plain(_one(time, "./span[" + _class("nutcracker-date-number") + "]")),
            "year": plain(_one(time, "./span[" + _class("nutcracker-date-year") + "]")).lstrip(", "),
            "dateTime": time.get("datetime", ""), "showLabel": plain(show_time),
            "showDateTime": show_time.get("datetime", ""), "sortOrder": order, "isVisible": True,
        })
    hero_template = deepcopy(hero_rows[0])
    year = _one(hero_template, ".//span[" + _class("nutcracker-date-year") + "]")
    year.text = ", "
    year_value = html.Element("span", {"data-cms-date-year": ""})
    year_value.text = records[0]["year"]
    year.append(year_value)
    builder.listing(hero, "DiShowDates", records, outer(hero_template), [
        field("time", "dateTime", "attribute", attribute="datetime"),
        field(".nutcracker-date-prefix", "datePrefix"),
        field(".nutcracker-date-number", "dayNumber"),
        field("[data-cms-date-year]", "year"),
    ])
    builder.listing(detail, "DiShowDates", records, outer(show_times[0].getparent()), [
        field("time", "showLabel"),
        field("time", "showDateTime", "attribute", attribute="datetime"),
    ])


def _nutcracker(builder, route, doc):
    _heading(builder, doc, route, "//*[@id='nutcracker-title']", "nutcracker-title", "Nutcracker page title")
    hero_image = _one(doc, "//*[" + _class("nutcracker-hero") + "]/img")
    builder.image(hero_image, "nutcracker-hero", "Nutcracker hero photograph", route)
    # Preserve the authored crop instead of replacing it with a centered crop.
    builder.collections["DiImages"]["nutcracker-hero"]["focalY"] = 70
    _show_dates(builder, doc)
    for name, label in [("shows", "Nutcracker Shows"), ("prep", "Nutcracker Prep Week"),
                        ("auditions", "Nutcracker Auditions"), ("rehearsals", "Nutcracker Rehearsals"),
                        ("merch", "Merch")]:
        _heading(builder, doc, route, "//*[" + _class("nutcracker-" + name) + "]/h2",
                 "nutcracker-" + name + "-title", label + " heading")
    details = _one(doc, "//*[" + _class("nutcracker-show-details") + "]")
    for index, key in [(1, "when"), (2, "where")]:
        builder.text(_one(details, "./dt[" + str(index) + "]"), "nutcracker-" + key + "-label", key.capitalize() + " label", route)
    venue = _one(doc, "//*[" + _class("nutcracker-show-venue") + "]")
    # The link contains a location icon; bind its existing span separately.
    builder.link(venue, "nutcracker-venue-link", "Show venue directions", route, keep_label=True)
    builder.text(_one(venue, "./span"), "nutcracker-venue", "Show venue name", route)
    _status_and_link(builder, _one(doc, "//*[" + _class("nutcracker-ticket-note") + "]"),
                     "nutcracker-tickets", "Nutcracker tickets", route)
    builder.text(_one(doc, "//*[" + _class("nutcracker-prep") + "]/div"),
                 "nutcracker-prep-body", "Nutcracker Prep Week details", route, rich=True)
    audition_time = _one(doc, "//*[" + _class("nutcracker-audition-time") + "]/time")
    builder.singleton(audition_time, "DiPageContent", "nutcracker-audition-date",
                      {"title": "Nutcracker audition date", "page": route,
                       "text": plain(audition_time), "dateTime": audition_time.get("datetime", "")},
                      [field(":scope", "text"), field(":scope", "dateTime", "attribute", attribute="datetime")])
    builder.text(_one(doc, "//*[" + _class("nutcracker-audition-status") + "]"),
                 "nutcracker-audition-status", "Nutcracker audition status", route)
    rehearsal_copy = _one(doc, "//*[" + _class("nutcracker-rehearsals") + "]/div")
    builder.text(_one(rehearsal_copy, "./p[1]"), "nutcracker-rehearsal-date", "Rehearsal schedule", route)
    builder.text(_one(rehearsal_copy, "./p[2]"), "nutcracker-rehearsal-body", "Rehearsal details and registration link", route, rich=True)
    _status_and_link(builder, _one(doc, "//*[" + _class("nutcracker-merch") + "]/p"),
                     "nutcracker-merch", "Nutcracker merchandise", route)
    _galleries(builder, doc, "nutcracker")
    contact = _one(doc, "//*[" + _class("show-contact") + "]")
    builder.text(_one(contact, "./h2"), "nutcracker-contact-title", "Nutcracker contact heading", route)
    builder.link(_one(contact, "./a"), "nutcracker-contact-link", "Nutcracker contact link", route)


def _competition(builder, route, doc):
    _heading(builder, doc, route, "//main//h1", "competition-title", "Competition page title")
    _galleries(builder, doc, "competition")
    builder.text(_one(doc, "//*[" + _class("competition-introduction") + "]/div"),
                 "competition-introduction", "Competition introduction", route, rich=True)
    section = _one(doc, "//*[" + _class("competition-information") + "]")
    container = _one(section, "./div")
    rows = container.xpath("./section[" + _class("competition-info-row") + "]")
    records = []
    for order, row in enumerate(rows):
        title = _one(row, "./h2")
        records.append({"key": _slug(plain(title)), "title": plain(title),
                        "body": "".join(outer(child) for child in row if child is not title),
                        "sortOrder": order, "isVisible": True})
    template = deepcopy(rows[0])
    body = html.Element("div", {"data-cms-competition-body": ""})
    for child in list(template):
        if child.tag != "h2":
            template.remove(child)
            body.append(child)
    template.append(body)
    builder.listing(container, "DiCompetitionInfo", records, outer(template), [
        field("h2", "title"), field("[data-cms-competition-body]", "body", "rich")])


def _recital(builder, route, doc):
    _heading(builder, doc, route, "//*[@id='recital-title']", "recital-title", "Recital page title")
    _galleries(builder, doc, "recital")
    _heading(builder, doc, route, "//*[@id='recital-shows-title']", "recital-shows-title", "Recital shows heading")
    _heading(builder, doc, route, "//*[@id='recital-gala-title']", "recital-gala-title", "Recital gala heading")
    _heading(builder, doc, route, "//*[@id='recital-volunteering-title']", "recital-volunteering-title", "Recital volunteering heading")
    for class_name, key, label in [("recital-copy-space", "recital-information", "Recital information"),
                                    ("recital-gala-copy", "recital-gala", "Recital gala"),
                                    ("recital-volunteering-space", "recital-volunteering", "Recital volunteering")]:
        container = _one(doc, "//*[" + _class(class_name) + "]")
        container.attrib.pop("aria-hidden", None)
        existing = container.xpath("./div[" + _class("show-detail-copy") + "]")
        if existing:
            body = existing[0]
        else:
            body = html.Element("div", {"class": "show-detail-copy", "hidden": "hidden"})
            container.append(body)
        builder.singleton(body, "DiPageContent", key,
                          {"title": label, "page": route, "body": inner(body)},
                          [field(":scope", "body", "rich", hideIfEmpty=True)])
        _optional_link(builder, container, key + "-link", label + " link", route)


def bind_page(builder, route, doc):
    """Register bindings for owned routes; leave all other pages untouched."""
    binders = {
        "about/teachers/index.html": _teachers,
        "about/studio-policies/index.html": _policies,
        "shows-and-competition/nutcracker/index.html": _nutcracker,
        "shows-and-competition/competition/index.html": _competition,
        "shows-and-competition/recital/index.html": _recital,
    }
    binder = binders.get(route.lstrip("/"))
    if binder is None:
        return False
    binder(builder, route, doc)
    return True
