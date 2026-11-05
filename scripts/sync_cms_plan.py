#!/usr/bin/env python3
"""Prepare (never execute) an incremental Wix CMS sync for ExecuteWixAPI.

Examples:
  python scripts/sync_cms_plan.py --mode inspect > /tmp/cms-inspect.json
  python scripts/sync_cms_plan.py --mode apply --include-backup > /tmp/cms-apply.json

The JSON output is the tool's complete argument object. Its `code` is an async
function, and its `files` contains the source snapshot, not credentials. Pass it
to ExecuteWixAPI only after reviewing the desired generated CMS files. `inspect`
is read-only. Both modes re-read Wix and build the plan from current data.

The baseline is the last provisioned source, NOT a snapshot of editor changes.
After an apply, use --finalize-report PATH with the saved JSON response to advance
cms/sync-baseline.json from its compact baselineDelta. This only advances fields
actually inserted/patched or already at desired values; external edits retain
their previous baseline so future runs keep protecting them. The source digest
must still match, preventing a later local build from advancing unrelated values.
No row is deleted, no item is replaced, no permissions/plugins are changed, and
no site/editor frontend is published. Removed source rows are merely hidden when
the entire row is still unchanged. Deleted baseline rows are never resurrected.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SITE_ID = "f3c88b1a-e358-495d-bcfd-78c490531ee8"
DOCS = [
    "https://dev.wix.com/docs/api-reference/business-solutions/cms/collection-management/data-collections/get-data-collection",
    "https://dev.wix.com/docs/api-reference/business-solutions/cms/collection-management/data-collections/create-data-collection",
    "https://dev.wix.com/docs/api-reference/business-solutions/cms/collection-management/data-collections/create-data-collection-field",
    "https://dev.wix.com/docs/api-reference/business-solutions/cms/data-items/query-data-items",
    "https://dev.wix.com/docs/api-reference/business-solutions/cms/data-items/bulk-insert-data-items",
    "https://dev.wix.com/docs/api-reference/business-solutions/cms/data-items/bulk-patch-data-items",
    "https://dev.wix.com/docs/api-reference/business-solutions/cms/skills/cms-publishing-flow-visible-hidden",
    "https://dev.wix.com/docs/api-reference/articles/work-with-wix-apis/data-retrieval/about-the-wix-api-query-language",
]

# Public URLs come from the exact method schemas (not old recipe URL aliases).
CODE = r'''async function() {
  const inputFile = files.find(file => file.path === "cms-sync-input.json");
  if (!inputFile || inputFile.encoding === "base64") {
    throw new Error("Expected the generated text cms-sync-input.json file.");
  }
  const input = JSON.parse(inputFile.content);
  if (siteId !== input.siteId || input.siteId !== "f3c88b1a-e358-495d-bcfd-78c490531ee8") {
    throw new Error("CMS sync site mismatch; no requests were made.");
  }
  if (!["inspect", "apply"].includes(input.mode)) {
    throw new Error("Unknown sync mode.");
  }
  const api = "https://www.wixapis.com/data/v2";
  const owns = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
  const clone = value => JSON.parse(JSON.stringify(value));
  const stable = value => {
    if (value === undefined) return "undefined";
    if (value === null || typeof value !== "object") return JSON.stringify(value);
    if (Array.isArray(value)) return "[" + value.map(stable).join(",") + "]";
    return "{" + Object.keys(value).sort().map(key => JSON.stringify(key) + ":" + stable(value[key])).join(",") + "}";
  };
  const equal = (a, b) => stable(a) === stable(b);
  const clean = row => Object.fromEntries(Object.entries(row).filter(([key]) => !key.startsWith("_")));
  const idOf = item => item.id || item.data?._id;
  const schemaById = new Map(input.schema.collections.map(collection => [collection.id, collection]));
  const collectionIds = [...new Set([...schemaById.keys(), ...Object.keys(input.baseline.collections)])];
  const report = {
    mode: input.mode,
    siteId: input.siteId,
    sourceDigest: input.sourceDigest,
    status: "READING",
    collections: [],
    conflicts: [],
    blockers: [],
    applied: [],
    failures: []
  };
  const states = new Map();
  const nextBaseline = clone(input.baseline);
  nextBaseline.sourceDigest = input.sourceDigest;
  nextBaseline.lastSyncAt = new Date().toISOString();
  const backup = {
    version: 1,
    siteId: input.siteId,
    capturedAt: new Date().toISOString(),
    sourceDigest: input.sourceDigest,
    scope: "Only designated website collections and public allowlisted fields; not a backup of private or unrelated CMS fields.",
    schemas: {},
    collections: {}
  };

  function boundedResult() {
    // ExecuteWixAPI truncates large results. Never let an optional backup cut
    // off the authoritative mutation report or baseline delta.
    if (report.backup && JSON.stringify(report).length > 80000) {
      delete report.backup;
      report.backupOmitted = "Public snapshot exceeded the safe tool-return budget; no complete backup was exported.";
    }
    return report;
  }

  async function request(method, url, body) {
    const options = {
      scope: "site",
      method: method,
      url: url
    };
    if (body !== undefined) options.body = body;
    const response = await wix.request(options);
    if (response.status < 200 || response.status >= 300) {
      const error = new Error("Wix returned HTTP " + response.status);
      error.status = response.status;
      throw error;
    }
    return response.data;
  }

  function isNotFound(error) {
    const text = String(error?.message || error);
    return error?.status === 404 || error?.statusCode === 404 || /\b404\b|COLLECTION_NOT_FOUND|WDE0025/.test(text);
  }

  async function getSchema(id, allowMissing) {
    try {
      const data = await request("GET", api + "/collections/" + encodeURIComponent(id) + "?consistentRead=true");
      if (!data.collection || data.collection.id !== id || !Array.isArray(data.collection.fields)) {
        throw new Error("Malformed schema response for " + id);
      }
      return data.collection;
    } catch (error) {
      if (allowMissing && isNotFound(error)) return null;
      throw error;
    }
  }

  function validateSchema(id, current, wanted) {
    if (!current) return;
    if (current.collectionType !== "NATIVE") {
      report.blockers.push({ collection: id, reason: "Only native user collections may be synced." });
    }
    // Publishing plugins require a separately reviewed draft workflow. Do not
    // silently publish, bypass drafts, or change any plugin configuration.
    for (const plugin of current.plugins || []) {
      if (plugin.type !== "EDITABLE_PAGE_LINK") {
        report.blockers.push({ collection: id, reason: "Unreviewed collection plugin", plugin: plugin.type });
      }
    }
    const currentFields = new Map(current.fields.map(field => [field.key, field]));
    for (const field of wanted?.fields || []) {
      const existing = currentFields.get(field.key);
      if (existing && (existing.type !== field.type || existing.encrypted || existing.readOnly || existing.immutable)) {
        report.blockers.push({ collection: id, field: field.key, reason: "Existing field type/access conflicts with source schema; left unchanged." });
      }
    }
    // These are declared by the live collection schema. They protect offset
    // ordering and atomic compare-and-set conditions, including concurrent edits.
    const idField = currentFields.get("_id");
    const updatedField = currentFields.get("_updatedDate");
    if (!idField?.capabilities?.sortable || !idField?.capabilities?.queryOperators?.includes("EQ") ||
        !updatedField?.capabilities?.queryOperators?.includes("EQ")) {
      report.blockers.push({ collection: id, reason: "Cannot verify required ID/date filter and ID sort capabilities." });
    }
  }

  async function queryAll(id, schema) {
    const all = [];
    const ids = new Set();
    const limit = Math.min(100, schema.maxPageSize || 100);
    let total;
    for (let offset = 0; offset < input.maxItemsPerCollection; offset += limit) {
      const body = {
        dataCollectionId: id,
        consistentRead: true,
        returnTotalCount: true,
        query: {
          sort: [{ fieldName: "_id", order: "ASC" }],
          paging: { limit: limit, offset: offset }
        }
      };
      const data = await request("POST", api + "/items/query", body);
      const rows = data.dataItems;
      const count = data.pagingMetadata?.total;
      if (!Array.isArray(rows) || !Number.isInteger(count) || count < 0 || data.pagingMetadata?.tooManyToCount) {
        throw new Error("Incomplete query metadata for " + id);
      }
      if (total !== undefined && count !== total) throw new Error("Collection changed during paging: " + id);
      total = count;
      if (total > input.maxItemsPerCollection) throw new Error("Collection exceeds bounded sync limit: " + id);
      for (const item of rows) {
        const itemId = idOf(item);
        if (!itemId || !item.data || ids.has(itemId)) throw new Error("Missing/duplicate item during paging: " + id);
        ids.add(itemId);
        all.push(item);
      }
      if (all.length === total) return all;
      if (rows.length !== limit || all.length > total) throw new Error("Incomplete/inconsistent paging: " + id);
    }
    throw new Error("Paging bound reached: " + id);
  }

  function conflict(collection, row, fields, reason) {
    report.conflicts.push({ collection: collection, id: row._id || idOf(row), key: row.key || row.data?.key, fields: fields, reason: reason });
  }

  function advance(id, rowId, field, value) {
    const rows = nextBaseline.collections[id] || (nextBaseline.collections[id] = []);
    let row = rows.find(entry => entry._id === rowId);
    if (!row) {
      row = { _id: rowId };
      rows.push(row);
    }
    row[field] = clone(value);
  }

  function buildPlan(id, current, items) {
    const desiredRows = input.seed.collections[id] || [];
    const baselineRows = input.baseline.collections[id] || [];
    const wanted = schemaById.get(id);
    const baselineIds = new Map(baselineRows.map(row => [row._id, row]));
    const currentIds = new Map(items.map(item => [idOf(item), item]));
    const currentKeys = new Map();
    for (const item of items) {
      const key = item.data.key;
      if (key !== undefined) currentKeys.set(key, [...(currentKeys.get(key) || []), item]);
    }
    const plan = {
      collection: id,
      create: !current && !!wanted,
      addFields: wanted?.fields.filter(field => !current?.fields.some(existing => existing.key === field.key)) || [],
      inserts: [],
      patches: [],
      before: currentIds
    };
    if (plan.create) plan.addFields = [];
    for (const row of desiredRows) {
      const existing = currentIds.get(row._id);
      const baseline = baselineIds.get(row._id);
      const sameKey = currentKeys.get(row.key) || [];
      if (sameKey.some(item => idOf(item) !== row._id)) {
        conflict(id, row, ["key"], "Content key belongs to another or duplicate item; row skipped.");
        continue;
      }
      if (!existing) {
        if (baseline) {
          conflict(id, row, [], "Previously provisioned item was deleted; not recreated.");
        } else {
          plan.inserts.push({ id: row._id, data: clean(row) });
        }
        continue;
      }
      if (existing.data.key !== row.key) {
        conflict(id, row, ["key"], "Existing item's content key was edited; row skipped.");
        continue;
      }
      const modifications = [];
      const skipped = [];
      for (const [field, value] of Object.entries(clean(row))) {
        if (equal(existing.data[field], value)) {
          advance(id, row._id, field, value);
          continue;
        }
        const safelyUnchanged = baseline && owns(baseline, field) &&
          owns(existing.data, field) && equal(existing.data[field], baseline[field]);
        const safelyNew = baseline && !owns(baseline, field) && !owns(existing.data, field);
        if (safelyUnchanged || safelyNew) {
          modifications.push({ fieldPath: field, action: "SET_FIELD", setFieldOptions: { value: value } });
        } else {
          skipped.push(field);
        }
      }
      if (skipped.length) conflict(id, row, skipped, "External edits or untracked existing values preserved.");
      if (modifications.length) {
        if (!existing.data._updatedDate) {
          conflict(id, row, modifications.map(modification => modification.fieldPath), "Missing update timestamp; cannot protect concurrent edits.");
        } else {
          plan.patches.push({ id: row._id, key: row.key, modifications: modifications, updatedDate: existing.data._updatedDate, reason: "update" });
        }
      }
    }
    const desiredIds = new Set(desiredRows.map(row => row._id));
    for (const row of baselineRows) {
      if (desiredIds.has(row._id)) continue;
      const existing = currentIds.get(row._id);
      if (!existing) continue;
      // Compare ALL non-system values, not just allowlisted fields. An extra
      // editor field also blocks automatic hiding; it is never exported.
      if (existing.data.isVisible === false) continue;
      if (equal(clean(existing.data), clean(row)) && existing.data._updatedDate) {
        plan.patches.push({
          id: row._id,
          key: row.key,
          modifications: [{ fieldPath: "isVisible", action: "SET_FIELD", setFieldOptions: { value: false } }],
          updatedDate: existing.data._updatedDate,
          reason: "hide-removed-source-row"
        });
      } else {
        conflict(id, row, ["isVisible"], "Removed source row has editor changes; kept visible and unchanged.");
      }
    }
    return plan;
  }

  function publicBackup(id, current, items) {
    const desired = schemaById.get(id);
    const allowed = new Set(desired?.fields.map(field => field.key) || []);
    for (const row of input.baseline.collections[id] || []) {
      for (const field of Object.keys(row)) if (!field.startsWith("_")) allowed.add(field);
    }
    // Export source-designated public columns only. Unknown fields and _owner
    // never leave Wix; schemas likewise exclude unrelated editor-added columns.
    backup.collections[id] = items.map(item => ({
      _id: idOf(item),
      ...Object.fromEntries(Object.entries(item.data).filter(([field]) => allowed.has(field)))
    }));
    backup.schemas[id] = current ? {
      id: id,
      displayName: current.displayName,
      revision: current.revision,
      permissions: current.permissions,
      plugins: current.plugins,
      fields: current.fields.filter(field => allowed.has(field.key)).map(field => ({
        key: field.key,
        type: field.type,
        displayName: field.displayName
      }))
    } : null;
  }

  // Batch independent collection reads, but bound concurrency and inspect every
  // result. Any malformed/missing existing collection blocks ALL writes.
  for (let offset = 0; offset < collectionIds.length; offset += 4) {
    const batch = collectionIds.slice(offset, offset + 4);
    const results = await Promise.allSettled(batch.map(async id => {
      const current = await getSchema(id, !owns(input.baseline.collections, id));
      validateSchema(id, current, schemaById.get(id));
      if (report.blockers.some(blocker => blocker.collection === id)) return;
      const items = current ? await queryAll(id, current) : [];
      publicBackup(id, current, items);
      const plan = buildPlan(id, current, items);
      states.set(id, { current: current, plan: plan });
      report.collections.push({
        id: id,
        existingItems: items.length,
        createCollection: plan.create,
        addFields: plan.addFields.map(field => field.key),
        insertIds: plan.inserts.map(item => item.id),
        patchItems: plan.patches.map(patch => ({ id: patch.id, fields: patch.modifications.map(change => change.fieldPath), reason: patch.reason }))
      });
    }));
    results.forEach((result, index) => {
      if (result.status === "rejected") {
        report.blockers.push({ collection: batch[index], reason: String(result.reason?.message || result.reason) });
      }
    });
  }
  report.collections.sort((a, b) => collectionIds.indexOf(a.id) - collectionIds.indexOf(b.id));
  report.totals = {
    collectionsRead: states.size,
    createCollections: report.collections.filter(collection => collection.createCollection).length,
    addFields: report.collections.reduce((sum, collection) => sum + collection.addFields.length, 0),
    insertItems: report.collections.reduce((sum, collection) => sum + collection.insertIds.length, 0),
    patchItems: report.collections.reduce((sum, collection) => sum + collection.patchItems.length, 0),
    hideItems: report.collections.reduce((sum, collection) => sum + collection.patchItems.filter(patch => patch.reason === "hide-removed-source-row").length, 0),
    conflictItems: report.conflicts.length
  };
  if (input.includeBackup) report.backup = backup;
  if (report.blockers.length || input.mode === "inspect") {
    report.status = report.blockers.length ? "BLOCKED_NO_WRITES" : "INSPECTED_NO_WRITES";
    return boundedResult();
  }

  function schemaField(field) {
    const allowed = ["key", "displayName", "type", "typeMetadata", "description", "required"];
    return Object.fromEntries(Object.entries(field).filter(([key]) => allowed.includes(key)));
  }

  function verifiedItem(id, operation, before, after, expected) {
    if (!after || idOf(after) !== id || !after.data) throw new Error("Missing returned item after " + operation + ": " + id);
    for (const [field, value] of Object.entries(expected)) {
      if (!equal(after.data[field], value)) throw new Error("Verification failed for " + id + "." + field);
    }
    for (const [field, value] of Object.entries(clean(before?.data || {}))) {
      if (!owns(expected, field) && !equal(after.data[field], value)) {
        throw new Error("Untouched field changed during " + operation + ": " + id + "." + field);
      }
    }
  }

  async function applyBulk(id, operation, entries, body, expectedFor) {
    report.inFlight = { collection: id, operation: operation, ids: entries.map(entry => entry.id) };
    const data = await request("POST", api + "/bulk/items/" + operation, body);
    if (!Array.isArray(data.results) || data.results.length !== entries.length || !data.bulkActionMetadata) {
      throw new Error("Malformed bulk response; stop and inspect Wix before retrying " + id + ".");
    }
    const indexes = new Set();
    let successes = 0;
    let failures = 0;
    for (const result of data.results) {
      const metadata = result.itemMetadata;
      const index = Number.isInteger(metadata?.originalIndex) ? metadata.originalIndex :
        entries.findIndex(entry => entry.id === (metadata?.id || idOf(result.dataItem || {})));
      if (!Number.isInteger(index) || index < 0 || index >= entries.length || indexes.has(index)) {
        throw new Error("Invalid bulk result index for " + id);
      }
      indexes.add(index);
      const entry = entries[index];
      if (!metadata.success) {
        failures += 1;
        report.failures.push({ collection: id, id: entry.id, operation: operation, code: metadata.error?.code, reason: metadata.error?.description || "Conditional write rejected; existing item preserved." });
        continue;
      }
      successes += 1;
      const expected = expectedFor(entry);
      const applied = { collection: id, id: entry.id, operation: operation, fields: Object.keys(expected), verified: false };
      report.applied.push(applied);
      verifiedItem(entry.id, operation, states.get(id).plan.before.get(entry.id), result.dataItem, expected);
      for (const [field, value] of Object.entries(expected)) advance(id, entry.id, field, value);
      applied.verified = true;
    }
    if ((data.bulkActionMetadata.totalSuccesses || 0) !== successes || (data.bulkActionMetadata.totalFailures || 0) !== failures) {
      throw new Error("Bulk result totals do not match item outcomes for " + id);
    }
    delete report.inFlight;
    if (failures) throw new Error("Bulk writes rejected; no additional mutations attempted.");
  }

  try {
    for (const id of collectionIds) {
      const state = states.get(id);
      const plan = state.plan;
      const wanted = schemaById.get(id);
      if (plan.create) {
        const body = {
          collection: {
            id: id,
            displayName: wanted.displayName,
            fields: wanted.fields.map(schemaField),
            permissions: wanted.permissions
          }
        };
        report.inFlight = { collection: id, operation: "createCollection" };
        const response = await request("POST", api + "/collections", body);
        state.current = response.collection || await getSchema(id, false);
        const applied = { collection: id, operation: "createCollection", verified: false };
        report.applied.push(applied);
        validateSchema(id, state.current, wanted);
        if (!wanted.fields.every(field => state.current.fields.some(actual => actual.key === field.key && actual.type === field.type))) {
          throw new Error("New collection did not return all requested fields: " + id);
        }
        if (!equal(state.current.permissions, wanted.permissions)) throw new Error("New collection permissions failed verification: " + id);
        if (report.blockers.length) throw new Error("Created collection needs manual schema/plugin review.");
        applied.verified = true;
        delete report.inFlight;
      }
      for (const field of plan.addFields) {
        const body = {
          dataCollectionId: id,
          field: schemaField(field)
        };
        report.inFlight = { collection: id, operation: "addField", field: field.key };
        const response = await request("POST", api + "/collections/create-field", body);
        state.current = response.dataCollection || await getSchema(id, false);
        const applied = { collection: id, field: field.key, operation: "addField", verified: false };
        report.applied.push(applied);
        const actual = state.current.fields?.find(candidate => candidate.key === field.key);
        if (!actual || actual.type !== field.type) throw new Error("Added field failed verification: " + id + "." + field.key);
        applied.verified = true;
        delete report.inFlight;
      }
      for (let offset = 0; offset < plan.inserts.length; offset += 1000) {
        const entries = plan.inserts.slice(offset, offset + 1000);
        const body = {
          dataCollectionId: id,
          dataItems: entries,
          returnEntity: true
        };
        await applyBulk(id, "insert", entries, body, entry => entry.data);
      }
      // The server evaluates the condition atomically. If anything in a row
      // changes after the read, its timestamp no longer matches and it is skipped
      // by Wix instead of overwriting even an edit to an unrelated field.
      for (let offset = 0; offset < plan.patches.length; offset += 100) {
        const entries = plan.patches.slice(offset, offset + 100);
        const body = {
          dataCollectionId: id,
          patches: entries.map(entry => ({
            dataItemId: entry.id,
            fieldModifications: entry.modifications
          })),
          returnEntity: true,
          condition: {
            filter: {
              $or: entries.map(entry => ({
                $and: [
                  { _id: { $eq: entry.id } },
                  { _updatedDate: { $eq: entry.updatedDate } }
                ]
              }))
            }
          }
        };
        await applyBulk(id, "patch", entries, body, entry => Object.fromEntries(entry.modifications.map(change => [change.fieldPath, change.setFieldOptions.value])));
      }
    }
    report.status = "APPLIED_VERIFIED";
  } catch (error) {
    report.status = "STOPPED_AFTER_PARTIAL_APPLY";
    report.failures.push({ reason: String(error?.message || error) });
  }
  // Return references into the exact source digest instead of repeating every
  // text/image value. This remains small, and never advances a conflicted field.
  report.baselineDelta = {};
  for (const [id, rows] of Object.entries(nextBaseline.collections)) {
    const previous = new Map((input.baseline.collections[id] || []).map(row => [row._id, row]));
    const desired = new Map((input.seed.collections[id] || []).map(row => [row._id, row]));
    const delta = { sourceRows: [], sourceFields: {}, hiddenRows: [] };
    for (const row of rows) {
      if (equal(row, previous.get(row._id))) continue;
      const source = desired.get(row._id);
      if (source && Object.entries(clean(source)).every(([field, value]) => equal(row[field], value))) {
        delta.sourceRows.push(row._id);
      } else if (source) {
        const fields = Object.keys(clean(source)).filter(field =>
          equal(row[field], source[field]) && !equal(row[field], previous.get(row._id)?.[field]));
        if (fields.length) delta.sourceFields[row._id] = fields;
      } else if (row.isVisible === false && previous.get(row._id)?.isVisible !== false) {
        delta.hiddenRows.push(row._id);
      }
    }
    if (delta.sourceRows.length || Object.keys(delta.sourceFields).length || delta.hiddenRows.length) {
      report.baselineDelta[id] = delta;
    }
  }
  report.completedAt = new Date().toISOString();
  report.verifiedMutations = report.applied.filter(operation => operation.verified).length;
  return boundedResult();
}'''


def load(path):
    return json.loads(path.read_text())


def validate(schema, seed, baseline):
    if schema.get("siteId") != SITE_ID or baseline.get("siteId") != SITE_ID:
        raise ValueError("Schema/baseline site does not match Michele's designated Wix site")
    ids = [c["id"] for c in schema["collections"]]
    if len(ids) != len(set(ids)) or set(ids) != set(seed["collections"]):
        raise ValueError("Collections and seed must have exactly the same unique IDs")
    for collection in schema["collections"]:
        collection_id = collection["id"]
        if not collection_id.startswith("Di"):
            raise ValueError("Only designated Di website collections are allowed")
        if collection.get("permissions") != dict.fromkeys(("insert", "update", "remove", "read"), "ADMIN"):
            raise ValueError("New collections must retain ADMIN permissions")
        fields = [f["key"] for f in collection["fields"]]
        if len(fields) != len(set(fields)) or any(not f.isidentifier() or f.startswith("_") for f in fields):
            raise ValueError(f"Invalid/duplicate source fields: {collection_id}")
        row_ids, keys = set(), set()
        for row in seed["collections"][collection_id]:
            if not row.get("_id") or not row.get("key") or row["_id"] in row_ids or row["key"] in keys:
                raise ValueError(f"Missing/duplicate source row identity: {collection_id}")
            row_ids.add(row["_id"])
            keys.add(row["key"])
            if set(row) - {"_id"} - set(fields):
                raise ValueError(f"Undeclared seed fields in {collection_id}/{row['key']}")
            if len(row) - 1 > 100:
                raise ValueError(f"Row exceeds safe bulk patch modification limit: {collection_id}/{row['key']}")
    if any(not key.startswith("Di") for key in baseline["collections"]):
        raise ValueError("Baseline includes non-website collections")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=("inspect", "apply"), default="inspect")
    parser.add_argument("--format", choices=("request", "code", "input"), default="request")
    parser.add_argument("--include-backup", action="store_true", help="Return public allowlisted pre-change CMS data for saving by the caller")
    parser.add_argument("--max-items-per-collection", type=int, default=10000)
    parser.add_argument("--finalize-report", type=Path, help="Advance baseline only from a saved verified sync response and matching source digest")
    args = parser.parse_args()
    if not 100 <= args.max_items_per_collection <= 100000:
        parser.error("Bound must be between 100 and 100000 rows per collection")
    schema = load(ROOT / "cms/collections.json")
    seed = load(ROOT / "cms/seed.json")
    baseline = load(ROOT / "cms/sync-baseline.json")
    validate(schema, seed, baseline)
    digest = hashlib.sha256(json.dumps({"schema": schema, "seed": seed}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    if args.finalize_report:
        report = load(args.finalize_report)
        if report.get("siteId") != SITE_ID or report.get("sourceDigest") != digest:
            raise ValueError("Report does not match the designated site and exact current source snapshot")
        if report.get("status") not in ("APPLIED_VERIFIED", "STOPPED_AFTER_PARTIAL_APPLY") or "baselineDelta" not in report:
            raise ValueError("Report has no verified baseline delta")
        for cid, delta in report["baselineDelta"].items():
            rows = {row["_id"]: row for row in baseline["collections"].get(cid, [])}
            desired = {row["_id"]: row for row in seed["collections"].get(cid, [])}
            for row_id in delta["sourceRows"]:
                rows.setdefault(row_id, {"_id": row_id}).update(desired[row_id])
            for row_id, fields in delta["sourceFields"].items():
                for field in fields:
                    rows.setdefault(row_id, {"_id": row_id})[field] = desired[row_id][field]
            for row_id in delta["hiddenRows"]:
                rows[row_id]["isVisible"] = False
            baseline["collections"][cid] = list(rows.values())
        baseline["sourceDigest"] = digest
        baseline["lastSyncAt"] = report.get("completedAt")
        (ROOT / "cms/sync-baseline.json").write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n")
        print("Advanced baseline from verified fields only.")
        return
    content = {
        "siteId": SITE_ID,
        "mode": args.mode,
        "sourceDigest": digest,
        "includeBackup": args.include_backup,
        "maxItemsPerCollection": args.max_items_per_collection,
        "schema": schema,
        "seed": seed,
        "baseline": baseline,
    }
    if args.format == "code":
        print(CODE)
    elif args.format == "input":
        print(json.dumps(content, ensure_ascii=False, indent=2))
    else:
        request = {
            "siteId": SITE_ID,
            "hasMutations": args.mode == "apply",
            "reason": "Add the remaining editable website CMS fields and content while preserving Michele's changes, permissions, unrelated data, and existing Wix frontend.",
            "sourceDocUrls": DOCS,
            "code": CODE,
            "files": "=== FILE: cms-sync-input.json ===\n" + json.dumps(content, ensure_ascii=False, indent=2),
        }
        print(json.dumps(request, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError) as error:
        sys.exit(str(error))
