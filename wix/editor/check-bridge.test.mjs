/* Node checks of the actual iframe request/response functions. No Wix requests. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(new URL('./editor.html', import.meta.url), 'utf8');
const start = source.indexOf('    function trustedParent(');
const end = source.indexOf('    async function connect()', start);
assert(start >= 0 && end > start, 'Editor communication functions are discoverable');
const actualFunctions = source.slice(start, end);

function fixture() {
  let serial = 0;
  const timers = new Map(), listeners = new Map(), sent = [];
  const nodes = Object.fromEntries(['.workspace', '.app-header', 'unsaved-notice', 'saving-cover', 'saving-message'].map(key => [key, { inert: false, hidden: true, textContent: '' }]));
  const parent = { postMessage: (message, origin) => sent.push({ message: structuredClone(message), origin }) };
  const window = { parent, addEventListener: (type, callback) => listeners.set(type, callback) };
  const context = {
    window, document: { querySelector: key => nodes[key] }, URL, Date, Map, JSON, Math, Error,
    setTimeout: (callback, delay) => { const id = ++serial; timers.set(id, { callback, delay }); return id; },
    clearTimeout: id => timers.delete(id), nodes, exports: {}
  };
  vm.runInNewContext(`
const CHANNEL='di-editor-v1';
const state={pending:new Map(),sequence:0,parentOrigin:'https://manage.wix.com',mutationCount:0,pendingRecovery:null};
const $=id=>nodes[id];
${actualFunctions}
exports.communicate=communicate;exports.state=state;
`, context);
  const send = (message, { origin = 'https://manage.wix.com', source = parent } = {}) => listeners.get('message')({ data: message, origin, source });
  return { ...context.exports, nodes, timers, sent, send, parent };
}

test('in-flight mutation locks editable UI until confirmed response', async () => {
  const f = fixture(); const result = f.communicate('save', { id: 'test', changes: { text: 'Draft' } });
  assert.equal(f.nodes['.workspace'].inert, true);
  assert.equal(f.nodes['.app-header'].inert, true);
  assert.equal(f.nodes['saving-cover'].hidden, false);
  const request = f.sent[0].message;
  f.send({ channel: request.channel, id: request.id, ok: true, data: { item: { _id: 'test', text: 'Draft' } } });
  assert.equal((await result).item.text, 'Draft');
  assert.equal(f.nodes['.workspace'].inert, false);
  assert.equal(f.nodes['saving-cover'].hidden, true);
  assert.equal(f.state.pending.size, 0);
});

test('slow create retries the identical request ID while staying locked', async () => {
  const f = fixture(); const result = f.communicate('create', { listId: 'test-list', values: { title: 'New' } });
  const original = f.sent[0]; const timer = [...f.timers.values()][0];
  assert.equal(timer.delay, 45000); timer.callback();
  assert.equal(f.sent.length, 2);
  assert.deepEqual(f.sent[1], original);
  assert.equal(f.state.pending.size, 1);
  assert.equal(f.nodes['.workspace'].inert, true);
  assert.match(f.nodes['saving-message'].textContent, /same save/);
  f.send({ channel: original.message.channel, id: original.message.id, ok: true, data: { item: { _id: 'created-once' } } });
  assert.equal((await result).item._id, 'created-once');
  assert.equal(f.state.mutationCount, 0);
});

test('untrusted origins and non-parent messages cannot finish a save', async () => {
  const f = fixture(); const result = f.communicate('save', { id: 'test', changes: { text: 'Draft' } });
  const request = f.sent[0].message; const reply = { channel: request.channel, id: request.id, ok: true, data: { item: { _id: 'test' } } };
  f.send(reply, { origin: 'https://wix.com.evil.example' });
  f.send(reply, { source: {} });
  f.send(reply, { origin: 'https://other.wix.com' });
  assert.equal(f.state.pending.size, 1); assert.equal(f.nodes['.workspace'].inert, true);
  f.send(reply); await result;
  assert.equal(f.state.pending.size, 0);
});

test('confirmed failure unlocks and returns the safe error for draft retention', async () => {
  const f = fixture(); const result = f.communicate('save', { id: 'test' }); const request = f.sent[0].message;
  f.send({ channel: request.channel, id: request.id, ok: false, error: { message: 'Content changed. Reload before saving.' }, data: { code: 'CONFLICT' } });
  await assert.rejects(result, error => error.message.includes('Reload') && error.data.code === 'CONFLICT');
  assert.equal(f.nodes['.workspace'].inert, false); assert.equal(f.state.mutationCount, 0);
});

test('read-only init timeout rejects without an indefinite mutation lock', async () => {
  const f = fixture(); const result = f.communicate('init');
  [...f.timers.values()][0].callback(); await assert.rejects(result, /taking longer/);
  assert.equal(f.state.pending.size, 0); assert.equal(f.state.mutationCount, 0); assert.equal(f.sent.length, 1);
});

test('unreconciled saved result blocks a new write before sending', async () => {
  const f = fixture(); f.state.pendingRecovery = { createdId: 'already-created' };
  await assert.rejects(f.communicate('create', {}), /Reload the latest content/);
  assert.equal(f.sent.length, 0); assert.equal(f.state.mutationCount, 0);
});
