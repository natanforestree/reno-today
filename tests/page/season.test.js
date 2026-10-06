// The header's seasonal layers (art/season-NN.lua): one strip per month, the same size the
// .season rule in docs/style.css animates (16 frames of 176x96), each with its own CSS rule.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const docs = new URL('../../docs/', import.meta.url);
const MONTHS = Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, '0'));

test('every month has a 2816x96 strip and a CSS rule that shows it', () => {
  const css = readFileSync(new URL('style.css', docs), 'utf8');
  for (const mm of MONTHS) {
    const png = readFileSync(new URL(`art/season-${mm}.png`, docs));
    assert.equal(png.toString('ascii', 12, 16), 'IHDR', mm);
    assert.deepEqual([png.readUInt32BE(16), png.readUInt32BE(20)], [2816, 96], mm);
    assert.match(css, new RegExp(`\\.season\\[data-month="${mm}"\\] \\{ background-image: url\\(art/season-${mm}\\.png`), mm);
  }
});
