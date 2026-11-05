/* Hydrate the existing design from public Wix content. The bundled HTML is the fallback. */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else {
    root.DanceCMS = api;
    var script = document.currentScript;
    var base = new URL('../', script.src).href;
    root.siteContentReady = api.start(document, root.DanceWixCMS, base);
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  var own = Function.call.bind(Object.prototype.hasOwnProperty);
  var MAX_TEXT = 100000;
  var EDITABLE_ATTRIBUTES = new Set(['datetime', 'aria-label', 'placeholder', 'content',
    'data-expand-label', 'data-collapse-label', 'data-feedback-message',
    'data-subject', 'data-open-label', 'data-close-label']);
  function text(value) {
    if (value === null || value === undefined) return '';
    if (typeof value !== 'string' && typeof value !== 'number' && typeof value !== 'boolean') throw new Error('Invalid CMS field value');
    var result = String(value);
    if (result.length > MAX_TEXT) throw new Error('CMS field is too large');
    return result;
  }
  function safeUrl(value, base, current) {
    value = text(value).trim();
    if (!value || /[\u0000-\u001f\u007f\\]/.test(value)) return '';
    if (/^(?:mailto|tel):/i.test(value)) {
      return /^[^<>"']+$/.test(value) ? value : '';
    }
    try {
      var target;
      if (value.startsWith('@/')) target = new URL(value.slice(2), base);
      else if (/^https:\/\//i.test(value)) target = new URL(value);
      else if (/^[a-z][a-z0-9+.-]*:/i.test(value) || value.startsWith('//')) return '';
      else target = new URL(value, current || base);
      var site = new URL(base);
      if (target.username || target.password) return '';
      if (!/^https:\/\//i.test(value)) {
        if (target.origin !== site.origin || !target.pathname.startsWith(site.pathname)) return '';
      } else if (target.protocol !== 'https:') return '';
      return target.href;
    } catch (_) { return ''; }
  }
  function phoneHref(value) {
    var cleaned = text(value).replace(/[()\s.\-]/g, '');
    return /^\+?\d{7,15}$/.test(cleaned) ? 'tel:' + cleaned : '';
  }
  function emailHref(value) {
    var address = text(value).trim();
    return /^[^\s<>"'@?&#]+@[^\s<>"'@?&#]+\.[^\s<>"'@?&#]+$/.test(address) ? 'mailto:' + address : '';
  }
  function mapHref(value) {
    var address = text(value).trim();
    return address ? 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(address.replace(/\s+/g, ' ')) : '';
  }
  function sawyerUrl(value) {
    try {
      var url = new URL(text(value));
      return url.protocol === 'https:' && /^(?:www\.)?hisawyer\.com$/.test(url.hostname) && !url.username && !url.password ? url.href : '';
    } catch (_) { return ''; }
  }
  function coordinate(value) {
    return typeof value === 'number' && Number.isFinite(value) ? Math.max(0, Math.min(100, value)) : null;
  }
  function imageUrl(value, adapter, base) {
    var source = adapter.imageUrl(value);
    if (!source) return '';
    if (source.startsWith('https://')) return source;
    source = source.replace(/^(?:\.\.\/|\.\/|\/)+/, '');
    return /^assets\/images\//.test(source) ? new URL(source, base).href : '';
  }
  function visibleRows(rows, filter) {
    if (!Array.isArray(rows)) throw new Error('Missing CMS collection');
    var keys = new Set();
    return rows.filter(function (row) {
      if (!row || typeof row !== 'object' || Array.isArray(row)) throw new Error('Invalid CMS item');
      if (row.isVisible !== true) return false;
      if (typeof row.key !== 'string' || !row.key || keys.has(row.key)) throw new Error('Invalid or duplicate CMS key');
      keys.add(row.key);
      return !filter || Object.keys(filter).every(function (key) { return row[key] === filter[key]; });
    }).sort(function (a, b) {
      var orderA = Number.isFinite(a.sortOrder) ? a.sortOrder : 0;
      var orderB = Number.isFinite(b.sortOrder) ? b.sortOrder : 0;
      return orderA - orderB;
    });
  }
  function contentCollections(manifest) {
    if (!manifest || !Array.isArray(manifest.records) || !Array.isArray(manifest.lists) || !Array.isArray(manifest.galleries)) throw new Error('Invalid CMS binding manifest');
    var names = new Set();
    function collect(entry, depth) {
      if (!entry || typeof entry.collection !== 'string' || !entry.collection || depth > 4) throw new Error('Invalid CMS collection binding');
      names.add(entry.collection);
      if (entry.children !== undefined) {
        if (!Array.isArray(entry.children)) throw new Error('Invalid nested CMS lists');
        entry.children.forEach(function (child) {
          if (!child.match || typeof child.match.field !== 'string' || typeof child.match.parentField !== 'string') throw new Error('Missing nested CMS relationship');
          collect(child, depth + 1);
        });
      }
    }
    manifest.records.concat(manifest.lists, manifest.galleries).forEach(function (entry) { collect(entry, 0); });
    return Array.from(names);
  }
  function sanitizeHtml(document, value, base, current, inlineOnly) {
    var template = document.createElement('template');
    template.innerHTML = text(value);
    var result = document.createDocumentFragment();
    var allowed = new Set(['P', 'BR', 'STRONG', 'B', 'EM', 'I', 'U', 'UL', 'OL', 'LI', 'A']);
    var blocks = new Set(['P', 'UL', 'OL', 'LI']);
    var discard = new Set(['SCRIPT', 'STYLE', 'IFRAME', 'OBJECT', 'EMBED', 'SVG', 'MATH', 'FORM', 'INPUT', 'BUTTON', 'TEXTAREA', 'SELECT', 'TEMPLATE', 'LINK', 'META', 'BASE', 'AUDIO', 'VIDEO']);
    function copy(node, destination) {
      if (node.nodeType === 3) { destination.appendChild(document.createTextNode(node.textContent)); return; }
      if (node.nodeType !== 1) return;
      var tag = node.tagName.toUpperCase();
      if (discard.has(tag)) return;
      if (inlineOnly && blocks.has(tag)) {
        if (destination.lastChild && destination.lastChild.nodeName !== 'BR') destination.appendChild(document.createElement('br'));
        Array.from(node.childNodes).forEach(function (child) { copy(child, destination); });
        if (destination.lastChild && destination.lastChild.nodeName !== 'BR') destination.appendChild(document.createElement('br'));
        return;
      }
      var target = destination;
      if (allowed.has(tag)) {
        target = document.createElement(tag.toLowerCase());
        if (tag === 'A') {
          var href = safeUrl(node.getAttribute('href') || '', base, current);
          if (href) target.setAttribute('href', href);
          if (node.getAttribute('target') === '_blank') { target.setAttribute('target', '_blank'); target.setAttribute('rel', 'noopener noreferrer'); }
        }
        destination.appendChild(target);
      }
      Array.from(node.childNodes).forEach(function (child) { copy(child, target); });
    }
    Array.from(template.content.childNodes).forEach(function (node) { copy(node, result); });
    if (inlineOnly) {
      while (result.firstChild && result.firstChild.nodeName === 'BR') result.firstChild.remove();
      while (result.lastChild && result.lastChild.nodeName === 'BR') result.lastChild.remove();
    }
    return result;
  }
  function targets(root, selector) {
    if (selector === ':scope' || !selector) return [root];
    return Array.from(root.querySelectorAll(selector));
  }
  function uniqueIds(root, suffix) {
    var idMap = new Map();
    [root].concat(Array.from(root.querySelectorAll('[id]'))).forEach(function (node) {
      if (!node.id) return;
      var old = node.id;
      node.id = old + '-' + suffix;
      idMap.set(old, node.id);
    });
    [root].concat(Array.from(root.querySelectorAll('*'))).forEach(function (node) {
      ['aria-labelledby', 'aria-describedby', 'aria-controls', 'for'].forEach(function (attribute) {
        if (!node.hasAttribute(attribute)) return;
        node.setAttribute(attribute, node.getAttribute(attribute).split(/\s+/).map(function (id) { return idMap.get(id) || id; }).join(' '));
      });
      var href = node.getAttribute('href');
      if (href && href[0] === '#' && idMap.has(href.slice(1))) node.setAttribute('href', '#' + idMap.get(href.slice(1)));
      node.removeAttribute('data-cms-target');
    });
  }
  function applyFields(root, row, fields, context) {
    fields.forEach(function (field) {
      var matches = targets(root, field.selector);
      if (!matches.length) throw new Error('CMS template target is missing: ' + field.selector);
      var value = own(row, field.field) ? row[field.field] : '';
      var string = field.kind === 'image' ? '' : text(value);
      var isEmpty = field.kind === 'image' ? !context.adapter.imageUrl(value) : !string.trim();
      matches.forEach(function (node) {
        var emptyTarget = field.emptyTarget ? targets(root, field.emptyTarget)[0] : node;
        if (field.hideIfEmpty) node.hidden = isEmpty;
        if (field.emptyClass && emptyTarget) emptyTarget.classList.toggle(field.emptyClass, isEmpty);
        if (field.toggleClass) targets(root, field.toggleTarget || field.selector).forEach(function (target) { target.classList.toggle(field.toggleClass, !isEmpty); });
        var kind = field.kind || 'text';
        if (kind === 'text') node.textContent = string + (string ? field.suffix || '' : '');
        else if (kind === 'rich') node.replaceChildren(sanitizeHtml(context.document, string, context.base, context.current, /^(?:P|H[1-6]|SPAN)$/.test(node.tagName)));
        else if (kind === 'addressLines') {
          var lines = string.split(/\r?\n/);
          node.replaceChildren();
          lines.forEach(function (line, index) { if (index) node.appendChild(context.document.createElement('br')); node.appendChild(context.document.createTextNode(line)); });
        } else if (kind === 'addressInline') node.textContent = string.replace(/\s*\r?\n\s*/g, ' · ');
        else if (kind === 'attribute') {
          if (!EDITABLE_ATTRIBUTES.has(field.attribute)) throw new Error('Unsupported CMS attribute');
          if (string) node.setAttribute(field.attribute, string); else node.removeAttribute(field.attribute);
        } else if (kind === 'image') {
          var source = imageUrl(value, context.adapter, context.base);
          if (source) { node.src = source; node.hidden = false; node.removeAttribute('srcset'); node.removeAttribute('sizes'); }
          else { node.removeAttribute('src'); node.hidden = true; }
          if (field.altField) node.alt = text(row[field.altField]);
          var x = coordinate(row[field.xField]);
          var y = coordinate(row[field.yField]);
          if (x !== null && y !== null) node.style.objectPosition = x + '% ' + y + '%';
        } else {
          var url;
          if (kind === 'link') url = safeUrl(string, context.base, context.current);
          else if (kind === 'phoneHref') url = phoneHref(string);
          else if (kind === 'emailHref' || kind === 'formEmail') url = emailHref(string);
          else if (kind === 'mapHref') url = mapHref(string);
          else if (kind === 'sawyer') url = sawyerUrl(string);
          else throw new Error('Unsupported CMS field type: ' + kind);
          var attribute = kind === 'formEmail' ? 'action' : kind === 'sawyer' && node.tagName === 'IFRAME' ? 'src' : 'href';
          if (url) { node.setAttribute(attribute, url); node.removeAttribute('aria-disabled'); if (kind === 'sawyer') node.hidden = false; }
          else { node.removeAttribute(attribute); node.setAttribute('aria-disabled', 'true'); if (kind === 'sawyer') node.hidden = true; }
          if (node.getAttribute('target') === '_blank') node.setAttribute('rel', 'noopener noreferrer');
        }
      });
    });
  }
  function orderedSectionSlots(entries) {
    // Missing/hidden sections retain their slot. Equal or absent orders retain
    // the current DOM order, rather than falling back to unrelated row IDs.
    var movable = entries.filter(function (entry) { return entry.row && Number.isFinite(entry.row.sortOrder); });
    var ordered = movable.slice().sort(function (a, b) { return a.row.sortOrder - b.row.sortOrder; });
    var cursor = 0;
    return entries.map(function (entry) { return movable.includes(entry) ? ordered[cursor++] : entry; });
  }
  function hydrate(document, manifest, collections, adapter, base) {
    // Validate nested collections even when their parent list is empty/hidden.
    // A broken snapshot must not partially replace a complete page or its title.
    contentCollections(manifest).forEach(function (name) { visibleRows(collections[name]); });
    var draft = document.documentElement.cloneNode(true);
    var context = { document: document, adapter: adapter, base: base, current: document.URL };
    var entries = manifest.records.concat(manifest.lists, manifest.galleries);
    var selectors = Array.from(new Set(entries.map(function (entry) { return entry.selector; })));
    selectors.forEach(function (selector) { if (!draft.querySelector(selector)) throw new Error('CMS page target is missing'); });
    var layoutRoots = [];
    var sectionEntries = manifest.records.filter(function (entry) { return entry.collection === 'DiSections'; });
    var sectionRows = sectionEntries.length ? visibleRows(collections.DiSections) : [];
    var sectionGroups = new Map();
    sectionEntries.forEach(function (entry) {
      var node = draft.querySelector(entry.selector);
      var original = document.querySelector(entry.selector);
      if (!original || !node.parentElement) throw new Error('CMS section target is missing');
      var group = sectionGroups.get(node.parentElement);
      if (!group) {
        group = { parent: node.parentElement, original: original.parentElement, entries: [] };
        sectionGroups.set(node.parentElement, group);
      }
      if (group.entries.some(function (candidate) { return candidate.node === node; })) return;
      group.entries.push({ node: node, row: sectionRows.find(function (row) { return row.key === entry.key; }) });
    });
    // Previously positioned optional blocks must disappear when hidden or moved.
    // Only wrappers created for this manifest's designated block lists qualify.
    var extraLists = manifest.lists.filter(function (entry) { return entry.collection === 'DiContentBlocks' && entry.placementField === 'afterSection'; });
    var extraSelectors = new Set(extraLists.map(function (entry) { return entry.selector; }));
    var placedBlocksChanged = false;
    Array.from(draft.querySelectorAll('[data-cms-extra-source]')).forEach(function (node) {
      if (extraSelectors.has(node.getAttribute('data-cms-extra-source'))) { node.remove(); placedBlocksChanged = true; }
    });
    // Undo only visibility previously imposed by CMS records. Keep the original
    // state of conditional UI (menus, empty optional links, disclosure controls).
    selectors.forEach(function (selector) {
      var target = draft.querySelector(selector);
      if (target.hasAttribute('data-cms-hidden')) {
        target.hidden = target.getAttribute('data-cms-hidden') === 'true';
        target.removeAttribute('data-cms-hidden');
      }
    });
    var hiddenRecords = new Set();
    manifest.records.forEach(function (entry) {
      var target = draft.querySelector(entry.selector);
      var row = visibleRows(collections[entry.collection]).find(function (item) { return item.key === entry.key; });
      if (!row) { hiddenRecords.add(target); return; }
      applyFields(target, row, entry.fields, context);
    });
    function fillList(target, entry, groupKey, parentRow) {
      var filter = entry.filter ? Object.assign({}, entry.filter) : undefined;
      if (parentRow) {
        filter = filter || {};
        filter[entry.match.field] = parentRow[entry.match.parentField];
      }
      var rows = visibleRows(collections[entry.collection], filter);
      var template = document.createElement('template');
      template.innerHTML = entry.template;
      if (template.content.children.length !== 1) throw new Error('Invalid CMS list template');
      var fragment = document.createDocumentFragment();
      rows.forEach(function (row, index) {
        var item = template.content.firstElementChild.cloneNode(true);
        uniqueIds(item, 'cms-' + groupKey + '-' + index);
        item.setAttribute('data-cms-item-collection', entry.collection);
        item.setAttribute('data-cms-item-key', row.key);
        applyFields(item, row, entry.fields, context);
        (entry.children || []).forEach(function (child, childIndex) {
          var container = item.querySelector(child.selector);
          if (!container) throw new Error('Nested CMS template target is missing');
          fillList(container, child, groupKey + '-' + index + '-' + childIndex, row);
        });
        fragment.appendChild(item);
      });
      target.replaceChildren(fragment);
    }
    manifest.lists.forEach(function (entry, groupIndex) {
      fillList(draft.querySelector(entry.selector), entry, String(groupIndex));
    });
    manifest.galleries.forEach(function (entry) {
      var target = draft.querySelector(entry.selector);
      var rows = visibleRows(collections[entry.collection], { gallery: entry.group });
      var photos = rows.map(function (row) {
        var source = imageUrl(row.image, adapter, base);
        if (!source) throw new Error('A gallery image is invalid');
        var x = coordinate(row.focalX), y = coordinate(row.focalY);
        return { src: source, alt: text(row.alt), position: (x === null ? 50 : x) + '% ' + (y === null ? 50 : y) + '%' };
      });
      var data = target.querySelector('[data-gallery-items]');
      if (!data) throw new Error('CMS gallery data target is missing');
      data.textContent = JSON.stringify(photos);
      target.hidden = !photos.length;
      var image = target.querySelector('[data-show-stage-image]');
      var stage = target.querySelector('[data-show-stage]');
      if (photos.length && image) { image.src = photos[0].src; image.alt = photos[0].alt; image.style.objectPosition = photos[0].position; }
      if (photos.length && stage) stage.setAttribute('aria-label', photos[0].alt);
    });
    // A section's visibility wins over another binding on the same element,
    // including galleries that normally reveal themselves when photos exist.
    hiddenRecords.forEach(function (target) {
      target.setAttribute('data-cms-hidden', String(target.hidden));
      target.hidden = true;
    });
    sectionGroups.forEach(function (group) {
      var children = Array.from(group.parent.children);
      var originalOrder = group.entries.slice().sort(function (a, b) { return children.indexOf(a.node) - children.indexOf(b.node); });
      var nextOrder = orderedSectionSlots(originalOrder);
      if (nextOrder.every(function (entry, index) { return entry === originalOrder[index]; })) return;
      // Keep each unbound sibling at its exact position using temporary slots.
      var slots = originalOrder.map(function (entry) {
        var marker = document.createComment('cms-section-slot');
        entry.node.replaceWith(marker);
        return marker;
      });
      slots.forEach(function (slot, index) { slot.replaceWith(nextOrder[index].node); });
      layoutRoots.push({ original: group.original, replacement: group.parent });
    });
    extraLists.forEach(function (entry) {
      var container = draft.querySelector(entry.selector);
      var main = draft.querySelector('main');
      if (!main || !main.contains(container)) return;
      var rows = visibleRows(collections[entry.collection], entry.filter);
      var buckets = new Map();
      Array.from(container.children).forEach(function (block, index) {
        var key = rows[index] && rows[index].afterSection;
        if (typeof key !== 'string' || !key) return;
        var section = sectionEntries.find(function (candidate) { return candidate.key === key; });
        var anchor = section && draft.querySelector(section.placementSelector || section.selector);
        if (!anchor || anchor === main || !main.contains(anchor)) return;
        // Explicit build-time anchors respect inner page flow while keeping
        // pricing/contact grids together. Older manifests use their main wrapper.
        if (!section.placementSelector) while (anchor.parentElement !== main) anchor = anchor.parentElement;
        if (anchor === container || anchor.contains(container)) return;
        var bucket = buckets.get(anchor);
        if (!bucket) {
          bucket = document.createElement('div');
          bucket.className = (anchor.parentElement.closest('.section-shell') ? '' : 'section-shell ') + 'cms-extra-sections';
          bucket.setAttribute('data-cms-extra-source', entry.selector);
          buckets.set(anchor, bucket);
        }
        bucket.appendChild(block);
      });
      buckets.forEach(function (bucket, anchor) { anchor.after(bucket); placedBlocksChanged = true; });
    });
    if (placedBlocksChanged) {
      var originalMain = document.querySelector('main');
      var draftMain = draft.querySelector('main');
      if (!originalMain || !draftMain) throw new Error('CMS block placement target is missing');
      layoutRoots.push({ original: originalMain, replacement: draftMain });
    }
    // Prepare every replacement before touching the visible document. Nested
    // bindings are already contained in their ancestor's prepared replacement.
    var roots = selectors.map(function (selector) { return { original: document.querySelector(selector), replacement: draft.querySelector(selector) }; }).concat(layoutRoots);
    if (roots.some(function (pair) { return !pair.original || !pair.replacement; })) throw new Error('CMS target changed while loading');
    roots = roots.filter(function (pair, index) { return roots.findIndex(function (candidate) { return candidate.original === pair.original; }) === index; });
    roots = roots.filter(function (pair) { return !roots.some(function (other) { return other !== pair && other.original.contains(pair.original); }); });
    roots.forEach(function (pair) { pair.original.replaceWith(pair.replacement); });
    return { status: 'connected', collections: Object.keys(collections).length };
  }
  async function start(document, adapter, base, options) {
    options = options || {};
    var marker = document.getElementById('dance-cms-bindings');
    if (!marker || !adapter) return { status: 'bundled' };
    var fetchImpl = options.fetchImpl || fetch;
    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, 5000);
    try {
      var configResponse = await fetchImpl(new URL('assets/cms-config.json', base).href, { cache: 'no-store', credentials: 'same-origin', signal: controller.signal });
      if (!configResponse.ok) throw new Error('CMS configuration unavailable');
      var config = await configResponse.json();
      if (!config || config.enabled !== true) return { status: 'bundled' };
      var manifest = JSON.parse(marker.textContent);
      var ids = contentCollections(manifest);
      var collections = await adapter.loadCollections(config, ids, { signal: controller.signal, timeoutMs: 4500 });
      if (controller.signal.aborted) throw new Error('CMS content request timed out');
      return hydrate(document, manifest, collections, adapter, base);
    } catch (error) {
      // The visitor continues seeing the complete checked-in page. Details are
      // available to developers without displaying a broken CMS panel to families.
      if (typeof console !== 'undefined') console.warn('Live content unavailable; using the saved site content.', error.message);
      return { status: 'fallback' };
    } finally { clearTimeout(timer); }
  }
  return Object.freeze({ safeUrl: safeUrl, phoneHref: phoneHref, emailHref: emailHref, mapHref: mapHref, sawyerUrl: sawyerUrl, coordinate: coordinate, visibleRows: visibleRows, contentCollections: contentCollections, sanitizeHtml: sanitizeHtml, orderedSectionSlots: orderedSectionSlots, hydrate: hydrate, start: start });
});
