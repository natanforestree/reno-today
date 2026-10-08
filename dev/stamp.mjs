// Version-stamp the page's assets with a hash of their content (?v=1a2b3c4d), so a
// browser's cached copy is replaced as soon as a file changes. GitHub Pages lets
// browsers reuse files for 10 minutes, which otherwise hides new page code.
//
//   node dev/stamp.mjs     rewrite the stamps (run after editing anything in docs/)
//
// tests/page/stamp.test.js fails while any stamp is out of date.
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

// In dependency order: a file's own stamps are updated before its hash is taken.
const RULES = [
  { in: 'app.js', ref: "'./lib.js", asset: 'lib.js' },
  { in: 'style.css', ref: 'url(art/arch.png', asset: 'art/arch.png' },
  ...Array.from({ length: 12 }, (_, i) => {
    const asset = `art/season-${String(i + 1).padStart(2, '0')}.png`;
    return { in: 'style.css', ref: `url(${asset}`, asset };
  }),
  { in: 'style.css', ref: 'url(art/icons.png', asset: 'art/icons.png' },
  { in: 'index.html', ref: '"art/favicon.png', asset: 'art/favicon.png' },
  { in: 'index.html', ref: '"style.css', asset: 'style.css' },
  { in: 'index.html', ref: '"app.js', asset: 'app.js' },
];

const hash = (path) => createHash('sha256').update(readFileSync(path)).digest('hex').slice(0, 8);
const escape = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const pattern = (ref) => new RegExp(`${escape(ref)}(\\?v=[0-9a-f]*)?(?=["')])`, 'g');

export function stampProblems(root) {
  const docs = join(root, 'docs');
  const problems = [];
  for (const r of RULES) {
    const want = `${r.ref}?v=${hash(join(docs, r.asset))}`;
    const found = readFileSync(join(docs, r.in), 'utf8').match(pattern(r.ref)) || [];
    if (found.length !== 1 || found[0] !== want) {
      problems.push(`docs/${r.in}: ${r.asset} should be referenced as ${want}, found ${found.join(', ') || 'nothing'}`);
    }
  }
  return problems;
}

export function applyStamps(root) {
  const docs = join(root, 'docs');
  for (const r of RULES) {
    const file = join(docs, r.in);
    const text = readFileSync(file, 'utf8');
    const next = text.replace(pattern(r.ref), `${r.ref}?v=${hash(join(docs, r.asset))}`);
    if (next !== text) writeFileSync(file, next);
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const root = fileURLToPath(new URL('../', import.meta.url));
  applyStamps(root);
  const left = stampProblems(root);
  console.log(left.length ? left.join('\n') : 'stamps up to date');
  process.exitCode = left.length ? 1 : 0;
}
