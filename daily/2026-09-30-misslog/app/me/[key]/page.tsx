import { notFound } from 'next/navigation';
import { headers } from 'next/headers';
import { getStore } from '../../../lib/store.ts';
import Profile from '../../../components/Profile.tsx';
import Settings from '../../../components/Settings.tsx';
export const dynamic = 'force-dynamic';
export const metadata = { robots: { index: false } };

export default async function Me({ params }: { params: Promise<{ key: string }> }) {
  const { key } = await params;
  const store = await getStore();
  const u = await store.userByKey(key);
  if (!u) notFound();
  const h = await headers();
  const origin = `${h.get('x-forwarded-proto') || 'https'}://${h.get('host')}`;
  return (
    <main className="wrap">
      <Settings k={u.key} handle={u.handle} pub={u.public} share={u.share_data} origin={origin} />
      <Profile handle={u.handle} events={await store.events(u.id, 2000)} />
    </main>
  );
}
