/* Native Wix Dashboard Page API. Keep every collection's permissions ADMIN.
 * Requires @wix/data in Wix's package manager. No API keys or elevation.
 * Current patch API: /docs/sdk/data-items-sdk/data/items/bulk-patch
 */
import wixData from 'wix-data';
import { items } from '@wix/data';
import { Permissions, webMethod } from 'wix-web-module';
import { PUBLIC_COLLECTIONS } from 'backend/content-schema.js';
import { EDITOR_MODEL } from 'backend/editor-model.js';

const PAGE_SIZE = 1000;
const MAX_ITEMS = 10000;
const MAX_REORDER = 100;
const MAX_TEXT = 100000;
const own = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
const plainObject = value => value !== null && typeof value === 'object' && !Array.isArray(value)
  && (Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null);
const forbidden = new Set(['__proto__', 'prototype', 'constructor']);
const locked = new Set(['key', '_id', '_updatedDate', '_createdDate', '_owner', 'page', 'gallery', 'sortOrder', 'categoryOrder']);
const lists = new Map();
const records = [];
for (const page of EDITOR_MODEL.pages) {
  for (const sectionGroup of page.sectionGroups || []) lists.set(sectionGroup.id, sectionGroup);
  for (const group of page.groups) {
    for (const list of group.lists || []) {
      if (lists.has(list.id) && JSON.stringify(lists.get(list.id)) !== JSON.stringify(list)) throw new Error('Conflicting editor list');
      lists.set(list.id, list);
    }
    records.push(...(group.records || []));
    for (const visibility of group.visibility || []) records.push({ ...visibility, fields: [{ key: 'isVisible', type: 'boolean' }] });
  }
}

class EditorError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.code = code;
    this.details = details;
  }
}
function fail(code, message, details) { throw new EditorError(code, message, details); }
function requestObject(value, allowed, required = allowed) {
  if (!plainObject(value) || Object.keys(value).some(key => forbidden.has(key) || !allowed.includes(key))
    || required.some(key => !own(value, key))) fail('INVALID_REQUEST', 'This edit could not be understood. Please reload and try again.');
}
function collectionSchema(collection) {
  if (typeof collection !== 'string' || !own(PUBLIC_COLLECTIONS, collection) || !own(EDITOR_MODEL.collections, collection)) {
    fail('INVALID_COLLECTION', 'This content is not available in the studio editor.');
  }
  return EDITOR_MODEL.collections[collection];
}
function itemId(value) {
  if (typeof value !== 'string' || !/^[A-Za-z0-9_-]{1,256}$/.test(value)) fail('INVALID_ITEM', 'Choose an existing item and try again.');
  return value;
}
function timestamp(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(value)
    || !Number.isFinite(new Date(value).getTime())) fail('INVALID_VERSION', 'Reload this item before saving.');
  return new Date(value);
}
function publicItem(collection, item) {
  if (!item || typeof item._id !== 'string') fail('MISSING_ITEM', 'This item is no longer available. Reload the page.');
  const result = { _id: item._id };
  const date = item._updatedDate instanceof Date ? item._updatedDate : new Date(item._updatedDate);
  if (!Number.isFinite(date.getTime())) fail('INVALID_VERSION', 'This item could not be loaded safely. Please reload.');
  result._updatedDate = date.toISOString();
  for (const field of PUBLIC_COLLECTIONS[collection]) {
    if (!own(item, field)) continue;
    const value = item[field];
    if (value === null || ['string', 'number', 'boolean'].includes(typeof value)) result[field] = value;
    else if (value instanceof Date) result[field] = value.toISOString();
  }
  // Match the public adapter: new list rows use Wix's automatic ID as their
  // stable binding key, including in the editor's live preview.
  if (result.key == null || (typeof result.key === 'string' && !result.key.trim())) result.key = item._id;
  if (typeof result.key !== 'string' || !result.key || result.key.length > 256) fail('INVALID_ITEM', 'This item has an invalid content key.');
  return result;
}
async function readOne(collection, id) {
  collectionSchema(collection);
  return wixData.get(collection, itemId(id), { consistentRead: true });
}
async function readCollection(collection) {
  collectionSchema(collection);
  // No suppressAuth: the logged-in collaborator must retain CMS access.
  let page = await wixData.query(collection).ascending('_id').limit(PAGE_SIZE).find({ consistentRead: true });
  const total = page.totalCount;
  if (!Number.isSafeInteger(total) || total < 0 || total > MAX_ITEMS) fail('COLLECTION_SIZE', 'This collection is too large to edit here.');
  const result = [], seen = new Set();
  while (true) {
    if (!Array.isArray(page.items) || page.totalCount !== total) fail('CONTENT_CHANGED', 'Content changed while loading. Please reload.');
    for (const row of page.items) {
      if (!row || seen.has(row._id) || result.length >= MAX_ITEMS) fail('CONTENT_CHANGED', 'Content changed while loading. Please reload.');
      seen.add(row._id);
      result.push(publicItem(collection, row));
    }
    if (!page.hasNext()) break;
    if (!page.items.length || result.length >= total) fail('CONTENT_CHANGED', 'Content changed while loading. Please reload.');
    page = await page.next();
  }
  if (result.length !== total) fail('CONTENT_CHANGED', 'Content changed while loading. Please reload.');
  return result;
}
function matches(list, row) {
  return (!list.keys || list.keys.includes(row.key || row._id))
    && Object.entries(list.filter || {}).every(([key, value]) => row[key] === value);
}
function definitionsFor(collection, row) {
  const key = row.key || row._id;
  return [
    ...records.filter(record => record.collection === collection && record.key === key),
    ...[...lists.values()].filter(list => list.collection === collection && matches(list, row))
  ];
}
function permittedFields(collection, definitions) {
  const schema = collectionSchema(collection);
  const allowed = new Map();
  for (const definition of definitions) {
    for (const field of definition.fields || []) {
      if (!field.virtual) allowed.set(field.key, field);
      if (field.type === 'image') {
        allowed.set(field.altField || 'alt', { type: 'text' });
        allowed.set(field.xField || 'focalX', { type: 'number', min: 0, max: 100 });
        allowed.set(field.yField || 'focalY', { type: 'number', min: 0, max: 100 });
      }
    }
    for (const field of definition.composite?.storageFields || []) allowed.set(field, { type: 'text' });
    if (definition.hide || schema.editableFields.includes('isVisible')) allowed.set('isVisible', { type: 'boolean' });
  }
  for (const key of allowed.keys()) {
    if (locked.has(key) || !schema.editableFields.includes(key) || !PUBLIC_COLLECTIONS[collection].includes(key)) allowed.delete(key);
  }
  return allowed;
}
function safeUrl(value, image = false) {
  if (typeof value !== 'string' || value.length > 4096 || /[\u0000-\u001f\u007f<>"\\]/.test(value)) return false;
  if (!value) return true;
  let decoded;
  try { decoded = decodeURIComponent(value); } catch (_) { return false; }
  if (/[\u0000-\u001f\u007f\\]/.test(decoded)) return false;
  if (image && /^wix:image:\/\/v1\/[A-Za-z0-9_~.-]+\//.test(value)) return !decoded.split(/[/?#]/).includes('..');
  if (/\s/.test(value)) return false;
  if (image && /^assets\/images\/[A-Za-z0-9_./-]+$/.test(value)) return !decoded.split('/').includes('..');
  if (!image && (/^@\//.test(value) || /^\/(?!\/)/.test(value) || /^#[A-Za-z][A-Za-z0-9_-]*$/.test(value))) {
    return !decoded.split(/[/?#]/).includes('..');
  }
  // Preserve existing rich-copy relative links; they can only address a known
  // static website page, never a protocol-relative or executable destination.
  if (!image && /^(?:\.\.\/)*[A-Za-z0-9_/-]+\.html(?:#[A-Za-z0-9_-]+)?$/.test(value)) {
    const relative = value.replace(/^(?:\.\.\/)+/, '').split('#')[0];
    return EDITOR_MODEL.pages.some(page => page.previewPath === relative);
  }
  if (!image && /^mailto:[^\s@?]+@[^\s@?]+(?:\?[^\r\n]*)?$/.test(value)) return true;
  if (!image && /^tel:\+?[0-9().-]+$/.test(value)) return true;
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && !url.username && !url.password && Boolean(url.hostname);
  } catch (_) { return false; }
}
function decodeAttribute(value) {
  const named = { amp: '&', quot: '"', apos: "'", lt: '<', gt: '>' };
  return value.replace(/&(#x[0-9a-f]+|#\d+|amp|quot|apos|lt|gt);/gi, (_, entity) => {
    if (entity[0] === '#') {
      const number = entity[1].toLowerCase() === 'x' ? parseInt(entity.slice(2), 16) : parseInt(entity.slice(1), 10);
      return number <= 0x10ffff ? String.fromCodePoint(number) : '\u0000';
    }
    return named[entity.toLowerCase()];
  });
}
function validRichText(value) {
  // Semantic markup only. Never accept styles, scripts, SVG, or event attributes.
  const tags = new Set(['p', 'div', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'ul', 'ol', 'li', 'a', 'blockquote', 'h2', 'h3', 'h4', 'span']);
  const tokens = value.match(/<[^>]*>|[^<]+/g) || [];
  if (tokens.join('') !== value) return false;
  for (const token of tokens) {
    if (token[0] !== '<') continue;
    const match = token.match(/^<(\/)?([a-z][a-z0-9]*)([\s\S]*?)\s*(\/?)>$/i);
    if (!match || !tags.has(match[2].toLowerCase())) return false;
    const [, closing, name, attributeText] = match;
    if (closing) { if (attributeText.trim()) return false; continue; }
    const tag = name.toLowerCase();
    let remainder = attributeText;
    const used = new Set();
    while (remainder.trim()) {
      const attribute = remainder.match(/^\s+([a-z][a-z0-9-]*)\s*=\s*(?:"([^"]*)"|'([^']*)')/i);
      if (!attribute) return false;
      const key = attribute[1].toLowerCase(), content = decodeAttribute(attribute[2] ?? attribute[3]);
      if (used.has(key)) return false;
      used.add(key);
      if (key === 'class') { if (!/^[a-zA-Z0-9_ -]*$/.test(content)) return false; }
      else if (tag === 'a' && key === 'href') { if (!safeUrl(content)) return false; }
      else if (tag === 'a' && key === 'target') { if (!['_blank', '_self'].includes(content)) return false; }
      else if (tag === 'a' && key === 'rel') { if (!/^(?:(?:noopener|noreferrer|nofollow)\s*)+$/.test(content)) return false; }
      else return false;
      remainder = remainder.slice(attribute[0].length);
    }
  }
  return true;
}
function compositeValues(composite, row) {
  const date = row.dateTime;
  if (typeof date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(date)) fail('INVALID_DATE', 'Choose a valid date.');
  const parsed = new Date(date + 'T12:00:00.000Z');
  if (!Number.isFinite(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== date) fail('INVALID_DATE', 'Choose a valid date.');
  const weekday = parsed.toLocaleDateString('en-US', { weekday: 'long', timeZone: 'UTC' });
  const month = parsed.toLocaleDateString('en-US', { month: 'long', timeZone: 'UTC' });
  const day = parsed.getUTCDate(), year = parsed.getUTCFullYear();
  if (composite.type === 'auditionDate') return { text: `${month} ${day}`, dateTime: date };
  if (composite.type === 'showDate') {
    if (typeof row.showDateTime !== 'string' || !new RegExp('^' + date + 'T(?:[01]\\d|2[0-3]):[0-5]\\d$').test(row.showDateTime)) fail('INVALID_TIME', 'Choose a valid show time.');
    const [hour, minute] = row.showDateTime.slice(11).split(':').map(Number);
    const clock = `${hour % 12 || 12}${minute ? ':' + String(minute).padStart(2, '0') : ''} ${hour >= 12 ? 'PM' : 'AM'}`;
    return { dateLabel: `${weekday}, ${month} ${day}, ${year}`, datePrefix: `${weekday}, ${month} `,
      dayNumber: String(day), year: String(year), dateTime: date, showLabel: `${weekday}, ${month} ${day} at ${clock}`, showDateTime: row.showDateTime };
  }
  return {};
}
async function validateChanges(collection, changes, definitions, current = {}) {
  if (!plainObject(changes) || !Object.keys(changes).length || Object.keys(changes).length > 30) fail('INVALID_FIELDS', 'Choose a field to change.');
  const allowed = permittedFields(collection, definitions);
  const schema = collectionSchema(collection);
  const result = {};
  for (const [key, value] of Object.entries(changes)) {
    if (forbidden.has(key) || !allowed.has(key)) fail('INVALID_FIELD', 'This field cannot be changed here.');
    const definition = allowed.get(key);
    const storage = schema.fields.find(field => field.key === key)?.type;
    if (storage === 'BOOLEAN' || definition.type === 'boolean') {
      if (typeof value !== 'boolean') fail('INVALID_VALUE', 'Choose whether this item should be visible.');
    } else if (storage === 'NUMBER' || definition.type === 'number') {
      if (value !== null && (typeof value !== 'number' || !Number.isFinite(value)
        || value < (definition.min ?? -1000000) || value > (definition.max ?? 1000000))) fail('INVALID_VALUE', 'Enter a number in the allowed range.');
    } else {
      if (typeof value !== 'string' || value.length > MAX_TEXT || /\u0000/.test(value)) fail('INVALID_VALUE', 'This text is too long or contains an unsupported character.');
      if (storage === 'IMAGE' || definition.type === 'image') {
        if (!safeUrl(value, true)) fail('INVALID_IMAGE', 'Choose an image from the media manager or use a valid HTTPS image link.');
      } else if (key === 'url' || definition.type === 'url') {
        if (!safeUrl(value)) fail('INVALID_LINK', 'Use an HTTPS, email, phone, or website page link.');
      } else if (definition.type === 'email' && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) fail('INVALID_EMAIL', 'Enter a valid email address.');
      else if (definition.type === 'phone' && value && !/^\+?[0-9() .-]{5,40}$/.test(value)) fail('INVALID_PHONE', 'Enter a valid phone number.');
      if ((storage === 'RICH_TEXT' || definition.type === 'richText') && !validRichText(value)) fail('INVALID_FORMATTING', 'Use the formatting buttons for this text; unsupported HTML cannot be saved.');
      if (definition.type === 'select' && definition.source) {
        const source = definition.source;
        const choices = await readCollection(source.collection);
        if (!choices.some(row => String(row[source.valueField] || row[source.fallbackValueField || '_id']) === value)) fail('INVALID_CATEGORY', 'Choose an existing class group.');
      }
      if (definition.type === 'select' && definition.options && !definition.options.some(option => option.value === value)) fail('INVALID_CHOICE', 'Choose one of the available options.');
      if (key === 'afterSection' && value) {
        const page = current.page || definitions.find(definition => definition.filter?.page)?.filter.page;
        const sections = await readCollection('DiSections');
        if (!sections.some(section => section.page === page && (section.key || section._id) === value)) fail('INVALID_SECTION', 'Choose an existing section on this page.');
      }
    }
    result[key] = value;
  }
  for (const definition of definitions) {
    const composite = definition.composite;
    if (composite?.storageFields.some(field => own(changes, field))) Object.assign(result, compositeValues(composite, { ...current, ...result }));
  }
  const merged = { isVisible: true, ...current, ...result };
  if (collection === 'DiGalleryPhotos' && merged.isVisible === true
    && (!merged.image || !safeUrl(merged.image, true))) {
    fail('REQUIRED_IMAGE', 'Choose a photo before showing this gallery item, or hide the item from the website.');
  }
  return result;
}
function errorResult(error) {
  if (error instanceof EditorError) return { ok: false, error: { code: error.code, message: error.message }, ...error.details };
  return { ok: false, error: { code: 'WIX_UNAVAILABLE', message: 'Wix could not complete this action. Check that you are signed in with CMS access, then reload before trying again.' } };
}
async function guardedPatch(collection, id, expectedUpdatedDate, changes) {
  const expected = timestamp(expectedUpdatedDate);
  let patch = items.bulkPatch(collection, [id]);
  for (const [field, value] of Object.entries(changes)) patch = patch.setField(field, value);
  const result = await patch.run({ condition: items.filter().eq('_updatedDate', expected) });
  if (result.updated !== 1 || !result.updatedItemIds?.includes(id) || result.errors?.length) {
    fail('CONFLICT', 'Someone changed this item after you opened it. Reload it before saving.');
  }
  // Read the primary database in this same call; never return an optimistic copy.
  try { return publicItem(collection, await readOne(collection, id)); }
  catch (_) {
    fail('SAVED_RELOAD_REQUIRED', 'Your change was saved, but Wix could not reload it. Reload the editor before making another change.',
      { applied: true, reloadRequired: true, updatedIds: [id] });
  }
}

export const loadStudioContent = webMethod(Permissions.Admin, async () => {
  try {
    const entries = await Promise.all(Object.keys(PUBLIC_COLLECTIONS).map(async collection => [collection, await readCollection(collection)]));
    return { ok: true, model: EDITOR_MODEL, collections: Object.fromEntries(entries) };
  } catch (error) { return errorResult(error); }
});

export const saveStudioItem = webMethod(Permissions.Admin, async request => {
  try {
    requestObject(request, ['collection', 'id', 'expectedUpdatedDate', 'changes']);
    const { collection, expectedUpdatedDate } = request;
    const id = itemId(request.id);
    timestamp(expectedUpdatedDate);
    const row = await readOne(collection, id);
    if (!row) fail('MISSING_ITEM', 'This item is no longer available. Reload the page.');
    const changes = await validateChanges(collection, request.changes, definitionsFor(collection, row), row);
    return { ok: true, item: await guardedPatch(collection, id, expectedUpdatedDate, changes) };
  } catch (error) { return errorResult(error); }
});

export const createStudioItem = webMethod(Permissions.Admin, async request => {
  try {
    requestObject(request, ['listId', 'values']);
    const list = lists.get(request.listId);
    if (!list?.allowAdd) fail('INVALID_LIST', 'New items cannot be added to this section.');
    const values = await validateChanges(list.collection, request.values, [list]);
    for (const field of list.fields || []) {
      if (!field.virtual && field.required && !values[field.key]) fail('REQUIRED_FIELD', `Enter ${field.label.toLowerCase()} before adding this item.`);
    }
    const existing = (await readCollection(list.collection)).filter(row => matches(list, row));
    const sortOrder = Math.max(-1, ...existing.map(row => Number.isFinite(row.sortOrder) ? row.sortOrder : -1)) + 1;
    // Wix supplies the ID. The public adapter uses it as a key for new list rows.
    // Clients can never create singleton binding keys or move items across pages.
    const insert = { isVisible: true, ...values, ...list.filter, sortOrder };
    if (list.collection === 'DiClassCategories') insert.categoryOrder = sortOrder;
    const inserted = await wixData.insert(list.collection, insert);
    try { return { ok: true, item: publicItem(list.collection, await readOne(list.collection, inserted._id)) }; }
    catch (_) {
      fail('SAVED_RELOAD_REQUIRED', 'Your new item was added, but Wix could not reload it. Reload the editor before adding it again.',
        { applied: true, reloadRequired: true, createdId: inserted._id });
    }
  } catch (error) { return errorResult(error); }
});

export const reorderStudioItems = webMethod(Permissions.Admin, async request => {
  const saved = [];
  try {
    requestObject(request, ['listId', 'items']);
    const list = lists.get(request.listId);
    if (!list?.reorder || !Array.isArray(request.items) || !request.items.length || request.items.length > MAX_REORDER) fail('INVALID_ORDER', 'This list could not be reordered. Please reload it.');
    const seen = new Set();
    for (const entry of request.items) {
      requestObject(entry, ['id', 'expectedUpdatedDate']);
      itemId(entry.id); timestamp(entry.expectedUpdatedDate);
      if (seen.has(entry.id)) fail('INVALID_ORDER', 'Each item must appear once in the order.');
      seen.add(entry.id);
    }
    const current = (await readCollection(list.collection)).filter(row => matches(list, row));
    // Require the entire list, including hidden items, so unmentioned rows keep
    // neither duplicate nor surprising order positions after a concurrent add.
    if (current.length !== seen.size || (list.keys && current.length !== list.keys.length)
      || current.some(row => !seen.has(row._id))) fail('CONFLICT', 'This list changed after you opened it. Reload before reordering.');
    for (const entry of request.items) {
      const row = current.find(candidate => candidate._id === entry.id);
      if (row._updatedDate !== entry.expectedUpdatedDate) fail('CONFLICT', 'This list changed after you opened it. Reload before reordering.');
    }
    for (let index = 0; index < request.items.length; index++) {
      const entry = request.items[index];
      const changes = { sortOrder: index };
      if (list.collection === 'DiClassCategories') changes.categoryOrder = index;
      saved.push(await guardedPatch(list.collection, entry.id, entry.expectedUpdatedDate, changes));
    }
    return { ok: true, items: saved };
  } catch (error) {
    // Reordering is not a transaction. Report confirmed writes so the UI can
    // retain them and visibly request a refresh instead of implying rollback.
    const result = errorResult(error);
    if (saved.length && !result.applied) result.error.message = `${saved.length} position${saved.length === 1 ? ' was' : 's were'} saved before the list changed. Reload to see the current order before continuing.`;
    return { ...result, items: saved, partial: saved.length > 0 || result.applied === true };
  }
});
