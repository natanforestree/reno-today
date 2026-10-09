// The feedback address never appears written out in the site's files, where address-collecting
// bots look; the page builds it when someone taps "Email me" (lib.js contactAddress).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';

const docs = new URL('../../docs/', import.meta.url);

test('no site file contains the feedback address in plain text', () => {
  const plain = ['hello', 'renotoday.org'].join('@');
  for (const name of readdirSync(docs).filter((f) => /\.(html|js|css|json)$/.test(f))) {
    assert.ok(!readFileSync(new URL(name, docs), 'utf8').includes(plain), name);
  }
  for (const name of readdirSync(new URL('data/', docs))) {
    assert.ok(!readFileSync(new URL(`data/${name}`, docs), 'utf8').includes(plain), name);
  }
});

test('the footer offers the email link', () => {
  const app = readFileSync(new URL('app.js', docs), 'utf8');
  assert.match(app, /Feedback or found a bug\? <a href="#contact" class="contact">Email me<\/a>/);
});
