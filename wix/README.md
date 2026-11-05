# Connect the GitHub website to Wix CMS

This integration preserves the existing coded website and reads its public content from Wix CMS. Michele edits the content in the Wix dashboard. It does not convert the site into native Wix Editor blocks, migrate its frontend, change DNS, or publish a new frontend by itself.

**Current status:** the browser connection defaults to disabled in `assets/cms-config.json`. Setup is incomplete until the backend is installed on the correct Wix site, the live collections are populated, and the published endpoint works from the actual website origin.

Target the existing shared **My Site**, site ID **`f3c88b1a-e358-495d-bcfd-78c490531ee8`**. Do not create a replacement project or use the separate “Passion Moves Us Dance” project.

## Files

| File | Purpose |
| --- | --- |
| `cms/collections.json` | Generated collection IDs, field types and permissions |
| `cms/seed.json` | Initial public content taken from the current website source |
| `cms/media.json` | Bundled photograph/logo paths mapped to the corresponding uploaded Wix media URLs |
| `wix/backend/http-functions.js` | Read-only `danceContent` backend function |
| `wix/backend/content-schema.js` | Generated collection/field allowlist used by the backend |
| `assets/cms-config.json` | Connection switch, endpoint and optional collection-ID mapping |
| `assets/cms-wix.js` | Validated browser transport and Wix image conversion |
| `assets/cms.js` | Applies CMS fields and lists to the existing page layout |
| `scripts/cms_bind.py` | Adds page bindings and generates collection/seed/allowlist files after rendering |
| `cms/README.md` | Michele’s day-to-day content editing guide |

Run the normal site renderer before generating bindings. Do not run the binding pass repeatedly over already-bound pages. The seed is generated from source; it is not a backup/export of the current Wix database.

## One-time setup

The initial collection creation, 206-item import and 16 media uploads are complete; see `cms/provisioning.json`. Resume at backend installation below. No frontend or domain was migrated, and no Wix site was published during this setup.

1. **Check the site identity.** Open the shared My Site project and confirm its site ID above. Inspect existing collections before creating or updating anything.
2. **Create/update the content collections** according to `cms/collections.json`, preserving the exact IDs and field keys. The schema uses admin-only collection permissions. Michele must have the appropriate owner/admin CMS access. The public website does not receive write access.
3. **Seed the live data** from `cms/seed.json`, preserving `_id`, `key`, `sortOrder`, `isVisible` and the content fields. Confirm all required collections exist, including empty ones. Do not re-import initial seed records over Michele’s later edits. If an Image field does not accept a bundled relative image path, import that media into Wix or use a verified absolute HTTPS image URL while retaining the correct photograph and crop.
4. **Install the backend files** in the same Wix site: put the function in `Backend/http-functions.js` and the allowlist in `Backend/content-schema.js`. If `http-functions.js` already has functions, merge these exports rather than replacing existing code. Preserve the import path `backend/content-schema.js`.
5. **Check allowed origins.** `ALLOWED_ORIGINS` in the backend lists the current preview and studio-domain origins. Add the verified production frontend origin if it changes. An origin is only the scheme and hostname, with no path or trailing slash. An origin allowlist is not authentication: everything returned by this endpoint is public website content.
6. **Publish the backend deliberately.** Wix’s production HTTP-function endpoint requires publication. Publishing the Wix site can also publish other pending editor changes, so inspect the pending site state first. Backend deployment is a separate step from moving the custom frontend or connecting the studio domain.
7. **Verify the actual endpoint** and all required collection responses before enabling the frontend. Use the published function URL for this Wix site, not a URL guessed from the site name or a domain still served by another host.
8. **Configure and deploy the custom frontend.** Set the verified endpoint in `assets/cms-config.json`, enable it only after validation, and deploy the updated site. Then make a reversible CMS edit and confirm it appears on refresh before handing the system over to Michele.

## Endpoint and configuration

The function name is `danceContent`. Wix uses `<site-base-url>/_functions/danceContent` for the production endpoint. A Wix-hosted subdirectory URL includes that site's path before `/_functions/`.

Example configuration shape—not a real endpoint to copy:

```json
{
  "enabled": false,
  "transport": "http-function",
  "endpoint": "https://ACCOUNT.wixsite.com/SITE/_functions/danceContent",
  "collectionIds": {}
}
```

Keep `collectionIds` empty when the collection IDs match the generated schema. If existing IDs need a mapping, update the generated allowlist and confirm the mapped IDs are permitted by the transport. Do not put administrator API keys, OAuth secrets or access tokens in this configuration, browser JavaScript, page HTML or GitHub.

The endpoint accepts GET requests with a comma-separated `collections` query, such as:

```text
<verified-endpoint>?collections=DiStudio,DiPageContent
```

A successful response has `version: 1`, `complete: true`, and an array for **each** requested collection. It returns only explicitly allowed fields from rows with `isVisible === true`. A new list item with no content key uses its Wix item ID as its public key; existing bound content keeps its stable seeded key. Duplicate/invalid keys, incomplete paging, invalid collections and query errors cause a failed response rather than partial content. The function never writes data.

## Required checks before activation

- Request every generated collection and verify its expected records, image values and unique keys. Test live data, not only editor preview/sandbox data.
- Make a real browser request from the preview/production origin. Confirm successful CORS, the published URL, and the complete response shape. Wix documents HTTP functions primarily for server-to-server use; browser access must be verified in this deployment rather than assumed from local tests.
- Confirm that unrelated collections/fields cannot be requested and the endpoint exposes no private customer information.
- Refresh representative pages after changing text, a schedule cell, a price-display field and a gallery image/order. Restore test content afterward.
- Confirm a hidden row stays hidden; empty optional links remain absent; teacher blanks and photo crops remain correct; both Nutcracker date displays use the same rows.
- Confirm Sawyer still opens and embeds its own membership flow. Test the contact form as an email draft, not as a completed submission.
- Disable or make the content endpoint unavailable in a test configuration and confirm the bundled site remains usable. Set `enabled` back to `false` to roll back the connection without discarding CMS edits.

## Publishing and fallback behavior

Once connected, each fresh page load requests the relevant live CMS collections. Saving/publishing content in Wix can therefore update that content without another GitHub deployment. A page already open in a browser needs a refresh.

If the load fails, the frontend keeps the bundled HTML content. This avoids blank pages but may show older dates, prices or announcements. CMS edits **do not update the bundled source or seed automatically**. Periodically exporting/reconciling Wix content into the source and rebuilding the fallback is a separate developer task. There is no implemented one-command CMS-to-source export in this change.

The initial seed must not become an automated overwrite of live Wix content. Future code deployments should preserve CMS records; refresh the fallback intentionally from the current approved content.

Sawyer payment configuration and the contact form’s mailto behavior are separate from this content bridge. The CMS controls displayed prices and links, not charges or form delivery infrastructure.

## Wix references

- [HTTP functions introduction](https://dev.wix.com/docs/velo/velo-only-apis/wix-http-functions/introduction)
- [Site API calls and endpoint URLs](https://dev.wix.com/docs/develop-websites/articles/coding-with-velo/integrations/exposing-services/site-api-calls)
- [Manage collection content](https://support.wix.com/en/article/cms-managing-your-collection-content)
- [Live and sandbox collections](https://support.wix.com/en/article/cms-accessing-and-syncing-your-sandbox-and-live-collections)
- [Collection permissions](https://support.wix.com/en/article/changing-your-content-collection-permissions)
