import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const root = new URL('../', import.meta.url);
const source = readFileSync(new URL('wix/backend/studio-editor.web.js', root), 'utf8')
  .replace(/^import .*;\n/gm, '').replace(/^export /gm, '');
const model = JSON.parse(readFileSync(new URL('wix/editor/model.json', root), 'utf8'));
const schemaSource = readFileSync(new URL('wix/backend/content-schema.js', root), 'utf8');
const PUBLIC_COLLECTIONS = JSON.parse(schemaSource.match(/PUBLIC_COLLECTIONS = ([\s\S]*);\s*$/)[1]);
const clone = value => structuredClone(value);
const stamp = '2026-11-05T12:00:00.000Z';
const row = (id, fields = {}) => ({ _id: id, _updatedDate: new Date(stamp), isVisible: true, sortOrder: 0, ...fields });

function harness(initial = {}, options = {}) {
  const database = Object.fromEntries(Object.keys(PUBLIC_COLLECTIONS).map(collection => [collection, clone(initial[collection] || [])]));
  const calls = { reads: 0, writes: 0, inserts: 0, registrations: 0 };
  let clock = 1;
  function find(collection, id) { return database[collection].find(item => item._id === id); }
  const context = {
    Object, Date, URL, Set, Map, JSON, Error, Number, String, Boolean, Math,
    PUBLIC_COLLECTIONS, EDITOR_MODEL: model, module: { exports: {} },
    Permissions: { Admin: 'Admin' },
    webMethod(permission, callback) {
      assert.equal(permission, 'Admin'); calls.registrations++;
      return async (...args) => {
        if (options.authorized === false) throw new Error('Forbidden');
        return callback(...args);
      };
    },
    wixData: {
      async get(collection, id, readOptions) {
        assert.equal(JSON.stringify(readOptions), '{"consistentRead":true}'); calls.reads++;
        if (options.failReadback && (calls.writes || calls.inserts)) throw new Error('Readback unavailable');
        return clone(find(collection, id));
      },
      query(collection) {
        const chain = {
          ascending(field) { assert.equal(field, '_id'); return chain; },
          limit(number) { assert.equal(number, 1000); return chain; },
          async find(readOptions) {
            assert.equal(JSON.stringify(readOptions), '{"consistentRead":true}'); calls.reads++;
            return { items: clone(database[collection]), totalCount: database[collection].length, hasNext: () => false };
          }
        };
        return chain;
      },
      async insert(collection, values) {
        assert.equal(values._id, undefined); assert.equal(values.key, undefined);
        calls.inserts++;
        const inserted = row('created-' + calls.inserts, clone(values));
        database[collection].push(inserted);
        return clone(inserted);
      }
    },
    items: {
      filter() { return { eq: (field, value) => ({ field, value }) }; },
      bulkPatch(collection, ids) {
        assert.equal(ids.length, 1);
        const fields = {};
        const chain = {
          setField(field, value) { fields[field] = value; return chain; },
          async run(patchOptions) {
            assert.deepEqual(Object.keys(patchOptions), ['condition']);
            assert.equal(patchOptions.condition.field, '_updatedDate');
            calls.writes++;
            const current = find(collection, ids[0]);
            options.beforePatch?.({ collection, id: ids[0], current, calls });
            if (!current || +current._updatedDate !== +patchOptions.condition.value) return { updated: 0, updatedItemIds: [], errors: [], skipped: 1 };
            Object.assign(current, clone(fields), { _updatedDate: new Date(new Date(stamp).getTime() + clock++ * 1000) });
            return { updated: 1, updatedItemIds: [ids[0]], errors: [], skipped: 0 };
          }
        };
        return chain;
      }
    }
  };
  vm.runInNewContext(source + '\nmodule.exports = {loadStudioContent,saveStudioItem,createStudioItem,reorderStudioItems};', context);
  return { ...context.module.exports, database, calls };
}
const edit = (changes, extra = {}) => ({ collection: 'DiPolicies', id: 'policy-1', expectedUpdatedDate: stamp, changes, ...extra });

test('every editor entry point requires Admin before any data read or write', async () => {
  const api = harness({}, { authorized: false });
  assert.equal(api.calls.registrations, 4);
  for (const method of ['loadStudioContent', 'saveStudioItem', 'createStudioItem', 'reorderStudioItems']) await assert.rejects(api[method]({}), /Forbidden/);
  assert.equal(api.calls.reads, 0); assert.equal(api.calls.writes, 0); assert.equal(api.calls.inserts, 0);
});

test('authorized load includes hidden content but strips all nonpublic fields', async () => {
  const api = harness({ DiPolicies: [row('policy-1', { key: 'safety', title: 'Safety', isVisible: false, privateNotes: 'Never expose', privateObject: { secret: true } })] });
  const result = await api.loadStudioContent();
  assert.equal(result.ok, true); assert.equal(result.model.siteId, model.siteId);
  assert.deepEqual(JSON.parse(JSON.stringify(result.collections.DiPolicies)), [{ _id: 'policy-1', _updatedDate: stamp, key: 'safety', title: 'Safety', isVisible: false, sortOrder: 0 }]);
});

test('patches only named allowed fields and reads back the confirmed live version', async () => {
  const api = harness({ DiPolicies: [row('policy-1', { key: 'safety', title: 'Safety', body: '<p>Old</p>', privateNotes: 'Keep me' })] });
  const result = await api.saveStudioItem(edit({ body: '<p>New <strong>copy</strong>.</p>' }));
  assert.equal(result.ok, true); assert.equal(result.item.body, '<p>New <strong>copy</strong>.</p>');
  assert.notEqual(result.item._updatedDate, stamp); assert.equal(result.item.title, 'Safety'); assert.equal(result.item.privateNotes, undefined);
  assert.equal(api.database.DiPolicies[0].privateNotes, 'Keep me'); assert.equal(api.calls.writes, 1);
});

test('server rejects unknown collections, protected keys, unsafe links and rich HTML', async () => {
  const api = harness({ DiPolicies: [row('policy-1', { key: 'safety', title: 'Safety' })] });
  const attempts = [
    edit({ title: 'x' }, { collection: 'PrivateMembersData' }), edit({ key: 'another-binding' }), edit({ sortOrder: 500 }),
    edit({ privateNotes: 'x' }), edit({ body: '<img src="x" onerror="alert(1)">' }),
    edit({ body: '<p style="display:none">x</p>' }), edit({ body: '<a href="jav&#x61;script:alert(1)">x</a>' })
  ];
  for (const request of attempts) assert.equal((await api.saveStudioItem(request)).ok, false);
  assert.equal(api.calls.writes, 0);
});

test('stale changes are rejected atomically even when another write occurs after reading', async () => {
  const api = harness({ DiPolicies: [row('policy-1', { title: 'Original' })] }, {
    beforePatch({ current }) { current.title = 'Michele’s latest'; current._updatedDate = new Date('2026-11-05T12:01:00.000Z'); }
  });
  const result = await api.saveStudioItem(edit({ title: 'Stale edit' }));
  assert.equal(result.ok, false); assert.equal(result.error.code, 'CONFLICT');
  assert.equal(api.database.DiPolicies[0].title, 'Michele’s latest'); assert.equal(api.calls.writes, 1);
});

test('creates only allowed list rows with server-owned context, identity and order', async () => {
  const api = harness({ DiGalleryPhotos: [row('photo-1', { gallery: 'competition', sortOrder: 4 })] });
  const listId = 'digalleryphotos-gallery-competition';
  for (const values of [{ image: 'https://example.com/a.jpg', gallery: 'nutcracker' }, { image: 'https://example.com/a.jpg', key: 'hero' }]) {
    assert.equal((await api.createStudioItem({ listId, values })).ok, false);
  }
  const result = await api.createStudioItem({ listId, values: { image: 'wix:image://v1/abc~mv2.jpg/Dance photo.jpg', alt: 'Dancers on stage' } });
  assert.equal(result.ok, true); assert.equal(result.item.gallery, 'competition'); assert.equal(result.item.sortOrder, 5);
  assert.equal(result.item._id, 'created-1'); assert.equal(api.calls.inserts, 1);
});

test('class category edits must reference a real current group', async () => {
  const api = harness({ DiClasses: [row('class-1', { category: 'ballet' })], DiClassCategories: [row('category-1', { key: 'ballet', title: 'Ballet' })] });
  const request = { collection: 'DiClasses', id: 'class-1', expectedUpdatedDate: stamp, changes: { category: 'not-a-group' } };
  assert.equal((await api.saveStudioItem(request)).error.code, 'INVALID_CATEGORY');
  assert.equal(api.calls.writes, 0);
});

test('reorder reports confirmed partial writes without retrying or overwriting concurrent changes', async () => {
  const api = harness({ DiPolicies: [row('policy-1', { sortOrder: 0 }), row('policy-2', { sortOrder: 1 })] }, {
    beforePatch({ current, calls }) { if (calls.writes === 2) { current.title = 'Concurrent'; current._updatedDate = new Date('2026-11-05T12:10:00.000Z'); } }
  });
  const result = await api.reorderStudioItems({ listId: 'dipolicies', items: [{ id: 'policy-2', expectedUpdatedDate: stamp }, { id: 'policy-1', expectedUpdatedDate: stamp }] });
  assert.equal(result.ok, false); assert.equal(result.partial, true); assert.equal(result.items.length, 1);
  assert.equal(result.items[0]._id, 'policy-2'); assert.equal(result.error.code, 'CONFLICT');
  assert.equal(api.calls.writes, 2); assert.equal(api.database.DiPolicies[0].title, 'Concurrent');
});

test('section reordering is limited to its exact generated sibling key set', async () => {
  const group = model.pages.find(page => page.id === 'home').sectionGroups[0];
  const sections = group.keys.map((key, index) => row('section-' + index, { key, page: 'home', sortOrder: index }));
  const api = harness({ DiSections: [...sections, row('foreign-section', { key: 'elsewhere', page: 'contact' })] });
  const order = sections.toReversed().map(item => ({ id: item._id, expectedUpdatedDate: stamp }));
  const bad = await api.reorderStudioItems({ listId: group.id, items: [...order.slice(1), { id: 'foreign-section', expectedUpdatedDate: stamp }] });
  assert.equal(bad.ok, false); assert.equal(api.calls.writes, 0);
  const valid = await api.reorderStudioItems({ listId: group.id, items: order });
  assert.equal(valid.ok, true); assert.equal(valid.items.length, sections.length);
  assert.equal(api.database.DiSections.find(item => item._id === 'foreign-section').sortOrder, 0);
});

test('extra sections can be placed only at an allowed live anchor on their own page', async () => {
  const api = harness({ DiSections: [row('section-1', { key: 'home-home-about', page: 'home' })] });
  const listId = 'dicontentblocks-page-home';
  const bad = await api.createStudioItem({ listId, values: { title: 'New', afterSection: 'contact-introduction' } });
  assert.equal(bad.ok, false); assert.equal(api.calls.inserts, 0);
  const good = await api.createStudioItem({ listId, values: { title: 'New', afterSection: 'home-home-about' } });
  assert.equal(good.ok, true); assert.equal(good.item.page, 'home'); assert.equal(good.item.afterSection, 'home-home-about');
});

test('show dates are validated and all displayed labels are derived consistently on the server', async () => {
  const api = harness();
  const invalid = await api.createStudioItem({ listId: 'dishowdates', values: { dateTime: '2026-02-31', showDateTime: '2026-02-31T18:00' } });
  assert.equal(invalid.error.code, 'INVALID_DATE');
  const good = await api.createStudioItem({ listId: 'dishowdates', values: { dateTime: '2026-12-18', showDateTime: '2026-12-18T18:00', showLabel: 'Incorrect label' } });
  assert.equal(good.ok, true); assert.equal(good.item.showLabel, 'Friday, December 18 at 6 PM'); assert.equal(good.item.year, '2026');
});

test('a confirmed write with failed readback is explicitly marked saved and requires reload', async () => {
  const api = harness({ DiPolicies: [row('policy-1', { title: 'Original' })] }, { failReadback: true });
  const saved = await api.saveStudioItem(edit({ title: 'New title' }));
  assert.equal(saved.error.code, 'SAVED_RELOAD_REQUIRED'); assert.equal(saved.reloadRequired, true); assert.equal(saved.applied, true);
  assert.equal(api.database.DiPolicies[0].title, 'New title'); assert.equal(api.calls.writes, 1);
});

test('visible gallery items always retain an image while hiding an item remains possible', async () => {
  const api = harness({ DiGalleryPhotos: [row('photo-1', { gallery: 'competition', image: 'https://example.com/photo.jpg' })] });
  const request = { collection: 'DiGalleryPhotos', id: 'photo-1', expectedUpdatedDate: stamp, changes: { image: '' } };
  assert.equal((await api.saveStudioItem(request)).error.code, 'REQUIRED_IMAGE');
  assert.equal(api.calls.writes, 0);
  assert.equal((await api.createStudioItem({ listId: 'digalleryphotos-gallery-competition', values: { alt: 'Missing photo' } })).error.code, 'REQUIRED_IMAGE');
  assert.equal(api.calls.inserts, 0);
  const hidden = await api.saveStudioItem({ ...request, changes: { isVisible: false, image: '' } });
  assert.equal(hidden.ok, true); assert.equal(hidden.item.isVisible, false);
  const shown = await api.saveStudioItem({ ...request, expectedUpdatedDate: hidden.item._updatedDate, changes: { isVisible: true } });
  assert.equal(shown.error.code, 'REQUIRED_IMAGE');
  assert.equal(api.calls.writes, 1);
});
