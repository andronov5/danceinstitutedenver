/* Public, read-only Wix CMS transport. No administrator credentials belong here. */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.DanceWixCMS = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  var MAX_COLLECTIONS = 30;
  var MAX_ITEMS = 10000;
  var own = Function.call.bind(Object.prototype.hasOwnProperty);

  function object(value) {
    return value !== null && typeof value === 'object' && !Array.isArray(value);
  }

  function failure(message) {
    return new Error('Wix CMS: ' + message);
  }

  function endpointUrl(value) {
    var url;
    try { url = new URL(value); } catch (_) { throw failure('a published content endpoint is required.'); }
    var wixHost = /^[a-z0-9-]+\.(?:wixsite|wixstudio)\.com$/.test(url.hostname);
    var studioHost = /^(?:www\.)?danceinstitutedenver\.com$/.test(url.hostname);
    if (url.protocol !== 'https:' || url.username || url.password || url.port ||
        (!wixHost && !studioHost) || !/^\/(?:[a-zA-Z0-9_-]+\/)?_functions\/danceContent$/.test(url.pathname) ||
        url.search || url.hash) {
      throw failure('the content endpoint must be the studio’s published Wix danceContent function.');
    }
    return url;
  }

  function collectionPairs(config, ids) {
    if (!Array.isArray(ids) || ids.length > MAX_COLLECTIONS) throw failure('invalid collection request.');
    var mapping = config.collectionIds || {};
    if (!object(mapping)) throw failure('invalid collection mapping.');
    var seen = new Set();
    return ids.filter(function (id) {
      if (typeof id !== 'string' || !/^[A-Za-z][A-Za-z0-9_]{0,79}$/.test(id)) {
        throw failure('invalid collection identifier.');
      }
      if (seen.has(id)) return false;
      seen.add(id);
      return true;
    }).map(function (id) {
      var actual = own(mapping, id) ? mapping[id] : id;
      if (typeof actual !== 'string' || !/^Di[A-Za-z0-9_]{1,77}$/.test(actual)) {
        throw failure('only Dance Institute content collections may be requested.');
      }
      return [id, actual];
    });
  }

  function publicRows(rows) {
    if (!Array.isArray(rows) || rows.length > MAX_ITEMS) throw failure('invalid collection response.');
    var keys = new Set();
    return rows.filter(function (row) {
      if (!object(row)) throw failure('invalid content item.');
      // Visibility is enforced on the backend and again here, including missing flags.
      return row.isVisible === true;
    }).map(function (row) {
      if (typeof row.key !== 'string' || !row.key || row.key.length > 256 || keys.has(row.key)) {
        throw failure('missing or duplicate content key.');
      }
      keys.add(row.key);
      return Object.assign({}, row);
    });
  }

  /**
   * Return a complete set of requested collections, keyed by their logical IDs.
   * An empty published collection is []; a missing/incomplete one rejects the
   * whole load so callers can retain the page's bundled content unchanged.
   */
  async function loadCollections(config, ids, options) {
    options = options || {};
    if (!config || config.enabled !== true) return {};
    if (config.transport && config.transport !== 'http-function') throw failure('unsupported transport.');
    var pairs = collectionPairs(config, ids);
    if (!pairs.length) return {};
    var url = endpointUrl(config.endpoint);
    url.searchParams.set('collections', Array.from(new Set(pairs.map(function (pair) { return pair[1]; }))).join(','));
    var fetchImpl = options.fetchImpl || (typeof fetch === 'function' ? fetch : null);
    if (!fetchImpl) throw failure('fetch is unavailable.');
    var controller = new AbortController();
    var signal = options.signal;
    var timeoutMs = options.timeoutMs === undefined ? 12000 : options.timeoutMs;
    if (!Number.isFinite(timeoutMs) || timeoutMs < 1 || timeoutMs > 30000) throw failure('invalid request timeout.');
    function abort() { controller.abort(signal.reason); }
    if (signal) {
      if (signal.aborted) abort();
      else signal.addEventListener('abort', abort, { once: true });
    }
    var timer = setTimeout(function () { controller.abort(); }, timeoutMs);
    try {
      if (controller.signal.aborted) throw controller.signal.reason || failure('request cancelled.');
      var response = await fetchImpl(url.href, {
        method: 'GET',
        mode: 'cors',
        credentials: 'omit',
        cache: 'no-store',
        redirect: 'error',
        headers: { Accept: 'application/json' },
        signal: controller.signal
      });
      if (!response || response.ok !== true) throw failure('content request failed' + (response && Number.isInteger(response.status) ? ' (HTTP ' + response.status + ')' : '') + '.');
      var payload = await response.json();
      if (controller.signal.aborted) throw controller.signal.reason || failure('request cancelled.');
      if (!object(payload) || payload.version !== 1 || payload.complete !== true || !object(payload.collections)) {
        throw failure('incomplete content response.');
      }
      var result = {};
      pairs.forEach(function (pair) {
        if (!own(payload.collections, pair[1])) throw failure('a requested collection is missing.');
        result[pair[0]] = publicRows(payload.collections[pair[1]]);
      });
      return result;
    } finally {
      clearTimeout(timer);
      if (signal) signal.removeEventListener('abort', abort);
    }
  }

  /** Convert Wix CMS image fields without allowing executable URL schemes. */
  function imageUrl(value) {
    if (object(value)) value = value.src || value.url || '';
    if (typeof value !== 'string' || !value || /[\u0000-\u001f\u007f\\<>"']/.test(value)) return '';
    var wix = /^wix:image:\/\/v1\/([A-Za-z0-9_~-]+(?:\.[A-Za-z0-9]+)?)(?:\/[^?#]*)?(?:\?[^#]*)?(?:#.*)?$/.exec(value);
    if (wix) return 'https://static.wixstatic.com/media/' + wix[1];
    if (/^https:\/\//i.test(value)) {
      try {
        var url = new URL(value);
        return url.protocol === 'https:' && !url.username && !url.password ? url.href : '';
      } catch (_) { return ''; }
    }
    // Local checked-in images continue to work before a Wix image is selected.
    if (/^(?:\.\.\/|\.\/|\/)?(?:\.\.\/)*assets\/images\/[A-Za-z0-9_./~-]+$/.test(value) && !value.includes('/../')) return value;
    return '';
  }

  return Object.freeze({ loadCollections: loadCollections, imageUrl: imageUrl });
});
