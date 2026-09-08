import { i18n } from '@/i18n'

/** Today's date as YYYY-MM-DD, for DatePicker's `min`/`max` props and past/future-date checks. */
export function todayIso(): string {
  return new Date().toISOString().slice(0, 10)
}

const DISPLAY_FORMAT: Intl.DateTimeFormatOptions = {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
}

const DISPLAY_FORMAT_WITH_TIME: Intl.DateTimeFormatOptions = {
  ...DISPLAY_FORMAT,
  hour: '2-digit',
  minute: '2-digit',
}

const SHORT_DATE_FORMAT: Intl.DateTimeFormatOptions = {
  day: 'numeric',
  month: 'short',
}

const TIME_FORMAT: Intl.DateTimeFormatOptions = {
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
}

export function formatDate(isoDate: string): string {
  const date = new Date(isoDate)
  if (Number.isNaN(date.getTime())) return isoDate
  return date.toLocaleDateString('en-GB', DISPLAY_FORMAT)
}

export function formatDateTime(isoDateTime: string): string {
  const date = new Date(isoDateTime)
  if (Number.isNaN(date.getTime())) return isoDateTime
  return date.toLocaleString('en-GB', DISPLAY_FORMAT_WITH_TIME)
}

/** D/M/YYYY with Western digits, matching the lettered templates' own date style (e.g. 28/9/2025). */
export function formatDateNumeric(isoDate: string): string {
  const date = new Date(isoDate)
  if (Number.isNaN(date.getTime())) return isoDate
  return `${date.getDate()}/${date.getMonth() + 1}/${date.getFullYear()}`
}

/** Compact "5 Jan" style, for widgets too narrow for the full year (dashboard cards, due-date chips). */
export function formatShortDate(isoDate: string): string {
  const date = new Date(isoDate)
  if (Number.isNaN(date.getTime())) return isoDate
  return date.toLocaleDateString('en-GB', SHORT_DATE_FORMAT)
}

/** "5 Jan, 14:30" -- the formatShortDate() style with a time appended. */
export function formatShortDateTime(isoDateTime: string): string {
  const date = new Date(isoDateTime)
  if (Number.isNaN(date.getTime())) return isoDateTime
  return date.toLocaleString('en-GB', { ...SHORT_DATE_FORMAT, ...TIME_FORMAT })
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
