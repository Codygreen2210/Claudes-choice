// Compare two catalog snapshots of the same store and list what changed,
// in the terms a shop owner cares about.

const money = (n) => `$${n.toFixed(2)}`;
const pct = (from, to) => Math.round(((to - from) / from) * 100);

function label(product, variant) {
  return variant && variant.title ? `${product.title} (${variant.title})` : product.title;
}

export function diffCatalogs(before, after) {
  const events = [];
  const old = new Map(before.products.map((p) => [p.id, p]));
  const now = new Map(after.products.map((p) => [p.id, p]));

  for (const p of after.products) {
    const was = old.get(p.id);
    if (!was) {
      const low = Math.min(...p.variants.map((v) => v.price));
      events.push({ type: 'new', product: p.title, handle: p.handle, text: `New product: ${p.title} at ${money(low)}` });
      continue;
    }
    const oldVariants = new Map(was.variants.map((v) => [v.id, v]));
    for (const v of p.variants) {
      const ov = oldVariants.get(v.id);
      if (!ov) continue;
      const name = label(p, v);
      if (v.price !== ov.price) {
        const dir = v.price < ov.price ? 'price_down' : 'price_up';
        events.push({ type: dir, product: name, handle: p.handle, from: ov.price, to: v.price,
          text: `${dir === 'price_down' ? 'Price cut' : 'Price raised'}: ${name} ${money(ov.price)} → ${money(v.price)} (${pct(ov.price, v.price) > 0 ? '+' : ''}${pct(ov.price, v.price)}%)` });
      }
      const onSale = v.compareAt && v.compareAt > v.price;
      const wasOnSale = ov.compareAt && ov.compareAt > ov.price;
      if (onSale && !wasOnSale) events.push({ type: 'sale_start', product: name, handle: p.handle, text: `Sale started: ${name} now ${money(v.price)} (was ${money(v.compareAt)})` });
      if (!onSale && wasOnSale) events.push({ type: 'sale_end', product: name, handle: p.handle, text: `Sale ended: ${name} back to ${money(v.price)}` });
      if (!v.available && ov.available) events.push({ type: 'sold_out', product: name, handle: p.handle, text: `Sold out: ${name}` });
      if (v.available && !ov.available) events.push({ type: 'restock', product: name, handle: p.handle, text: `Back in stock: ${name}` });
    }
  }
  for (const p of before.products) {
    if (!now.has(p.id)) events.push({ type: 'removed', product: p.title, handle: p.handle, text: `Removed from store: ${p.title}` });
  }
  return events;
}

// Order that matters most to a seller: price moves first, then stock, then catalog.
const ORDER = ['price_down', 'sale_start', 'price_up', 'sold_out', 'restock', 'sale_end', 'new', 'removed'];
export function sortEvents(events) {
  return [...events].sort((a, b) => ORDER.indexOf(a.type) - ORDER.indexOf(b.type));
}
