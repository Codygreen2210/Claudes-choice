#!/usr/bin/env node
// For the seller, not buyers.
//   node tools/keygen.mjs init          makes a key pair: puts the PUBLIC key into lib/license.mjs and
//                                       prints the PRIVATE key once. Store it as LAUNCHREEL_PRIVATE_KEY
//                                       (e.g. in Vercel env vars). Never commit it.
//   node tools/keygen.mjs issue a@b.co  prints a license key for that buyer (needs LAUNCHREEL_PRIVATE_KEY)
import { generateKeyPairSync, sign, createPrivateKey } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
const [cmd, email] = process.argv.slice(2);
if (cmd === 'init') {
  const { publicKey, privateKey } = generateKeyPairSync('ed25519');
  const pub = publicKey.export({ format: 'der', type: 'spki' }).toString('base64');
  const f = new URL('../lib/license.mjs', import.meta.url);
  writeFileSync(f, readFileSync(f, 'utf8').replace(/export const PUBLIC_KEY = .*;/, `export const PUBLIC_KEY = '${pub}';`));
  console.log('Public key written to lib/license.mjs.\nPrivate key (save it somewhere safe, shown once):\n' + privateKey.export({ format: 'der', type: 'pkcs8' }).toString('base64'));
} else if (cmd === 'issue' && email) {
  const pk = process.env.LAUNCHREEL_PRIVATE_KEY;
  if (!pk) { console.error('Set LAUNCHREEL_PRIVATE_KEY first.'); process.exit(1); }
  const payload = Buffer.from(JSON.stringify({ email, plan: 'pro', issued: new Date().toISOString().slice(0, 10) }));
  const sig = sign(null, payload, createPrivateKey({ key: Buffer.from(pk, 'base64'), format: 'der', type: 'pkcs8' }));
  console.log(payload.toString('base64url') + '.' + sig.toString('base64url'));
} else console.error('Usage: node tools/keygen.mjs init | issue buyer@email.com');
