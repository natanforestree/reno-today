// The sections a visitor can fold away (lib.js FOLDABLE) are <details> that start open.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { FOLDABLE } from '../../docs/lib.js';

test('each foldable section is a <details> that starts open', () => {
  const html = readFileSync(new URL('../../docs/index.html', import.meta.url), 'utf8');
  for (const id of FOLDABLE) assert.match(html, new RegExp(`<details id="${id}" class="block"( hidden)? open>`), id);
});
