# Private visual editor

This adds **Website Editor** inside the existing Wix dashboard. Michele uses her
existing Wix account. The GitHub website remains the frontend; saved content is
stored in the existing Wix CMS collections.

## Build

After updating the public page HTML, editor model, runtime or editor UI:

```sh
python3 scripts/build_editor.py
python3 scripts/build_editor.py --check
node --test tests/studio-editor.test.mjs tests/cms-runtime.test.mjs tests/cms-wix.test.mjs
node --test wix/editor/check-bridge.test.mjs
```

Run the normal site/model build first when page bindings change. The editor build
does not run it automatically. Do not re-import `cms/seed.json` over live edits.

The generator bundles 13 page layouts plus the Studio/Home preview, shared CSS,
inline fonts and Wix media URLs into `wix/public/editor-previews.js`. It injects
the exact current `assets/cms-wix.js` and `assets/cms.js` into `install.html`
without starting the public CMS loader. The install file contains no credentials
or live CMS values. Its preview content and model arrive through the admin init
request. All editor files are excluded from the public `dist/` build.

## Install in the existing shared project

Use **My Site**, site ID `f3c88b1a-e358-495d-bcfd-78c490531ee8`.

1. Enable Velo and install the `@wix/data` npm package in that site.
2. Add/update these Velo files, preserving their exact names:

   | Repository file | Velo destination |
   | --- | --- |
   | `wix/backend/studio-editor.web.js` | `backend/studio-editor.web.js` |
   | `wix/backend/editor-model.js` | `backend/editor-model.js` |
   | `wix/backend/content-schema.js` | `backend/content-schema.js` |
   | `wix/public/editor-previews.js` | `public/editor-previews.js` |

3. Create a **Dashboard Page** named Website Editor. The installed page's Wix
   route is `blank-2` (Wix retained its generated path).
   This is a dashboard extension, not a public website page.
4. Add one HTML component and set its ID to `studioEditor`. Give it enough room
   for the editor (about 1,250 px wide and 900 px tall when the dashboard permits).
   Paste the entire generated `wix/editor/install.html` into its HTML code.
5. Paste `wix/editor/dashboard-page.js` into that dashboard page's code.
6. Publish the reviewed Wix changes, then open Website Editor from the actual
   Wix dashboard. Test a reversible text edit, a photo selection and a new block.
   Confirm the saved change appears on the coded website, then restore the test.

The HTML component alone cannot save anything. The page bridge must be installed,
and all backend web methods require `Permissions.Admin`. Keep collection
permissions admin-only. Never put an admin key in the component or public module.

## Editing behavior

- Choose a page, then click its text/photo preview or choose a section.
- Change text, links, photos/crops, class rows, schedules, pricing and galleries.
- Add text, photo, or text-and-photo sections; choose where they appear.
- Reorder repeatable items and supported section groups; show/hide content.
- **Save changes** writes to the live CMS. The coded website reads those changes
  on refresh. There is no separate approval/publish stage for these content edits.

This is a content-focused visual editor for the existing design. It is not the
entire Wix layout builder: arbitrary CSS, navigation hierarchy, new page routes
and new component types still require a code change.

## Verification and limits

Installed and published on the shared Wix site on 2026-11-05. Open it at:

https://manage.wix.com/dashboard/f3c88b1a-e358-495d-bcfd-78c490531ee8/admin-pages/blank-2

The live dashboard loaded all 14 page choices, the current Wix content, and the
clickable Home preview, showing **Connected to Wix**. The browser connection
became unavailable before a live save/media-picker test could be completed.
Those checks remain required before relying on this editor for routine updates.
The `afterSection` TEXT field was added to `DiContentBlocks` without changing
existing fields, content rows, or ADMIN collection permissions. Wix package
`@wix/data` 1.0.541 is installed.

The build check covers script syntax, no runtime auto-start, preserved binding and
gallery data, absolute asset URLs, bundled CSS/fonts and artifact freshness.
Node tests cover the read/write API contract and data transformations using
fixtures; they do not validate the real Wix deployment or account permissions.

For DOM hydration checks, serve the repository root locally and open
`/wix/editor/offline-qa.html` through the approved Browser tool. This fixture reads
checked-in content and runs against detached documents. It makes no Wix CMS/API
calls, saves nothing, and does not exercise the Wix login/media picker. Public
photo URLs may still be fetched by the browser. Keep it out of public
deployments. Real dashboard interaction and saved-content refresh need a separate
live browser check before handoff.
