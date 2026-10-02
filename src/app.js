/*
 * Planning Knowledge Hub: dependency-free, offline-capable browser application.
 * Shared data is read-only here. Browser drafts never modify published data.
 * Do not put credentials in this file, JSON data, or client-side storage.
 */
(function () {
  'use strict';
  const DATA = JSON.parse(document.getElementById('hub-data').textContent);
  const CONFIG = DATA.config;
  const TAX = DATA.taxonomy;
  const PUBLISHED = DATA.resources;
  const COLLECTIONS = DATA.collections;
  const EXAMPLES = DATA.examples;
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const norm = value => String(value ?? '').trim().toLocaleLowerCase();
  const words = value => String(value ?? '').trim().split(/\s+/u).filter(Boolean).length;
  const idPattern = /^[a-z0-9][a-z0-9-]{0,99}$/;
  const repoPattern = /^[A-Za-z0-9][A-Za-z0-9-]{0,38}\/[A-Za-z0-9_.-]{1,100}$/;
  const repo = repoPattern.test(CONFIG.githubRepository || '') && !/\/(\.|\.\.)$/.test(CONFIG.githubRepository) ? CONFIG.githubRepository : '';
  const repoURL = repo ? 'https://github.com/' + repo : '';
  const storageKey = (CONFIG.storageNamespace || 'planning-knowledge-hub-v2') + ':' + (repo || 'prototype');
  let persistenceAvailable = true;
  let storageWarning = '';
  let view = 'published';
  let currentResource = null;
  let currentCollection = null;

  function plainObject(value) {
    return value !== null && typeof value === 'object' && !Array.isArray(value);
  }
  function text(value, max, label, required = false) {
    if (value !== undefined && value !== null && typeof value !== 'string') throw new Error(label + ' must be text.');
    const result = (value || '').trim();
    if (required && !result) throw new Error(label + ' is required.');
    if (result.length > max) throw new Error(label + ' is too long.');
    return result;
  }
  function list(value, allowed, label, max = 24) {
    if (value === undefined) return [];
    if (!Array.isArray(value) || value.length > max || value.some(x => typeof x !== 'string' || x.length > 140)) throw new Error(label + ' must be a short list of text values.');
    const clean = [...new Set(value.map(x => x.trim()).filter(Boolean))];
    if (allowed && clean.some(x => !allowed.includes(x))) throw new Error(label + ' contains an unknown category.');
    return clean;
  }
  function safeURL(value) {
    try {
      const url = new URL(value);
      return ['http:', 'https:'].includes(url.protocol) && !url.username && !url.password && url.hostname ? url.href : '';
    } catch (_) { return ''; }
  }
  function uid(prefix) {
    const random = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID().replaceAll('-', '').slice(0, 12) : Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
    return prefix + '-' + random;
  }
  function normalizeRecord(raw, kind) {
    if (!plainObject(raw)) throw new Error('The record must be a JSON object.');
    const id = text(raw.id, 100, 'Record ID', true);
    if (!idPattern.test(id)) throw new Error('Record IDs must use lowercase letters, numbers, and hyphens.');
    const record = {
      id,
      title: text(raw.title, kind === 'resource' ? 160 : 140, 'Title', true),
      description: text(raw.description, 2200, 'Description', true),
      fields: list(raw.fields, TAX.fields.map(x => x.id), 'Fields'),
      topics: list(raw.topics, TAX.topics.map(x => x.id), 'Planning tracks')
    };
    const count = words(record.description);
    const minWords = kind === 'resource' ? 50 : 20;
    if (count < minWords || count > 100) throw new Error('The description must contain ' + minWords + '–100 words (currently ' + count + ').');
    if (!record.fields.length) throw new Error('Select at least one field / discipline.');
    if (kind === 'resource') {
      if (id.startsWith('example-')) throw new Error('Example IDs are reserved for fictional display records.');
      record.url = text(raw.url, 1500, 'Resource URL', true);
      if (!safeURL(record.url)) throw new Error('Use a valid http or https resource URL without embedded credentials.');
      record.domain = text(raw.domain, 40, 'Domain', true);
      record.resourceType = text(raw.resourceType, 60, 'Resource type', true);
      if (!TAX.domains.includes(record.domain)) throw new Error('Select a valid resource domain.');
      if (!TAX.resourceTypes.includes(record.resourceType)) throw new Error('Select a valid resource type.');
      record.collectionIds = list(raw.collectionIds, null, 'Collections');
      if (record.collectionIds.some(x => !idPattern.test(x))) throw new Error('A collection ID is invalid.');
      record.method = text(raw.method, 120, 'Method');
      record.keywords = list(raw.keywords, null, 'Keywords', 20);
      record.institution = text(raw.institution, 180, 'Institution');
      record.contributor = text(raw.contributor, 120, 'Contributor');
      record.date = text(raw.date, 60, 'Date / version');
      record.geography = text(raw.geography, 140, 'Geography');
      record.license = text(raw.license, 700, 'Reuse notes');
      record.audience = text(raw.audience, 180, 'Audience');
    } else {
      record.organizerType = text(raw.organizerType, 80, 'Group type', true);
      if (!TAX.organizerTypes.includes(record.organizerType)) throw new Error('Select a valid group type.');
      record.organizer = text(raw.organizer, 180, 'Organizer');
      record.institution = text(raw.institution, 250, 'Institutions');
      record.status = 'proposed'; // A local import never creates an official collection.
    }
    return record;
  }
  function normalizePacket(raw) {
    if (!plainObject(raw)) throw new Error('Expected a contribution packet or resource record.');
    let p = raw;
    if (!p.kind && p.id) p = {schemaVersion: 1, kind: Object.hasOwn(p, 'url') ? 'resource' : 'collection', action: 'add', record: p};
    if (p.schemaVersion !== 1 || !['resource', 'collection'].includes(p.kind)) throw new Error('Unsupported packet type or schema version.');
    const action = p.action || 'add';
    if (!['add', 'update'].includes(action)) throw new Error('Unsupported contribution action.');
    return {schemaVersion: 1, kind: p.kind, action, record: normalizeRecord(p.record, p.kind)};
  }
  function normalizeWorkspace(raw) {
    if (!plainObject(raw) || !Array.isArray(raw.resources) || !Array.isArray(raw.collections)) throw new Error('Invalid workspace format.');
    if (raw.resources.length + raw.collections.length > 500) throw new Error('A workspace may contain at most 500 drafts.');
    const clean = {resources: [], collections: []};
    for (const [key, kind] of [['collections','collection'], ['resources','resource']]) {
      const seen = new Set();
      clean[key] = raw[key].map(p => {
        const packet = normalizePacket(p);
        if (packet.kind !== kind || seen.has(packet.record.id)) throw new Error('Incorrect or duplicate draft in workspace.');
        seen.add(packet.record.id);
        return packet;
      });
    }
    checkCollectionReferences(clean.resources, clean.collections);
    return clean;
  }
  function checkCollectionReferences(resources, collections) {
    const ids = new Set([...COLLECTIONS.map(x => x.id), ...collections.map(x => x.record.id)]);
    for (const packet of resources) {
      if (packet.record.collectionIds.some(id => !ids.has(id))) throw new Error('A resource refers to an unknown collection. Import its collection packet first, or include it in the workspace.');
    }
  }
  function loadState() {
    try {
      const value = localStorage.getItem(storageKey);
      return value ? normalizeWorkspace(JSON.parse(value)) : {resources: [], collections: []};
    } catch (error) {
      storageWarning = 'Saved drafts could not be loaded. No published data was changed. ' + error.message;
      return {resources: [], collections: []};
    }
  }
  let state = loadState();
  function persist() {
    try {
      localStorage.setItem(storageKey, JSON.stringify(state));
      persistenceAvailable = true;
      return true;
    } catch (_) {
      persistenceAvailable = false;
      return false;
    }
  }
  function status(id, message, isError = false) {
    const el = $(id);
    el.hidden = false;
    el.classList.toggle('error', isError);
    el.textContent = message;
  }
  function options(id, items, placeholder, keep = false) {
    const el = $(id), old = keep ? el.value : '';
    el.innerHTML = '<option value="">' + esc(placeholder) + '</option>' + items.map(x => {
      const value = typeof x === 'string' ? x : x.id;
      const label = typeof x === 'string' ? x : x.label;
      return '<option value="' + esc(value) + '">' + esc(label) + '</option>';
    }).join('');
    if ([...el.options].some(x => x.value === old)) el.value = old;
  }
  function checkboxes(id, items, selected = []) {
    $(id).innerHTML = items.map(x => '<label class="check-option"><input type="checkbox" value="' + esc(x.id) + '"' + (selected.includes(x.id) ? ' checked' : '') + '><span>' + esc(x.label) + '</span></label>').join('');
  }
  const checked = id => [...$(id).querySelectorAll('input:checked')].map(x => x.value);
  function setChecked(id, values) {
    $(id).querySelectorAll('input').forEach(x => { x.checked = (values || []).includes(x.value); });
  }
  function allCollections() {
    const map = new Map(COLLECTIONS.map(x => [x.id, x]));
    state.collections.forEach(p => { if (!map.has(p.record.id)) map.set(p.record.id, {...p.record, local: true}); });
    return [...map.values()];
  }
  const labels = (ids, taxonomy) => (ids || []).map(id => taxonomy.find(x => x.id === id)?.label || id);
  const fieldLabels = ids => labels(ids, TAX.fields);
  const topicLabels = ids => labels(ids, TAX.topics);
  const collectionNames = ids => (ids || []).map(id => allCollections().find(x => x.id === id)?.title || id);

  function initTaxonomy() {
    options('domain', TAX.domains, 'All domains');
    options('formDomain', TAX.domains, 'Select a domain');
    options('fieldFilter', TAX.fields, 'All fields');
    options('planningTopic', TAX.topics, 'All planning tracks');
    options('resourceType', TAX.resourceTypes, 'All types');
    options('formType', TAX.resourceTypes, 'Select a type');
    options('organizerType', TAX.organizerTypes, 'Select a group type');
    checkboxes('formFields', TAX.fields);
    checkboxes('collectionFields', TAX.fields);
    checkboxes('formTopics', TAX.topics);
    checkboxes('collectionTopics', TAX.topics);
    $('methodOptions').innerHTML = TAX.methods.map(x => '<option value="' + esc(x) + '"></option>').join('');
  }
  function refreshDynamicOptions() {
    const selected = checked('formCollections');
    const collections = allCollections().map(x => ({id: x.id, label: x.title + (x.local ? ' (local draft)' : '')}));
    options('collectionFilter', collections, 'All collections', true);
    checkboxes('formCollections', collections, selected);
    const methods = [...new Set([...TAX.methods, ...PUBLISHED.map(x => x.method), ...EXAMPLES.map(x => x.method), ...state.resources.map(x => x.record.method)].filter(Boolean))].sort((a,b) => a.localeCompare(b));
    options('methodFilter', methods, 'All methods, including non-AI', true);
  }
  function sourceRecords() {
    return view === 'examples' ? EXAMPLES : view === 'drafts' ? state.resources.map(p => ({...p.record, local: true, action: p.action})) : PUBLISHED;
  }
  function filteredRecords() {
    const query = norm($('search').value);
    const result = sourceRecords().filter(r => {
      const haystack = norm([r.title, r.description, r.domain, r.resourceType, r.method, r.institution, r.contributor, r.geography, r.audience, ...fieldLabels(r.fields), ...topicLabels(r.topics), ...collectionNames(r.collectionIds), ...(r.keywords || [])].join(' '));
      return (!query || query.split(/\s+/).every(term => haystack.includes(term)))
        && (!$('domain').value || r.domain === $('domain').value)
        && (!$('fieldFilter').value || (r.fields || []).includes($('fieldFilter').value))
        && (!$('planningTopic').value || (r.topics || []).includes($('planningTopic').value))
        && (!$('collectionFilter').value || (r.collectionIds || []).includes($('collectionFilter').value))
        && (!$('resourceType').value || r.resourceType === $('resourceType').value)
        && (!$('methodFilter').value || norm(r.method) === norm($('methodFilter').value));
    });
    return result.sort((a, b) => ($('sort').value === 'domain' ? a.domain.localeCompare(b.domain) : 0) || a.title.localeCompare(b.title));
  }
  function renderResource(r, mode = view, controls = true) {
    const isExample = mode === 'examples' || r.isExample;
    const isLocal = mode === 'drafts' || r.local;
    const url = safeURL(r.url);
    const title = !isExample && url ? '<a class="resource-title" href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">' + esc(r.title) + '</a>' : '<span class="resource-title">' + esc(r.title) + '</span>';
    const badge = isExample ? '<span class="badge">Fictional example</span>' : isLocal ? '<span class="badge draft">Local draft' + (r.action === 'update' ? ' · Suggested update' : '') + '</span>' : '<span class="badge">Published entry</span>';
    const metadata = [fieldLabels(r.fields).join(' · '), r.institution, r.date].filter(Boolean);
    const detailRows = [
      ['Planning tracks', topicLabels(r.topics).join('; ')],
      ['Collections', collectionNames(r.collectionIds).join('; ')],
      ['Method / tool', r.method], ['Keywords', (r.keywords || []).join(', ')],
      ['Audience', r.audience], ['Geography', r.geography],
      ['Contributor', r.contributor], ['Reuse / attribution', r.license || 'Not specified. Check the original source.']
    ].filter(x => x[1]);
    const action = !controls || isExample ? '' : isLocal ? '<button class="link-button" type="button" data-edit-resource="' + esc(r.id) + '">Edit local draft</button>' : '<button class="link-button" type="button" data-suggest-id="' + esc(r.id) + '">Suggest an update</button>';
    return '<article class="resource-item"><div class="resource-top"><span class="resource-type">' + esc(r.domain) + ' / ' + esc(r.resourceType) + '</span>' + badge + '</div><h3>' + title + '</h3><p class="resource-description">' + esc(r.description) + '</p><div class="resource-meta">' + metadata.map(x => '<span>' + esc(x) + '</span>').join('') + '</div><details><summary>Resource details</summary>' + detailRows.map(x => '<p><strong>' + esc(x[0]) + ':</strong> ' + esc(x[1]) + '</p>').join('') + '</details>' + (action ? '<div class="resource-actions">' + action + '</div>' : '') + '</article>';
  }
  function renderCatalog() {
    document.querySelectorAll('.segmented [data-view]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.view === view)));
    $('publishedCount').textContent = PUBLISHED.length;
    $('draftCount').textContent = state.resources.length;
    $('exampleNotice').hidden = view !== 'examples';
    $('draftNotice').hidden = view !== 'drafts';
    $('catalogNote').textContent = view === 'examples' ? 'Demonstration only. No real resources are represented.' : view === 'drafts' ? 'Private to this browser, not a shared account.' : PUBLISHED.length ? 'Resources included in this version of the public catalog.' : 'The public catalog is ready for its first resources.';
    const result = filteredRecords(), total = sourceRecords().length;
    const noun = view === 'examples' ? 'example entries' : view === 'drafts' ? 'local resource drafts' : 'published resources';
    $('resultCount').textContent = result.length + ' of ' + total + ' ' + noun;
    if (result.length) { $('resourceList').innerHTML = result.map(r => renderResource(r)).join(''); return; }
    const isFiltered = ['search','domain','fieldFilter','planningTopic','collectionFilter','resourceType','methodFilter'].some(id => $(id).value);
    let title = 'The library starts with your contributions.';
    let message = 'No resources have been published in this prototype. Explore fictional examples to see how different fields fit, or prepare the first resource.';
    let buttons = '<button class="btn secondary compact" type="button" data-set-view="examples">Preview example entries</button><a class="btn compact" href="#contribute" data-open-tab="resource">Prepare a resource</a>';
    if (isFiltered) {
      title = 'No matching entries in this view.';
      message = 'Try a broader search or clear the filters. Example entries, local drafts, and the published catalog are intentionally kept separate.';
      buttons = '<button class="btn secondary compact" type="button" data-clear-all>Clear filters</button>';
    } else if (view === 'drafts') {
      title = 'Your local workspace is empty.';
      message = 'Save a resource through the contribution form to preview it here. Nothing is sent or published when you create a local draft.';
      buttons = '<a class="btn compact" href="#contribute" data-open-tab="resource">Prepare a resource</a>';
    }
    $('resourceList').innerHTML = '<div class="empty-state"><div class="empty-symbol" aria-hidden="true">+</div><h3>' + title + '</h3><p>' + message + '</p><div class="button-row">' + buttons + '</div></div>';
  }
  function renderCollection(c, local = false, controls = true) {
    const count = PUBLISHED.filter(r => (r.collectionIds || []).includes(c.id)).length;
    const badge = local ? 'Local collection draft' : c.status === 'starter' ? 'Starter collection' : c.status === 'proposed' ? 'Proposed collection' : 'Collection';
    const initials = c.title.split(/\s+/).slice(0, 2).map(x => x[0]).join('').toUpperCase();
    const organizer = c.organizer ? c.organizer : 'Organizer not yet assigned';
    const footer = controls ? '<div class="collection-footer"><span>' + (local ? 'Not published' : count + ' published resources') + '</span><button class="link-button" type="button" data-filter-collection="' + esc(c.id) + '" data-collection-local="' + local + '">' + (local ? 'Browse local drafts' : 'Browse collection') + ' →</button></div>' : '';
    return '<article class="card collection-card"><div class="collection-header"><span class="collection-initial" aria-hidden="true">' + esc(initials) + '</span><span class="badge' + (local ? ' draft' : '') + '">' + badge + '</span></div><h3>' + esc(c.title) + '</h3><p>' + esc(c.description) + '</p><div class="collection-meta"><strong>' + esc(organizer) + '</strong>' + (c.institution ? '<br>' + esc(c.institution) : '') + '<br>' + esc(fieldLabels(c.fields).join(' · ')) + '</div>' + footer + '</article>';
  }
  function renderCollections() {
    $('collectionGrid').innerHTML = COLLECTIONS.map(c => renderCollection(c)).join('') + state.collections.map(p => renderCollection(p.record, true)).join('');
  }
  function renderDrafts() {
    const packets = [...state.collections, ...state.resources];
    $('draftsList').innerHTML = packets.length ? packets.map(p => '<div class="draft-item"><div><strong>' + esc(p.record.title) + '</strong><small>' + (p.kind === 'resource' ? 'Resource' : 'Collection') + ' · ' + (p.action === 'update' ? 'Suggested update' : 'New contribution') + ' · Local only</small></div><div class="draft-actions"><button class="link-button" type="button" data-draft-action="edit" data-kind="' + p.kind + '" data-id="' + esc(p.record.id) + '">Edit</button><button class="link-button" type="button" data-draft-action="export" data-kind="' + p.kind + '" data-id="' + esc(p.record.id) + '">Export</button><button class="link-button" type="button" data-draft-action="delete" data-kind="' + p.kind + '" data-id="' + esc(p.record.id) + '">Delete</button></div></div>').join('') : '<p class="muted small">No drafts saved yet.</p>';
    $('downloadAllDrafts').disabled = !packets.length;
    $('clearAllDrafts').disabled = !packets.length;
  }
  function refresh() { refreshDynamicOptions(); renderCatalog(); renderCollections(); renderDrafts(); }
  function setView(value) { if (['published','examples','drafts'].includes(value)) { view = value; renderCatalog(); } }
  function clearFilters() {
    ['search','domain','fieldFilter','planningTopic','collectionFilter','resourceType','methodFilter'].forEach(id => { $(id).value = ''; });
    $('sort').value = 'title'; renderCatalog();
  }
  function navigateTo(id) {
    if (location.hash !== '#' + id) location.hash = id;
    $(id)?.scrollIntoView({block: 'start'});
  }
  function setTab(key, focus = false) {
    if (!['resource','collection','drafts'].includes(key)) return;
    document.querySelectorAll('[data-tab]').forEach(b => {
      const active = b.dataset.tab === key;
      b.setAttribute('aria-selected', String(active)); b.tabIndex = active ? 0 : -1;
      $('panel-' + b.dataset.tab).hidden = !active;
      if (active && focus) b.focus();
    });
  }
  function updateWordCounts() {
    const n = words($('resourceDescription').value), c = words($('collectionDescription').value);
    $('wordCount').textContent = n + ' words · Target: 50–100 words';
    $('collectionWordCount').textContent = c + ' words · Target: 20–100 words';
  }
  function downloadJSON(value, filename) {
    const blob = new Blob([JSON.stringify(value, null, 2) + '\n'], {type: 'application/json;charset=utf-8'});
    const url = URL.createObjectURL(blob), a = document.createElement('a');
    a.href = url; a.download = filename; document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  }
  function markdown(packet) {
    return '## ' + (packet.kind === 'resource' ? 'Resource contribution' : 'Collection proposal') + '\n\nAction: ' + packet.action + '\n\nPlease check the source, metadata, reuse conditions, and collection ownership before adding this packet to the shared repository.\n\n```json\n' + JSON.stringify(packet, null, 2) + '\n```\n\nThis packet was prepared with the Planning Knowledge Hub form. It is not an automatic publication request or an assertion of official committee status.\n';
  }
  function setupHandoff(packet) {
    const kind = packet.kind, link = $(kind + 'GitHub'), note = $(kind + 'HandoffNote');
    const body = markdown(packet);
    $(kind + 'PacketText').value = body;
    if (!repoURL) {
      link.removeAttribute('href'); link.setAttribute('aria-disabled', 'true'); link.tabIndex = -1;
      note.textContent = 'GitHub handoff is not connected. Download the JSON file and share it with the designated maintainer. Saving or downloading does not submit it.';
      return;
    }
    const url = new URL(repoURL + '/issues/new');
    url.searchParams.set('template', packet.kind + '.md');
    url.searchParams.set('title', '[' + (packet.kind === 'resource' ? 'Resource' : 'Collection') + '] ' + packet.record.title);
    url.searchParams.set('body', body);
    if (url.href.length > 7000) {
      url.searchParams.delete('body');
      note.textContent = 'This packet is too long for this site’s URL-prefill limit. Copy the submission above, open GitHub, paste it into the issue, and submit it there. A GitHub account is required.';
    } else {
      note.textContent = 'This opens a prefilled GitHub issue. Sign in, check the public content, and submit the issue there. Opening the link alone does not send or publish the contribution.';
    }
    link.href = url.href; link.removeAttribute('aria-disabled'); link.tabIndex = 0;
  }
  async function copyPacket(kind) {
    const packet = kind === 'resource' ? currentResource : currentCollection;
    if (!packet) return;
    const value = markdown(packet);
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(value);
      status(kind + 'Status', 'Submission text copied. Nothing has been sent or published.');
    } catch (_) {
      const area = $(kind + 'PacketText'); area.closest('details').open = true; area.focus(); area.select();
      status(kind + 'Status', 'Automatic copying is unavailable here. The submission text is selected; copy it using your browser or keyboard.');
    }
  }
  function showPreview(packet) {
    const kind = packet.kind;
    if (kind === 'resource') { currentResource = packet; $('resourcePreviewCard').innerHTML = renderResource({...packet.record, local: true, action: packet.action}, 'drafts', false); }
    else { currentCollection = packet; $('collectionPreviewCard').innerHTML = renderCollection(packet.record, true, false); }
    $(kind + 'Preview').hidden = false;
    setupHandoff(packet);
  }
  function upsert(packet) {
    const key = packet.kind === 'resource' ? 'resources' : 'collections';
    const i = state[key].findIndex(p => p.record.id === packet.record.id);
    if (i === -1 && state.resources.length + state.collections.length >= 500) throw new Error('The local workspace is limited to 500 drafts. Export and remove older drafts first.');
    if (i === -1) state[key].push(packet); else state[key][i] = packet;
  }
  function saveResource(event) {
    event.preventDefault();
    if (!$('resourceForm').reportValidity()) return;
    try {
      const record = normalizeRecord({
        id: $('recordId').value || uid('res'), title: $('resourceTitle').value, url: $('resourceUrl').value,
        description: $('resourceDescription').value, domain: $('formDomain').value, resourceType: $('formType').value,
        fields: checked('formFields'), topics: checked('formTopics'), collectionIds: checked('formCollections'),
        method: $('formMethod').value, keywords: $('formKeywords').value.split(',').map(x => x.trim()).filter(Boolean),
        institution: $('institution').value, contributor: $('contributor').value, date: $('resourceDate').value,
        geography: $('geography').value, license: $('license').value, audience: $('audience').value
      }, 'resource');
      const packet = {schemaVersion: 1, kind: 'resource', action: $('recordAction').value || 'add', record};
      checkCollectionReferences([packet], state.collections);
      $('recordId').value = record.id;
      upsert(packet); const saved = persist(); refresh(); showPreview(packet);
      status('resourceStatus', saved ? 'Saved in this browser only. Preview the entry below, then download or explicitly share its contribution packet. It is not published.' : 'Prepared for this session only: browser storage is unavailable. Download the JSON now to keep a copy. Nothing was sent or published.');
      $('resourceStatus').focus({preventScroll: true});
    } catch (error) { status('resourceStatus', error.message, true); $('resourceStatus').focus(); }
  }
  function saveCollection(event) {
    event.preventDefault();
    if (!$('collectionForm').reportValidity()) return;
    try {
      const record = normalizeRecord({
        id: $('collectionId').value || uid('collection'), title: $('collectionTitle').value,
        description: $('collectionDescription').value, organizerType: $('organizerType').value,
        organizer: $('organizer').value, institution: $('collectionInstitution').value,
        fields: checked('collectionFields'), topics: checked('collectionTopics')
      }, 'collection');
      const old = state.collections.find(p => p.record.id === record.id);
      const packet = {schemaVersion: 1, kind: 'collection', action: old?.action || 'add', record};
      $('collectionId').value = record.id; upsert(packet); const saved = persist(); refresh(); showPreview(packet);
      status('collectionStatus', saved ? 'Collection draft saved in this browser. It can now be selected for local resource drafts. No official collection, publishing access, or shared record has been created.' : 'Collection prepared for this session only. Browser storage is unavailable, so export the JSON to keep a copy. This does not create a shared collection.');
      $('collectionStatus').focus({preventScroll: true});
    } catch (error) { status('collectionStatus', error.message, true); $('collectionStatus').focus(); }
  }
  function resetResource() {
    $('resourceForm').reset(); $('recordId').value = ''; $('recordAction').value = 'add';
    $('resourceFormHeading').textContent = 'Prepare a resource';
    $('resourcePreview').hidden = true; $('resourceStatus').hidden = true; currentResource = null; updateWordCounts();
  }
  function resetCollection() {
    $('collectionForm').reset(); $('collectionId').value = '';
    $('collectionPreview').hidden = true; $('collectionStatus').hidden = true; currentCollection = null; updateWordCounts();
  }
  function editResource(record, action = 'add') {
    resetResource();
    const fields = {recordId:'id',resourceTitle:'title',resourceUrl:'url',resourceDescription:'description',formDomain:'domain',formType:'resourceType',formMethod:'method',institution:'institution',contributor:'contributor',resourceDate:'date',geography:'geography',license:'license',audience:'audience'};
    for (const [id, key] of Object.entries(fields)) $(id).value = record[key] || '';
    $('recordAction').value = action; $('formKeywords').value = (record.keywords || []).join(', ');
    setChecked('formFields', record.fields); setChecked('formTopics', record.topics); setChecked('formCollections', record.collectionIds);
    $('resourceFormHeading').textContent = action === 'update' ? 'Suggest an update to a published resource' : 'Edit your local resource draft';
    updateWordCounts(); setTab('resource'); navigateTo('contribute'); $('resourceTitle').focus({preventScroll: true});
  }
  function editCollection(packet) {
    resetCollection(); const r = packet.record;
    const fields = {collectionId:'id',collectionTitle:'title',collectionDescription:'description',organizerType:'organizerType',organizer:'organizer',collectionInstitution:'institution'};
    for (const [id, key] of Object.entries(fields)) $(id).value = r[key] || '';
    setChecked('collectionFields', r.fields); setChecked('collectionTopics', r.topics);
    updateWordCounts(); setTab('collection'); navigateTo('contribute'); $('collectionTitle').focus({preventScroll: true});
  }
  async function importJSON(event) {
    const file = event.target.files?.[0]; if (!file) return;
    try {
      if (file.size > 1024 * 1024) throw new Error('The import file is larger than 1 MB.');
      const raw = JSON.parse(await file.text());
      let incoming;
      if (raw.kind === 'workspace' && raw.schemaVersion === 1) incoming = normalizeWorkspace(raw);
      else {
        const packet = normalizePacket(raw);
        incoming = {resources: packet.kind === 'resource' ? [packet] : [], collections: packet.kind === 'collection' ? [packet] : []};
      }
      const merged = {resources: [...state.resources], collections: [...state.collections]};
      for (const key of ['collections','resources']) {
        for (const p of incoming[key]) {
          const i = merged[key].findIndex(x => x.record.id === p.record.id);
          if (i === -1) merged[key].push(p); else merged[key][i] = p;
        }
      }
      checkCollectionReferences(merged.resources, merged.collections);
      if (merged.resources.length + merged.collections.length > 500) throw new Error('This import exceeds the 500-draft workspace limit.');
      state = merged; const saved = persist(); refresh();
      status('workspaceStatus', 'Imported ' + (incoming.resources.length + incoming.collections.length) + ' contribution packet(s) as local drafts. ' + (saved ? 'Saved in this browser. ' : 'Storage is unavailable; export before closing. ') + 'No shared or published records were changed.');
    } catch (error) { status('workspaceStatus', 'Import stopped: ' + error.message, true); }
    event.target.value = '';
  }
  function handleDraftAction(button) {
    const key = button.dataset.kind === 'resource' ? 'resources' : 'collections';
    const p = state[key].find(x => x.record.id === button.dataset.id); if (!p) return;
    if (button.dataset.draftAction === 'export') { downloadJSON(p, p.record.id + '.json'); return; }
    if (button.dataset.draftAction === 'edit') { p.kind === 'resource' ? editResource(p.record, p.action) : editCollection(p); return; }
    if (p.kind === 'collection' && !COLLECTIONS.some(c => c.id === p.record.id) && state.resources.some(r => r.record.collectionIds.includes(p.record.id))) {
      status('workspaceStatus', 'This collection is used by local resource drafts. Remove those collection associations before deleting the collection draft.', true); return;
    }
    if (!confirm('Delete this local draft? Published records will not change.')) return;
    state[key] = state[key].filter(x => x.record.id !== p.record.id);
    if (p.kind === 'resource' && $('recordId').value === p.record.id) resetResource();
    if (p.kind === 'collection' && $('collectionId').value === p.record.id) resetCollection();
    const saved = persist(); refresh();
    status('workspaceStatus', saved ? 'Local draft deleted. Published records were not changed.' : 'Draft removed for this session, but browser storage could not be updated.');
  }
  function handleHash() {
    const hash = location.hash.slice(1);
    const legacy = {education:'Education',research:'Research',practice:'Practice'};
    if (legacy[hash]) { clearFilters(); $('domain').value = legacy[hash]; setView('published'); $('explore').scrollIntoView(); }
    else if (hash.startsWith('explore?')) {
      const params = new URLSearchParams(hash.split('?')[1]);
      clearFilters();
      if (allCollections().some(c => c.id === params.get('collection'))) $('collectionFilter').value = params.get('collection');
      setView('published'); $('explore').scrollIntoView();
    }
  }

  // Event setup. Dynamic controls use one delegated click listener.
  $('resourceForm').addEventListener('submit', saveResource);
  $('collectionForm').addEventListener('submit', saveCollection);
  $('resetResource').addEventListener('click', resetResource);
  $('resetCollection').addEventListener('click', resetCollection);
  for (const kind of ['resource','collection']) {
    $(kind + 'Form').addEventListener('input', () => {
      $(kind + 'Preview').hidden = true; $(kind + 'Status').hidden = true;
      if (kind === 'resource') currentResource = null; else currentCollection = null;
      updateWordCounts();
    });
    $(kind + 'Form').addEventListener('change', () => { $(kind + 'Preview').hidden = true; });
  }
  $('downloadResource').addEventListener('click', () => { if (currentResource) downloadJSON(currentResource, currentResource.record.id + '.json'); });
  $('downloadCollection').addEventListener('click', () => { if (currentCollection) downloadJSON(currentCollection, currentCollection.record.id + '.json'); });
  $('copyResource').addEventListener('click', () => copyPacket('resource'));
  $('copyCollection').addEventListener('click', () => copyPacket('collection'));
  $('importFile').addEventListener('change', importJSON);
  $('downloadAllDrafts').addEventListener('click', () => downloadJSON({schemaVersion: 1, kind: 'workspace', ...state}, 'planning-hub-local-workspace.json'));
  $('clearAllDrafts').addEventListener('click', () => {
    if (!confirm('Delete all drafts in this browser? Export a backup first. Published data will not change.')) return;
    state = {resources: [], collections: []}; const saved = persist(); resetResource(); resetCollection(); refresh();
    status('workspaceStatus', saved ? 'All local drafts deleted. Published records were not changed.' : 'Drafts cleared in this session, but browser storage could not be updated.');
  });
  $('search').addEventListener('input', renderCatalog);
  ['domain','fieldFilter','planningTopic','collectionFilter','resourceType','methodFilter','sort'].forEach(id => $(id).addEventListener('change', renderCatalog));
  $('clearFilters').addEventListener('click', clearFilters);
  document.addEventListener('click', event => {
    const el = event.target.closest('button,a'); if (!el) return;
    if (el.getAttribute('aria-disabled') === 'true') { event.preventDefault(); return; }
    if (el.dataset.view || el.dataset.setView) { setView(el.dataset.view || el.dataset.setView); return; }
    if (el.hasAttribute('data-clear-all')) { clearFilters(); return; }
    if (el.dataset.tab) { setTab(el.dataset.tab); return; }
    if (el.dataset.openTab) { setTab(el.dataset.openTab); }
    if (el.dataset.domain) { event.preventDefault(); clearFilters(); $('domain').value = el.dataset.domain; setView('published'); navigateTo('explore'); }
    if (el.dataset.filterCollection) { clearFilters(); $('collectionFilter').value = el.dataset.filterCollection; setView(el.dataset.collectionLocal === 'true' ? 'drafts' : 'published'); navigateTo('explore'); }
    if (el.dataset.editResource) { const p = state.resources.find(x => x.record.id === el.dataset.editResource); if (p) editResource(p.record, p.action); }
    if (el.dataset.suggestId) { const r = PUBLISHED.find(x => x.id === el.dataset.suggestId); if (r) editResource(r, 'update'); }
    if (el.dataset.draftAction) handleDraftAction(el);
  });
  document.querySelector('[role="tablist"]').addEventListener('keydown', e => {
    if (!['ArrowLeft','ArrowRight','Home','End'].includes(e.key)) return;
    const tabs = [...document.querySelectorAll('[data-tab]')], i = tabs.indexOf(document.activeElement);
    if (i < 0) return;
    e.preventDefault();
    const next = e.key === 'Home' ? 0 : e.key === 'End' ? tabs.length - 1 : (i + (e.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
    setTab(tabs[next].dataset.tab, true);
  });
  const toggle = document.querySelector('.nav-toggle'), nav = $('site-navigation');
  toggle.addEventListener('click', () => { const open = nav.classList.toggle('open'); toggle.setAttribute('aria-expanded', String(open)); });
  nav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => { nav.classList.remove('open'); toggle.setAttribute('aria-expanded','false'); }));
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && nav.classList.contains('open')) { nav.classList.remove('open'); toggle.setAttribute('aria-expanded','false'); toggle.focus(); } });
  $('openDeveloperGuide').addEventListener('click', () => { $('developerGuide').open = true; });
  window.addEventListener('hashchange', handleHash);
  document.querySelectorAll('[data-site-title]').forEach(el => { el.textContent = CONFIG.siteTitle; });
  document.title = CONFIG.siteTitle;
  document.querySelector('.brand').setAttribute('aria-label', CONFIG.siteTitle + ' home');
  $('version').textContent = CONFIG.version;
  $('year').textContent = new Date().getFullYear();
  if (repoURL) {
    $('repositoryLink').href = repoURL; $('repositoryLink').textContent = 'View shared repository ↗'; $('repositoryLink').removeAttribute('aria-disabled'); $('repositoryLink').tabIndex = 0;
    $('connectionLabel').textContent = 'Working prototype · GitHub handoff configured';
    $('repoSetupNote').textContent = 'Repository handoff is configured. GitHub sign-in, repository permissions, and a maintainer action are still required to submit and publish changes.';
  }
  initTaxonomy(); refresh(); updateWordCounts(); handleHash();
  if (storageWarning) status('workspaceStatus', storageWarning, true);
})();
