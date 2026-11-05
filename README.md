# Dance Institute Denver

A static HTML/CSS/JavaScript website using the owner's supplied copy and requested additions. Home keeps the full-photo hero, expands the About section, adds a free-trial strip, and presents six floating cards over a licensed ballet-feet photograph. Reviews now slide across the page with swipe, arrow, dot and automatic navigation; the `template` review by Lera Andronova remains.

## Pages and editing

- `index.html` — Home.
- `dance-classes/` — supplied class descriptions in native expandable sections, all open initially. Baby Moves has been removed; Intro to Poms and its supplied duration/age line have been added under Additional Classes.
- `about/studio-policies/`, `about/teachers/` — the About menu opens only these two pages. Policies contains Mission and Announcements. Teachers uses alternating photo/biography rows, Michele's supplied photograph and complete biography, and empty photo/bio spaces for the five other named teachers. Michele's longer biography expands with an icon control.
- `schedule/` — the complete 2026–2027 weekly table, with all 28 classes and 36 meetings visible. Descriptions sit below class names; the Class column stays visible while the table scrolls horizontally on narrow screens. The original image viewer and internal Register Now link remain.
- `shows-and-competition/nutcracker/`, `shows-and-competition/competition/`, `shows-and-competition/recital/` — the Shows & Competition menu opens these three pages. Nutcracker contains the supplied audition/rehearsal information and reserved Show Information space. Competition has one confirmed competition photograph, two empty photo slots and the requested short description. Recital has studio photographs and a Volunteering space.
- `summer-intensive/` — the supplied **2025 Summer Schedule**, intensive courses, camps, prices and registration instructions. The year and dates have not been updated or inferred.
- `register/` — tuition, discounts, membership instructions, and the actual live Sawyer iframe.
- `contact/` — existing contact content, direct phone/email links and email-draft form. The address opens Google Maps from both Contact and the footer.
- `privacy-policy/`, `accessibility-statement/` — retained draft policy pages.

There is no separate About or Shows hub in the navigation. `about/` and `about-1/` redirect to Teachers; `shows-and-competition/`, `nutcracker/` and `performances/` redirect to Nutcracker. `class-schedule/`, `competition/`, `registration/`, `adult-kids-dance-classes/`, and `courses/` redirect to the relevant current pages. Superseded example course detail pages have been removed.

Edit source in `scripts/render*.py`, reference copy in `reference/*-request.json`, and presentation in `assets/`. Builds overwrite generated HTML. The current requests supersede the old Wix template content, which remains archived in the original reference files. Additional marketing subtitles are omitted. Supplied wording, older dates, spelling, prices and class ages remain unchanged except for the owner's explicit additions and removals.

`assets/site.js` handles the mobile menu, contact email draft and reveal motion. `assets/content-pages.js` handles both desktop dropdowns. `assets/schedule.js` opens only the original schedule image; it does not filter or hide table rows. `assets/reviews.js` handles the sliding review gallery, including touch/mouse swiping, arrow keys, dots and automatic advancement. There is no pause button; automatic movement waits while reviews have pointer hover or keyboard focus and is disabled for reduced motion. `assets/shows.js` handles the Competition and Recital image viewers. Standard links work independently of page transition support; class accordions and the complete schedule table remain available without JavaScript.

## Content still to complete or confirm

- Teacher photographs and biographies are still blank for Miss Jennifer, Miss Rachel, Miss Susie, Miss Brianna and Miss Ellary.
- Only one photograph is confirmed as a Competition image. Two gallery slots remain empty. Show Information and Recital volunteering details remain reserved spaces.
- The schedule includes classes without separate Dance Classes descriptions: Trot'n Tots, Pointe Adv Tech, and Leaps, Turns, Tricks Adv 1/2 and Adv 3/4. Rehearsals is a separate Nutcracker & Competition event block. Jazz, Contemporary/Lyrical and Pointe levels are covered broadly in the supplied class copy; Poms is now listed.
- Hip-Hop sources differ: the class copy gives Intro ages 5–7 and Hip-Hop 1 ages 7–10, while the timetable gives ages 5–8 and 8–11. Hip-Hop 2 and 3 are one hour for ages 10–13 and 14-up in the copy, but both are 1.25 hours for ages 11-Up in the timetable. Neither source has been silently corrected.
- Studio Policies announces Nutcracker auditions on Aug 29th, 10:00–1:30; the Nutcracker page says Saturday Aug 23rd, 10:00AM–1:00PM. Confirm the intended date/time before launch. Summer still uses the supplied 2025 wording.

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

The contact form prepares an email draft in the visitor's email app; they must send it. It does not silently claim to deliver a message or store submissions. Connect a submission service separately if direct web delivery is needed.

## Verification

The build reads every current `reference/*-request.json` file and checks its supplied text against the generated pages, alongside retained policy/contact copy. It also checks required routes, redirect destinations, internal links, anchors, duplicate IDs, assets and upload limits. Counts are reported by each build rather than fixed in this document.

The weekly table is checked for seven columns, 28 class rows and 36 populated meeting cells, with no day filtering. Browser review should cover desktop and mobile navigation, the table's contained horizontal scrolling and sticky Class column, class/teacher disclosure controls, review sliding/swiping and reduced motion, image viewers, and Register Now links. Static and browser presentation checks do not validate payment transactions or email delivery; the contact form still uses `mailto:`.

Photo provenance is in `reference/new-assets.json`; existing photo/font references remain in `reference/`. Development references do not enter the deployment ZIP.
