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
  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays > 1 && diffDays < 7) return `${diffDays} days ago`
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
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
