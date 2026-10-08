// Runs in a far-away time zone on purpose: everything must follow Reno's clock.
process.env.TZ = 'Asia/Tokyo';

import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as L from '../../docs/lib.js';

const ev = (o = {}) => ({
  id: 'x:1', title: 'T', start: '2026-10-10T10:00:00-07:00', end: null, allDay: false, ongoing: false,
  venue: null, area: 'reno', drive: null, price: null, tier: 'general', hints: [], links: [], lovingReno: null, ...o,
});

test('renoDate follows Reno, not the device', () => {
  assert.equal(L.renoDate(Date.UTC(2026, 9, 11, 6, 30)), '2026-10-10');   // 23:30 PDT
  assert.equal(L.renoDate(Date.UTC(2026, 9, 11, 7, 30)), '2026-10-11');   // 00:30 PDT
  assert.equal(L.renoDate(Date.UTC(2026, 10, 1, 8, 30)), '2026-11-01');   // 01:30 PDT on the fall-back day
  assert.equal(L.renoDate(Date.UTC(2026, 10, 2, 7, 30)), '2026-11-01');   // 23:30 PST that evening
});

test('day tabs', () => {
  const tabs = L.dayTabs('2026-10-10');
  assert.equal(tabs.length, 8);
  assert.deepEqual(tabs.slice(0, 3).map((t) => t.label), ['Today', 'Tomorrow', 'Mon 12']);
  assert.equal(tabs[7].date, '2026-10-17');
  assert.equal(L.addDays('2026-10-30', 3), '2026-11-02');
  assert.equal(L.weekday('2026-10-10'), 'sat');
});

test('eventsOn: one-off events on their day; ongoing, all-day and long ones across their run', () => {
  const once = ev({ id: 'a' });
  const exhibit = ev({ id: 'b', ongoing: true, start: '2026-10-01T10:00:00-07:00', end: '2026-10-20T17:00:00-07:00' });
  assert.deepEqual(L.eventsOn([once, exhibit], '2026-10-10').map((e) => e.id), ['a', 'b']);
  assert.deepEqual(L.eventsOn([once, exhibit], '2026-10-11').map((e) => e.id), ['b']);
  assert.deepEqual(L.eventsOn([once, exhibit], '2026-10-21').map((e) => e.id), []);
  const fest = ev({ id: 'c', allDay: true, start: '2026-10-09T00:00:00-07:00', end: '2026-10-11T00:00:00-07:00' });
  const late = ev({ id: 'd', start: '2026-10-10T21:00:00-07:00', end: '2026-10-11T01:00:00-07:00' });
  assert.deepEqual(L.eventsOn([fest, late], '2026-10-10').map((e) => e.id), ['c', 'd']);
  assert.deepEqual(L.eventsOn([fest, late], '2026-10-11').map((e) => e.id), ['c']);
});

test('part of day', () => {
  const at = (h) => ev({ start: `2026-10-10T${String(h).padStart(2, '0')}:00:00-07:00` });
  assert.deepEqual([9, 12, 16, 17, 20, 21, 23].map((h) => L.partOfDay(at(h))),
    ['morning', 'afternoon', 'afternoon', 'evening', 'evening', 'late', 'late']);
  assert.equal(L.partOfDay(ev({ allDay: true })), 'allday');
});

test('on now uses the end, or two hours when there is none', () => {
  const t = (iso) => Date.parse(iso);
  const e = ev({ start: '2026-10-10T10:00:00-07:00', end: '2026-10-10T10:45:00-07:00' });
  assert.equal(L.onNow(e, t('2026-10-10T10:30:00-07:00')), true);
  assert.equal(L.onNow(e, t('2026-10-10T10:46:00-07:00')), false);
  assert.equal(L.onNow(ev(), t('2026-10-10T11:59:00-07:00')), true);
  assert.equal(L.onNow(ev({ allDay: true }), t('2026-10-10T11:00:00-07:00')), false);
});

test('filters', () => {
  const free = ev({ price: { free: true }, hints: ['outdoors', 'daytime'] });
  const adult = ev({ hints: ['21+'] });
  const little = ev({ tier: 'little' });
  assert.equal(L.passes(free, { free: true, outdoors: true }), true);
  assert.equal(L.passes(adult, { free: true }), false);
  assert.equal(L.passes(adult, { hide21: true }), false);
  assert.equal(L.passes(little, { little: true }), true);
  assert.equal(L.passes(free, { little: true }), false);
});

test('dayView groups the day', () => {
  const events = [
    ev({ id: 'story', tier: 'little', start: '2026-10-10T10:30:00-07:00' }),
    ev({ id: 'show', start: '2026-10-10T19:30:00-07:00' }),
    ev({ id: 'fest', allDay: true, start: '2026-10-10T00:00:00-07:00' }),
    ev({ id: 'club', start: '2026-10-10T22:00:00-07:00', hints: ['21+'] }),
    ev({ id: 'tahoe', area: 'tahoe', tier: 'little', start: '2026-10-10T11:00:00-07:00' }),
    ev({ id: 'exhibit', ongoing: true, start: '2026-10-01T10:00:00-07:00', end: '2026-10-30T17:00:00-07:00' }),
    ev({ id: 'tomorrow', start: '2026-10-11T09:00:00-07:00' }),
  ];
  const v = L.dayView(events, '2026-10-10', {});
  assert.deepEqual(v.little.map((e) => e.id), ['story']);
  assert.deepEqual(v.parts.allday.map((e) => e.id), ['fest']);
  assert.deepEqual(v.parts.evening.map((e) => e.id), ['show']);
  assert.deepEqual(v.parts.late.map((e) => e.id), ['club']);
  assert.deepEqual(v.drive.map((e) => e.id), ['tahoe']);
  assert.deepEqual(v.ongoing.map((e) => e.id), ['exhibit']);
  assert.equal(v.littleCount, 1);
  assert.equal(v.total, 6);
  const filtered = L.dayView(events, '2026-10-10', { hide21: true, little: true });
  assert.equal(filtered.parts.late.length, 0);
  assert.equal(filtered.littleCount, 1, 'counted before filters');
});

test('times and prices', () => {
  const at = (hm) => ev({ start: `2026-10-10T${hm}:00-07:00` });
  assert.deepEqual(['10:30', '13:05', '19:00', '12:00', '00:15'].map((hm) => L.fmtTime(at(hm))),
    ['10:30am', '1:05pm', '7pm', '12pm', '12:15am']);
  assert.equal(L.fmtTime(ev({ allDay: true })), 'All day');
  assert.equal(L.fmtClock('17:00'), '5pm');
  assert.equal(L.fmtClock('09:30'), '9:30am');
  assert.equal(L.fmtPrice({ free: true }), 'Free');
  assert.equal(L.fmtPrice({ min: 25, max: 25 }), '$25');
  assert.equal(L.fmtPrice({ min: 25, max: 60.5 }), '$25–60.50');
  assert.equal(L.fmtPrice(null), '');
});

test('places and weather notes', () => {
  const discovery = { hours: { mon: null, sat: '10:00-17:00' } };
  const splash = { months: [6, 7, 8], hours: { sat: '11:00-19:00' } };
  assert.equal(L.hoursOn(discovery, '2026-10-10'), '10:00-17:00');
  assert.equal(L.hoursOn(discovery, '2026-10-12'), null);
  assert.equal(L.hoursOn(splash, '2026-10-10'), null);
  assert.equal(L.shortHours('09:30-16:00'), '9:30–4');
  assert.equal(L.shortHours('dawn-dusk'), 'dawn–dusk');
  assert.deepEqual(L.placesOpen([discovery, splash], '2026-10-10').map(([, h]) => h), ['10:00-17:00']);
  assert.equal(L.niceNote({ nice: [{ from: '10:00', to: '17:00' }] }), 'Nice outside 10am–5pm');
  assert.equal(L.niceNote({ nice: [] }), '');
  assert.equal(L.niceNote(null), '');
});

test('escaping and links', () => {
  assert.equal(L.esc('<img src=x onerror="alert(1)">&\''), '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;&amp;&#39;');
  assert.equal(L.esc(null), '');
  assert.equal(L.safeUrl('javascript:alert(1)'), null);
  assert.equal(L.safeUrl('data:text/html,hi'), null);
  assert.equal(L.safeUrl('//evil.example'), null);
  assert.equal(L.safeUrl('not a url'), null);
  assert.equal(L.safeUrl('https://a.example/b?c=1'), 'https://a.example/b?c=1');
  assert.equal(L.mapsUrl({ name: 'The Discovery', address: '490 S Center St' }),
    'https://www.google.com/maps/search/?api=1&query=The%20Discovery%2C%20490%20S%20Center%20St');
  assert.equal(L.mapsUrl(null), null);
});

test('freshness', () => {
  const now = Date.parse('2026-10-10T15:00:00Z');
  assert.equal(L.ago('2026-10-10T14:30:00Z', now), '30 min ago');
  assert.equal(L.ago('2026-10-10T12:00:00Z', now), '3 hours ago');
  assert.equal(L.isStale('2026-10-10T12:00:00Z', now), false);
  assert.equal(L.isStale('2026-10-10T08:00:00Z', now), true);
  assert.equal(L.isStale(null, now), true);
});

test('a tab left open overnight: "Today" follows the clock, a picked day stays while it is a tab', () => {
  assert.equal(L.dayAfterRollover('2026-10-10', '2026-10-10', '2026-10-11'), '2026-10-11');   // was on Today
  assert.equal(L.dayAfterRollover('2026-10-13', '2026-10-10', '2026-10-11'), '2026-10-13');   // picked Tue: keep
  assert.equal(L.dayAfterRollover('2026-10-11', '2026-10-10', '2026-10-11'), '2026-10-11');   // picked Tomorrow
  assert.equal(L.dayAfterRollover('2026-10-18', '2026-10-11', '2026-10-12'), '2026-10-18');   // last tab
  assert.equal(L.dayAfterRollover('2026-10-17', '2026-10-10', '2026-10-19'), '2026-10-19');   // gone after days away
  assert.equal(L.dayAfterRollover('2026-10-31', '2026-10-31', '2026-11-01'), '2026-11-01');   // across the fall-back
});

test('sourceNotes: quiet about a short blip, plain words when a source is really down', () => {
  const now = Date.parse('2026-10-06T18:00:00Z');
  const s = (label, ok, count, lastSuccess, error = 'bad JSON: Expecting value (https://example.org/feed)') =>
    ({ label, ok, count, lastSuccess, error });
  const notes = L.sourceNotes([
    s('UNR events', true, 57, '2026-10-06T17:30:00Z'),
    s('Virginia City', false, 8, '2026-10-06T15:00:00Z'),        // 3 h, still showing its list: quiet
    s('City of Reno', false, 30, '2026-10-06T10:00:00Z'),        // 8 h: say so
    s('Ticketmaster', false, 0, null, 'not set up yet'),          // nothing to show: say so
  ], now);
  assert.deepEqual(notes, [
    "City of Reno hasn't updated since 8 hours ago; showing its last list.",
    "Ticketmaster couldn't be reached, so its events are missing for now.",
  ]);
  assert.ok(notes.every((n) => !/JSON|https?:|set up/.test(n)), 'no technical detail on the page');
  assert.deepEqual(L.sourceNotes([], now), []);
});

test('shouldCountVisit: only the real hosts, once per Reno day', () => {
  for (const host of ['natanforestree.github.io', 'renotoday.org', 'www.renotoday.org']) {
    assert.equal(L.shouldCountVisit(host, null, '2026-10-06'), true, host);
    assert.equal(L.shouldCountVisit(host, undefined, '2026-10-06'), true, host);
    assert.equal(L.shouldCountVisit(host, '2026-10-05', '2026-10-06'), true, host);
    assert.equal(L.shouldCountVisit(host, '2026-10-06', '2026-10-06'), false, host);
  }
  for (const host of ['localhost', '127.0.0.1', '', 'example.com', 'evil.renotoday.org', 'renotoday.org.evil.example', 'github.io']) {
    assert.equal(L.shouldCountVisit(host, null, '2026-10-06'), false, host);
  }
});

test('seasonOf: the header art follows the month on Reno\'s clock', () => {
  assert.equal(L.seasonOf(Date.UTC(2026, 9, 6, 19, 0)), '10');    // Oct 6, noon PDT
  assert.equal(L.seasonOf(Date.UTC(2026, 10, 1, 6, 30)), '10');   // Oct 31, 11:30pm PDT (Nov 1 in UTC and Tokyo)
  assert.equal(L.seasonOf(Date.UTC(2026, 10, 1, 7, 5)), '11');    // Nov 1, 12:05am PDT
  assert.equal(L.seasonOf(Date.UTC(2027, 0, 1, 7, 59)), '12');    // Dec 31, 11:59pm PST
  assert.equal(L.seasonOf(Date.UTC(2027, 0, 1, 8, 0)), '01');     // Jan 1, midnight PST
  assert.equal(L.seasonOf(Date.UTC(2027, 8, 15, 19, 0)), '09');
});

test('passes: the live music filter', () => {
  const show = ev({ hints: ['music'] });
  const show21 = ev({ hints: ['music', '21+'] });
  const talk = ev();
  assert.equal(L.passes(show, { music: true }), true);
  assert.equal(L.passes(talk, { music: true }), false);
  assert.equal(L.passes(talk, {}), true);
  assert.equal(L.passes(show21, { music: true, hide21: true }), false);   // all-ages live music
});

test('looksAutomated: robots that say so are not counted, real browsers are', () => {
  const people = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBAV/480.0]',
    'Mozilla/5.0 (Linux; Android 10; CUBOT X30) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36',   // a phone brand
    '',
  ];
  const robots = [
    'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.70 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/129.0.0.0 Safari/537.36',
    'Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)',
    'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
    'Mozilla/5.0 (Linux; Android 11; moto g power (2022)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36 Chrome-Lighthouse',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko; Google-PageRenderer Google (+https://developers.google.com/+/web/snippet/)) Chrome/56.0.2924.87 Safari/537.36',
  ];
  for (const ua of people) assert.equal(L.looksAutomated(ua, false), false, ua);
  for (const ua of robots) assert.equal(L.looksAutomated(ua, false), true, ua);
  assert.equal(L.looksAutomated(people[0], true), true);        // automation flag (navigator.webdriver)
  assert.equal(L.looksAutomated(undefined, undefined), false);
});

test('weatherIcon: the same weather types as collector/weather.py CODES', () => {
  const cases = [[0, 'clear'], [1, 'mostly-clear'], [2, 'partly-cloudy'], [3, 'cloudy'], [45, 'fog'], [48, 'fog'],
    [51, 'showers'], [57, 'showers'], [61, 'rain'], [67, 'rain'], [71, 'snow'], [77, 'snow'], [80, 'showers'],
    [82, 'showers'], [85, 'snow'], [86, 'snow'], [95, 'thunder'], [99, 'thunder']];
  for (const [code, name] of cases) assert.equal(L.weatherIcon(code), name, String(code));
  for (const bad of [null, undefined, 100, -1, 'x']) assert.equal(L.weatherIcon(bad), null, String(bad));
  for (const [, name] of cases) assert.ok(L.ICONS.includes(name), name);
});
