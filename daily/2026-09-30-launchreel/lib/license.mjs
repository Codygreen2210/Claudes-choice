// Offline license keys. A key is "<payload>.<signature>", signed with Ed25519. The public key
// below checks it; the private key stays with the seller (see tools/keygen.mjs) and is never
// in this repo. No key = free version (a small "Made with LaunchReel" line on the end card).
import { verify, createPublicKey } from 'node:crypto';

// Set by `node tools/keygen.mjs init` (null until the seller sets one up).
export const PUBLIC_KEY = null;

export function checkLicense(key, pub = PUBLIC_KEY) {
  if (!key || !pub) return null;
  try {
    const [p, s] = String(key).trim().split('.');
    const ok = verify(null, Buffer.from(p, 'base64url'), createPublicKey({ key: Buffer.from(pub, 'base64'), format: 'der', type: 'spki' }), Buffer.from(s, 'base64url'));
    if (!ok) return null;
    const data = JSON.parse(Buffer.from(p, 'base64url').toString('utf8'));
    return data && data.email ? data : null;
  } catch { return null; }
}
