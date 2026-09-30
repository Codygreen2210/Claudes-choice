// Blueprint: read an app's code (no AI, nothing leaves your machine) and work out
// what it's made of: framework, pages, API routes, database tables, outside
// services, environment variables, and where it deploys. The point is a map a
// non-coder (and their AI builder) can read instead of re-reading the whole app.
import { readdirSync, readFileSync, statSync, existsSync } from 'node:fs';
import { join, relative, extname, sep } from 'node:path';

const SKIP = new Set(['node_modules', '.git', '.next', 'dist', 'build', 'out', '.vercel', '.turbo', 'coverage', '.cache', '.svelte-kit', 'vendor']);
const CODE = new Set(['.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.vue', '.svelte', '.astro']);
const MAX_FILE = 400 * 1024;

// Package -> plain-English service name. Only the ones that matter to an owner.
const SERVICES = {
  '@supabase/supabase-js': 'Supabase (database + logins)', '@supabase/ssr': 'Supabase (database + logins)',
  stripe: 'Stripe (payments)', '@stripe/stripe-js': 'Stripe (payments)',
  openai: 'OpenAI (AI)', '@anthropic-ai/sdk': 'Anthropic Claude (AI)', '@google/generative-ai': 'Google Gemini (AI)',
  resend: 'Resend (email)', '@sendgrid/mail': 'SendGrid (email)', nodemailer: 'Email sending (nodemailer)', postmark: 'Postmark (email)',
  prisma: 'Prisma (database layer)', '@prisma/client': 'Prisma (database layer)', 'drizzle-orm': 'Drizzle (database layer)',
  firebase: 'Firebase', 'firebase-admin': 'Firebase (server)', '@clerk/nextjs': 'Clerk (logins)', 'next-auth': 'NextAuth (logins)',
  '@vercel/analytics': 'Vercel Analytics', 'posthog-js': 'PostHog (analytics)', '@sentry/nextjs': 'Sentry (error tracking)',
  twilio: 'Twilio (texts/calls)', '@upstash/redis': 'Upstash Redis', 'uploadthing': 'UploadThing (file uploads)', cloudinary: 'Cloudinary (images)',
  'lemonsqueezy.js': 'Lemon Squeezy (payments)', '@lemonsqueezy/lemonsqueezy.js': 'Lemon Squeezy (payments)',
};
const FRAMEWORKS = [['next', 'Next.js'], ['@remix-run/react', 'Remix'], ['@sveltejs/kit', 'SvelteKit'], ['nuxt', 'Nuxt'], ['astro', 'Astro'], ['vite', 'Vite'], ['express', 'Express'], ['react', 'React']];

function walk(dir, root = dir, out = []) {
  for (const name of readdirSync(dir)) {
    if (SKIP.has(name) || (name.startsWith('.') && name !== '.env.example')) continue;
    const full = join(dir, name);
    const st = statSync(full);
    if (st.isDirectory()) walk(full, root, out);
    else out.push({ path: relative(root, full).split(sep).join('/'), size: st.size });
  }
  return out;
}

const uniqSorted = (a) => [...new Set(a)].sort();

export function analyze(root) {
  const files = walk(root);
  const pkg = existsSync(join(root, 'package.json')) ? JSON.parse(readFileSync(join(root, 'package.json'), 'utf8')) : {};
  const deps = { ...(pkg.dependencies || {}), ...(pkg.devDependencies || {}) };

  const framework = FRAMEWORKS.find(([d]) => deps[d])?.[1] || (files.some((f) => f.path.endsWith('.html')) ? 'Plain HTML/JS' : 'Unknown');
  const services = uniqSorted(Object.keys(deps).filter((d) => SERVICES[d]).map((d) => SERVICES[d]));

  const env = new Map();      // name -> { public, files:Set }
  const tables = new Map();   // table -> Set(files)
  const buckets = new Set(); const rpcs = new Set(); const hosts = new Set();
  for (const f of files) {
    if (!CODE.has(extname(f.path)) || f.size > MAX_FILE) continue;
    const text = readFileSync(join(root, f.path), 'utf8');
    for (const m of text.matchAll(/(?:process\.env|import\.meta\.env)\.([A-Z][A-Z0-9_]+)/g)) {
      const name = m[1];
      const e = env.get(name) || { public: /^(NEXT_PUBLIC_|VITE_|PUBLIC_|EXPO_PUBLIC_|NUXT_PUBLIC_)/.test(name), files: new Set() };
      e.files.add(f.path); env.set(name, e);
    }
    for (const m of text.matchAll(/process\.env\[['"]([A-Z][A-Z0-9_]+)['"]\]/g)) {
      const e = env.get(m[1]) || { public: /^(NEXT_PUBLIC_|VITE_|PUBLIC_)/.test(m[1]), files: new Set() }; e.files.add(f.path); env.set(m[1], e);
    }
    // Supabase / PostgREST style: .from('table') but not storage.from('bucket')
    for (const m of text.matchAll(/(\bstorage\s*)?\.from\(\s*['"`]([A-Za-z0-9_]+)['"`]\s*\)/g)) {
      if (m[1]) buckets.add(m[2]);
      else { const s = tables.get(m[2]) || new Set(); s.add(f.path); tables.set(m[2], s); }
    }
    for (const m of text.matchAll(/\.rpc\(\s*['"`]([A-Za-z0-9_]+)['"`]/g)) rpcs.add(m[1]);
    for (const m of text.matchAll(/fetch\(\s*['"`](https:\/\/[^/'"`$]+)/g)) hosts.add(new URL(m[1]).host);
  }

  // Pages and API routes (Next.js app + pages router, SvelteKit, Vercel functions).
  const pages = []; const apis = [];
  for (const { path } of files) {
    let m;
    if ((m = path.match(/^(?:src\/)?app\/(.*?)\/?page\.(?:tsx|jsx|ts|js|mdx)$/))) pages.push('/' + cleanRoute(m[1]));
    else if ((m = path.match(/^(?:src\/)?app\/(.*?)\/?route\.(?:ts|js)$/))) apis.push('/' + cleanRoute(m[1]));
    else if ((m = path.match(/^(?:src\/)?pages\/api\/(.*)\.(?:ts|js)$/))) apis.push('/api/' + m[1].replace(/\/?index$/, ''));
    else if ((m = path.match(/^(?:src\/)?pages\/(?!_)(.*)\.(?:tsx|jsx|ts|js)$/))) pages.push('/' + m[1].replace(/\/?index$/, ''));
    else if ((m = path.match(/^src\/routes\/(.*?)\/?\+page\.svelte$/))) pages.push('/' + cleanRoute(m[1]));
    else if ((m = path.match(/^api\/(.*)\.(?:ts|js|mjs)$/))) apis.push('/api/' + m[1]);
  }

  const deploy = [];
  if (existsSync(join(root, 'vercel.json')) || deps.next) deploy.push('Vercel');
  if (existsSync(join(root, 'netlify.toml'))) deploy.push('Netlify');
  if (existsSync(join(root, 'railway.json')) || existsSync(join(root, 'railway.toml'))) deploy.push('Railway');
  if (existsSync(join(root, 'Dockerfile'))) deploy.push('Docker');
  const wfDir = join(root, '.github', 'workflows');
  const workflows = existsSync(wfDir) ? readdirSync(wfDir).filter((n) => /\.ya?ml$/.test(n)).sort() : [];

  // Big picture of folders, and the largest code files (where an AI should look first or last).
  const folders = new Map();
  for (const f of files) { const top = f.path.includes('/') ? f.path.split('/')[0] + '/' : '(root)'; folders.set(top, (folders.get(top) || 0) + 1); }
  const biggest = files.filter((f) => CODE.has(extname(f.path))).sort((a, b) => b.size - a.size).slice(0, 5);

  const warnings = [];
  for (const [name, e] of env) {
    if (e.public && /SECRET|SERVICE_ROLE|PRIVATE|PASSWORD|SK_/.test(name)) warnings.push(`${name} is marked public (the browser can see it) but its name says it's a secret. Move it to a server-only variable and rotate it.`);
  }

  return {
    name: pkg.name || root.split(sep).pop(), framework, services,
    scripts: pkg.scripts || {}, deploy: uniqSorted(deploy), workflows,
    pages: uniqSorted(pages.map((p) => p.replace(/\/+$/, '') || '/')), apis: uniqSorted(apis),
    env: [...env].map(([name, e]) => ({ name, public: e.public, files: [...e.files].sort() })).sort((a, b) => a.name.localeCompare(b.name)),
    tables: [...tables].map(([t, s]) => ({ table: t, files: [...s].sort() })).sort((a, b) => a.table.localeCompare(b.table)),
    buckets: uniqSorted([...buckets]), rpcs: uniqSorted([...rpcs]), hosts: uniqSorted([...hosts]),
    folders: [...folders].sort((a, b) => b[1] - a[1]), biggest, fileCount: files.length, warnings,
  };
}

function cleanRoute(r) {
  return r.split('/').filter((s) => !/^\(.*\)$/.test(s) && !s.startsWith('@')).join('/'); // drop (groups) and @slots
}
