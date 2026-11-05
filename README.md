# Dance Institute Denver

A static HTML/CSS/JavaScript website using the owner's supplied copy and requested additions. The small header logo uses the owner's original transparent PNG without a background. Home keeps the full-photo hero with a larger overlapping title, centered stage photograph, and a slim linked address bar beneath it, expands the About section, adds a free-trial strip, and presents six floating cards over a licensed ballet-feet photograph. Pink accents highlight primary buttons, heading emphasis and navigation without changing the layout or typography. Reviews use a slightly more compact layout and slide across the page with swipe, arrow, dot and automatic navigation; Lera Andronova’s supplied testimonial replaces the former placeholder.

## Pages and editing

- `index.html` — Home.
- `dance-classes/` — concise class descriptions in a simple list with names aligned beside descriptions on desktop and stacked on mobile, category jump links, and native expandable sections, all open initially. Advanced Classes follows Combo Classes and contains Jazz 1–4 and Contemporary/Lyrical 1–4. Ages, levels and durations follow the supplied 2026–2027 schedule. Baby Moves is removed; Additional Classes includes Trot'n Tots, Intro to Poms, both Leaps, Turns, Tricks levels and Adult Tap. Advanced Pointe Technique is under Ballet. Class descriptions omit recital references.
- `about/studio-policies/`, `about/teachers/` — the About menu contains Dance Classes, Studio Policies and Teachers. Policies restores the original section rows with headings on the left and supplied policy text on the right. Teachers uses alternating photo/biography rows, Michele's supplied photograph and complete biography, and empty photo/bio spaces for the five other named teachers. Michele's full biography is always visible, with no disclosure control.
- `schedule/` — the complete 2026–2027 weekly table, with all 28 entries and 36 meetings available in compact rows. Class names and details occupy adjacent columns; day headings and class names remain visible within the scrollable timetable. Phone layouts place details below the class name to keep the first day visible. The original schedule image and image-viewer control are removed; the internal Register Now link remains.
- `shows-and-competition/nutcracker/`, `shows-and-competition/competition/`, `shows-and-competition/recital/` — the Shows & Competition menu opens these three pages. Nutcracker uses the newly supplied stage photo as a full-width stage backdrop fading into the dark opening, with a clear oversized title and dates integrated at the top, followed by a compact Shows section with performance times, a venue directions link and a ticket availability notice, a closed-auditions status with August 29, 2026 as a draft date to confirm, Prep Week information, December 18–19 shows, and a contained gallery. Competition has eight photographs in a mixed order: seven unique owner uploads and the retained Rainbow photo. All three show pages use a contained gallery with one frame-filling image, arrows and swipe support. They advance automatically in a continuous loop, without counters or thumbnail strips. Automatic motion pauses on hover/focus, and offscreen, and respects reduced motion. Photos crop to fill the stage; there is no expand control or image modal. Competition uses a smaller centered gallery. Recital retains two studio photographs and a Volunteering space. More photos can be appended to each gallery without scattering placeholders around the page.
- `summer-intensive/` — the supplied **2025 Summer Schedule**, intensive courses, camps, prices and registration instructions. Course cards keep dates, times and prices together; camp options use a consistent card layout, with lunch/drop-off logistics below them. The heading remains 2025 at the owner’s request; supplied date ranges, times and prices are retained.
- `register/` — Monthly Tuition on the left, with Discounts Given and Membership Fee stacked in the right column, followed by the original instructions and actual live Sawyer iframe.
- `contact/` — the original introduction directly under the title, above a side-by-side contact/form layout, with the photograph integrated into the contact information panel and a prominent address. The address opens Google Maps from Contact, the Home address bar, and every footer. Every page uses the hot pink accent color across the full footer with dark text.
- `privacy-policy/`, `accessibility-statement/` — retained draft policy pages.

There is no separate About or Shows hub in the navigation. `about/` and `about-1/` redirect to Teachers; `shows-and-competition/`, `nutcracker/` and `performances/` redirect to Nutcracker. `class-schedule/`, `competition/`, `registration/`, `adult-kids-dance-classes/`, and `courses/` redirect to the relevant current pages. Superseded example course detail pages have been removed.

Edit source in `scripts/render*.py`, reference copy in `reference/*-request.json`, and presentation in `assets/`. Builds overwrite generated HTML. The current requests supersede the old Wix template content, which remains archived in the original reference files. Additional marketing subtitles are omitted. Class descriptions are shortened at the owner's request and aligned with the supplied schedule; the current policy text is preserved exactly. Other supplied wording, older dates, spelling and prices remain unchanged except for authorized additions and removals.

`assets/site.js` handles the mobile menu, contact email draft and reveal motion. `assets/content-pages.js` handles both desktop dropdowns. The schedule remains a complete native HTML table, without image-viewer controls or day filtering. `assets/reviews.js` handles the sliding review gallery, including touch/mouse swiping, arrow keys, dots and automatic advancement. There is no pause button; automatic movement waits while reviews have pointer hover or keyboard focus and is disabled for reduced motion. `assets/shows.js` handles all three looping show galleries. Standard links work independently of page transition support; class accordions and the complete schedule table remain available without JavaScript.

## Content still to complete or confirm

- Teacher photographs and biographies are still blank for Miss Jennifer, Miss Rachel, Miss Susie, Miss Brianna and Miss Ellary.
- The Competition gallery is filled; repeated uploads appear once. Nutcracker and Recital galleries are ready for additional photos; Recital volunteering details remain reserved.
- Summer retains the supplied 2025 heading and date ranges. The owner tentatively recalled Nutcracker auditions as August 29, 2026; confirm this draft date. Shows are December 18 at 6 PM and December 19 at 1 PM at Adams City High School; tickets will be available soon. The venue link opens Google Maps directions to 7200 Quebec Parkway, Commerce City, CO 80022, confirmed against https://achs.adams14.org/about. Prep Week has no updated dates yet.

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

Earlier browser checks observed the iframe loading actual memberships at desktop and phone widths. Learn More opened the correct General Membership details in a new tab, following Sawyer's own behavior. No login, registration or payment was submitted, and no transactions were tested during this revision. Recheck the full checkout flow after publishing to the final Wix domain. The direct Click Here link is retained above the iframe. Its contents and new-tab behavior are controlled by Sawyer; a later account-provided embed snippet can replace the URL-based iframe if desired.

The static note below the contact button is removed at the owner’s request. The contact form prepares an email draft in the visitor's email app; they must send it. It does not silently claim to deliver a message or store submissions. Connect a submission service separately if direct web delivery is needed.

## Verification

The build reads every current `reference/*-request.json` file and checks its supplied text against the generated pages, alongside retained policy/contact copy. It also checks required routes, redirect destinations, internal links, anchors, duplicate IDs, assets and upload limits. Counts are reported by each build rather than fixed in this document.

The weekly table is checked for eight columns (class name, details and six days), 28 schedule rows and 36 populated meeting cells, with no day filtering. Browser review should cover desktop and mobile navigation, the table's contained horizontal scrolling and sticky Class column, class section controls and the always-visible teacher biography, review sliding/swiping and reduced motion, gallery navigation and Register Now links. Static and browser presentation checks do not validate payment transactions or email delivery; the contact form still uses `mailto:`.

Photo provenance is in `reference/new-assets.json`; existing photo/font references remain in `reference/`. Development references do not enter the deployment ZIP.
