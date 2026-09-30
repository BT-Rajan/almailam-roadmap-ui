// Date ranges for reports: one set of presets shared by every report, all
// worked out from Kuwait's "today" (todayIso) with plain calendar maths in
// UTC, so no browser timezone can shift a boundary by a day.

import { todayIso } from '@/utils/dateFormatter'

export type RangePreset =
  | 'this-month'
  | 'last-month'
  | 'this-quarter'
  | 'last-quarter'
  | 'this-year'
  | 'last-year'
  | 'last-12-months'
  | 'custom'

export const RANGE_PRESETS: Exclude<RangePreset, 'custom'>[] = [
  'this-month',
  'last-month',
  'this-quarter',
  'last-quarter',
  'this-year',
  'last-year',
  'last-12-months',
]

/** An inclusive date range, both ends YYYY-MM-DD. */
export interface DateRange {
  from: string
  to: string
}

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/

export function isIsoDate(value: unknown): value is string {
  if (typeof value !== 'string' || !ISO_DATE.test(value)) return false
  const date = new Date(`${value}T00:00:00Z`)
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value
}

function iso(year: number, monthIndex: number, day: number): string {
  return new Date(Date.UTC(year, monthIndex, day)).toISOString().slice(0, 10)
}

export function presetRange(preset: Exclude<RangePreset, 'custom'>, today: string = todayIso()): DateRange {
  const [year, month] = today.split('-').map(Number)
  const monthIndex = month - 1
  const quarterStart = monthIndex - (monthIndex % 3)
  switch (preset) {
    case 'this-month':
      return { from: iso(year, monthIndex, 1), to: iso(year, monthIndex + 1, 0) }
    case 'last-month':
      return { from: iso(year, monthIndex - 1, 1), to: iso(year, monthIndex, 0) }
    case 'this-quarter':
      return { from: iso(year, quarterStart, 1), to: iso(year, quarterStart + 3, 0) }
    case 'last-quarter':
      return { from: iso(year, quarterStart - 3, 1), to: iso(year, quarterStart, 0) }
    case 'this-year':
      return { from: iso(year, 0, 1), to: iso(year, 11, 31) }
    case 'last-year':
      return { from: iso(year - 1, 0, 1), to: iso(year - 1, 11, 31) }
    case 'last-12-months':
      return { from: iso(year, monthIndex - 11, 1), to: iso(year, monthIndex + 1, 0) }
  }
}

/** A readable "1 Sep 2026 – 30 Sep 2026" for headers and printouts. */
export function formatRange(range: DateRange): string {
  const format = (value: string) =>
    new Date(`${value}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })
  return range.from === range.to ? format(range.from) : `${format(range.from)} – ${format(range.to)}`
}
