# Dance Institute Denver

A static HTML/CSS/JavaScript website using the owner's supplied copy. The original full-photo home hero, About section, and animated reviews are retained. The new home section has six floating cards over a licensed ballet-feet photograph.

## Pages and editing

- `index.html` — Home.
- `dance-classes/` — supplied class descriptions in native expandable sections.
- `about/`, `about/studio-policies/`, `about/teachers/` — About, Mission/Announcements, Michele's supplied biography/photo, and named empty spaces for the five other teachers.
- `schedule/` — the supplied 2026–2027 timetable, weekday tabs, and original image viewer.
- `shows-and-competition/` — title and blank body, as requested.
- `register/` — tuition, discounts, membership instructions, and the actual live Sawyer iframe.
- `contact/` — existing contact content and email-draft form.
- `privacy-policy/`, `accessibility-statement/` — retained draft policy pages.

`about-1/`, `class-schedule/`, `performances/`, `competition/`, `registration/`, `adult-kids-dance-classes/`, and `courses/` redirect to the relevant new pages. Superseded example course detail pages have been removed.

Edit source in `scripts/render*.py`, reference copy in `reference/*-request.json`, and presentation in `assets/`. Builds overwrite generated HTML. The current request supersedes the old Wix template content, which remains archived in the original reference files. No marketing subtitles or additional descriptive copy have been added. Schedule wording, older dates, supplied spelling, prices and class ages have been retained as supplied.

`assets/site.js` handles menu/reviews, `assets/content-pages.js` handles the About submenu, and `assets/schedule.js` handles day selection and the image dialog. Motion respects reduced-motion settings. Standard links work independently of page transition support; class accordions and full schedule content remain available without JavaScript.

## Build and package

```sh
python3 scripts/site.py package
```

This renders the pages, checks required routes, internal links, anchors, asset files, duplicate IDs, upload limits and supplied copy, then creates `exports/dance-institute-denver-wix.zip`. The ZIP has `index.html` at its root. `dist/` is the same generated site without ZIP compression. Python is used only to build; the website needs no server, database, framework or npm dependencies.

For a local development preview outside ChatGPT, serve `dist/` with any ordinary static server. In the managed ChatGPT workspace, use `sites-preview start` with this checkout's absolute path.

## Wix deployment

Upload the generated ZIP or the contents of `dist/` at [Wix Headless Drop](https://www.wix.com/headless/drop). This creates a **separate Wix-managed headless project**; it does not import the layout into the classic Wix visual Editor. GitHub pushes do not automatically deploy to Wix unless a separate workflow is configured.

The export uses only supported static files, relative page links and assets, and browser JavaScript. It is checked against Wix's documented 20 MB total/per-file and 5,000-file limits. Wix serves the files unchanged. CSS view transitions are progressive enhancement; unsupported browsers use normal navigation.

Official requirements (checked November 5, 2026):
- https://dev.wix.com/docs/go-headless/wix-managed-headless/other-frameworks/your-own-frontend/what-you-can-upload
- https://dev.wix.com/docs/go-headless/wix-managed-headless/other-frameworks/your-own-frontend/upload-a-static-site

The existing Wix site, paid plan, domain and DNS have not been changed. Existing plan/domain assignment must be handled in the chosen Wix project before launch. This build retains `noindex,nofollow` for the draft. The retained draft legal pages still need owner review before production.

## Sawyer registration

`register/index.html` embeds this real live URL:

https://www.hisawyer.com/dance-institute-denver/schedules/membership-plans

Sawyer's official Wix guide supports embedding the live customer registration URL without a curated widget code: https://help.hisawyer.com/en/articles/11105556-how-to-embed-a-widget-on-wix

The iframe was observed loading actual memberships at desktop and phone widths. Learn More opened the correct General Membership details in a new tab, following Sawyer's own behavior. No login, registration or payment was submitted. Recheck the full checkout flow after publishing to the final Wix domain. The direct Click Here link is retained above the iframe. Its contents and new-tab behavior are controlled by Sawyer; a later account-provided embed snippet can replace the URL-based iframe if desired.

The contact form prepares an email draft in the visitor's email app; they must send it. It does not silently claim to deliver a message or store submissions. Connect a submission service separately if direct web delivery is needed.

## Verification

The build checks 204 supplied/retained source text blocks across the 11 content pages, plus all redirect links and assets. Browser checks covered desktop and 375px content width, menus and About subpages, class accordion expansion, keyboard schedule selection, original schedule dialog, Register Now navigation, the live Sawyer display/detail destination, and the retained Lera review placeholder. No horizontal overflow was observed on the six new/reworked mobile layouts checked.

Photo provenance is in `reference/new-assets.json`; existing photo/font references remain in `reference/`. Development references do not enter the deployment ZIP.
