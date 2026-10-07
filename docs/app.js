// Reno Today page: loads docs/data/*.json and renders the chosen day.
// Every piece of text from the data goes through L.esc, and every link through L.safeUrl.
import * as L from './lib.js?v=5fbf11a6';

const RAW = 'https://raw.githubusercontent.com/natanforestree/reno-today/main/docs/data/';
const FILTERS_KEY = 'reno-today:filters';
const FILTERS = [['free', 'Free'], ['outdoors', 'Outdoors'], ['little', 'Little ones only'], ['hide21', 'Hide 21+'],
  ['music', 'Live music']];
const HINT_LABEL = { 'all-ages': 'all ages', outdoors: 'outdoors', '21+': '21+' };
const params = new URLSearchParams(location.search);
const fakeNow = Date.parse(params.get('now') ?? '');
const now = () => (Number.isFinite(fakeNow) ? fakeNow : Date.now());
const $ = (id) => document.getElementById(id);
const state = { data: null, day: null, today: null, loadedAt: 0, loading: false, filters: loadFilters() };
const RELOAD_AFTER_MS = 3600e3;   // a tab that stays open fetches the data again after an hour
const TICK_MS = 5 * 60e3;
const COUNTED_KEY = 'reno-today:counted';
const SEEN_MS = 5000;   // a visit counts once the page has been on screen this long (previews and scanners leave sooner)
const VISIT_URL = 'https://ruby-radar.nathanforestlee.workers.dev/api/visit/reno-today';
let countedInMemory = null;   // the day counted by this page load, in case localStorage is off
let seenTimer = null;

function loadFilters() {
  try {
    const saved = JSON.parse(localStorage.getItem(FILTERS_KEY) || '{}');
    return Object.fromEntries(FILTERS.map(([k]) => [k, saved[k] === true]));
  } catch {
    return {};
  }
}

function saveFilters() {
  try { localStorage.setItem(FILTERS_KEY, JSON.stringify(state.filters)); } catch { /* storage off */ }
}

// ?data=<relative folder>/ reads fixtures (same origin only). On the live site the
// repo's raw files come first: they update within minutes of each data commit, even
// when a GitHub Pages deploy is stuck. The copy Pages published is the fallback.
function dataBases() {
  const d = params.get('data');
  if (d && /^[\w./-]+\/$/.test(d) && !d.startsWith('//')) return [d];
  const h = location.hostname;
  return h.endsWith('github.io') || h === 'renotoday.org' || h === 'www.renotoday.org' ? [RAW, 'data/'] : ['data/'];
}

async function loadJson(name, fallback) {
  for (const base of dataBases()) {
    try {
      const res = await fetch(base + name, { cache: 'no-cache' });
      if (res.ok) return await res.json();
    } catch { /* try the next place */ }
  }
  return fallback;
}

// Daily visitor count: one body-less POST per Reno day per browser. The worker stores only
// (site, date, count). "Already counted today" lives in this browser's localStorage only.
// Counted only after SEEN_MS on screen, and never for browsers that say they're automated.
// Skipped for fixtures (?data=) and the fake clock (?now=). Never blocks or breaks the page.
function countWhenSeen() {
  clearTimeout(seenTimer);
  if (document.visibilityState === 'visible') seenTimer = setTimeout(countVisit, SEEN_MS);
}

function countVisit() {
  try {
    if (params.has('data') || params.has('now')) return;
    if (L.looksAutomated(navigator.userAgent, navigator.webdriver)) return;
    const today = L.renoDate(now());
    let stored = null;
    try { stored = localStorage.getItem(COUNTED_KEY); } catch { /* storage off */ }
    if (countedInMemory === today) stored = today;
    if (!L.shouldCountVisit(location.hostname, stored, today)) return;
    countedInMemory = today;
    try { localStorage.setItem(COUNTED_KEY, today); } catch { /* storage off */ }
    fetch(VISIT_URL, { method: 'POST', keepalive: true }).catch(() => {});
  } catch { /* counting must never break the page */ }
}

const link = (url, label) => `<a href="${L.esc(url)}" target="_blank" rel="noopener">${L.esc(label)}</a>`;

function card(e, nowMs) {
  const live = state.day === L.renoDate(nowMs) && L.onNow(e, nowMs);
  const where = [e.venue?.name, e.area !== 'reno' ? L.AREA_LABEL[e.area] : null].filter(Boolean).join(' · ');
  const badges = [];
  const price = L.fmtPrice(e.price);
  if (price) badges.push(`<span class="b${e.price?.free ? ' b-free' : ''}">${L.esc(price)}</span>`);
  for (const h of e.hints) {
    if (HINT_LABEL[h]) badges.push(`<span class="b${h === '21+' ? ' b-adult' : ''}">${HINT_LABEL[h]}</span>`);
  }
  if (e.drive) badges.push(`<span class="b">🚗 ${L.esc(e.drive)}</span>`);
  const lr = e.lovingReno && L.safeUrl(e.lovingReno.url);
  if (lr) badges.push(`<a class="b b-lr" href="${L.esc(lr)}" target="_blank" rel="noopener">Loving Reno pick</a>`);
  const links = (e.links || []).map((l) => [L.safeUrl(l.url), L.SOURCE_LABEL[l.source] || l.source]).filter(([u]) => u);
  const maps = L.mapsUrl(e.venue);
  if (maps) links.push([maps, 'Directions']);
  const time = e.ongoing && e.end && !e.allDay
    ? `${L.fmtTime(e)}–${L.fmtTime({ allDay: false, start: e.end })}` : L.fmtTime(e);
  return `<article class="card${e.tier === 'little' ? ' is-little' : ''}${live ? ' is-now' : ''}">
    <div class="when">${L.esc(time)}${live ? '<span class="now">on now</span>' : ''}</div>
    <div class="what">
      <h3>${L.esc(e.title)}</h3>
      ${where ? `<p class="where">${L.esc(where)}</p>` : ''}
      ${badges.length ? `<p class="badges">${badges.join('')}</p>` : ''}
      ${links.length ? `<p class="links">${links.map(([u, label]) => link(u, label)).join(' · ')}</p>` : ''}
    </div>
  </article>`;
}

function placeCard(p, hours) {
  const url = L.safeUrl(p.url);
  const maps = L.mapsUrl({ name: p.name, address: p.address });
  const sub = [p.goodFor, p.area !== 'reno' ? L.AREA_LABEL[p.area] : null, p.setting].filter(Boolean).join(' · ');
  const links = [url && link(url, 'Check hours'), maps && link(maps, 'Directions')].filter(Boolean);
  return `<article class="card place">
    <div class="when">${L.esc(L.shortHours(hours))}</div>
    <div class="what">
      <h3>${L.esc(p.name)}</h3>
      ${sub ? `<p class="where">${L.esc(sub)}</p>` : ''}
      ${p.notes ? `<p class="note small">${L.esc(p.notes)}</p>` : ''}
      ${links.length ? `<p class="links">${links.join(' · ')}</p>` : ''}
    </div>
  </article>`;
}

function renderNotice() {
  const gen = state.data.generatedAt;
  $('notice').innerHTML = L.isStale(gen, now())
    ? `<p>⚠️ ${gen ? `Last updated ${L.esc(L.ago(gen, now()))}` : 'No data yet'}, so this list may be out of date.</p>`
    : '';
}

function renderDays() {
  $('days').innerHTML = L.dayTabs(L.renoDate(now())).map((t) =>
    `<button type="button" data-day="${t.date}" aria-pressed="${t.date === state.day}">${L.esc(t.label)}</button>`).join('');
  $('tagline').textContent = new Date(`${state.day}T12:00:00Z`)
    .toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', timeZone: 'UTC' });
}

function renderWeather() {
  const day = state.data.weather?.days?.find((d) => d.date === state.day);
  if (!day) {
    $('weather').innerHTML = '<span class="muted">Weather unavailable for this day.</span>';
    return;
  }
  const nice = L.niceNote(day);
  $('weather').innerHTML = `<span class="wx-emoji" aria-hidden="true">${L.esc(day.emoji)}</span>
    <span class="wx-temp">${L.esc(day.low)}° → ${L.esc(day.high)}°</span>
    <span>${L.esc(day.summary)}${day.rain ? ` · ${L.esc(day.rain)}% rain` : ''}</span>
    ${nice ? `<span class="wx-nice">🌿 ${L.esc(nice)}</span>` : ''}`;
}

function renderChips() {
  $('chips').innerHTML = FILTERS.map(([key, label]) =>
    `<button type="button" class="chip" data-filter="${key}" aria-pressed="${Boolean(state.filters[key])}">${label}</button>`).join('');
}

function renderLists() {
  const nowMs = now();
  const v = L.dayView(state.data.events, state.day, state.filters);
  const list = (items) => items.map((e) => card(e, nowMs)).join('');
  const filtered = Object.values(state.filters).some(Boolean) ? ' with these filters' : '';

  $('little').innerHTML = '<h2>👶 Great for little ones</h2>'
    + (v.little.length ? list(v.little) : `<p class="empty">Nothing made for little ones${filtered} on this day.</p>`);

  const groups = L.PARTS.filter(([k]) => v.parts[k].length)
    .map(([k, label]) => `<h3 class="part">${label}</h3>${list(v.parts[k])}`).join('');
  const rest = $('rest');
  rest.hidden = Boolean(state.filters.little);
  rest.innerHTML = '<h2>Everything else</h2>' + (groups || `<p class="empty">Nothing else listed${filtered}.</p>`);

  const ongoing = $('ongoing');
  ongoing.hidden = !v.ongoing.length;
  ongoing.innerHTML = `<summary><h2>Ongoing · <span class="n">${v.ongoing.length}</span></h2></summary>${list(v.ongoing)}`;

  const drive = $('drive');
  drive.hidden = !v.drive.length;
  drive.innerHTML = `<h2>🚗 Worth the drive</h2>${list(v.drive)}`;

  const open = L.placesOpen(state.data.places, state.day);
  const always = $('always');
  always.hidden = !open.length;
  if (always.dataset.day !== state.day) {     // only reset open/closed when the day changes
    always.open = v.littleCount < 3;
    always.dataset.day = state.day;
  }
  always.innerHTML = `<summary><h2>🏠 Always an option · <span class="n">${open.length}</span></h2></summary>`
    + open.map(([p, h]) => placeCard(p, h)).join('')
    + '<p class="muted small">Hours change with the seasons; check before you go.</p>';
}

function renderGuide() {
  const g = state.data.guide;
  const url = g && L.safeUrl(g.url);
  const el = $('guide');
  el.hidden = !url;
  if (!url) return;
  el.innerHTML = `<h2>📖 From Loving Reno</h2>
    <a class="guide-card" href="${L.esc(url)}" target="_blank" rel="noopener">
      <span class="guide-title">${L.esc(g.shortTitle || g.title)}</span>
      <span class="muted">Their latest guide${g.published ? ` · ${L.esc(g.published)}` : ''} →</span>
    </a>`;
}

function renderFooter() {
  const nowMs = now();
  const sources = Object.values(state.data.status?.sources ?? {});
  const gen = state.data.generatedAt;
  $('footer').innerHTML = `
    ${L.sourceNotes(sources, nowMs).map((n) => `<p class="warn small">${L.esc(n)}</p>`).join('')}
    <p class="small">Updated ${gen ? L.esc(L.ago(gen, nowMs)) : 'never'} · Sources: ${sources.map((s) => L.esc(s.label)).join(', ') || 'none yet'}</p>
    <p class="small">Times, places and prices come from each source; check its link before you go.</p>
    ${state.data.status?.sources?.ticketmaster ? '<p class="small">Concert and show listings from <a href="https://www.ticketmaster.com/" target="_blank" rel="noopener">Ticketmaster</a>.</p>' : ''}`;
}

// This month's decorations over the arch (art/season-NN.lua); they change at midnight in Reno.
function renderSeason() {
  $('season').dataset.month = L.seasonOf(now());
}

function render() {
  renderSeason();
  renderNotice();
  renderDays();
  renderWeather();
  renderChips();
  renderLists();
  renderGuide();
  renderFooter();
}

async function loadData() {
  const [events, weather, status, guide, places] = await Promise.all([
    loadJson('events.json', null), loadJson('weather.json', null), loadJson('status.json', null),
    loadJson('guide.json', null), loadJson('places.json', []),
  ]);
  return {
    events: Array.isArray(events?.events) ? events.events : [],
    generatedAt: events?.generatedAt ?? null,
    weather, status, guide,
    places: Array.isArray(places) ? places : [],
  };
}

async function main() {
  state.data = await loadData();
  state.loadedAt = now();
  state.today = state.day = L.renoDate(now());
  render();
}

// A tab left open overnight, or brought back from the back/forward cache, catches up:
// on a new Reno day "Today" moves on and the data reloads; data over an hour old
// reloads; the timer also refreshes the "on now" marks and the stale-data notice.
async function catchUp(tick) {
  if (!state.data || state.loading || document.hidden) return;
  const today = L.renoDate(now());
  if (today === state.today && now() - state.loadedAt < RELOAD_AFTER_MS) {
    if (tick) { renderNotice(); renderLists(); }
    return;
  }
  state.loading = true;
  try {
    const data = await loadData();
    if (data.generatedAt || !state.data.generatedAt) {   // offline just after waking: keep what we had
      state.data = data;
      state.loadedAt = now();
    }
    state.day = L.dayAfterRollover(state.day, state.today, today);
    state.today = today;
    render();
    countWhenSeen();   // a tab left open past midnight counts once for the new day
  } finally {
    state.loading = false;
  }
}

$('days').addEventListener('click', (ev) => {
  const b = ev.target.closest('button[data-day]');
  if (b && state.data) { state.day = b.dataset.day; render(); }
});
$('chips').addEventListener('click', (ev) => {
  const b = ev.target.closest('button[data-filter]');
  if (!b || !state.data) return;
  state.filters[b.dataset.filter] = !state.filters[b.dataset.filter];
  saveFilters();
  render();
});
renderSeason();   // before the data arrives
countWhenSeen();
document.addEventListener('visibilitychange', countWhenSeen);   // hiding the tab restarts the wait
main().catch((err) => {
  console.error(err);
  $('notice').innerHTML = '<p>Something went wrong loading the list. Try reloading.</p>';
});
const catchUpLogged = (tick) => catchUp(tick).catch((err) => console.error(err));
document.addEventListener('visibilitychange', () => catchUpLogged(false));
window.addEventListener('pageshow', (ev) => { if (ev.persisted) catchUpLogged(false); });
window.addEventListener('focus', () => catchUpLogged(false));
setInterval(() => catchUpLogged(true), TICK_MS);
