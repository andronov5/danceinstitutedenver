# Michele’s website content guide

The GitHub website keeps its current design. Michele can change its content in **Wix → CMS**, using her existing Wix login. These are content tables, not draggable blocks in the Wix Editor. Routine text, photo, date and price-display changes do not require GitHub or coding.

**Current status:** connected on November 5, 2026. The CMS covers 23 collections, including all existing page copy and images, navigation labels, extra text/photo blocks, complete section visibility, legal content, and dynamic class categories. Saved live CMS edits appear when the [coded website](https://dance-institute-denver-design.gnotobiot.chatgpt.site) is refreshed. See `cms/activation.json` for connection verification; the earlier import results remain in `cms/provisioning.json` and `cms/sync-report.json`.

Use the **CMS** dashboard to change the coded website. **Edit Site** opens the older Wix template, which is published at its temporary Wix address to host the content connection; it is separate from the coded website's layout.

Use the shared **My Site** project: `f3c88b1a-e358-495d-bcfd-78c490531ee8`.

[Open Michele’s Wix CMS](https://manage.wix.com/dashboard/f3c88b1a-e358-495d-bcfd-78c490531ee8/wix-cms)

## Make an edit

1. Open **My Site → CMS**, then choose the relevant collection below.
2. Find the item by its **Title**, **Name**, or **Page**. Edit its text, image or other content fields.
3. Save the item. If Wix shows draft/published statuses, publish the finished item. If you are working in a sandbox collection, the corresponding live collection must also be updated.
4. Open the website and refresh the page to check the result. An already-open page does not update while someone is reading it.

The **Title** field in Page text, Page photos and logo, and Buttons and links identifies an item in Wix; edit **Text**, **Body**, **Image**, **Label** or **Url** to change what visitors see.

## Where to edit

| Collection | What it controls |
| --- | --- |
| Studio contact information (`DiStudio`) | Studio name, phone, email, address and “Call or Text” wording; shared contact links and map directions |
| Page text (`DiPageContent`) | Hero words, introductions, section headings, announcements, instructions, dropdown labels, contact form wording, schedule headings and other page copy |
| Page photos and logo (`DiImages`) | Hero and page photographs, logo, alt text and photo focus |
| Buttons and links (`DiLinks`) | Desktop/mobile navigation links and labels, header/footer links, buttons, venue directions, optional ticket and merchandise links |
| What sets us apart (`DiFeatures`) | Home-page feature titles and descriptions |
| Testimonials (`DiTestimonials`) | Review text, names and order |
| Class categories (`DiClassCategories`) | Add, name, hide and reorder class groups |
| Dance classes (`DiClasses`) | Class names, descriptions and category placement |
| Weekly schedule (`DiSchedule`) | Schedule rows and their day/time values |
| Teachers (`DiTeachers`) | Teacher names, complete biographies and photos |
| Studio policies (`DiPolicies`) | Policy headings and content, including the Rules and Safety list |
| Nutcracker show dates (`DiShowDates`) | Dates shown in both the hero and show-information section |
| Competition information (`DiCompetitionInfo`) | Competition information sections and their order |
| Photo galleries (`DiGalleryPhotos`) | Nutcracker, competition and recital gallery photographs |
| Summer intensive courses (`DiSummerCourses`) | Intensive course names, times, displayed prices and notes |
| Summer camps (`DiSummerCamps`) | Camp names, dates, times, descriptions, displayed prices and notes |
| Monthly tuition (`DiTuition`) | Tuition rows and displayed prices |
| Tuition discounts (`DiDiscounts`) | Discount rows and displayed amounts |
| Registration settings (`DiRegistration`) | Displayed membership fee and Sawyer membership URL |
| Page titles and descriptions (`DiPages`) | Browser title and description for each existing page |
| Show or hide sections (`DiSections`) | Hide entire existing sections, including their backgrounds and spacing |
| Additional text and photos (`DiContentBlocks`) | Add optional text, photo and linked-button sections at the bottom of any existing page |
| Legal page sections (`DiLegalSections`) | Privacy/Accessibility section headings, rich text, links and order |

## Add, hide and reorder items

- **Display order** (`sortOrder`): smaller numbers appear first. Use numbers such as 10, 20 and 30 to leave room for later additions. Sorting the table view in Wix does not change the website’s order.
- **Show on website** (`isVisible`): check it to show an item; uncheck it to hide it. New items need this checked. It is separate from any Wix draft/published status.
- **Content key** (`key`): leave an existing key unchanged. It connects that item to the website. For a new list item, leave the key blank so the connection can use Wix’s unique item ID, or enter a unique key such as `teacher-new-name`. If duplicating an item, clear its copied key or replace it with a unique value; do not reuse another item’s key.
- Add rows to the relevant list collection to add a teacher, review, class, policy, camp or gallery photo. For a new class, copy an existing row in the same category and keep the category key consistent. New page layouts or entirely new page types still require a website code change.
- Keep the existing page-text, shared studio and registration setting keys. Adding an arbitrary row to those collections does not create a new section automatically. Use **Additional text and photos** for new content sections.

## Add a class category

1. Add an item to **Class categories**. Give it a unique Content key, such as `adult-classes`, a Title, a Display order, and check Show on website.
2. Add classes to **Dance classes**. Put that exact category key in each class’s Category field.
3. Display order in Class categories controls category order; Display order in Dance classes controls order within each category. All categories start open. A hidden category hides its classes without deleting them.

## Add text, an image or a button

Use **Additional text and photos** and add an item (or duplicate its hidden starter item and clear/change the Content key). Choose the existing page using one of these exact Page values:

`home`, `dance-classes`, `about/teachers`, `about/studio-policies`, `schedule`, `shows-and-competition/nutcracker`, `shows-and-competition/competition`, `shows-and-competition/recital`, `summer-intensive`, `register`, `contact`, `privacy-policy`, `accessibility-statement`.

Fill in any combination of Title, Body and Image. Use Label and Url together for a button. Set Display order and check Show on website. Blank optional fields add no placeholder wording. These new sections appear after the page’s existing content; they inherit its typography and spacing. Use Photo galleries for additions to the existing rotating galleries.

## Hide an existing section

Open **Show or hide sections**, find the Page and section Title, and uncheck Show on website. Its text remains saved in the other collections. Recheck it to restore the section. Keep the Content key unchanged; this table controls the existing sections and does not create new ones.

## Add a gallery photograph

1. Open **Photo galleries** and add or duplicate an item.
2. Leave Content key blank for a new item, or enter a unique key. Clear/change a copied key when duplicating. Set **Gallery** to exactly `nutcracker`, `competition` or `recital`.
3. Select/upload the photograph in **Image**. Enter a short, useful description in **Alt**.
4. Set Display order and check Show on website. Save/publish as applicable, then refresh the gallery page.

**Photo horizontal focus** (`focalX`) and **Photo vertical focus** (`focalY`) use 0–100. Fill in both to override a page photo’s crop. Fifty centers the crop; larger vertical values reveal more of the lower part of a photograph. Blank focus fields keep the existing page-photo styling; gallery photos use 50 for a blank coordinate. These controls reposition the crop, not the original image. The existing gallery controls and looping behavior remain in place.

Teacher photos and biographies use the Teachers collection. A teacher with an empty photo or biography keeps the existing blank space until those fields are filled.

## Update Nutcracker dates and links

Each Nutcracker show has one record used in both date displays. Keep the visible date fields and machine-readable date fields consistent:

| Field | Example |
| --- | --- |
| Date label | Friday, December 18, 2026 |
| Date prefix | Friday, December *(keep a trailing space)* |
| Day number | 18 |
| Year | 2026 |
| Date time | `2026-12-18` |
| Show label | Friday, December 18 at 6 PM |
| Show date time | `2026-12-18T18:00` |

Audition dates/status, rehearsal details and prep-week copy are in **Page text**. Ticket and merchandise status text is there too. Their optional purchase links are in **Buttons and links**; fill in both Label and Url when ready. Those links stay hidden while the URL is empty. The existing “coming soon” status does not disappear automatically—update that text when tickets or merchandise become available.

Recital Shows and Our Gala have their supplied copy in Page text. Volunteering copy remains empty until it is ready. Their optional links are in Buttons and links; blank fields do not add public placeholder wording.

## Shared labels and contact form

Edit navigation entries in **Buttons and links** to update the matching desktop/mobile links together. Dropdown names are in **Page text**. Existing page addresses and the navigation arrangement remain part of the design.

Contact field labels, the Submit label, email subject and draft feedback message are in **Page text** under Contact. Keep `{email}` in the feedback message when you want the current studio email inserted automatically. These controls change wording; they do not add form fields or change the form into an automatic submission service.

## What remains separate

- **Sawyer:** the website’s tuition, discounts and membership fee are display text. Changing them in Wix does **not** change Sawyer’s charges, memberships, availability or registrations. Update those in Sawyer as well. The Sawyer URL setting connects the website link and embedded membership page.
- **Classes and schedule:** these are separate collections. If a class changes, update its class description and schedule row wherever needed; one does not automatically rewrite the other.
- **Contact form:** the current form prepares an email in the visitor’s email application. The visitor still sends that email; this is not a Wix Inbox submission system. Editing the studio email changes its destination.
- **Design:** colors, layout, navigation structure, animation behavior and entirely new page types remain in the website code. Additional content blocks and class categories can be added through the collections above.
- **Page metadata:** the CMS updates browser titles and descriptions on load. The saved HTML remains the fallback; social previews and crawlers that do not run JavaScript may continue to see that saved metadata until the fallback is rebuilt.

## If an edit does not appear

Confirm the correct Wix project, live collection, published status where applicable, and Show on website checkbox, then refresh. Make sure a new row has a blank or unique key and the correct category/gallery value.

If the Wix content connection is unavailable, the page retains its bundled website content. That bundled copy may be older than the latest Wix edits. **Wix edits do not currently update the GitHub fallback automatically.** A developer must deliberately export/reconcile current CMS content into the source and rebuild the fallback later; that export workflow has not been implemented in this change.

Future schema/import maintenance must use the guarded sync plan, which preserves Wix changes rather than re-importing the whole seed over them.

Wix references: [Manage collection content](https://support.wix.com/en/article/cms-managing-your-collection-content), [live and sandbox collections](https://support.wix.com/en/article/cms-accessing-and-syncing-your-sandbox-and-live-collections), and [item publication status](https://support.wix.com/en/article/cms-controlling-live-site-item-visibility-from-your-collection).
