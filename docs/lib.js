// Pure helpers for the Reno Today page: Reno's dates, grouping, filters, formatting
// and escaping. No DOM here, so `npm test` covers it (tests/page/lib.test.js).

export const TZ = 'America/Los_Angeles';
export const LOCAL_AREAS = ['reno', 'sparks'];
export const AREA_LABEL = {
  reno: 'Reno', sparks: 'Sparks', tahoe: 'Lake Tahoe', carson: 'Carson City',
  'virginia-city': 'Virginia City', other: 'Nearby',
};
export const SOURCE_LABEL = {
  tm: 'Ticketmaster', unr: 'UNR', wolfpack: 'Wolf Pack', aces: 'Aces', library: 'Library',
  discovery: 'The Discovery', reno: 'City of Reno', sparks: 'City of Sparks', wcparks: 'Washoe Parks',
  carson: 'Visit Carson City', southtahoe: 'Visit Lake Tahoe', vcity: 'Virginia City', standing: 'Info',
};
export const PARTS = [
  ['allday', 'All day'], ['morning', 'Morning'], ['afternoon', 'Afternoon'], ['evening', 'Evening'], ['late', 'Late'],
];
export const STALE_HOURS = 6;
const WEEKDAYS = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];
const noon = (day) => new Date(`${day}T12:00:00Z`);
const two = (n) => String(n).padStart(2, '0');

export function renoDate(ms) {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-US', {
    timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(new Date(ms)).map((x) => [x.type, x.value]));
  return `${p.year}-${p.month}-${p.day}`;
}

export function addDays(day, n) {
  const d = noon(day);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

export const weekday = (day) => WEEKDAYS[noon(day).getUTCDay()];

export function dayTabs(today, n = 8) {
  return Array.from({ length: n }, (_, i) => {
    const date = addDays(today, i);
    const short = noon(date).toLocaleDateString('en-US', { weekday: 'short', timeZone: 'UTC' });
    return { date, label: i === 0 ? 'Today' : i === 1 ? 'Tomorrow' : `${short} ${Number(date.slice(8))}` };
  });
}

/** The day to show once Reno's date has moved on from wasToday to today: "Today"
 * follows the clock; a day the viewer picked stays while it's still one of the tabs. */
export function dayAfterRollover(shown, wasToday, today, n = 8) {
  if (shown === wasToday) return today;
  return today <= shown && shown <= addDays(today, n - 1) ? shown : today;
}

export const isLocal = (e) => LOCAL_AREAS.includes(e.area);

const MULTI_DAY_MS = 20 * 3600e3;

/** The last date an event shows on: all-day, ongoing and 20 h+ events cover their whole run. */
export function lastDay(e) {
  if (e.end && (e.allDay || e.ongoing || Date.parse(e.end) - Date.parse(e.start) >= MULTI_DAY_MS)) {
    return e.end.slice(0, 10);
  }
  return e.start.slice(0, 10);
}

export function eventsOn(events, day) {
  return events.filter((e) => e.start.slice(0, 10) <= day && day <= lastDay(e));
}

export function partOfDay(e) {
  if (e.allDay) return 'allday';
  const h = Number(e.start.slice(11, 13));
  return h < 12 ? 'morning' : h < 17 ? 'afternoon' : h < 21 ? 'evening' : 'late';
}

export function onNow(e, nowMs) {
  if (e.allDay || e.ongoing) return false;
  const start = Date.parse(e.start);
  const end = e.end ? Date.parse(e.end) : start + 2 * 3600e3;
  return start <= nowMs && nowMs < end;
}

export function passes(e, f) {
  return (!f.free || Boolean(e.price?.free))
    && (!f.outdoors || e.hints.includes('outdoors'))
    && (!f.little || e.tier === 'little')
    && (!f.hide21 || !e.hints.includes('21+'));
}

const byStart = (a, b) => a.start.localeCompare(b.start) || a.title.localeCompare(b.title);

/** Everything one day shows, filtered and sorted. littleCount ignores the filters. */
export function dayView(events, day, filters) {
  const all = eventsOn(events, day).sort(byStart);
  const parts = Object.fromEntries(PARTS.map(([key]) => [key, []]));
  const view = {
    little: [], parts, ongoing: [], drive: [], total: 0,
    littleCount: all.filter((e) => isLocal(e) && !e.ongoing && e.tier === 'little').length,
  };
  for (const e of all.filter((x) => passes(x, filters))) {
    view.total += 1;
    if (!isLocal(e)) view.drive.push(e);
    else if (e.ongoing) view.ongoing.push(e);
    else if (e.tier === 'little') view.little.push(e);
    else parts[partOfDay(e)].push(e);
  }
  return view;
}

function clock(h, m) {
  return `${h % 12 || 12}${m ? `:${two(m)}` : ''}${h < 12 ? 'am' : 'pm'}`;
}

export function fmtTime(e) {
  if (e.allDay) return 'All day';
  return clock(Number(e.start.slice(11, 13)), Number(e.start.slice(14, 16)));
}

export function fmtClock(hhmm) {
  const [h, m] = hhmm.split(':').map(Number);
  return clock(h, m);
}

export function fmtPrice(p) {
  if (!p) return '';
  if (p.free) return 'Free';
  const money = (n) => (Number.isInteger(n) ? `${n}` : n.toFixed(2));
  return p.min === p.max ? `$${money(p.min)}` : `$${money(p.min)}–${money(p.max)}`;
}

export function hoursOn(place, day) {
  if (place.months && !place.months.includes(Number(day.slice(5, 7)))) return null;
  return place.hours?.[weekday(day)] ?? null;
}

export function shortHours(h) {
  const [a, b] = String(h).split('-');
  if (!a?.includes(':') || !b?.includes(':')) return String(h).replace('-', '–');
  const c = (s) => { const [hh, mm] = s.split(':').map(Number); return `${hh % 12 || 12}${mm ? `:${two(mm)}` : ''}`; };
  return `${c(a)}–${c(b)}`;
}

export const placesOpen = (places, day) =>
  places.map((p) => [p, hoursOn(p, day)]).filter(([, h]) => h);

export function niceNote(wxDay) {
  if (!wxDay?.nice?.length) return '';
  return `Nice outside ${wxDay.nice.map((w) => `${fmtClock(w.from)}–${fmtClock(w.to)}`).join(', ')}`;
}

const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ESC[c]);

export function safeUrl(u) {
  try {
    const url = new URL(u);
    return url.protocol === 'https:' || url.protocol === 'http:' ? url.href : null;
  } catch {
    return null;
  }
}

export function mapsUrl(venue) {
  const q = [venue?.name, venue?.address].filter(Boolean).join(', ');
  return q ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(q)}` : null;
}

export function ago(iso, nowMs) {
  const min = Math.round((nowMs - Date.parse(iso)) / 60000);
  if (!Number.isFinite(min)) return '';
  if (min < 2) return 'just now';
  if (min < 90) return `${min} min ago`;
  const h = Math.round(min / 60);
  return h < 36 ? `${h} hours ago` : `${Math.round(h / 24)} days ago`;
}

export const isStale = (iso, nowMs) => !iso || !(nowMs - Date.parse(iso) <= STALE_HOURS * 3600e3);

const SOURCE_QUIET_HOURS = 6;   // a failed update or two while the last list still shows isn't worth a warning

// Footer notes for sources that are really down, in plain words. The technical
// error stays in status.json for debugging; it never reaches the page.
export function sourceNotes(sources, nowMs) {
  const notes = [];
  for (const s of sources) {
    if (s.ok) continue;
    if (!s.count) {
      notes.push(`${s.label} couldn't be reached, so its events are missing for now.`);
    } else if (!(nowMs - Date.parse(s.lastSuccess) <= SOURCE_QUIET_HOURS * 3600e3)) {   // also true when lastSuccess is missing
      notes.push(`${s.label} hasn't updated since ${ago(s.lastSuccess, nowMs) || 'a while ago'}; showing its last list.`);
    }
  }
  return notes;
}

export const COUNTED_HOSTS = ['natanforestree.github.io', 'renotoday.org', 'www.renotoday.org'];

/** Count a visit once per Reno day, and only on the real site (not localhost or a preview).
 * countedDay is the day this browser last counted (its own localStorage); it never leaves the device. */
export const shouldCountVisit = (hostname, countedDay, today) =>
  COUNTED_HOSTS.includes(hostname) && countedDay !== today;
