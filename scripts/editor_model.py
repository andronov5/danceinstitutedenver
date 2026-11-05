#!/usr/bin/env python3
"""Generate editor metadata from the site's actual CMS bindings, never content.

Run after cms_bind.py. The model describes fields and their page locations;
all values shown in an editor must be fetched from the live, authorized CMS.
No seed copy, HTML templates, media URLs, or field defaults are exported.
"""
from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import json
from pathlib import Path
import re

from lxml import html

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "wix/editor/model.json"
BACKEND_OUTPUT = ROOT / "wix/backend/editor-model.js"
PAGE_DEFS = [
    ("home", "", "Home"),
    ("dance-classes", "dance-classes", "Dance classes"),
    ("policies", "about/studio-policies", "Studio policies"),
    ("teachers", "about/teachers", "Teachers"),
    ("schedule", "schedule", "Schedule"),
    ("nutcracker", "shows-and-competition/nutcracker", "Nutcracker"),
    ("competition", "shows-and-competition/competition", "Competition"),
    ("recital", "shows-and-competition/recital", "Recital"),
    ("summer", "summer-intensive", "Summer"),
    ("register", "register", "Register"),
    ("contact", "contact", "Contact"),
    ("privacy", "privacy-policy", "Privacy policy"),
    ("accessibility", "accessibility-statement", "Accessibility statement"),
]
SECTION_NAMES = {
    "hero": "Hero", "home-address-bar": "Address bar", "home-about": "About",
    "trial-strip": "Free trial class", "apart-section": "What sets us apart",
    "testimonials": "Testimonials", "classes-accordion": "Class groups and classes",
    "teacher-rows": "Teachers", "policies-content": "Policies", "schedule-page": "Weekly schedule",
    "nutcracker-hero": "Hero", "nutcracker-shows": "Shows", "nutcracker-prep": "Prep week",
    "nutcracker-auditions": "Auditions", "nutcracker-rehearsals": "Rehearsals",
    "nutcracker-merch": "Merchandise", "nutcracker-gallery": "Gallery", "show-contact": "Contact link",
    "competition-opening": "Heading and gallery", "competition-introduction": "Introduction",
    "competition-information": "Competition information", "recital-opening": "Heading and gallery",
    "recital-shows": "Shows", "recital-gala": "Our gala", "recital-volunteering": "Volunteering",
    "summer-intensive": "Summer intensive", "summer-camps": "Summer camps",
    "summer-registration": "Registration button", "summer-contact": "Contact link",
    "contact-introduction": "Introduction", "contact-intro": "Contact details and photo",
    "contact-form-panel": "Contact form", "tuition-panel": "Monthly tuition",
    "discount-panel": "Discounts", "membership-panel": "Membership fee",
    "registration-how": "Registration instructions", "sawyer-link": "Registration link",
    "sawyer-frame": "Registration widget",
}
LIST_NAMES = {
    "DiFeatures": ("What sets us apart", "feature", "title"),
    "DiTestimonials": ("Testimonials", "testimonial", "title"),
    "DiClassCategories": ("Class groups", "class group", "title"),
    "DiClasses": ("Dance classes", "class", "title"),
    "DiTeachers": ("Teachers", "teacher", "name"),
    "DiPolicies": ("Policies", "policy", "title"),
    "DiSchedule": ("Weekly schedule", "class", "title"),
    "DiShowDates": ("Show dates", "show", "showLabel"),
    "DiGalleryPhotos": ("Gallery", "photo", "alt"),
    "DiCompetitionInfo": ("Competition information", "section", "title"),
    "DiSummerCourses": ("Intensive courses", "course", "title"),
    "DiSummerCamps": ("Summer camps", "camp", "title"),
    "DiTuition": ("Monthly tuition", "tuition option", "title"),
    "DiDiscounts": ("Discounts", "discount", "title"),
    "DiContentBlocks": ("Additional text and photos", "section", "title"),
    "DiLegalSections": ("Page sections", "section", "title"),
}
FIELD_LABELS = {
    "title": "Heading", "name": "Name", "text": "Text", "body": "Text",
    "description": "Description", "bio": "Biography", "quote": "Testimonial",
    "image": "Photo", "alt": "Image description", "url": "Link", "label": "Button text",
    "phone": "Phone number", "phoneSuffix": "Text beside phone number", "email": "Email address",
    "address": "Studio address", "price": "Price", "time": "Time", "dates": "Dates",
    "note": "Note", "discount": "Discount note", "category": "Class group",
    "expandLabel": "Expand button text", "collapseLabel": "Collapse button text",
    "monday": "Monday", "tuesday": "Tuesday", "wednesday": "Wednesday", "thursday": "Thursday",
    "friday": "Friday", "saturday": "Saturday", "date": "Date", "afterSection": "Place after",
}
TITLE_OVERRIDES = {
    "home-trial-h2": "Heading", "home-trial-p": "Trial class details",
    "home-discover": "Hero button", "home-schedule": "Trial class button",
    "home-hero-photo": "Hero photo", "home-about-main-photo": "Main photo",
    "home-about-small-photo": "Small photo", "home-apart-photo": "Background photo",
    "contact-data-feedback-message": "Message after submitting the form",
    "contact-data-subject": "Email subject", "sawyer-link-suffix": "Text after registration link",
    "classes-disclosure-labels": "Expand and collapse buttons", "logo-home-link": "Logo destination",
    "register-heading-1": "Page heading", "register-heading-2": "Tuition heading",
    "register-heading-3": "Discounts heading", "register-heading-4": "Membership heading",
    "register-heading-5": "Instructions heading",
}
TECHNICAL_FIELDS = {"key", "_id", "page", "gallery", "sortOrder", "categoryOrder", "isVisible"}
IMAGE_FIELDS = {"alt", "focalX", "focalY"}
RICH_TAGS = ["p", "br", "strong", "b", "em", "i", "u", "ul", "ol", "li", "a"]
SHOW_DATE_FIELDS = ["dateLabel", "datePrefix", "dayNumber", "year", "dateTime", "showLabel", "showDateTime"]


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def target_node(doc, selector):
    match = re.fullmatch(r'\[data-cms-target="([A-Za-z0-9_-]+)"\]', selector)
    if not match:
        raise ValueError("Unsupported generated CMS target: " + selector)
    nodes = doc.xpath('//*[@data-cms-target=$value]', value=match.group(1))
    if len(nodes) != 1:
        raise ValueError("Missing or duplicate generated CMS target: " + selector)
    return nodes[0]


def css_path(node):
    """An observed source DOM path, used only to locate section sibling groups."""
    target = node.get("data-cms-target")
    if target: return '[data-cms-target="' + target + '"]'
    identity = node.get("id", "")
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", identity): return "#" + identity
    parent = node.getparent()
    if parent is None: return node.tag
    same_tag = [child for child in parent if child.tag == node.tag]
    position = same_tag.index(node) + 1
    return css_path(parent) + " > " + node.tag + ":nth-of-type(" + str(position) + ")"


def display_title(metadata, collection, key):
    # Only descriptive labels are taken from the seed, never editable values.
    title = TITLE_OVERRIDES.get(key) or metadata.get((collection, key), {}).get("title") or key.replace("-", " ").capitalize()
    if title.startswith("Navigation: "):
        title = title.removeprefix("Navigation: ")
    return title


def new_group(group_id, title, collapsed=False):
    return {"id": group_id, "title": title, "collapsed": collapsed, "selectors": [],
            "sectionTargets": [], "visibility": [], "records": [], "lists": []}


def make_field(key, collection, schema, binding=None, node=None, label=None):
    binding = binding or {}
    kind = binding.get("kind", "text")
    source_type = schema[collection][key]
    field_type = "text"
    if key == "image" or kind == "image": field_type = "image"
    elif source_type == "RICH_TEXT" or kind == "rich": field_type = "richText"
    elif key == "email": field_type = "email"
    elif key == "phone": field_type = "phone"
    elif key == "url" or kind in ("link", "sawyer"): field_type = "url"
    elif key in ("description", "bio", "quote", "body", "address", "note") or kind in ("addressLines", "addressInline"):
        field_type = "textarea"
    elif key == "text" and node is not None and node.tag.lower() in ("p", "div", "blockquote"):
        field_type = "textarea"
    field = {"key": key, "label": label or FIELD_LABELS.get(key, key.capitalize()), "type": field_type}
    if field_type == "image":
        field.update({"altField": binding.get("altField", "alt"), "xField": binding.get("xField", "focalX"),
                      "yField": binding.get("yField", "focalY"), "focusMinimum": 0, "focusMaximum": 100})
    elif field_type == "richText":
        field["allowedTags"] = RICH_TAGS
    elif field_type == "url":
        field["allowInternalPages"] = kind != "sawyer" and collection != "DiRegistration"
        if kind == "sawyer" or collection == "DiRegistration":
            field["allowedHosts"] = ["hisawyer.com", "www.hisawyer.com"]
        else:
            field["allowedSchemes"] = ["https", "mailto", "tel"]
    if collection == "DiClasses" and key == "category":
        field.update({"type": "select", "source": {"collection": "DiClassCategories", "valueField": "key",
                       "fallbackValueField": "_id", "labelField": "title"}, "required": True})
    if collection in ("DiClasses", "DiSchedule") and key == "title": field["label"] = "Class name"
    if collection == "DiTestimonials" and key == "title": field["label"] = "Name"
    if collection == "DiTuition" and key == "title": field["label"] = "Class length or option"
    if collection == "DiDiscounts" and key == "title": field["label"] = "Classes"
    if collection == "DiDiscounts" and key == "price": field["label"] = "Discount"
    if collection == "DiPages" and key == "title": field["label"] = "Browser title"
    if collection == "DiPages" and key == "description": field["label"] = "Search description"
    return field


def field_names(field):
    if field.get("virtual"): return []
    return [field["key"], *[field[k] for k in ("altField", "xField", "yField") if field.get(k)]]


def merge_fields(destination, source):
    existing = {field["key"]: field for field in destination}
    for field in source:
        if field["key"] not in existing:
            destination.append(field)
            existing[field["key"]] = field
        elif field["type"] in ("richText", "image", "textarea", "url", "phone", "email"):
            existing[field["key"]].update(field)


def add_target(descriptor, binding):
    target = {"selector": binding["selector"], "fields": deepcopy(binding.get("fields", []))}
    if binding.get("parentSelector"): target["parentSelector"] = binding["parentSelector"]
    if target not in descriptor["targets"]:
        descriptor["targets"].append(target)


def date_composite(kind):
    fields = [{"key": "date", "label": "Date", "type": "date", "virtual": True, "required": True}]
    composite = {"type": kind, "dateField": "date", "readDateField": "dateTime", "locale": "en-US",
                 "timeZone": "America/Denver", "storageFields": ["text", "dateTime"]}
    if kind == "showDate":
        fields.append({"key": "time", "label": "Time", "type": "time", "virtual": True, "required": True})
        composite.update({"timeField": "time", "readDateTimeField": "showDateTime", "storageFields": SHOW_DATE_FIELDS})
    return fields, composite


def generate():
    schema_file = json.loads((ROOT / "cms/collections.json").read_text())
    seed = json.loads((ROOT / "cms/seed.json").read_text())["collections"]
    schema = {c["id"]: {f["key"]: f["type"] for f in c["fields"]} for c in schema_file["collections"]}
    metadata = {(cid, row["key"]): {"title": row.get("title"), "page": row.get("page")}
                for cid, rows in seed.items() for row in rows}
    model = {"version": 1, "siteId": schema_file["siteId"],
             "siteUrl": "https://dance-institute-denver-design.gnotobiot.chatgpt.site",
             "pages": [], "collections": {}}
    studio = {"id": "studio", "route": None, "title": "Studio & navigation", "previewPath": "index.html", "groups": []}
    studio_groups = OrderedDict()
    global_records = {}
    used = {cid: set() for cid in schema}

    def group_for(groups, group_id, title=None, collapsed=False):
        if group_id not in groups:
            groups[group_id] = new_group(group_id, title or group_id.replace("-", " ").capitalize(), collapsed)
        return groups[group_id]

    def note_fields(collection, fields):
        for field in fields:
            used[collection].update(field_names(field))

    for page_id, route, page_title in PAGE_DEFS:
        path = ROOT / route / "index.html"
        doc = html.document_fromstring(path.read_text())
        markers = doc.xpath('//script[@id="dance-cms-bindings"]')
        if len(markers) != 1: raise ValueError("Missing unique binding manifest in " + str(path))
        manifest = json.loads(markers[0].text)
        if manifest.get("route", "") != route: raise ValueError("Manifest route mismatch: " + route)
        page = {"id": page_id, "route": route or "home", "title": page_title,
                "previewPath": (route + "/" if route else "") + "index.html", "groups": [], "sectionGroups": []}
        groups = OrderedDict()
        sections = []
        for entry in manifest["records"]:
            if entry["collection"] != "DiSections": continue
            section_name = entry["key"].removeprefix((route or "home") + "-")
            node = target_node(doc, entry["selector"])
            group = group_for(groups, section_name, SECTION_NAMES.get(section_name))
            group["selectors"].append(entry["selector"])
            descriptor = {"collection": "DiSections", "key": entry["key"], "selector": entry["selector"],
                          "placementSelector": entry.get("placementSelector", entry["selector"]),
                          "placementTitle": group["title"] if entry.get("placementSelector", entry["selector"]) == entry["selector"]
                          else entry.get("placementTitle", group["title"])}
            group["sectionTargets"].append(descriptor)
            group["visibility"].append({"collection": "DiSections", "key": entry["key"], "label": "Show this section"})
            used["DiSections"].add("isVisible")
            sections.append((node, group))

        placement_targets = OrderedDict()
        for section_node, group in sections:
            target = group["sectionTargets"][0]
            canonical = placement_targets.setdefault(target["placementSelector"], target)
            group["placementKey"] = canonical["key"]
            group["placementTitle"] = canonical["placementTitle"]
        sibling_groups = OrderedDict()
        for section_node, group in sections:
            sibling_groups.setdefault(section_node.getparent(), []).append((section_node, group))
        for parent, siblings in sibling_groups.items():
            if len(siblings) < 2: continue
            siblings.sort(key=lambda pair: parent.index(pair[0]))
            order_id = "section-order-" + page_id + "-" + str(len(page["sectionGroups"]) + 1)
            items = []
            for section_node, group in siblings:
                target = next(target for target in group["sectionTargets"]
                              if target["selector"] == '[data-cms-target="' + section_node.get("data-cms-target") + '"]')
                items.append({"key": target["key"], "label": group["title"], "selector": target["selector"]})
                group["reorderGroupId"] = order_id
            page["sectionGroups"].append({"id": order_id, "collection": "DiSections", "label": "Section order",
                                           "keys": [item["key"] for item in items], "items": items,
                                           "filter": {"page": route or "home"}, "reorder": True,
                                           "parentSelector": css_path(parent), "selector": css_path(parent)})
        if page["sectionGroups"]: used["DiSections"].add("sortOrder")

        def group_for_binding(entry):
            node = target_node(doc, entry["selector"])
            if entry["collection"] == "DiPages":
                return group_for(groups, "search-settings", "Search settings", True)
            if entry["collection"] == "DiContentBlocks":
                return group_for(groups, "additional-content", "Additional text and photos", True)
            key = entry.get("key", "")
            if key.startswith("schedule-column-") or key == "schedule-region-label":
                return group_for(groups, "schedule-labels", "Table labels", True)
            if key.startswith("contact-field-") or key.startswith("contact-data-") or key == "contact-submit-label":
                return group_for(groups, "form-labels", "Form wording", True)
            if key == "classes-disclosure-labels":
                return group_for(groups, "button-labels", "Button wording", True)
            if entry["collection"] == "DiShowDates":
                return group_for(groups, "nutcracker-shows", "Shows")
            ancestors = [node, *node.iterancestors()]
            for ancestor in ancestors:
                for section_node, group in sections:
                    if ancestor is section_node: return group
            if entry["collection"] == "DiLegalSections":
                return group_for(groups, "page-sections", "Page sections")
            return group_for(groups, "page-heading", "Page heading")

        for entry in manifest["records"]:
            collection, key = entry["collection"], entry["key"]
            if collection == "DiSections" or key == "policies-ballet-photo": continue
            info = metadata.get((collection, key), {})
            shared = collection == "DiStudio" or info.get("page") == "All pages"
            if shared:
                if collection == "DiStudio": group = group_for(studio_groups, "contact", "Studio contact information")
                elif key == "studio-logo": group = group_for(studio_groups, "logo", "Logo")
                elif key in ("logo-home-label", "navigation-data-open-label", "navigation-data-close-label", "back-to-top", "skip-link"):
                    group = group_for(studio_groups, "accessible-labels", "Accessibility labels", True)
                elif key.startswith("footer-"): group = group_for(studio_groups, "footer-links", "Footer links")
                else: group = group_for(studio_groups, "navigation", "Navigation and buttons")
            else: group = group_for_binding(entry)
            identity = (collection, key)
            if identity not in global_records:
                label = display_title(metadata, collection, key)
                record = {"collection": collection, "key": key, "label": label, "fields": [], "targets": []}
                group["records"].append(record)
                global_records[identity] = record
            record = global_records[identity]
            # Targets on other pages remain useful for visual click selection.
            target = {"page": page_id, "selector": entry["selector"], "fields": deepcopy(entry.get("fields", []))}
            if target not in record["targets"]: record["targets"].append(target)
            node = target_node(doc, entry["selector"])
            fields = []
            for binding in entry["fields"]:
                field_key = binding["field"]
                if field_key in TECHNICAL_FIELDS or field_key in IMAGE_FIELDS or field_key == "dateTime": continue
                fields.append(make_field(field_key, collection, schema, binding, node,
                                         record["label"] if field_key in ("text", "body") else None))
            merge_fields(record["fields"], fields)
            if key == "nutcracker-audition-date":
                record["fields"], record["composite"] = date_composite("auditionDate")
                used[collection].update(record["composite"]["storageFields"])
            note_fields(collection, record["fields"])
            if collection not in ("DiStudio", "DiPages"): used[collection].add("isVisible")

        list_cache = {}
        def add_list(entry, group=None, parent=None):
            collection = entry["collection"]
            filter_values = deepcopy(entry.get("filter", {}))
            identity = (collection, json.dumps(filter_values, sort_keys=True))
            if identity not in list_cache:
                label, item_label, label_field = LIST_NAMES[collection]
                descriptor = {"id": slug(collection + "-" + json.dumps(filter_values, sort_keys=True)),
                              "collection": collection, "label": label, "itemLabel": item_label,
                              "labelField": label_field, "filter": filter_values, "fields": [],
                              "allowAdd": True, "reorder": True, "hide": True, "targets": []}
                (group or group_for_binding(entry))["lists"].append(descriptor)
                list_cache[identity] = descriptor
            descriptor = list_cache[identity]
            add_target(descriptor, entry)
            fields = [make_field(binding["field"], collection, schema, binding)
                      for binding in entry.get("fields", []) if binding["field"] not in TECHNICAL_FIELDS | IMAGE_FIELDS]
            merge_fields(descriptor["fields"], fields)
            if collection == "DiShowDates":
                descriptor["fields"], descriptor["composite"] = date_composite("showDate")
                used[collection].update(SHOW_DATE_FIELDS)
            if parent:
                match = entry["match"]
                relation = {"field": match["field"], "parentCollection": parent["collection"],
                            "parentKeyField": match["parentField"], "parentLabelField": "title"}
                descriptor["relation"] = relation
                merge_fields(descriptor["fields"], [make_field(match["field"], collection, schema)])
            note_fields(collection, descriptor["fields"])
            used[collection].update({"isVisible", "sortOrder", *filter_values.keys()})
            if collection == "DiGalleryPhotos":
                for field in descriptor["fields"]:
                    if field["key"] == "image": field["required"] = True
            if collection == "DiContentBlocks":
                descriptor["placement"] = "after-section-or-page-content"
                options = [{"value": "", "label": "End of page"}]
                for target in placement_targets.values():
                    options.append({"value": target["key"], "label": target["placementTitle"]})
                descriptor["placementField"] = "afterSection"
                merge_fields(descriptor["fields"], [{"key": "afterSection", "label": "Place after",
                                                    "type": "select", "options": options}])
                used[collection].add("afterSection")
            for child in entry.get("children", []):
                # Child selectors are scoped within the parent's repeated row.
                nested = deepcopy(child)
                nested["parentSelector"] = entry["selector"]
                add_list(nested, group or group_for_binding(entry), entry)
            return descriptor

        for entry in manifest["lists"]: add_list(entry)
        for gallery in manifest["galleries"]:
            add_list({"selector": gallery["selector"], "collection": "DiGalleryPhotos",
                      "filter": {"gallery": gallery["group"]}, "fields": [
                          {"field": "image", "kind": "image", "selector": "[data-show-stage-image]",
                           "altField": "alt", "xField": "focalX", "yField": "focalY"}]},
                     group_for_binding({"selector": gallery["selector"], "collection": "DiGalleryPhotos"}))
        if page_id == "contact":
            group_for(groups, "contact-intro", "Contact details and photo")["sharedSettings"] = [{"page": "studio", "group": "contact", "label": "Edit studio address, phone and email"}]
        if page_id == "home":
            group_for(groups, "home-address-bar", "Address bar")["sharedSettings"] = [{"page": "studio", "group": "contact", "label": "Edit studio address"}]
        # Heading first; existing sections retain document order; optional settings last.
        ordered = list(groups.values())
        tail = {"additional-content", "search-settings", "schedule-labels", "form-labels", "button-labels"}
        ordered.sort(key=lambda g: -1 if g["id"] == "page-heading" else 2 if g["id"] == "search-settings" else 1 if g["id"] in tail else 0)
        page["groups"] = ordered
        model["pages"].append(page)

    studio["groups"] = list(studio_groups.values())
    model["pages"].append(studio)
    for collection in schema_file["collections"]:
        cid = collection["id"]
        if not used[cid]: raise ValueError("Collection missing from editor model: " + cid)
        unknown = used[cid] - schema[cid].keys()
        if unknown: raise ValueError("Unknown editor fields for " + cid + ": " + repr(unknown))
        model["collections"][cid] = {"fields": [{"key": key, "type": value} for key, value in schema[cid].items()],
                                      "editableFields": sorted(used[cid])}
    validate_model(model)
    return model


def validate_model(model):
    fixed = set()
    for page in model["pages"]:
        order_ids = set()
        section_keys = {target["key"] for group in page["groups"] for target in group["sectionTargets"]}
        for ordering in page.get("sectionGroups", []):
            if ordering["id"] in order_ids: raise ValueError("Duplicate section ordering group")
            order_ids.add(ordering["id"])
            if len(ordering["keys"]) < 2 or len(set(ordering["keys"])) != len(ordering["keys"]):
                raise ValueError("Invalid section ordering group")
            if not set(ordering["keys"]) <= section_keys: raise ValueError("Unknown ordered section")
        group_ids = set()
        for group in page["groups"]:
            if group["id"] in group_ids: raise ValueError("Duplicate editor group")
            group_ids.add(group["id"])
            for record in group["records"]:
                identity = (record["collection"], record["key"])
                if identity in fixed: raise ValueError("Duplicate fixed editor record: " + repr(identity))
                fixed.add(identity)
            for descriptor in [*group["records"], *group["lists"]]:
                keys = [field["key"] for field in descriptor["fields"]]
                if len(keys) != len(set(keys)): raise ValueError("Duplicate field in editor descriptor")
                if set(keys) & TECHNICAL_FIELDS: raise ValueError("Technical field exposed in editor")
    if len(model["collections"]) != 23: raise ValueError("Expected the existing 23 content collections")


def main():
    model = generate()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n")
    BACKEND_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    BACKEND_OUTPUT.write_text("// Generated by scripts/editor_model.py; metadata only, never live content.\nexport const EDITOR_MODEL = " + json.dumps(model, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print("Editor model: " + str(len(model["pages"])) + " pages, " + str(len(model["collections"])) + " collections; content fetched live.")


if __name__ == "__main__":
    main()
