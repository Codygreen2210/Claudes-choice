// Read a Shopify store's public product catalog. Every Shopify store serves
// /products.json to anyone (it's what powers their own storefront), so this is
// the same data a shopper sees, in a clean form. We go slow and stop early:
// one page per second, at most MAX_PAGES pages, and a clear user-agent.

const MAX_PAGES = 20;          // 20 x 250 = 5,000 products, plenty for small stores
const PAGE_DELAY_MS = 1000;
const UA = 'RivalWatch/0.1 (price watch for small shops; +https://github.com/Codygreen2210/Claudes-choice)';

export function storeRoot(input) {
  let s = String(input).trim();
  if (!/^https?:\/\//i.test(s)) s = 'https://' + s;
  const u = new URL(s);
  return `${u.protocol}//${u.host}`;
}

export function normalizeProduct(p) {
  return {
    id: String(p.id),
    handle: p.handle,
    title: p.title,
    variants: (p.variants || []).map((v) => ({
      id: String(v.id),
      title: v.title === 'Default Title' ? '' : v.title,
      price: Number(v.price),
      compareAt: v.compare_at_price ? Number(v.compare_at_price) : null,
      available: v.available !== false,
    })),
  };
}

export async function fetchCatalog(store, { fetchImpl = globalThis.fetch, sleep = (ms) => new Promise((r) => setTimeout(r, ms)) } = {}) {
  const root = storeRoot(store);
  const products = [];
  for (let page = 1; page <= MAX_PAGES; page++) {
    const res = await fetchImpl(`${root}/products.json?limit=250&page=${page}`, { headers: { 'user-agent': UA, accept: 'application/json' } });
    if (res.status === 404) throw new Error(`${root} doesn't look like a Shopify store (no public product list).`);
    if (res.status === 429) throw new Error(`${root} asked us to slow down. Try again later.`);
    if (!res.ok) throw new Error(`${root} answered HTTP ${res.status}.`);
    const batch = (await res.json()).products || [];
    products.push(...batch.map(normalizeProduct));
    if (batch.length < 250) break;
    await sleep(PAGE_DELAY_MS);
  }
  return { store: root, takenAt: new Date().toISOString(), products };
}
