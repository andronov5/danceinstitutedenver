#!/usr/bin/env python3
"""Bundle the private Wix dashboard editor without rebuilding the public site.

Run after the normal site/model build and any editor/runtime changes:
    python3 scripts/build_editor.py
    python3 scripts/build_editor.py --check

Use --previews-only while editor.html is being developed. Copy the generated
wix/editor/install.html into the dashboard HTML component, and add the generated
wix/public/editor-previews.js as public/editor-previews.js in Velo. The dashboard
bridge imports EDITOR_PREVIEWS and supplies it in the authenticated init reply.
The model and live CMS records come from the admin backend, not this bundle.

The public-site builder copies a fixed list of page directories and assets/;
these wix/ editor artifacts intentionally are not included in public dist/.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urljoin, urlsplit

from lxml import etree, html


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "wix/editor/model.json"
PREVIEWS = ROOT / "wix/public/editor-previews.js"
SOURCE = ROOT / "wix/editor/editor.html"
INSTALL = ROOT / "wix/editor/install.html"
RUNTIME_MARKER = "<!-- DI_EDITOR_RUNTIME -->"
MAX_INSTALL_BYTES = 2_000_000
MAX_PREVIEW_BYTES = 1_000_000
CSS_URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.I)
CSS_IMPORT = re.compile(r"@import\b", re.I)
FONT_SUFFIXES = {".woff", ".woff2", ".ttf", ".otf", ".eot"}
URL_ATTRIBUTES = {"href", "src", "poster", "action", "xlink:href"}


def json_text(value: object) -> str:
    # Safe both as a module value and as the contents of a JSON script node.
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


class Bundler:
    def __init__(self) -> None:
        self.model = json.loads(MODEL.read_text(encoding="utf-8"))
        self.site_url = self.model["siteUrl"].rstrip("/") + "/"
        self.media = json.loads((ROOT / "cms/media.json").read_text(encoding="utf-8"))
        self.stylesheets: list[Path] = []
        self.fallback_assets: set[str] = set()
        self.inline_assets: set[str] = set()

    def local_path(self, source: Path, value: str) -> Path:
        parsed = urlsplit(value)
        path = unquote(parsed.path)
        target = (ROOT / path.lstrip("/") if path.startswith("/") else source.parent / path).resolve()
        if not target.is_relative_to(ROOT):
            raise ValueError(f"Asset outside site root: {value}")
        return target

    def rewrite_url(self, source: Path, value: str, *, font: bool = False) -> str:
        value = value.strip()
        parsed = urlsplit(value)
        if parsed.scheme or parsed.netloc:
            if parsed.scheme.lower() not in {"https", "http", "data", "mailto", "tel", "wix"} and not parsed.netloc:
                raise ValueError(f"Unsupported URL in {source.relative_to(ROOT)}: {value}")
            return value
        if not value:
            return value
        target = self.local_path(source, value)
        key = target.relative_to(ROOT).as_posix()
        if key in self.media:
            return self.media[key]
        if font or target.suffix.lower() in FONT_SUFFIXES:
            if not target.is_file():
                raise ValueError(f"Missing font: {key}")
            mime = mimetypes.guess_type(key)[0] or "application/octet-stream"
            self.inline_assets.add(key)
            return f"data:{mime};base64," + base64.b64encode(target.read_bytes()).decode("ascii")
        if key.startswith("assets/"):
            if not target.is_file():
                raise ValueError(f"Missing preview asset: {key}")
            self.fallback_assets.add(key)
        page_url = urljoin(self.site_url, source.relative_to(ROOT).as_posix())
        return urljoin(page_url, value)

    def rewrite_css(self, source: Path, text: str) -> str:
        if CSS_IMPORT.search(re.sub(r"/\*.*?\*/", "", text, flags=re.S)):
            raise ValueError(f"Resolve CSS imports before bundling: {source.relative_to(ROOT)}")
        return CSS_URL.sub(lambda match: 'url("' + self.rewrite_url(source, match.group(2)) + '")', text)

    def rewrite_json(self, source: Path, value: object, key: str = "") -> object:
        if isinstance(value, list):
            return [self.rewrite_json(source, item) for item in value]
        if isinstance(value, dict):
            return {field: self.rewrite_json(source, item, field) for field, item in value.items()}
        if isinstance(value, str) and key == "template":
            # Repeater templates are HTML too. Preserve their scoped selectors.
            fragment = html.fragment_fromstring(value, create_parent="div")
            self.rewrite_nodes(source, fragment, collect_css=False)
            return (fragment.text or "") + "".join(etree.tostring(child, encoding="unicode", method="html") for child in fragment)
        if isinstance(value, str) and key in {"src", "image", "poster"} and value:
            return self.rewrite_url(source, value)
        return value

    def rewrite_nodes(self, source: Path, document: html.HtmlElement, *, collect_css: bool) -> None:
        for node in list(document.iter()):
            if not isinstance(node.tag, str):
                continue
            tag = node.tag.lower()
            if tag == "script":
                allowed = node.get("type") == "application/json" and (node.get("id") == "dance-cms-bindings" or "data-gallery-items" in node.attrib)
                if not allowed:
                    node.drop_tree()
                    continue
                node.text = json_text(self.rewrite_json(source, json.loads(node.text or "null")))
                continue
            if tag == "link":
                if "stylesheet" in (node.get("rel") or "").split():
                    reference = node.get("href", "")
                    if urlsplit(reference).scheme or urlsplit(reference).netloc:
                        raise ValueError(f"External stylesheet must be bundled: {reference}")
                    stylesheet = self.local_path(source, reference)
                    if not stylesheet.is_file():
                        raise ValueError(f"Missing stylesheet: {stylesheet}")
                    if collect_css and stylesheet not in self.stylesheets:
                        self.stylesheets.append(stylesheet)
                node.drop_tree()
                continue
            if tag == "base" or (tag == "meta" and node.get("http-equiv", "").lower() == "refresh"):
                node.drop_tree()
                continue
            # The live checkout is an external service; never load it in the editor.
            if tag in {"iframe", "object", "embed"}:
                node.attrib.pop("src", None)
                node.attrib.pop("data", None)
                node.set("srcdoc", "<!doctype html><html><body style='font:16px Arial;padding:32px;color:#626575;background:#faf8f3'>Registration widget — available on the live website.</body></html>")
            for name, value in list(node.attrib.items()):
                if name.lower().startswith("on"):
                    del node.attrib[name]
                elif name in URL_ATTRIBUTES:
                    node.set(name, self.rewrite_url(source, value))
                elif name == "srcset":
                    if value.startswith("data:"):
                        continue
                    candidates = []
                    for candidate in value.split(","):
                        parts = candidate.strip().split()
                        if parts:
                            candidates.append(" ".join([self.rewrite_url(source, parts[0]), *parts[1:]]))
                    node.set(name, ", ".join(candidates))
                elif name == "style":
                    node.set(name, self.rewrite_css(source, value))
            if tag == "style" and node.text:
                node.text = self.rewrite_css(source, node.text)

    def page(self, source: Path) -> str:
        document = html.document_fromstring(source.read_text(encoding="utf-8"))
        self.rewrite_nodes(source, document, collect_css=True)
        result = etree.tostring(document, encoding="unicode", method="html", doctype="<!doctype html>")
        validate_page(result, str(source.relative_to(ROOT)))
        return result

    def previews(self) -> dict[str, object]:
        pages: dict[str, str] = {}
        cache: dict[Path, str] = {}
        for entry in self.model["pages"]:
            source = (ROOT / entry["previewPath"]).resolve()
            if not source.is_relative_to(ROOT) or not source.is_file():
                raise ValueError(f"Missing preview page: {source}")
            if source not in cache:
                cache[source] = self.page(source)
            pages[entry["id"]] = cache[source]
        css = "\n".join("/* " + source.relative_to(ROOT).as_posix() + " */\n" + self.rewrite_css(source, source.read_text(encoding="utf-8")) for source in self.stylesheets)
        for match in CSS_URL.finditer(css):
            if not urlsplit(match.group(2)).scheme:
                raise ValueError("Unresolved relative CSS asset in preview bundle")
        return {"pages": pages, "css": css}


def validate_page(text: str, label: str) -> None:
    document = html.document_fromstring(text)
    markers = document.xpath('//*[@id="dance-cms-bindings"]')
    if len(markers) != 1:
        raise ValueError(f"{label}: expected exactly one CMS binding manifest")
    json.loads(markers[0].text or "")
    for node in document.iter():
        if not isinstance(node.tag, str):
            continue
        if node.tag == "script":
            if node.get("type") != "application/json" or not (node.get("id") == "dance-cms-bindings" or "data-gallery-items" in node.attrib):
                raise ValueError(f"{label}: executable preview script")
            json.loads(node.text or "")
        if node.tag == "link":
            raise ValueError(f"{label}: unbundled external link resource")
        for name, value in node.attrib.items():
            if name.startswith("on"):
                raise ValueError(f"{label}: executable event handler")
            if name in URL_ATTRIBUTES and value and not urlsplit(value).scheme and not value.startswith("//"):
                raise ValueError(f"{label}: unresolved preview URL {value}")


def runtime_bundle() -> str:
    scripts = []
    for name, export in (("cms-wix.js", "EditorAdapter"), ("cms.js", "EditorCMS")):
        source = (ROOT / "assets" / name).read_text(encoding="utf-8")
        if re.search(r"</script\b", source, re.I):
            raise ValueError(f"{name} cannot be embedded verbatim: contains closing script tag")
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        scripts.append("/* Exact " + name + "; sha256 " + digest + " */\n(function () {\nvar module = { exports: {} };\n" + source + "\nwindow." + export + " = module.exports;\n})();")
    runtime = "\n".join(scripts)
    # This test exercises the UMD branch: no fetch/document/global auto-start is
    # allowed simply by loading the editor's exact public hydration runtime.
    program = r"""
const vm = require('node:vm');
const fs = require('node:fs');
const code = fs.readFileSync(0, 'utf8');
const context = {window:{}};
for (const key of ['document', 'fetch']) Object.defineProperty(context, key, {get(){throw new Error('Runtime auto-started: '+key)}});
vm.runInNewContext(code, context);
if (typeof context.window.EditorCMS?.hydrate !== 'function' || typeof context.window.EditorAdapter?.imageUrl !== 'function') throw new Error('Missing editor runtime exports');
"""
    subprocess.run(["node", "-e", program], input=runtime, text=True, capture_output=True, check=True)
    return "<script>\n" + runtime + "\n</script>"


def installer() -> str:
    source = SOURCE.read_text(encoding="utf-8")
    if source.count(RUNTIME_MARKER) != 1:
        raise ValueError("editor.html must contain exactly one " + RUNTIME_MARKER)
    result = source.replace(RUNTIME_MARKER, runtime_bundle())
    if len(result.encode("utf-8")) > MAX_INSTALL_BYTES:
        raise ValueError("The editor HTML exceeds its 2 MB installation budget")
    document = html.document_fromstring(result)
    if document.xpath('//script[@src]|//link[contains(@rel,"stylesheet")]'):
        raise ValueError("The install HTML has an external script or stylesheet dependency")
    scripts = "\n".join(node.text or "" for node in document.xpath('//script[not(@type="application/json")]'))
    subprocess.run(["node", "--check", "--input-type=commonjs"], input=scripts, text=True, capture_output=True, check=True)
    return result


def write_or_check(path: Path, content: str, check: bool) -> None:
    if check:
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            raise ValueError(f"Stale generated file: {path.relative_to(ROOT)}; run scripts/build_editor.py")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(f"{'Checked' if check else 'Built'} {path.relative_to(ROOT)} ({len(content.encode('utf-8')):,} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="Verify generated artifacts are current without writing")
    parser.add_argument("--previews-only", action="store_true", help="Skip the editor HTML until its source is ready")
    args = parser.parse_args()
    bundler = Bundler()
    previews = bundler.previews()
    module = "// Generated by scripts/build_editor.py; do not edit. Public page fallbacks only.\nexport const EDITOR_PREVIEWS = " + json_text(previews) + ";\n"
    if len(module.encode("utf-8")) > MAX_PREVIEW_BYTES:
        raise ValueError("The preview module exceeds its 1 MB editor paste budget")
    write_or_check(PREVIEWS, module, args.check)
    if not args.previews_only:
        write_or_check(INSTALL, installer(), args.check)
    print(f"Validated {len(previews['pages'])} previews, {len(bundler.stylesheets)} bundled stylesheets, {len(bundler.inline_assets)} inline fonts; no executable preview scripts or relative asset URLs.")
    if bundler.fallback_assets:
        print("Absolute public-site asset fallbacks: " + ", ".join(sorted(bundler.fallback_assets)))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"Editor build failed: {error}", file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr, file=sys.stderr)
        raise SystemExit(1)
