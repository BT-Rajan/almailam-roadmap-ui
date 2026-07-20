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
