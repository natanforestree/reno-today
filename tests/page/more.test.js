// "More local calendars": plain links to good local calendars Reno Today can't read
// automatically (no data feed). Nothing from them is copied onto the page.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

test('the More local calendars section links each calendar in a new tab', () => {
  const html = readFileSync(new URL('../../docs/index.html', import.meta.url), 'utf8');
  const section = html.slice(html.indexOf('<section id="more"'), html.indexOf('</section>', html.indexOf('<section id="more"')));
  for (const url of ['https://www.therenoscene.com/', 'https://www.nvbirds.org/event-calendar',
    'https://www.renolittletheater.org/', 'https://www.bruka.org/', 'https://www.villageatrancharrah.com/events']) {
    assert.ok(section.includes(`<a href="${url}" target="_blank" rel="noopener">`), url);
  }
  assert.ok(!html.includes('id="scene"'));
});
