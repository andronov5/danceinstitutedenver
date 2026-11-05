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
  await check('Classes: add, hide and reorder categories with their own class rows', async () => {
    const doc = await load('dance-classes/index.html'), win = frame.contentWindow;
    const manifest = JSON.parse(doc.getElementById('dance-cms-bindings').textContent);
    const list = manifest.lists.find(item => item.collection === 'DiClassCategories');
    const edited = clone(seed);
    const hidden = edited.DiClassCategories[0];
    hidden.isVisible = false;
    edited.DiClassCategories.push({key:'qa-new-category',title:'QA New Category',sortOrder:-1,isVisible:true});
    edited.DiClasses.push({key:'qa-new-class',title:'QA Class',description:'A short description.',category:'qa-new-category',sortOrder:1,isVisible:true});
    edited.DiClasses.push({key:'qa-first-class',title:'QA First Class',description:'First class in its group.',category:'qa-new-category',sortOrder:0,isVisible:true});
    edited.DiClasses.push({key:'qa-hidden-class',title:'QA Hidden Class',category:'qa-new-category',isVisible:false});
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    const container = doc.querySelector(list.selector), first = container.firstElementChild;
    assert(first.querySelector('h2').textContent === 'QA New Category', 'New category was not ordered first');
    assert(first.open, 'New category did not start expanded');
    assert(![...container.querySelectorAll('h2')].some(node => node.textContent === hidden.title), 'Hidden category still appears');
    const classNames = [...first.querySelectorAll('h3')].map(node => node.textContent);
    assert(JSON.stringify(classNames) === JSON.stringify(['QA First Class','QA Class']), 'Nested classes did not retain category, order and visibility');
    assert(first.dataset.cmsItemCollection === 'DiClassCategories' && first.dataset.cmsItemKey === 'qa-new-category', 'Category lost its visual editor identity');
    assert(first.querySelector('[data-cms-item-key="qa-first-class"]').dataset.cmsItemCollection === 'DiClasses', 'Nested class lost its visual editor identity');
    assert(container.children[1].querySelectorAll('h3').length > 0, 'Existing category lost its classes');
  });
  await check('Classes: missing or duplicate nested content cannot partially alter the page', async () => {
    const doc = await load('dance-classes/index.html'), win = frame.contentWindow;
    const manifest = JSON.parse(doc.getElementById('dance-cms-bindings').textContent);
    const before = doc.documentElement.innerHTML;
    for (const missing of [true, false]) {
      const edited = clone(seed);
      if (missing) {
        edited.DiClassCategories.forEach(row => { row.isVisible = false; });
        delete edited.DiClasses;
      } else edited.DiClasses.push({...edited.DiClasses[0]});
      let threw = false;
      try { win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root); } catch (_) { threw = true; }
      assert(threw && doc.documentElement.innerHTML === before, 'Invalid nested content changed the document');
    }
  });
  await check('Head metadata and control labels update safely and atomically', async () => {
    const doc = await load('dance-classes/index.html'), win = frame.contentWindow;
    const record = (selector, fields) => ({selector, collection:'QaSettings', key:'settings', fields});
    const manifest = {lists:[],galleries:[],records:[
      record('head > title', [{selector:':scope',field:'title',kind:'text'}]),
      record('meta[name="description"]', [{selector:':scope',field:'description',kind:'attribute',attribute:'content'}]),
      record('[data-classes-toggle]', [
        {selector:':scope',field:'expand',kind:'attribute',attribute:'data-expand-label'},
        {selector:':scope',field:'collapse',kind:'attribute',attribute:'data-collapse-label'},
        {selector:':scope',field:'accessible',kind:'attribute',attribute:'aria-label'}
      ])
    ]};
    const data = {QaSettings:[{key:'settings',isVisible:true,title:'QA Class title',description:'QA Description',expand:'Open every group',collapse:'Close every group',accessible:'Class group controls'}]};
    win.DanceCMS.hydrate(doc, manifest, data, win.DanceWixCMS, root);
    assert(doc.title === 'QA Class title' && doc.querySelector('meta[name="description"]').content === 'QA Description', 'Head metadata failed to update');
    const toggle = doc.querySelector('[data-classes-toggle]');
    assert(toggle.dataset.expandLabel === 'Open every group' && toggle.dataset.collapseLabel === 'Close every group' && toggle.getAttribute('aria-label') === 'Class group controls', 'Control labels failed to update');
    const before = doc.documentElement.innerHTML;
    for (const attribute of ['onclick', 'srcdoc', 'href']) {
      const bad = clone(manifest);
      bad.records[2].fields.push({selector:':scope',field:'title',kind:'attribute',attribute});
      let threw = false;
      try { win.DanceCMS.hydrate(doc, bad, data, win.DanceWixCMS, root); } catch (_) { threw = true; }
      assert(threw && doc.documentElement.innerHTML === before, 'Unsafe attribute partly changed the page: ' + attribute);
    }
  });
  await check('Shared navigation updates desktop and mobile together', async () => {
    const doc = await load('index.html'), win = frame.contentWindow;
    const manifest = JSON.parse(doc.getElementById('dance-cms-bindings').textContent), edited = clone(seed);
    Object.assign(edited.DiLinks.find(row => row.key === 'navigation-contact'), {label:'QA Reach us',url:'@/contact/index.html?source=qa'});
    edited.DiPageContent.find(row => row.key === 'navigation-group-about').text = 'QA About DI';
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    for (const selector of ['.desktop-nav', '.mobile-menu']) {
      const links = [...doc.querySelectorAll(selector + ' a')].filter(node => node.textContent === 'QA Reach us');
      assert(links.length === 1 && links[0].href === new URL('contact/index.html?source=qa', root).href, selector + ' link was not updated');
      assert(doc.querySelector(selector).textContent.includes('QA About DI'), selector + ' group label was not updated');
    }
    assert(doc.querySelector('.mobile-menu').hidden, 'Hydration unexpectedly opened the mobile menu');
  });
  await check('Extra content adds safe text, photos and links in the chosen page only', async () => {
    const doc = await load('index.html'), win = frame.contentWindow;
    const manifest = JSON.parse(doc.getElementById('dance-cms-bindings').textContent), edited = clone(seed);
    const list = manifest.lists.find(row => row.collection === 'DiContentBlocks');
    const starter = edited.DiContentBlocks[0];
    const image = edited.DiImages.find(row => row.key === 'home-hero-photo').image;
    edited.DiContentBlocks.push({...starter,key:'qa-extra',page:'home',title:'QA Extra content',body:'<p>Extra <strong>copy</strong>.</p>',image,alt:'QA photograph',focalX:30,focalY:80,url:'https://example.com/photos',label:'QA Photos',isVisible:true,sortOrder:-2});
    edited.DiContentBlocks.push({...starter,key:'qa-unsafe-link',page:'home',title:'QA Unsafe link',url:'javascript:alert(1)',label:'Unsafe link',isVisible:true,sortOrder:-1});
    edited.DiContentBlocks.push({...starter,key:'qa-hidden',page:'home',title:'QA Hidden block',isVisible:false});
    edited.DiContentBlocks.push({...starter,key:'qa-other-page',page:'contact',title:'QA Other page',isVisible:true});
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    const container = doc.querySelector(list.selector), first = container.firstElementChild;
    assert(container.children.length === 2 && first.querySelector('h2').textContent === 'QA Extra content', 'Block ordering, page filter or visibility failed');
    assert(first.querySelector('strong').textContent === 'copy', 'Extra rich text did not render');
    const photo = first.querySelector('img');
    assert(!photo.hidden && photo.alt === 'QA photograph' && photo.style.objectPosition === '30% 80%', 'Extra photo or crop failed');
    assert(first.querySelector('a').href === 'https://example.com/photos' && first.querySelector('a').textContent === 'QA Photos', 'Extra link failed');
    const unsafe = container.lastElementChild.querySelector('a');
    assert(!unsafe.hasAttribute('href') && unsafe.getAttribute('aria-disabled') === 'true', 'Unsafe block URL survived');
  });
  await check('Section order preserves the default layout and unbound siblings', async () => {
    const doc = await load('index.html'), win = frame.contentWindow;
    const manifest = JSON.parse(doc.getElementById('dance-cms-bindings').textContent), edited = clone(seed);
    const sections = manifest.records.filter(row => row.collection === 'DiSections');
    const spacer = doc.createElement('aside');
    spacer.id = 'qa-unbound';
    doc.querySelector(sections[2].selector).before(spacer);
    const tokens = () => [...doc.querySelector('main').children].map(node => node.getAttribute('data-cms-target') || node.id || node.tagName);
    const original = tokens();
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    assert(JSON.stringify(tokens()) === JSON.stringify(original), 'Default section order changed');
    const bound = sections.map(row => doc.querySelector(row.selector).getAttribute('data-cms-target'));
    const reversed = bound.slice().reverse();
    sections.forEach((section, index) => { edited.DiSections.find(row => row.key === section.key).sortOrder = -index; });
    let cursor = 0;
    const expected = original.map(token => bound.includes(token) ? reversed[cursor++] : token);
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    assert(JSON.stringify(tokens()) === JSON.stringify(expected), 'Declared sections did not move around fixed unbound slots');
    const section = sections[2], row = edited.DiSections.find(item => item.key === section.key);
    row.isVisible = false;
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    assert(doc.querySelector(section.selector).hidden, 'Reordered section did not hide');
    assert(JSON.stringify(tokens()) === JSON.stringify(expected), 'Hiding a section changed unrelated positions');
    row.isVisible = true;
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    assert(!doc.querySelector(section.selector).hidden && JSON.stringify(tokens()) === JSON.stringify(expected), 'Hidden section did not restore in its selected order');
  });
  await check('Nested sections stay in their own layout group', async () => {
    const doc = await load('register/index.html'), win = frame.contentWindow;
    const manifest = JSON.parse(doc.getElementById('dance-cms-bindings').textContent), edited = clone(seed);
    edited.DiSections.find(row => row.key === 'register-membership-panel').sortOrder = -100;
    edited.DiSections.find(row => row.key === 'register-tuition-panel').sortOrder = 10000;
    const list = manifest.lists.find(row => row.collection === 'DiContentBlocks');
    edited.DiContentBlocks.push({...edited.DiContentBlocks[0],key:'qa-price-followup',page:'register',title:'QA Pricing note',afterSection:'register-discount-panel',isVisible:true});
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    assert(doc.querySelector('.registration-side').firstElementChild.classList.contains('membership-panel'), 'Nested card did not move within its own group');
    assert(doc.querySelector('.tuition-panel').parentElement.classList.contains('registration-prices'), 'Tuition moved outside its pricing grid');
    const prices = doc.querySelector('.registration-prices'), placed = prices.nextElementSibling;
    assert(placed.querySelector('[data-cms-item-key="qa-price-followup"]'), 'Pricing note did not follow the complete pricing group');
    assert(placed.classList.contains('section-shell') && !prices.querySelector('.cms-content-block'), 'Extra block broke the pricing grid');
    assert(!doc.querySelector(list.selector).querySelector('[data-cms-item-key="qa-price-followup"]'), 'Placed block also remained at the bottom');
  });
  await check('Extra block anchors support page flow, fallback, move, hide and restore', async () => {
    const doc = await load('shows-and-competition/nutcracker/index.html'), win = frame.contentWindow;
    const manifest = JSON.parse(doc.getElementById('dance-cms-bindings').textContent), edited = clone(seed);
    const list = manifest.lists.find(row => row.collection === 'DiContentBlocks');
    const block = {...edited.DiContentBlocks[0],key:'qa-placed',page:manifest.route,title:'QA Prep note',afterSection:manifest.route+'-nutcracker-prep',isVisible:true,sortOrder:0};
    edited.DiContentBlocks.push(block);
    edited.DiContentBlocks.push({...block,key:'qa-bottom',title:'QA Bottom note',afterSection:'unknown-section',sortOrder:1});
    const hydrate = () => win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    const placed = () => doc.querySelector('[data-cms-item-key="qa-placed"]');
    hydrate();
    let wrapper = placed().parentElement;
    assert(doc.querySelector('.nutcracker-prep').nextElementSibling === wrapper, 'Extra block did not follow its selected inner section');
    assert(wrapper.parentElement.classList.contains('section-shell') && !wrapper.classList.contains('section-shell'), 'Extra block gained nested page margins');
    assert(doc.querySelector(list.selector).querySelector('[data-cms-item-key="qa-bottom"]'), 'Unknown anchor did not fall back to the bottom');
    block.afterSection = manifest.route+'-nutcracker-rehearsals';
    hydrate();
    assert(doc.querySelector('.nutcracker-rehearsals').nextElementSibling === placed().parentElement, 'Extra block did not move to the new anchor');
    assert(doc.querySelectorAll('[data-cms-item-key="qa-placed"]').length === 1, 'Moving an extra block duplicated it');
    block.isVisible = false;
    hydrate();
    assert(!placed() && !doc.querySelector('[data-cms-extra-source]'), 'Hidden positioned block or empty wrapper remained');
    block.isVisible = true;
    hydrate();
    assert(placed() && doc.querySelectorAll('[data-cms-extra-source]').length === 1, 'Positioned block did not restore exactly once');
    block.afterSection = '';
    hydrate();
    assert(doc.querySelector(list.selector).firstElementChild === placed() && !doc.querySelector('[data-cms-extra-source]'), 'Blank anchor did not restore default bottom placement and order');
  });
  await check('Section visibility respects overlapping records and can be restored', async () => {
    const doc = await load('contact/index.html'), win = frame.contentWindow;
    const manifest = JSON.parse(doc.getElementById('dance-cms-bindings').textContent), edited = clone(seed);
    const section = edited.DiSections.find(row => row.key === 'contact-contact-introduction');
    const copy = edited.DiPageContent.find(row => row.key === 'contact-introduction');
    section.isVisible = false;
    copy.text = 'QA Contact introduction';
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    assert(doc.querySelector('.contact-introduction').hidden && !doc.querySelector('.contact-form-panel').hidden, 'Hiding one section affected other content');
    section.isVisible = true;
    copy.isVisible = false;
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    assert(doc.querySelector('.contact-introduction').hidden, 'Visible section overrode its hidden content record');
    copy.isVisible = true;
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    assert(!doc.querySelector('.contact-introduction').hidden && doc.querySelector('.contact-introduction').textContent === 'QA Contact introduction', 'Re-enabled section did not return');
    assert(doc.querySelector('.mobile-menu').hidden && [...doc.querySelectorAll('.nav-dropdown-menu')].every(node => node.hidden), 'Restoring content opened conditional navigation');
  });
  await check('Hiding a gallery section wins over its nonempty photo list', async () => {
    const doc = await load('shows-and-competition/nutcracker/index.html'), win = frame.contentWindow;
    const manifest = JSON.parse(doc.getElementById('dance-cms-bindings').textContent), edited = clone(seed);
    const section = edited.DiSections.find(row => row.key === 'shows-and-competition/nutcracker-nutcracker-gallery');
    section.isVisible = false;
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    assert(doc.querySelector('.nutcracker-gallery').hidden && !doc.querySelector('.nutcracker-shows').hidden, 'Gallery content overrode section visibility');
    section.isVisible = true;
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    assert(!doc.querySelector('.nutcracker-gallery').hidden, 'Gallery did not return after re-enabling');
  });
  await check('Legal sections support edited bodies, order and visibility', async () => {
    const doc = await load('privacy-policy/index.html'), win = frame.contentWindow;
    const manifest = JSON.parse(doc.getElementById('dance-cms-bindings').textContent), edited = clone(seed);
    const list = manifest.lists.find(row => row.collection === 'DiLegalSections');
    const hidden = edited.DiLegalSections.find(row => row.page === 'privacy-policy');
    hidden.isVisible = false;
    edited.DiLegalSections.push({key:'qa-legal',page:'privacy-policy',title:'QA Privacy section',body:'<p>Updated privacy information.</p><ul><li>QA Detail</li></ul>',isVisible:true,sortOrder:-1});
    edited.DiLegalSections.push({key:'qa-other-legal',page:'accessibility-statement',title:'QA Different page',body:'<p>Other page.</p>',isVisible:true,sortOrder:-2});
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    const container = doc.querySelector(list.selector), first = container.firstElementChild;
    assert(first.querySelector('h2').textContent === 'QA Privacy section', 'New legal section order failed');
    assert(first.querySelector('li').textContent === 'QA Detail' && first.querySelector('p').textContent === 'Updated privacy information.', 'Legal body did not render');
    assert(!container.textContent.includes(hidden.title) && !container.textContent.includes('QA Different page'), 'Legal visibility/page filtering failed');
  });
  await check('Contact labels, email feedback and page metadata are editable', async () => {
    const doc = await load('contact/index.html'), win = frame.contentWindow;
    const manifest = JSON.parse(doc.getElementById('dance-cms-bindings').textContent), edited = clone(seed);
    for (const [key, value] of [['contact-field-first','QA Given name'],['contact-submit-label','QA Prepare message'],['contact-data-feedback-message','QA Send your draft to {email}.'],['contact-data-subject','QA Studio inquiry']]) {
      edited.DiPageContent.find(row => row.key === key).text = value;
    }
    Object.assign(edited.DiPages.find(row => row.key === 'contact'), {title:'QA Contact | Dance Institute',description:'QA Contact description'});
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    const form = doc.querySelector('[data-contact-form]');
    assert(form.querySelector('label[for="contact-first"]').textContent === 'QA Given name*', 'Field wording or required marker was lost');
    assert(form.querySelector('button[type="submit"]').textContent.trim() === 'QA Prepare message' && form.querySelector('button[type="submit"] svg'), 'Submit wording or icon was lost');
    assert(form.dataset.feedbackMessage === 'QA Send your draft to {email}.' && form.dataset.subject === 'QA Studio inquiry', 'Email settings failed to update');
    assert(doc.title === 'QA Contact | Dance Institute' && doc.querySelector('meta[name="description"]').content === 'QA Contact description', 'Contact metadata did not update');
    const photo = edited.DiImages.find(row => row.key === 'contact-photo'), originalImage = photo.image;
    photo.image = '';
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    assert(doc.querySelector('.contact-photo').hidden, 'An empty contact photo remained visible');
    photo.image = originalImage;
    win.DanceCMS.hydrate(doc, manifest, edited, win.DanceWixCMS, root);
    assert(!doc.querySelector('.contact-photo').hidden, 'Restoring a contact photo left it hidden');
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
