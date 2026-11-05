# Michele’s website content guide

The GitHub website keeps its current design. Once the connection is completed, Michele can change its content in **Wix → CMS**, using her existing Wix login. These are content tables, not draggable blocks in the Wix Editor. Routine text, photo, date and price-display changes will not require GitHub or coding.

**Current status:** the 19 content collections, 206 initial items and 16 photographs are now in Michele’s shared Wix site. The editing code is built and tested. The website connection remains disabled until the Wix backend is installed, published and tested. Dashboard edits will not appear on the website until that activation step is complete.

Use the shared **My Site** project: `f3c88b1a-e358-495d-bcfd-78c490531ee8`.

## Make an edit

1. Open **My Site → CMS**, then choose the relevant collection below.
2. Find the item by its **Title**, **Name**, or **Page**. Edit its text, image or other content fields.
3. Save the item. If Wix shows draft/published statuses, publish the finished item. If you are working in a sandbox collection, the corresponding live collection must also be updated.
4. Open the website and refresh the page to check the result. An already-open page does not update while someone is reading it.

The **Title** field in Page text, Page photos and logo, and Buttons and links identifies an item in Wix; edit **Text**, **Body**, **Image**, **Label** or **Url** to change what visitors see.

## Where to edit

| Collection | What it controls |
| --- | --- |
| Studio contact information (`DiStudio`) | Studio name, phone, email and address; shared contact links and map directions |
| Page text (`DiPageContent`) | Hero words, introductions, section headings, announcements, instructions and other page copy |
| Page photos and logo (`DiImages`) | Hero and page photographs, logo, alt text and photo focus |
| Buttons and links (`DiLinks`) | Connected button labels, contact/map links, optional ticket and merchandise links |
| What sets us apart (`DiFeatures`) | Home-page feature titles and descriptions |
| Testimonials (`DiTestimonials`) | Review text, names and order |
| Class categories (`DiClassCategories`) | Existing class-group headings and visibility |
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

## Add, hide and reorder items

- **Display order** (`sortOrder`): smaller numbers appear first. Use numbers such as 10, 20 and 30 to leave room for later additions. Sorting the table view in Wix does not change the website’s order.
- **Show on website** (`isVisible`): check it to show an item; uncheck it to hide it. New items need this checked. It is separate from any Wix draft/published status.
- **Content key** (`key`): leave an existing key unchanged. It connects that item to the website. For a new list item, leave the key blank so the connection can use Wix’s unique item ID, or enter a unique key such as `teacher-new-name`. If duplicating an item, clear its copied key or replace it with a unique value; do not reuse another item’s key.
- Add rows to the relevant list collection to add a teacher, review, class, policy, camp or gallery photo. For a new class, copy an existing row in the same category and keep the category key consistent. New page layouts or entirely new page types still require a website code change.
- Keep the existing page-text, shared studio and registration setting keys. Adding an arbitrary row to those collections does not create a new section automatically. Class-category order is also part of the current layout; its order fields do not rearrange those sections.

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

Recital information and volunteering copy start empty in Page text. Their optional links are in Buttons and links. Add the content when it is ready; the blank fields do not add public placeholder wording.

## What remains separate

- **Sawyer:** the website’s tuition, discounts and membership fee are display text. Changing them in Wix does **not** change Sawyer’s charges, memberships, availability or registrations. Update those in Sawyer as well. The Sawyer URL setting connects the website link and embedded membership page.
- **Classes and schedule:** these are separate collections. If a class changes, update its class description and schedule row wherever needed; one does not automatically rewrite the other.
- **Contact form:** the current form prepares an email in the visitor’s email application. The visitor still sends that email; this is not a Wix Inbox submission system. Editing the studio email changes its destination.
- **Design:** colors, layout, navigation structure, animation behavior and custom functionality remain in the website code.

## If an edit does not appear

Confirm the correct Wix project, live collection, published status where applicable, and Show on website checkbox, then refresh. Make sure a new row has a blank or unique key and the correct category/gallery value.

If the Wix content connection is unavailable, the page retains its bundled website content. That bundled copy may be older than the latest Wix edits. **Wix edits do not currently update the GitHub fallback automatically.** A developer must deliberately export/reconcile current CMS content into the source and rebuild the fallback later; that export workflow has not been implemented in this change.

Wix references: [Manage collection content](https://support.wix.com/en/article/cms-managing-your-collection-content), [live and sandbox collections](https://support.wix.com/en/article/cms-accessing-and-syncing-your-sandbox-and-live-collections), and [item publication status](https://support.wix.com/en/article/cms-controlling-live-site-item-visibility-from-your-collection).
