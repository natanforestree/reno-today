// Every page asset is loaded with ?v=<hash of its content>, so a browser holding a
// cached copy fetches the new file as soon as it changes. If this fails, run:
//   node dev/stamp.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { stampProblems } from '../../dev/stamp.mjs';

const root = fileURLToPath(new URL('../../', import.meta.url));

test('asset version stamps match the files (run `node dev/stamp.mjs` after editing docs/)', () => {
  assert.deepEqual(stampProblems(root), []);
});
