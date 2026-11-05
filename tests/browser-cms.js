/* Internal-only DOM integration fixture; copied to dist/cms-qa for QA, never shipped. */
(async () => {
  'use strict';
  const root = new URL('../', location.href).href;
  const frame = document.getElementById('page');
  const results = document.getElementById('results');
  const summary = document.getElementById('summary');
  let passed = 0, failed = 0;
  const report = (name, error) => {
    const line = document.createElement('li');
    line.className = error ? 'fail' : 'pass';
    line.textContent = `${error ? 'FAIL' : 'PASS'} — ${name}${error ? ': ' + error.message : ''}`;
    results.appendChild(line);
    if (error) failed++; else passed++;
    summary.textContent = `${passed} passed · ${failed} failed`;
    summary.dataset.finished = 'false';
  };
  const check = async (name, callback) => { try { await callback(); report(name); } catch (error) { report(name, error); } };
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const clone = value => JSON.parse(JSON.stringify(value));
  const load = route => new Promise((resolve, reject) => {
    const expected = new URL(route, root).href;
    let finishing = false;
    const timer = setTimeout(() => { clearInterval(poll); reject(new Error('Page load timed out: ' + route)); }, 15000);
    const poll = setInterval(async () => {
      const doc = frame.contentDocument;
      if (finishing || !doc || doc.URL !== expected || doc.readyState === 'loading' || !frame.contentWindow.DanceCMS) return;
      finishing = true;
      clearInterval(poll);
      try { await frame.contentWindow.siteContentReady; clearTimeout(timer); resolve(doc); }
      catch (error) { clearTimeout(timer); reject(error); }
    }, 50);
    frame.src = expected;
  });
  let seed;
  try {
    const response = await fetch(new URL('seed.json', location.href));
    if (!response.ok) throw new Error('Seed fixture not found');
    const payload = await response.json();
    seed = payload.collections || payload;
  } catch (error) { report('Load CMS seeds', error); summary.dataset.finished = 'true'; return; }
  const routes = ['index.html', 'dance-classes/index.html', 'about/teachers/index.html', 'about/studio-policies/index.html', 'schedule/index.html', 'shows-and-competition/nutcracker/index.html', 'shows-and-competition/competition/index.html', 'shows-and-competition/recital/index.html', 'summer-intensive/index.html', 'register/index.html', 'contact/index.html', 'privacy-policy/index.html', 'accessibility-statement/index.html'];
  for (const route of routes) {
    await check('Baseline CMS hydration: ' + route, async () => {
      const doc = await load(route);
      const win = frame.contentWindow;
      const marker = doc.getElementById('dance-cms-bindings');
      assert(marker, 'Binding manifest absent');
      const manifest = JSON.parse(marker.textContent);
      const result = win.DanceCMS.hydrate(doc, manifest, clone(seed), win.DanceWixCMS, root);
      assert(result.status === 'connected', 'Hydration did not complete');
      const ids = [...doc.querySelectorAll('[id]')].map(node => node.id);
      assert(ids.length === new Set(ids).size, 'Duplicate DOM IDs after CMS hydration');
      for (const list of manifest.lists) {
        const expected = win.DanceCMS.visibleRows(seed[list.collection], list.filter);
        const container = doc.querySelector(list.selector);
        assert(container.children.length === expected.length, `${list.collection}: expected ${expected.length} rows, got ${container.children.length}`);
      }
      for (const gallery of manifest.galleries) {
        const container = doc.querySelector(gallery.selector);
        const photos = JSON.parse(container.querySelector('[data-gallery-items]').textContent);
        const expected = seed[gallery.collection].filter(row => row.isVisible && row.gallery === gallery.group);
        assert(photos.length === expected.length, 'Gallery item count mismatch');
        if (photos.length) assert(container.querySelector('[data-show-stage-image]').src === photos[0].src, 'Gallery first image mismatch');
      }
      const edited = clone(seed);
      const globalPhone = manifest.records.find(entry => entry.fields.some(field => field.kind === 'phoneHref'));
      if (globalPhone) {
        const value = edited[globalPhone.collection].find(row => row.key === globalPhone.key);
        const phoneField = globalPhone.fields.find(field => field.kind === 'phoneHref');
        value[phoneField.field] = '303-555-0199';
        win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
        const parent = doc.querySelector(globalPhone.selector);
        const target = phoneField.selector === ':scope' ? parent : parent.querySelector(phoneField.selector);
        assert(target.getAttribute('href') === 'tel:3035550199', 'Shared phone did not update');
      }
      // Failure is atomic: an unavailable collection must never clear the page.
      const before = doc.body.innerHTML;
      const unavailable = clone(seed);
      delete unavailable[manifest.records[0].collection];
      let threw = false;
      try { win.DanceCMS.hydrate(doc, manifest, unavailable, win.DanceWixCMS, root); } catch (_) { threw = true; }
      assert(threw && doc.body.innerHTML === before, 'Incomplete content changed the page');
    });
  }
  await check('Teachers: add, hide, reorder, images and biography', async () => {
    const doc = await load('about/teachers/index.html'), win = frame.contentWindow;
    const manifest = JSON.parse(doc.getElementById('dance-cms-bindings').textContent);
    const list = manifest.lists.find(item => item.collection === 'DiTeachers');
    const edited = clone(seed);
    edited.DiTeachers[0].isVisible = false;
    edited.DiTeachers.push({ ...edited.DiTeachers[0], key:'qa-new-teacher', name:'QA Teacher', bio:'<p>A new biography.</p>', isVisible:true, sortOrder:-1 });
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    const container = doc.querySelector(list.selector);
    assert(container.firstElementChild.querySelector('h2').textContent === 'QA Teacher', 'New teacher was not ordered first');
    assert(!container.textContent.includes(edited.DiTeachers[0].name), 'Hidden teacher is still displayed');
    assert(container.firstElementChild.textContent.includes('A new biography.'), 'New biography missing');
  });
  await check('Classes: add a class to the chosen category', async () => {
    const doc = await load('dance-classes/index.html'), win = frame.contentWindow;
    const manifest = JSON.parse(doc.getElementById('dance-cms-bindings').textContent);
    const list = manifest.lists.find(item => item.collection === 'DiClasses');
    const edited = clone(seed);
    edited.DiClasses.push({key:'qa-new-class',title:'QA Class',description:'A short description.',category:list.filter.category,sortOrder:-1,isVisible:true});
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    assert(doc.querySelector(list.selector).firstElementChild.textContent.includes('QA Class'), 'Class was not added to its category');
  });
  await check('Competition gallery: reorder, hide and add photos', async () => {
    const doc = await load('shows-and-competition/competition/index.html'), win = frame.contentWindow;
    const manifest = JSON.parse(doc.getElementById('dance-cms-bindings').textContent);
    const gallery = manifest.galleries[0], edited = clone(seed);
    const original = edited.DiGalleryPhotos.find(row => row.gallery === gallery.group);
    original.isVisible = false;
    edited.DiGalleryPhotos.push({...original,key:'qa-new-gallery-photo',alt:'QA New photograph',isVisible:true,sortOrder:-1,focalX:20,focalY:80});
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    const container = doc.querySelector(gallery.selector);
    const photos = JSON.parse(container.querySelector('[data-gallery-items]').textContent);
    assert(photos[0].alt === 'QA New photograph' && photos[0].position === '20% 80%', 'New gallery image/order/crop missing');
    assert(!photos.some(row => row.alt === original.alt), 'Hidden gallery photo remains');
  });
  await check('Recital: empty optional copy and link can be filled', async () => {
    const doc = await load('shows-and-competition/recital/index.html'), win = frame.contentWindow;
    const manifest = JSON.parse(doc.getElementById('dance-cms-bindings').textContent);
    const edited = clone(seed);
    const bodyEntry = manifest.records.find(entry => entry.key === 'recital-information');
    edited[bodyEntry.collection].find(row => row.key === bodyEntry.key).body = '<p>QA Recital information</p>';
    const linkEntry = manifest.records.find(entry => entry.key === 'recital-information-link');
    Object.assign(edited[linkEntry.collection].find(row => row.key === linkEntry.key), {url:'https://example.com/tickets',label:'QA Tickets'});
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    assert(!doc.querySelector(bodyEntry.selector).hidden && doc.querySelector(bodyEntry.selector).textContent.includes('QA Recital information'), 'Optional recital copy remained hidden');
    assert(!doc.querySelector(linkEntry.selector).hidden && doc.querySelector(linkEntry.selector).href === 'https://example.com/tickets', 'Optional recital link remained hidden');
  });
  await check('Rich text removes executable markup and links', async () => {
    const doc = await load('index.html'), win = frame.contentWindow;
    const manifest = JSON.parse(doc.getElementById('dance-cms-bindings').textContent);
    const entry = manifest.records.find(item => item.fields.some(field => field.kind === 'rich'));
    assert(entry, 'No rich-text binding to test');
    const field = entry.fields.find(item => item.kind === 'rich'), edited = clone(seed);
    edited[entry.collection].find(row => row.key === entry.key)[field.field] = '<p onclick="window.CMS_XSS=1"><strong>QA Safe</strong><script>window.CMS_XSS=1</script><img src=x onerror="window.CMS_XSS=1"><svg onload="window.CMS_XSS=1"></svg><a href="javascript:alert(1)">bad link</a><a href="https://example.com">safe link</a></p>';
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    const rootNode = doc.querySelector(entry.selector);
    const target = field.selector === ':scope' ? rootNode : rootNode.querySelector(field.selector);
    assert(!target.querySelector('script,img,svg,[onclick],[onerror],a[href^="javascript:"]'), 'Unsafe rich HTML survived');
    assert(target.querySelector('strong').textContent === 'QA Safe', 'Safe formatting lost');
    assert(!win.CMS_XSS, 'Unsafe markup executed');
  });
  await check('Rich text paragraphs flatten safely inside headings and paragraphs', async () => {
    const win = frame.contentWindow, doc = frame.contentDocument;
    const fragment = win.DanceCMS.sanitizeHtml(doc, '<p>First <strong>line</strong></p><p>Second line</p><ul><li>Third line</li><li>Fourth line</li></ul>', root, doc.URL, true);
    const paragraph = doc.createElement('p'); paragraph.appendChild(fragment);
    assert(!paragraph.querySelector('p,ul,ol,li'), 'Block markup remained in an inline container');
    assert(paragraph.querySelectorAll('br').length === 3, 'Paragraph/list separation was not preserved');
    assert(paragraph.querySelector('strong').textContent === 'line', 'Inline formatting lost');
  });
  summary.textContent = `${passed} passed · ${failed} failed — finished`;
  summary.className = failed ? 'fail' : 'pass';
  summary.dataset.finished = 'true';
  document.title = `${failed ? 'FAIL' : 'PASS'} CMS checks: ${passed}/${passed + failed}`;
})();
