# Website notices — November 5, 2026

`legal-content.json` replaces the archived Wix legal template copy at the user's
request. These notices describe the current custom frontend, Wix content/media,
mailto contact form, and embedded Sawyer registration. They do not certify legal
compliance or complete accessibility conformance.

Source review confirmed no custom advertising pixels or browser storage, but it
cannot establish the hosting or embedded providers' complete cookie/logging
behavior. The accessibility statement identifies WCAG 2.2 AA as a goal, discloses
the compact mobile schedule and lack of persistent carousel pause controls, and
does not claim verified physical accessibility or a full assistive-technology audit.

Michele should confirm that the studio's actual information uses, retention,
photo permissions, and request-handling practices match the notice. No exact
retention period, signed photo release, response guarantee, or legal exemption
has been invented. Review these notices if forms, tracking, providers, or hosting
change. The website contact form currently creates an email draft; it does not
submit to a contact database.

Primary references reviewed:

- https://www.w3.org/WAI/planning/statements/
- https://www.w3.org/TR/WCAG22/
- https://www.ftc.gov/business-guidance/privacy-security/childrens-privacy
- https://coag.gov/resources/colorado-privacy-act/
- https://coag.gov/file-complaint/
- https://www.hisawyer.com/privacy
- https://www.wix.com/about/privacy

The live legal content is also in `DiLegalSections` and the matching
`DiPageContent` records. Patch those records along with source changes; never
replace the entire CMS with the seed file, which would erase unrelated edits.
Existing editor repeaters support the additional legal sections without a new
collection or field. The live dashboard save/media verification remains pending
because the originating browser connection is unavailable.
