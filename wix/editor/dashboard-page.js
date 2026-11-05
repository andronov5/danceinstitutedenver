/* Paste into the native Wix Dashboard Page's page code.
 * Add one HTML Component with ID #studioEditor containing editor-install.html.
 * The component contains no credentials; all writes use Admin web methods.
 */
import { openMediaManager } from 'wix-dashboard';
import { loadStudioContent, saveStudioItem, createStudioItem, reorderStudioItems } from 'backend/studio-editor.web';
import { EDITOR_PREVIEWS } from 'public/editor-previews.js';

const CHANNEL = 'di-editor-v1';
const ACTIONS = new Set(['init', 'save', 'create', 'reorder', 'pickImage']);
const responses = new Map();
let mutations = Promise.resolve();
let connected = false;

function validRequest(message) {
  if (!message || typeof message !== 'object' || Array.isArray(message) || message.channel !== CHANNEL
    || typeof message.id !== 'string' || !/^[A-Za-z0-9_-]{1,150}$/.test(message.id)
    || !ACTIONS.has(message.action) || !message.payload || typeof message.payload !== 'object' || Array.isArray(message.payload)
    || Object.keys(message).some(key => !['channel', 'id', 'action', 'payload'].includes(key))) return false;
  try { return JSON.stringify(message.payload).length <= 500000; } catch (_) { return false; }
}

async function execute(action, payload) {
  if (action === 'init') {
    if (Object.keys(payload).length) return { ok: false, error: { message: 'Reload the editor and try again.' } };
    const result = await loadStudioContent();
    if (!result.ok) return result;
    return { ...result, previews: EDITOR_PREVIEWS };
  }
  if (action === 'save') return saveStudioItem(payload);
  if (action === 'create') return createStudioItem(payload);
  if (action === 'reorder') return reorderStudioItems(payload);
  if (Object.keys(payload).length) return { ok: false, error: { message: 'Choose an image using the photo button.' } };
  const selection = await openMediaManager({ multiSelect: false, category: 'IMAGE' });
  const selected = selection?.items?.[0];
  if (!selected) return { ok: true, cancelled: true, image: '' };
  if (selected.private || (selected.mediaType && selected.mediaType !== 'IMAGE')) {
    return { ok: false, error: { message: 'Choose a public image for the website.' } };
  }
  const image = selected.media?.image?.image || selected.url;
  if (typeof image !== 'string' || !/^(?:wix:image:\/\/v1\/|https:\/\/)/.test(image)) {
    return { ok: false, error: { message: 'Wix could not provide this image. Please choose another.' } };
  }
  return { ok: true, image };
}

async function reply(message) {
  try {
    const result = await execute(message.action, message.payload);
    const { ok, error, ...data } = result;
    return { channel: CHANNEL, id: message.id, ok: ok === true, data, ...(error ? { error } : {}) };
  } catch (_) {
    // Wix can reject a web method before our backend runs, e.g. an expired
    // dashboard session. Never pass raw platform errors or data to the iframe.
    return { channel: CHANNEL, id: message.id, ok: false, error: {
      code: 'WIX_UNAVAILABLE',
      message: 'Wix could not complete this action. Your changes are still here. Check your Wix login and reload before trying again.'
    } };
  }
}

$w.onReady(() => {
  const editor = $w('#studioEditor');
  editor.onMessage(async event => {
    const message = event.data;
    if (!validRequest(message)) return;
    if (message.action === 'init') connected = true;
    // Repeated iframe messages with the same request ID reuse the first result.
    // Creates and reorders cannot accidentally run twice in this page session.
    let pending = responses.get(message.id);
    if (!pending) {
      if (['save', 'create', 'reorder', 'pickImage'].includes(message.action)) {
        pending = mutations.then(() => reply(message));
        mutations = pending.then(() => undefined, () => undefined);
      } else pending = reply(message);
      responses.set(message.id, pending);
      if (responses.size > 200) responses.delete(responses.keys().next().value);
    }
    editor.postMessage(await pending);
  });
  // An HTML component can finish loading after page onReady. The safe parent
  // handshake supplies the iframe's actual origin; the iframe replies only to
  // that exact origin after checking event.source and Wix's hostname.
  function connect(attempt = 0) {
    if (connected || attempt >= 20) return;
    editor.postMessage({ channel: CHANNEL, action: 'connect' });
    setTimeout(() => connect(attempt + 1), 500);
  }
  connect();
});
