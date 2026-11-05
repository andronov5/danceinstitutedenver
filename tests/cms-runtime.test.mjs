import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const cms = require('../assets/cms.js');
const base = 'https://example.com/studio/';
const current = base + 'about/teachers/index.html';

test('safe links keep internal routing and supported external protocols', () => {
  assert.equal(cms.safeUrl('@/register/index.html', base, current), base + 'register/index.html');
  assert.equal(cms.safeUrl('#main', base, current), current + '#main');
  assert.equal(cms.safeUrl('https://www.hisawyer.com/dance-institute-denver', base), 'https://www.hisawyer.com/dance-institute-denver');
  assert.equal(cms.safeUrl('tel:3035250011', base), 'tel:3035250011');
});
test('unsafe and origin-escaping links are discarded', () => {
  for (const value of ['javascript:alert(1)', 'data:text/html,foo', 'http://evil.test', '//evil.test', '@/../../admin', 'https://user:pass@evil.test', '\\evil.test', 'java\nscript:alert(1)']) {
    assert.equal(cms.safeUrl(value, base, current), '', value);
  }
});
test('contact helpers validate recipients and encode map destinations', () => {
  assert.equal(cms.phoneHref('(303) 525-0011'), 'tel:3035250011');
  assert.equal(cms.phoneHref('123;foo'), '');
  assert.equal(cms.emailHref('dance@example.com'), 'mailto:dance@example.com');
  assert.equal(cms.emailHref('dance@example.com?bcc=other@example.com'), '');
  assert.equal(cms.mapHref('10515 E 40th Ave\n#114\nDenver, CO 80239'), 'https://www.google.com/maps/search/?api=1&query=10515%20E%2040th%20Ave%20%23114%20Denver%2C%20CO%2080239');
});
test('Sawyer embeds cannot become arbitrary remote pages', () => {
  assert.equal(cms.sawyerUrl('https://www.hisawyer.com/dance-institute-denver/schedules/membership-plans'), 'https://www.hisawyer.com/dance-institute-denver/schedules/membership-plans');
  for (const url of ['https://hisawyer.com.evil.test/x', 'javascript:alert(1)', 'http://hisawyer.com/x', 'https://user@hisawyer.com/x']) assert.equal(cms.sawyerUrl(url), '');
});
test('public rows honor visibility, category and stable ordering', () => {
  const rows = [
    { key: 'late', isVisible: true, category: 'ballet', sortOrder: 3 },
    { key: 'hidden', isVisible: false, category: 'ballet', sortOrder: 0 },
    { key: 'first', isVisible: true, category: 'ballet', sortOrder: 1 },
    { key: 'other', isVisible: true, category: 'tap', sortOrder: 0 }
  ];
  assert.deepEqual(cms.visibleRows(rows, {category:'ballet'}).map(row => row.key), ['first','late']);
  assert.equal(rows[0].key, 'late');
  assert.deepEqual(cms.visibleRows([], null), []);
});
test('missing collections and ambiguous visible keys reject the transaction', () => {
  assert.throws(() => cms.visibleRows(undefined));
  assert.throws(() => cms.visibleRows([{isVisible:true,key:'same'},{isVisible:true,key:'same'}]));
  assert.throws(() => cms.visibleRows([null]));
});
test('CMS requests collections used by nested lists exactly once', () => {
  const manifest = {records:[{collection:'DiPageContent'}], galleries:[], lists:[{
    collection:'DiClassCategories', children:[{
      collection:'DiClasses', match:{field:'category',parentField:'key'}
    }]
  }, {collection:'DiClasses'}]};
  assert.deepEqual(cms.contentCollections(manifest), ['DiPageContent','DiClassCategories','DiClasses']);
});
test('invalid nested relationships and excessive depth are rejected before hydration', () => {
  const manifest = child => ({records:[],galleries:[],lists:[{collection:'Parent',children:[child]}]});
  assert.throws(() => cms.contentCollections(manifest({collection:'Child'})), /relationship/);
  assert.throws(() => cms.contentCollections(manifest({collection:'Child',match:{field:'category'}})), /relationship/);
  const entry = {collection:'Child',match:{field:'category',parentField:'key'}};
  entry.children = [entry];
  assert.throws(() => cms.contentCollections(manifest(entry)), /collection binding/);
});
test('image focal coordinates are constrained', () => {
  assert.equal(cms.coordinate(120), 100);
  assert.equal(cms.coordinate(-10), 0);
  assert.equal(cms.coordinate(72), 72);
  assert.equal(cms.coordinate('72'), null);
  assert.equal(cms.coordinate(Infinity), null);
});
test('section order moves only sortable sections and leaves unknown slots fixed', () => {
  const hero = { name:'hero', row:{sortOrder:30} };
  const missing = { name:'missing' };
  const about = { name:'about', row:{sortOrder:10} };
  const hidden = { name:'hidden', row:null };
  const reviews = { name:'reviews', row:{sortOrder:20} };
  const input = [hero,missing,about,hidden,reviews];
  assert.deepEqual(cms.orderedSectionSlots(input).map(item => item.name), ['about','missing','reviews','hidden','hero']);
  assert.deepEqual(input.map(item => item.name), ['hero','missing','about','hidden','reviews']);
});
test('default, absent and tied section ordering preserves existing layout', () => {
  const entries = [{row:{sortOrder:0}}, {row:{sortOrder:1}}, {row:{sortOrder:1}}, {}, {row:{sortOrder:'-9'}}];
  assert.deepEqual(cms.orderedSectionSlots(entries), entries);
  assert.deepEqual(cms.orderedSectionSlots([]), []);
});
test('CMS is inert when a page has no binding manifest', async () => {
  assert.deepEqual(await cms.start({getElementById: () => null}, {}, base), {status:'bundled'});
});
test('disabled configuration leaves the bundled page alone', async () => {
  const doc = {getElementById: () => ({textContent: 'not-parsed-when-disabled'})};
  const adapter = {loadCollections: () => {throw new Error('should not load');}};
  assert.deepEqual(await cms.start(doc, adapter, base, {fetchImpl: async () => ({ok:true,json:async()=>({enabled:false})})}), {status:'bundled'});
});
test('configuration failure keeps bundled content', async () => {
  const doc = {getElementById: () => ({textContent:'{}'})};
  assert.deepEqual(await cms.start(doc, {}, base, {fetchImpl:async()=>({ok:false})}), {status:'fallback'});
});
