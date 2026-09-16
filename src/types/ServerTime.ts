export interface ServerTime {
  // ISO date (YYYY-MM-DD), always Kuwait local time -- see
  // serverTimeStore.ts for why this is the sole source of "today" for
  // every overdue/due-date/expiry decision in the app.
  date: string
  datetime: string
  timezone: string
}
