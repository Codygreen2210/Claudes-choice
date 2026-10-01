export type User = { id: string; key: string; handle: string; created_at: string };

// One spending or income line. Money is stored in whole cents so totals never drift.
export type Entry = {
  id: string;
  user_id: string;
  kind: 'expense' | 'income';
  cents: number;
  category: string;  // lowercased, e.g. "groceries"
  note: string;      // short, scrubbed, e.g. "Walmart"
  day: string;       // YYYY-MM-DD the money moved
  created_at: string;
};

export type Budget = { user_id: string; category: string; cents: number };
