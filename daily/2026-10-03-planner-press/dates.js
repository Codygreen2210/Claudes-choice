// Planner Press: calendar math. No dependencies, no Date object, so it gives
// the same answer in the browser, in node, and in any time zone.
// Weekdays: 0 = Sunday ... 6 = Saturday.

export const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
export const WEEKDAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

export const isLeap = (y) => (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0;
export const daysInMonth = (y, m) => [31, isLeap(y) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1];
export const daysInYear = (y) => (isLeap(y) ? 366 : 365);

// Days since 1970-01-01 for a calendar date (proleptic Gregorian).
export function toDays(y, m, d) {
  const yy = m <= 2 ? y - 1 : y;
  const era = Math.floor(yy / 400);
  const yoe = yy - era * 400;
  const doy = Math.floor((153 * (m + (m > 2 ? -3 : 9)) + 2) / 5) + d - 1;
  const doe = yoe * 365 + Math.floor(yoe / 4) - Math.floor(yoe / 100) + doy;
  return era * 146097 + doe - 719468;
}

export function fromDays(n) {
  const z = n + 719468;
  const era = Math.floor(z / 146097);
  const doe = z - era * 146097;
  const yoe = Math.floor((doe - Math.floor(doe / 1460) + Math.floor(doe / 36524) - Math.floor(doe / 146096)) / 365);
  const doy = doe - (365 * yoe + Math.floor(yoe / 4) - Math.floor(yoe / 100));
  const mp = Math.floor((5 * doy + 2) / 153);
  const d = doy - Math.floor((153 * mp + 2) / 5) + 1;
  const m = mp < 10 ? mp + 3 : mp - 9;
  return { y: yoe + era * 400 + (m <= 2 ? 1 : 0), m, d };
}

// 1970-01-01 was a Thursday (4).
export const weekday = (y, m, d) => (((toDays(y, m, d) + 4) % 7) + 7) % 7;

const pad = (n) => String(n).padStart(2, '0');
export const iso = (y, m, d) => `${y}-${pad(m)}-${pad(d)}`;

// A day as the planner uses it: { y, m, d, dow, iso, n } (n = days since 1970).
export function day(n) {
  const { y, m, d } = fromDays(n);
  return { y, m, d, dow: (((n + 4) % 7) + 7) % 7, iso: iso(y, m, d), n };
}

export function daysOfYear(y) {
  const out = [];
  const start = toDays(y, 1, 1);
  for (let i = 0; i < daysInYear(y); i++) out.push(day(start + i));
  return out;
}

// Every week that touches the year, in order. Week 1 is the week that holds
// January 1; the last week is the one that holds December 31. Weeks at either
// end can include days from the neighbouring year (they are shown dimmed and
// are not counted as part of this year). Each week has exactly 7 days.
export function weeksOfYear(y, weekStart) {
  const first = toDays(y, 1, 1);
  const last = toDays(y, 12, 31);
  const back = (day(first).dow - weekStart + 7) % 7;
  const weeks = [];
  for (let s = first - back, n = 1; s <= last; s += 7, n++) {
    const days = [];
    for (let i = 0; i < 7; i++) days.push(day(s + i));
    weeks.push({ n, days });
  }
  return weeks;
}

// The month grid: rows of 7 cells, null for days that belong to other months.
export function monthRows(y, m, weekStart) {
  const first = toDays(y, m, 1);
  const lead = (day(first).dow - weekStart + 7) % 7;
  const total = lead + daysInMonth(y, m);
  const rows = [];
  for (let r = 0; r < Math.ceil(total / 7); r++) {
    const row = [];
    for (let c = 0; c < 7; c++) {
      const k = r * 7 + c - lead;
      row.push(k >= 0 && k < daysInMonth(y, m) ? day(first + k) : null);
    }
    rows.push(row);
  }
  return rows;
}

// Weekday headings in the order the week runs.
export const weekdayOrder = (weekStart) => Array.from({ length: 7 }, (_, i) => (weekStart + i) % 7);
