// The page's pixel icons (art/icons.lua): one 12x12 cell per name in lib.js ICONS, in that
// order, shown at 2x by the .ico-<name> rules in docs/style.css.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { ICONS } from '../../docs/lib.js';

const docs = new URL('../../docs/', import.meta.url);

test('the icon sheet has a cell for every icon and each has a CSS rule at its place', () => {
  const png = readFileSync(new URL('art/icons.png', docs));
  assert.deepEqual([png.readUInt32BE(16), png.readUInt32BE(20)], [ICONS.length * 12, 12]);
  const css = readFileSync(new URL('style.css', docs), 'utf8');
  assert.match(css, new RegExp(`background-size: ${ICONS.length * 24}px 24px`));
  ICONS.forEach((name, i) => {
    assert.match(css, new RegExp(`\\.ico-${name} \\{ background-position: ${i ? `-${i * 24}px` : '0'} 0; \\}`), name);
  });
});

test('every icon the page uses is in the sheet', () => {
  const used = new Set();
  for (const file of ['app.js', 'index.html']) {
    const text = readFileSync(new URL(file, docs), 'utf8');
    for (const m of text.matchAll(/icon\('([a-z-]+)'\)|ico-([a-z-]+)/g)) used.add(m[1] || m[2]);
  }
  for (const name of used) assert.ok(ICONS.includes(name), name);
});
