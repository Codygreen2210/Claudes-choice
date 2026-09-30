import { notFound } from 'next/navigation';
import { getStore } from '../../../lib/store.ts';
import Profile from '../../../components/Profile.tsx';
export const dynamic = 'force-dynamic';

export default async function PublicProfile({ params }: { params: Promise<{ handle: string }> }) {
  const { handle } = await params;
  const store = await getStore();
  const u = await store.userByHandle(handle);
  if (!u || !u.public) notFound();
  return <main className="wrap"><Profile handle={u.handle} events={await store.events(u.id, 2000)} showSearches={false} /></main>;
}
