import Survey from '../components/Survey.tsx';
import { occupations, areas } from '../lib/wages.ts';
export default function Home() {
  return (
    <main className="wrap" style={{ maxWidth: 620 }}>
      <h1>Are you paid fair for your trade?</h1>
      <p className="lead">Put in your job, your area and your pay. See where you land against everybody doing the same work near you, and what your money's worth after the cost of living there.</p>
      <Survey jobs={occupations()} areas={areas()} />
      <p className="note" style={{ marginTop: 16 }}>Covers 259 hands-on jobs in 393 metro areas, from government pay data. Gets sharper as more people add their real pay. For people 18 and older.</p>
    </main>
  );
}
