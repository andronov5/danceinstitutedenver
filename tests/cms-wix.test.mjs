import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const require = createRequire(import.meta.url);
const { loadCollections, imageUrl } = require('../assets/cms-wix.js');
const config = {
  enabled: true,
  transport: 'http-function',
  endpoint: 'https://dance1806.wixsite.com/my-site/_functions/danceContent',
  collectionIds: { copy: 'DiPageContent', teachers: 'DiTeachers' }
};
const row = (key, extra = {}) => ({ key, isVisible: true, ...extra });
const reply = collections => ({ ok: true, status: 200, json: async () => ({ version: 1, complete: true, collections }) });

test('disabled CMS keeps bundled content without making a request', async () => {
  assert.deepEqual(await loadCollections({ enabled: false }, ['copy'], { fetchImpl: () => assert.fail('Unexpected fetch') }), {});
});

test('fetches a complete public snapshot without credentials and maps collection IDs', async () => {
  let count = 0;
  const result = await loadCollections(config, ['copy', 'teachers', 'copy'], {
    fetchImpl: async (url, options) => {
      count++;
      assert.equal(new URL(url).searchParams.get('collections'), 'DiPageContent,DiTeachers');
      assert.equal(options.method, 'GET');
      assert.equal(options.credentials, 'omit');
      assert.equal(options.cache, 'no-store');
      assert.equal(options.redirect, 'error');
      assert.equal(options.headers.Authorization, undefined);
      return reply({ DiPageContent: [row('home-title', { text: 'Dance Institute' })], DiTeachers: [] });
    }
  });
  assert.equal(count, 1);
  assert.equal(result.copy[0].text, 'Dance Institute');
  assert.deepEqual(result.teachers, []);
});

test('never displays hidden or unspecified-visibility records', async () => {
  const result = await loadCollections(config, ['copy'], { fetchImpl: async () => reply({ DiPageContent: [row('visible'), row('hidden', { isVisible: false }), { key: 'draft' }] }) });
  assert.deepEqual(result.copy.map(item => item.key), ['visible']);
});

test('partial, missing, malformed, or duplicate snapshots reject atomically', async t => {
  const payloads = [
    { version: 1, complete: false, collections: { DiPageContent: [] } },
    { version: 1, complete: true, collections: {} },
    { version: 1, complete: true, collections: { DiPageContent: null } },
    { version: 1, complete: true, collections: { DiPageContent: [row('duplicate'), row('duplicate')] } },
    { version: 1, complete: true, collections: { DiPageContent: [{ isVisible: true }] } }
  ];
  for (let i = 0; i < payloads.length; i++) await t.test(String(i), async () => {
    await assert.rejects(loadCollections(config, ['copy'], { fetchImpl: async () => ({ ok: true, json: async () => payloads[i] }) }), /Wix CMS:/);
  });
});

test('HTTP errors, invalid JSON and network failure reject for fallback', async () => {
  await assert.rejects(loadCollections(config, ['copy'], { fetchImpl: async () => ({ ok: false, status: 503 }) }), /HTTP 503/);
  await assert.rejects(loadCollections(config, ['copy'], { fetchImpl: async () => ({ ok: true, json: async () => { throw new SyntaxError('Invalid JSON'); } }) }), SyntaxError);
  await assert.rejects(loadCollections(config, ['copy'], { fetchImpl: async () => { throw new TypeError('Failed to fetch'); } }), TypeError);
});

test('only accepts studio Wix function endpoints and content collections', async () => {
  const never = { fetchImpl: () => assert.fail('Unexpected fetch') };
  for (const endpoint of [
    'http://dance1806.wixsite.com/my-site/_functions/danceContent',
    'https://example.com/_functions/danceContent',
    'https://dance1806.wixsite.com/my-site/_functions/admin',
    'https://dance1806.wixsite.com/my-site/_functions-dev/danceContent',
    'https://user:password@danceinstitutedenver.com/_functions/danceContent',
    'https://danceinstitutedenver.com/_functions/danceContent?collection=private'
  ]) await assert.rejects(loadCollections({ ...config, endpoint }, ['copy'], never), /Wix CMS:/);
  await assert.rejects(loadCollections({ ...config, collectionIds: { copy: 'Members/PrivateMembersData' } }, ['copy'], never), /content collections/);
  await assert.rejects(loadCollections(config, ['__proto__'], never), /identifier/);
});

test('caller abort and timeout cancel outstanding fetches', async () => {
  const abortedFetch = (_url, { signal }) => new Promise((_resolve, reject) => {
    signal.addEventListener('abort', () => reject(signal.reason), { once: true });
  });
  const controller = new AbortController();
  const pending = loadCollections(config, ['copy'], { fetchImpl: abortedFetch, signal: controller.signal });
  controller.abort();
  await assert.rejects(pending, { name: 'AbortError' });
  await assert.rejects(loadCollections(config, ['copy'], { fetchImpl: abortedFetch, timeoutMs: 5 }), { name: 'AbortError' });
  await assert.rejects(loadCollections(config, ['copy'], { fetchImpl: () => assert.fail('Unexpected fetch'), signal: controller.signal }), { name: 'AbortError' });
});

test('converts Wix media references and rejects executable or malformed image URLs', () => {
  assert.equal(imageUrl('wix:image://v1/abc_123~mv2.jpg/Teacher.jpg#originWidth=500&originHeight=700'), 'https://static.wixstatic.com/media/abc_123~mv2.jpg');
  assert.equal(imageUrl({ src: 'wix:image://v1/abc_123~mv2.png/image.png' }), 'https://static.wixstatic.com/media/abc_123~mv2.png');
  assert.equal(imageUrl('wix:image://v1/abc_123~mv2.jpg/Miss Michele.jpg'), 'https://static.wixstatic.com/media/abc_123~mv2.jpg');
  assert.equal(imageUrl('assets/images/teacher.webp'), 'assets/images/teacher.webp');
  assert.equal(imageUrl('https://static.wixstatic.com/media/abc.jpg'), 'https://static.wixstatic.com/media/abc.jpg');
  for (const invalid of ['javascript:alert(1)', 'data:image/svg+xml,test', '//evil.test/img.jpg', 'https://name:password@evil.test/img.jpg', 'wix:image://v1/../evil.jpg', 'wix:image://v1/%2e%2e/evil.jpg', 'assets/images/../private', '<img>', null]) {
    assert.equal(imageUrl(invalid), '', String(invalid));
  }
});

// Execute the actual deployable Wix source with only Wix's environment imports
// replaced, so pagination and public-field boundaries are verified end to end.
function backend(pagesByCollection) {
  let queryCount = 0;
  const source = readFileSync(new URL('../wix/backend/http-functions.js', import.meta.url), 'utf8')
    .replace(/^import .*;\n/gm, '')
    .replace(/^export /gm, '');
  const context = {
    module: { exports: {} },
    PUBLIC_COLLECTIONS: { DiPageContent: ['key', 'isVisible', 'text'], DiTeachers: ['key', 'isVisible', 'name'] },
    response: value => value,
    wixData: {
      query(id) {
        queryCount++;
        const chain = {
          eq(field, value) { assert.equal(field, 'isVisible'); assert.equal(value, true); return chain; },
          ascending(field) { assert.equal(field, '_id'); return chain; },
          limit(limit) { assert.equal(limit, 1000); return chain; },
          async find(options) {
            assert.equal(options.suppressAuth, true);
            assert.equal(options.consistentRead, true);
            const pages = pagesByCollection[id];
            if (pages instanceof Error) throw pages;
            const wrap = index => ({ ...pages[index], hasNext: () => index < pages.length - 1, next: async () => wrap(index + 1) });
            return wrap(0);
          }
        };
        return chain;
      }
    }
  };
  vm.runInNewContext(source + '\nmodule.exports = { get_danceContent, options_danceContent };', context);
  return { ...context.module.exports, queryCount: () => queryCount };
}

function request(collections = 'DiPageContent', origin = 'https://dance-institute-denver-design.gnotobiot.chatgpt.site') {
  return { query: { collections }, headers: origin ? { origin } : {} };
}

test('Wix function reads every page and returns only allowlisted visible fields', async () => {
  const api = backend({ DiPageContent: [
    { totalCount: 3, items: [{ _id: '1', ...row('a', { text: 'First', privateNotes: 'Never public' }) }] },
    { totalCount: 3, items: [{ _id: '2', ...row('b', { text: 'Second' }) }, { _id: '3', ...row('hidden', { isVisible: false, privateNotes: 'Never public' }) }] }
  ] });
  const result = await api.get_danceContent(request());
  assert.equal(result.status, 200);
  assert.equal(result.headers['Access-Control-Allow-Origin'], 'https://dance-institute-denver-design.gnotobiot.chatgpt.site');
  assert.equal(result.headers['Cache-Control'], 'no-store');
  assert.deepEqual(JSON.parse(result.body), { version: 1, complete: true, collections: { DiPageContent: [row('a', { text: 'First' }), row('b', { text: 'Second' })] } });
});

test('Wix function distinguishes empty collections from unavailable collections', async () => {
  const api = backend({ DiPageContent: [{ totalCount: 0, items: [] }], DiTeachers: new Error('Private backend error') });
  const empty = await api.get_danceContent(request());
  assert.deepEqual(JSON.parse(empty.body).collections.DiPageContent, []);
  const partial = await api.get_danceContent(request('DiPageContent,DiTeachers'));
  assert.equal(partial.status, 503);
  assert.deepEqual(JSON.parse(partial.body), { error: 'Content temporarily unavailable' });
});

test('new Wix rows use their automatic ID when the content key is blank', async () => {
  const items = [
    { _id: 'new-missing', isVisible: true, name: 'New teacher' },
    { _id: 'new-empty', key: '', isVisible: true, name: 'Another teacher' },
    { _id: 'new-null', key: null, isVisible: true },
    { _id: 'new-whitespace', key: '  ', isVisible: true },
    { _id: 'existing-wix-id', key: 'existing-content-key', isVisible: true }
  ];
  const api = backend({ DiTeachers: [{ totalCount: items.length, items }] });
  const result = await api.get_danceContent(request('DiTeachers'));
  assert.equal(result.status, 200);
  const teachers = JSON.parse(result.body).collections.DiTeachers;
  assert.deepEqual(teachers.map(item => item.key), ['new-missing', 'new-empty', 'new-null', 'new-whitespace', 'existing-content-key']);
  assert.equal(teachers[0].name, 'New teacher');
  assert.equal(teachers[0]._id, undefined);
});

test('invalid nonblank keys and collisions still reject rather than replace stable keys', async () => {
  for (const items of [
    [{ _id: '1', key: 123, isVisible: true }],
    [{ _id: '1', key: 'x'.repeat(257), isVisible: true }],
    [{ _id: '1', ...row('duplicate') }, { _id: '2', ...row('duplicate') }],
    [{ _id: '1', ...row('2') }, { _id: '2', key: '', isVisible: true }]
  ]) {
    const result = await backend({ DiTeachers: [{ totalCount: items.length, items }] }).get_danceContent(request('DiTeachers'));
    assert.equal(result.status, 503);
  }
});

test('Wix function rejects arbitrary collections, query overrides and unapproved origins', async () => {
  const api = backend({});
  assert.equal((await api.get_danceContent(request('Members/PrivateMembersData'))).status, 400);
  assert.equal((await api.get_danceContent(request('DiUnknown'))).status, 400);
  assert.equal((await api.get_danceContent({ ...request(), query: { collections: 'DiPageContent', filter: '{}' } })).status, 400);
  assert.equal((await api.get_danceContent(request('DiPageContent', 'https://unapproved.test'))).status, 403);
  assert.equal((await api.get_danceContent(request('DiPageContent', 'https://unverified.wixsite.com'))).status, 403);
  assert.equal(api.queryCount(), 0);
  const preflight = api.options_danceContent(request());
  assert.equal(preflight.status, 204);
  assert.equal(preflight.headers['Access-Control-Allow-Methods'], 'GET, OPTIONS');
  assert.equal(preflight.headers['Access-Control-Allow-Credentials'], undefined);
});

test('Wix function rejects inconsistent or repeated pagination instead of partial content', async () => {
  const scenarios = [
    [{ totalCount: 2, items: [{ _id: '1', ...row('a') }] }],
    [{ totalCount: 2, items: [{ _id: '1', ...row('a') }] }, { totalCount: 3, items: [{ _id: '2', ...row('b') }] }],
    [{ totalCount: 2, items: [{ _id: '1', ...row('a') }] }, { totalCount: 2, items: [{ _id: '1', ...row('a') }] }],
    [{ totalCount: 10001, items: [] }],
    [{ totalCount: 2, items: [] }, { totalCount: 2, items: [{ _id: '2', ...row('b') }] }]
  ];
  for (const pages of scenarios) {
    const result = await backend({ DiPageContent: pages }).get_danceContent(request());
    assert.equal(result.status, 503);
    assert.equal(JSON.parse(result.body).collections, undefined);
  }
});
