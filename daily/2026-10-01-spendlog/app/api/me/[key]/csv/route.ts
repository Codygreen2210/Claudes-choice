// Download the whole book as a spreadsheet (CSV opens in Excel, Google Sheets, Numbers).
import { getStore } from '../../../../../lib/store.ts';
import { toCsv } from '../../../../../lib/money.ts';
export const dynamic = 'force-dynamic';
export async function GET(_req: Request, ctx: { params: Promise<{ key: string }> }) {
  const { key } = await ctx.params;
  const store = await getStore();
  const u = await store.userByKey(key);
  if (!u) return new Response('Unknown book.', { status: 404 });
  return new Response(toCsv(await store.entries(u.id)), { headers: { 'content-type': 'text/csv; charset=utf-8', 'content-disposition': 'attachment; filename="spendlog.csv"', 'cache-control': 'no-store' } });
}
