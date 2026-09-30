export type User = { id: string; key: string; handle: string; public: boolean; share_data: boolean; created_at: string };

export type Ev = {
  id: string;
  user_id: string;
  type: 'miss' | 'search';
  model: string;        // as the AI named itself, cleaned
  family: string;       // Claude, ChatGPT, Gemini, Grok...
  client: string;       // the app it came from, if known (claude.ai, cursor...)
  kind?: string;        // mistake kind (see KINDS)
  trying_to?: string;
  ask?: string;         // short, scrubbed summary of what the person asked
  mistake?: string;
  fix?: string;
  topic?: string;       // for searches
  searches?: number;    // how many searches/lookups in that research session
  tokens: number;       // estimated tokens burned by the mistake (0 for searches)
  dollars: number;      // estimated cost of those tokens
  created_at: string;
};
