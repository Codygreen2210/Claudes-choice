// Makes a simulated week of logs for a typical AI support app (seeded, so it's the same every run).
let s = 42; const r = () => (s = (s * 16807) % 2147483647) / 2147483647;
const pick = (a) => a[Math.floor(r() * a.length)];
const SYS = 'You are the help assistant for Brightside Plumbing Supply. ' + 'Product catalog and return policy details follow. '.repeat(700);
const TAG = 'Classify this ticket as billing, shipping, returns or other. Reply with one word.\n';
const qs = ['Where is my order?', 'How do I return a faucet?', 'Do you ship to Canada?', 'Is the PEX crimper in stock?', 'Can I change my address?'];
const rows = [];
for (let i = 0; i < 6000; i++) {
  const t = r();
  if (t < 0.6) rows.push({ model: 'gpt-4o-2024-08-06', messages: [{ role: 'system', content: SYS }, { role: 'user', content: r() < 0.35 ? pick(qs) : pick(qs) + ' order #' + Math.floor(r() * 1e5) }], output: 'x'.repeat(300 + Math.floor(r() * 900)) });
  else if (t < 0.9) rows.push({ model: 'claude-sonnet-4-5', messages: [{ role: 'user', content: TAG + 'Ticket ' + Math.floor(r() * 1e6) + ': ' + pick(qs) }], output: pick(['billing', 'shipping', 'returns', 'other']) });
  else rows.push({ model: 'gpt-4o-mini', prompt: 'Summarize: ' + 'call notes '.repeat(200 + Math.floor(r() * 200)), output: 'x'.repeat(400) });
}
process.stdout.write(rows.map((x) => JSON.stringify(x)).join('\n') + '\n');
