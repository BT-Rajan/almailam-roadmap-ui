import { i18n } from '@/i18n'
import { useServerTimeStore } from '@/stores/serverTimeStore'

/** Today's date as YYYY-MM-DD, for DatePicker's `min`/`max` props, past/future-date
 * checks, and period-scoped report queries (currentMonthRange below). Kuwait-local
 * (see serverTimeStore.ts), not the visiting browser's own clock/timezone -- falls
 * back to the browser's local date only for the brief window before the app's first
 * server-time fetch resolves. */
export function todayIso(): string {
  return useServerTimeStore().todayIso ?? new Date().toISOString().slice(0, 10)
}

/** `fromIso` (YYYY-MM-DD) shifted by `days` (negative to go back), returned as YYYY-MM-DD.
 * For DatePicker `min`/`max` bounds and range checks -- e.g. `addDaysIso(todayIso(), 180)`. */
export function addDaysIso(fromIso: string, days: number): string {
  const date = new Date(`${fromIso}T00:00:00`)
  date.setDate(date.getDate() + days)
  return date.toISOString().slice(0, 10)
}

/** First and last calendar day of the current month, both as YYYY-MM-DD
 * -- for period-scoped report queries (e.g. reportService.
 * getFinancialSummary's startDate/endDate), so a caller doesn't have to
 * work out month-length/leap-year edge cases itself. */
export function currentMonthRange(): { start: string; end: string } {
  const today = todayIso()
  const yearMonth = today.slice(0, 7)
  const [year, month] = today.split('-').map(Number)
  const lastDay = new Date(Date.UTC(year, month, 0)).getUTCDate()
  return { start: `${yearMonth}-01`, end: `${yearMonth}-${String(lastDay).padStart(2, '0')}` }
}

// Everywhere a date is shown as text (not typed into a native date
// input, which follows the browser/OS locale on its own -- see
// DatePicker.vue), it must read as DD-MM-YYYY. en-GB's 2-digit/2-digit/
// numeric order is already day/month/year; swapping its "/" separator
// for "-" gets the exact DD-MM-YYYY string without hand-rolling
// zero-padding or a separate timezone-handling path for every caller.
const DISPLAY_FORMAT: Intl.DateTimeFormatOptions = {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
}

const DISPLAY_FORMAT_WITH_TIME: Intl.DateTimeFormatOptions = {
  ...DISPLAY_FORMAT,
  hour: '2-digit',
  minute: '2-digit',
}

const SHORT_DATE_FORMAT: Intl.DateTimeFormatOptions = {
  day: '2-digit',
  month: '2-digit',
}

const TIME_FORMAT: Intl.DateTimeFormatOptions = {
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
}

export function formatDate(isoDate: string): string {
  const date = new Date(isoDate)
  if (Number.isNaN(date.getTime())) return isoDate
  return date.toLocaleDateString('en-GB', DISPLAY_FORMAT).replace(/\//g, '-')
}

export function formatDateTime(isoDateTime: string): string {
  const date = new Date(isoDateTime)
  if (Number.isNaN(date.getTime())) return isoDateTime
  return date.toLocaleString('en-GB', DISPLAY_FORMAT_WITH_TIME).replace(/\//g, '-')
}

/** Compact "05-01" style (day-month, no year), for widgets too narrow for the full year (dashboard cards, due-date chips). */
export function formatShortDate(isoDate: string): string {
  const date = new Date(isoDate)
  if (Number.isNaN(date.getTime())) return isoDate
  return date.toLocaleDateString('en-GB', SHORT_DATE_FORMAT).replace(/\//g, '-')
}

/** "05-01, 14:30" -- the formatShortDate() style with a time appended. */
export function formatShortDateTime(isoDateTime: string): string {
  const date = new Date(isoDateTime)
  if (Number.isNaN(date.getTime())) return isoDateTime
  return date.toLocaleString('en-GB', { ...SHORT_DATE_FORMAT, ...TIME_FORMAT }).replace(/\//g, '-')
}

/** 24-hour "14:30", from an already-parsed Date (e.g. a calendar grid cell). */
export function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-GB', TIME_FORMAT)
}

/** "Today" / "Yesterday" / "N days ago" for a date-only ISO string,
 * falling back to a plain short date for anything further back OR in
 * the future. Deliberately does NOT extend the relative phrasing to
 * future dates ("in 3 days") for the *_ago_ cases -- the bug this
 * exists to fix was exactly that: an upcoming (future-dated) item's
 * age comes out negative and rendered verbatim as "-35 days ago". */
export function formatRelativeDate(isoDate: string): string {
  const date = new Date(isoDate)
  if (Number.isNaN(date.getTime())) return isoDate
  const todayUTC = Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth(), new Date().getUTCDate())
  const diffDays = Math.floor((todayUTC - date.getTime()) / (1000 * 60 * 60 * 24))
  if (diffDays === 0) return i18n.global.t('common.today')
  if (diffDays === 1) return i18n.global.t('common.yesterday')
  if (diffDays > 1 && diffDays < 7) return i18n.global.t('common.daysAgo', { count: diffDays })
  return formatShortDate(isoDate)
}

/** Whether a date-only ISO string ("YYYY-MM-DD") is strictly before
 * today's calendar date -- for "is this overdue" checks. Both sides
 * are compared in UTC: an ISO date-only string parses as UTC
 * midnight, so deriving "today" from the browser's own local
 * timezone would shift the cutoff by the client's UTC offset, and
 * comparing raw instants (`new Date(dueDate) < new Date()`) would
 * mark anything due "today" as already overdue the moment the clock
 * ticks past UTC midnight, rather than at the end of today. */
export function isPastDate(isoDate: string): boolean {
  const date = new Date(isoDate)
  if (Number.isNaN(date.getTime())) return false
  const todayUTC = Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth(), new Date().getUTCDate())
  return date.getTime() < todayUTC
}
