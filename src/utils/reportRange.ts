// Date ranges for reports: one set of presets shared by every report, all
// worked out from Kuwait's "today" (todayIso) with plain calendar maths in
// UTC, so no browser timezone can shift a boundary by a day.

import { todayIso } from '@/utils/dateFormatter'

export type RangePreset =
  | 'today'
  | 'last-7-days'
  | 'last-30-days'
  | 'this-month'
  | 'last-month'
  | 'this-quarter'
  | 'last-quarter'
  | 'this-year'
  | 'last-year'
  | 'last-12-months'
  | 'custom'

export const RANGE_PRESETS: Exclude<RangePreset, 'custom'>[] = [
  'today',
  'last-7-days',
  'last-30-days',
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
  const [year, month, day] = today.split('-').map(Number)
  const monthIndex = month - 1
  const quarterStart = monthIndex - (monthIndex % 3)
  switch (preset) {
    case 'today':
      return { from: today, to: today }
    case 'last-7-days':
      return { from: iso(year, monthIndex, day - 6), to: today }
    case 'last-30-days':
      return { from: iso(year, monthIndex, day - 29), to: today }
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

const DAY_MS = 86_400_000
const toTime = (value: string) => Date.parse(`${value}T00:00:00Z`)
const fromTime = (time: number) => new Date(time).toISOString().slice(0, 10)

/** Whole calendar months (1st to month-end): how many, or null if not aligned. */
function wholeMonths(range: DateRange): number | null {
  const [fy, fm, fd] = range.from.split('-').map(Number)
  const [ty, tm] = range.to.split('-').map(Number)
  if (fd !== 1 || range.to !== iso(ty, tm, 0)) return null
  return (ty - fy) * 12 + (tm - fm) + 1
}

/**
 * The period just before `range`, for "compared with previous period":
 * whole months shift by months (March -> February, Q3 -> Q2), anything
 * else by the same number of days immediately before.
 */
export function previousPeriod(range: DateRange): DateRange {
  const months = wholeMonths(range)
  if (months !== null) {
    const [fy, fm] = range.from.split('-').map(Number)
    return { from: iso(fy, fm - 1 - months, 1), to: iso(fy, fm - 1, 0) }
  }
  const days = Math.round((toTime(range.to) - toTime(range.from)) / DAY_MS) + 1
  const to = toTime(range.from) - DAY_MS
  return { from: fromTime(to - (days - 1) * DAY_MS), to: fromTime(to) }
}

/** The same dates a year earlier (29 Feb becomes 28 Feb; month-ends stay month-ends). */
export function samePeriodLastYear(range: DateRange): DateRange {
  const shift = (value: string, isEnd: boolean) => {
    const [y, m, d] = value.split('-').map(Number)
    const lastDay = Number(iso(y - 1, m, 0).slice(8))
    const wasMonthEnd = value === iso(y, m, 0)
    return iso(y - 1, m - 1, isEnd && wasMonthEnd ? lastDay : Math.min(d, lastDay))
  }
  return { from: shift(range.from, false), to: shift(range.to, true) }
}

/** A readable "1 Sep 2026 – 30 Sep 2026" for headers and printouts. */
export function formatRange(range: DateRange): string {
  const format = (value: string) =>
    new Date(`${value}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })
  return range.from === range.to ? format(range.from) : `${format(range.from)} – ${format(range.to)}`
}
