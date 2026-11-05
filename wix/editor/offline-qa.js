/* Developer-only detached DOM fixture. No Wix CMS/API calls or live writes. */
import { EDITOR_PREVIEWS } from '../public/editor-previews.js';

const results = document.getElementById('results');
const summary = document.getElementById('summary');
const cms = window.EditorCMS;
const adapter = window.EditorAdapter;
let passed = 0, failed = 0;
function assert(value, message) { if (!value) throw new Error(message); }
function check(name, action) {
  const node = document.createElement('li');
  try { action(); passed++; node.className = 'pass'; node.textContent = 'PASS — ' + name; }
  catch (error) { failed++; node.className = 'fail'; node.textContent = 'FAIL — ' + name + ': ' + error.message; }
  results.appendChild(node);
  summary.textContent = passed + ' passed · ' + failed + ' failed';
}
const clone = value => JSON.parse(JSON.stringify(value));
try {
  const [modelResponse, seedResponse] = await Promise.all([fetch('./model.json'), fetch('../../cms/seed.json')]);
  assert(modelResponse.ok && seedResponse.ok, 'Local fixtures unavailable; serve the repository root');
  const model = await modelResponse.json();
  const seed = (await seedResponse.json()).collections;
  const base = model.siteUrl.replace(/\/$/, '') + '/';
  function page(id) {
    const doc = new DOMParser().parseFromString(EDITOR_PREVIEWS.pages[id], 'text/html');
    const manifest = JSON.parse(doc.getElementById('dance-cms-bindings').textContent);
    return { doc, manifest, hydrate: values => cms.hydrate(doc, manifest, values, adapter, base) };
  }
  for (const entry of model.pages) check(entry.title + ': hydrate current preview and edit shared contact', () => {
    const { doc, manifest, hydrate } = page(entry.id);
    const values = clone(seed);
    const result = hydrate(values);
    assert(result.status === 'connected', 'Hydration failed');
    assert(!doc.querySelector('script:not([type="application/json"]),link[rel="stylesheet"]'), 'Unbundled executable resource');
    const ids = [...doc.querySelectorAll('[id]')].map(node => node.id);
    assert(ids.length === new Set(ids).size, 'Duplicate DOM IDs');
    for (const list of manifest.lists) {
      const count = cms.visibleRows(values[list.collection], list.filter).length;
      const items = doc.querySelectorAll('[data-cms-item-collection="' + list.collection + '"]');
      if (list.collection === 'DiContentBlocks') assert(items.length === count, 'Added block count mismatch');
      else assert(doc.querySelector(list.selector).children.length === count, list.collection + ' count mismatch');
    }
    for (const gallery of manifest.galleries) {
      const target = doc.querySelector(gallery.selector);
      const photos = JSON.parse(target.querySelector('[data-gallery-items]').textContent);
      assert(photos.length === cms.visibleRows(values[gallery.collection], { gallery: gallery.group }).length, 'Gallery count mismatch');
    }
    values.DiStudio[0].phone = '303-555-0199'; hydrate(values);
    assert(doc.querySelector('a[href="tel:3035550199"]'), 'Shared phone edit not reflected');
  });
  check('Page text: draft content replaces fallback text', () => {
    const { doc, manifest, hydrate } = page('home'); const values = clone(seed);
    const entry = manifest.records.find(record => record.key === 'home-hero-subtitle');
    values.DiPageContent.find(row => row.key === entry.key).text = 'Offline draft preview'; hydrate(values);
    assert(doc.querySelector(entry.selector).textContent === 'Offline draft preview', 'Draft not visible');
  });
  check('Schedule: weekly row change, addition and hiding remain tabular', () => {
    const { doc, manifest, hydrate } = page('schedule'); const values = clone(seed);
    const list = manifest.lists.find(item => item.collection === 'DiSchedule');
    values.DiSchedule[0].isVisible = false;
    const row = { ...values.DiSchedule[1], key: 'offline-new-schedule', title: 'Offline class', monday: '8:45 AM', isVisible: true, sortOrder: -1 };
    values.DiSchedule.push(row); hydrate(values);
    const target = doc.querySelector(list.selector);
    assert(target.firstElementChild.tagName === 'TR', 'Schedule lost table rows');
    assert(target.firstElementChild.textContent.includes('8:45 AM'), 'New Monday time missing');
  });
  check('Gallery: hidden image removed, replacement image and crop reorder first', () => {
    const { doc, manifest, hydrate } = page('competition'); const values = clone(seed);
    const entry = manifest.galleries[0]; const rows = values.DiGalleryPhotos.filter(row => row.gallery === entry.group);
    assert(rows.length > 1, 'Gallery fixture needs two photos'); rows[0].isVisible = false;
    Object.assign(rows[1], { image: 'wix:image://v1/offline_test.webp/image.webp', alt: 'Offline replacement', focalX: 20, focalY: 80, sortOrder: -1 }); hydrate(values);
    const target = doc.querySelector(entry.selector); const data = JSON.parse(target.querySelector('[data-gallery-items]').textContent);
    assert(data[0].src === 'https://static.wixstatic.com/media/offline_test.webp', 'Wix image not converted');
    assert(data[0].position === '20% 80%' && data[0].alt === 'Offline replacement', 'Crop/alt lost');
    assert(data.length === rows.filter(row => row.isVisible).length, 'Hidden image still included');
  });
  check('New section: add below selected section, then hide without duplication', () => {
    const { doc, manifest, hydrate } = page('home'); const values = clone(seed);
    const group = model.pages.find(item => item.id === 'home').groups.find(item => item.placementKey && item.id !== 'hero');
    values.DiContentBlocks.push({ key: 'offline-added', page: 'home', title: 'Offline new section', body: '<p>New section body.</p>', image: '', afterSection: group.placementKey, isVisible: true, sortOrder: 500 }); hydrate(values);
    const entry = manifest.records.find(record => record.collection === 'DiSections' && record.key === group.placementKey);
    const anchor = doc.querySelector(entry.placementSelector || entry.selector);
    assert(anchor.nextElementSibling.textContent.includes('Offline new section'), 'Block placement failed');
    values.DiContentBlocks.at(-1).isVisible = false; hydrate(values);
    assert(!doc.body.textContent.includes('Offline new section'), 'Hidden added block remains');
  });
  check('Fixed sections reorder within the permitted parent', () => {
    const { doc, hydrate } = page('home'); const values = clone(seed);
    const group = model.pages.find(item => item.id === 'home').sectionGroups[0];
    group.keys.forEach((key, index) => { values.DiSections.find(row => row.key === key).sortOrder = group.keys.length - index; }); hydrate(values);
    const parent = doc.querySelector(group.parentSelector);
    const nodes = group.items.map(item => doc.querySelector(item.selector));
    const present = [...parent.children].filter(node => nodes.includes(node));
    assert(present[0] === nodes.at(-1) && present.at(-1) === nodes[0], 'Sections did not reverse');
  });
  check('Incomplete content fails atomically without clearing the preview', () => {
    const { doc, hydrate } = page('home'); const before = doc.documentElement.innerHTML; const values = clone(seed); delete values.DiStudio;
    let rejected = false; try { hydrate(values); } catch { rejected = true; }
    assert(rejected && before === doc.documentElement.innerHTML, 'Failure modified the preview');
  });
} catch (error) { check('Load local fixture', () => { throw error; }); }
summary.dataset.finished = 'true';
summary.dataset.passed = String(passed);
summary.dataset.failed = String(failed);
