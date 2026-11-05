/*
 * Deploy in Michele's existing Wix site's Backend/http-functions.js.
 * Import the generated public-field allowlist alongside this file.
 * This function publishes website copy only; it never writes to CMS.
 * Wix reference: https://dev.wix.com/docs/velo/velo-only-apis/wix-http-functions/introduction
 */
import wixData from 'wix-data';
import { response } from 'wix-http-functions';
import { PUBLIC_COLLECTIONS } from 'backend/content-schema.js';

// TODO before enabling the connection: add the exact verified Wix frontend
// origin here if it differs from these domains. Never allow all Wix subdomains.
// A same-origin request that sends an Origin header must also be allowlisted.
const ALLOWED_ORIGINS = new Set([
  'https://dance-institute-denver-design.gnotobiot.chatgpt.site',
  'https://danceinstitutedenver.com',
  'https://www.danceinstitutedenver.com'
]);
const PAGE_SIZE = 1000;
const MAX_ITEMS = 10000;
const MAX_COLLECTIONS = 30;
const own = (value, key) => Object.prototype.hasOwnProperty.call(value, key);

function headersFor(request) {
  const origin = request.headers && request.headers.origin;
  if (origin && !ALLOWED_ORIGINS.has(origin)) return null;
  const headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
    'Vary': 'Origin'
  };
  if (origin) headers['Access-Control-Allow-Origin'] = origin;
  return headers;
}

function answer(status, headers, value) {
  return response({ status, headers: headers || { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }, body: JSON.stringify(value) });
}

function requestedCollections(request) {
  const query = request.query || {};
  if (Object.keys(query).some(key => key !== 'collections') || typeof query.collections !== 'string' || query.collections.length > 2500) return null;
  const ids = [...new Set(query.collections.split(','))];
  if (!ids.length || ids.length > MAX_COLLECTIONS || ids.some(id => !/^Di[A-Za-z0-9_]{1,77}$/.test(id) || !own(PUBLIC_COLLECTIONS, id))) return null;
  return ids;
}

async function readCollection(id) {
  const fields = PUBLIC_COLLECTIONS[id];
  if (!Array.isArray(fields) || !fields.includes('key') || !fields.includes('isVisible')) throw new Error('Invalid public field configuration');
  // Backend-only elevation lets CMS read/write permissions remain Admin-only.
  // Clients cannot choose a filter, private collection, field, or query option.
  let page = await wixData.query(id).eq('isVisible', true).ascending('_id').limit(PAGE_SIZE).find({ suppressAuth: true, consistentRead: true });
  const total = page.totalCount;
  if (!Number.isSafeInteger(total) || total < 0 || total > MAX_ITEMS) throw new Error('Invalid collection size');
  const result = [];
  const seenIds = new Set();
  const seenKeys = new Set();
  let received = 0;
  let pages = 0;
  while (true) {
    pages++;
    if (pages > MAX_ITEMS / PAGE_SIZE + 1 || page.totalCount !== total || !Array.isArray(page.items) || page.items.length > PAGE_SIZE) throw new Error('Content changed while reading');
    for (const item of page.items) {
      if (!item || typeof item._id !== 'string' || !item._id || item._id.length > 256 || seenIds.has(item._id)) throw new Error('Repeated or invalid content item');
      seenIds.add(item._id);
      received++;
      if (received > total || received > MAX_ITEMS) throw new Error('Invalid paging result');
      // A second visibility guard protects against accidental query-hook changes.
      if (item.isVisible !== true) continue;
      // New list rows can use Wix's automatic ID; Michele need not invent keys.
      // Existing seeded keys remain unchanged so singleton bindings stay stable.
      const blankKey = item.key == null || (typeof item.key === 'string' && !item.key.trim());
      const publicKey = blankKey ? item._id : item.key;
      if (typeof publicKey !== 'string' || !publicKey || publicKey.length > 256 || seenKeys.has(publicKey)) throw new Error('Invalid content key');
      seenKeys.add(publicKey);
      const publicItem = {};
      for (const field of fields) {
        if (/^[A-Za-z][A-Za-z0-9_]*$/.test(field) && own(item, field)) publicItem[field] = item[field];
      }
      publicItem.key = publicKey;
      result.push(publicItem);
    }
    if (typeof page.hasNext !== 'function') throw new Error('Missing paging metadata');
    if (!page.hasNext()) break;
    if (!page.items.length || received >= total || typeof page.next !== 'function') throw new Error('Incomplete paging result');
    page = await page.next();
  }
  if (received !== total) throw new Error('Incomplete collection result');
  return result;
}

export async function get_danceContent(request) {
  const headers = headersFor(request);
  if (!headers) return answer(403, null, { error: 'Origin not allowed' });
  const ids = requestedCollections(request);
  if (!ids) return answer(400, headers, { error: 'Invalid content request' });
  try {
    const entries = await Promise.all(ids.map(async id => [id, await readCollection(id)]));
    return answer(200, headers, { version: 1, complete: true, collections: Object.fromEntries(entries) });
  } catch (_) {
    // Never publish a partial snapshot or details about backend data/errors.
    return answer(503, headers, { error: 'Content temporarily unavailable' });
  }
}

export function options_danceContent(request) {
  const headers = headersFor(request);
  if (!headers) return answer(403, null, { error: 'Origin not allowed' });
  return response({ status: 204, headers: { ...headers, 'Access-Control-Allow-Methods': 'GET, OPTIONS', 'Access-Control-Allow-Headers': 'Accept', 'Access-Control-Max-Age': '600' } });
}
