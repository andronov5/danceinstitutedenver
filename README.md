# Dance Institute Denver

A responsive, static rebuild of the existing Wix website. The design uses the current site's pages and copy as its reference, with a more expressive hero, clearer information hierarchy, and accessible motion.

## Project structure

- `index.html` — Home.
- `about-1/`, `performances/`, `class-schedule/`, `competition/`, `contact/`, `courses/` — individual pages, each with an `index.html`. The original About URL is retained; `about/` provides an alias.
- `courses/*/index.html` — all six original course details, including their original placeholder content.
- `privacy-policy/`, `accessibility-statement/` — existing policy pages.
- `assets/` — shared CSS, JavaScript, images, and fonts.
- `reference/` — captured Wix content, source asset mappings, and font license notes.
- `scripts/render.py`, `scripts/render_inner.py` — HTML generation from captured source content.
- `scripts/site.py`, `scripts/check_copy.py` — dependency-free static build, checks, copy comparison, and ZIP packaging.
- `dist/` — generated website files; ignored by Git.
- `exports/` — generated upload ZIP; ignored by Git.

Reference content and development notes stay outside the upload. The site itself needs no Node server, database, framework, or npm dependencies. Python 3.10 or newer is used only for development tooling; npm is an optional command shortcut.

## Build and preview

```sh
npm run build
python3 -m http.server 4173 --directory dist
```

Open `http://localhost:4173`. Stop the preview with Ctrl+C.

Without npm, run `python3 scripts/site.py build`. The generated pages use relative links and assets and can also be opened directly from `dist/index.html`; use the HTTP preview when testing forms or third-party embeds.

The build first regenerates HTML from the renderer and reference data. It checks all nine original pages, the About alias, all six course details, local HTML/CSS asset references, internal page links and anchors, duplicate HTML IDs, supported file types, file count, and total upload size. A separate copy check compares source text blocks against each page's main content while ignoring whitespace and invisible separators; it includes policy list items omitted from the original block capture. For captured dynamic pages, it compares the first H1-delimited page segment, excluding stale content retained during Wix navigation. It does not submit forms, test third-party checkout, or verify external URLs. To repeat checks without rebuilding:

```sh
npm run check
npm run check:copy
```

## Prepare a Wix upload

```sh
npm run package
```

This rebuilds and checks the site, then creates `exports/dance-institute-denver-wix.zip`. Its `index.html` is at the ZIP root. Upload **the contents of `dist/` or that ZIP**, not the whole GitHub repository.

The export is checked against Wix Headless Drop's documented limits: static files only, an HTML entry file at the top level, at most 5,000 files, and at most 20 MB total. The checker uses a conservative 20,000,000-byte budget. Optimize photographs and host large video files separately when needed.

Wix upload requirements: <https://dev.wix.com/docs/go-headless/wix-managed-headless/other-frameworks/your-own-frontend/what-you-can-upload>

## Hosting status and launch work

This repository does **not** migrate the existing Wix site, connect its domain, transfer a paid plan, or publish to Wix. Wix Headless Drop creates a separate project; moving the existing site's frontend is a different workflow. The owner's existing Business plan and domain setup must be handled through the chosen Wix workflow.

Original placeholder copy, example course offerings, instructor names, policy text, and footer credits have intentionally been preserved. They are not newly verified business claims. Every generated page currently includes `noindex,nofollow` so search engines are asked not to index this draft. Review the content and production configuration before removing that metadata for launch.

The contact forms currently prepare an email draft using the visitor's email application; visitors must send that draft themselves. Course **Enroll** links open email inquiries and do not create registrations or take payments. The existing public Sawyer registration destination is available at <https://www.hisawyer.com/dance-institute-denver/schedules/membership-plans>. A Sawyer embed is not configured or tested in this build.

Before production launch:

- Decide whether to retain email-draft contact forms or connect a submission backend and verify delivery. Static HTML alone cannot send or store form submissions.
- Add the approved Sawyer embed and test it on desktop and mobile, including registration and checkout. Preserve the existing Sawyer account and payment setup.
- Verify page content, accessibility, preserved reference placeholders, and links with the site owner; remove `noindex,nofollow` only when the production configuration is ready.
- Configure the final domain, preserve existing email DNS records, and retain or redirect the old site's public URLs as appropriate.

Keep service credentials and private keys out of HTML, browser JavaScript, and the repository. Public widget embed code is configured separately from payment account credentials.

## Editing

Edit the templates in `scripts/render.py` and `scripts/render_inner.py`, the approved content in `reference/`, and the shared files in `assets/`, then rebuild. Generated HTML files are overwritten during builds. Future layout changes happen in this code; the static frontend is not a Wix drag-and-drop Editor theme. Changes pushed to GitHub do not automatically deploy to Wix unless a separate deployment workflow has been configured.
