import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { niceTicks } from '@/components/reports/chartUtils'
import { addDaysIso } from '@/utils/dateFormatter'
import { formatRange, isIsoDate, presetRange } from '@/utils/reportRange'

beforeEach(() => setActivePinia(createPinia()))

describe('presetRange', () => {
  it('works out month, quarter and year bounds from today', () => {
    const today = '2026-09-30'
    expect(presetRange('this-month', today)).toEqual({ from: '2026-09-01', to: '2026-09-30' })
    expect(presetRange('last-month', today)).toEqual({ from: '2026-08-01', to: '2026-08-31' })
    expect(presetRange('this-quarter', today)).toEqual({ from: '2026-07-01', to: '2026-09-30' })
    expect(presetRange('last-quarter', today)).toEqual({ from: '2026-04-01', to: '2026-06-30' })
    expect(presetRange('this-year', today)).toEqual({ from: '2026-01-01', to: '2026-12-31' })
    expect(presetRange('last-year', today)).toEqual({ from: '2025-01-01', to: '2025-12-31' })
    expect(presetRange('last-12-months', today)).toEqual({ from: '2025-10-01', to: '2026-09-30' })
  })

  it('crosses the year boundary in January', () => {
    const today = '2026-01-15'
    expect(presetRange('last-month', today)).toEqual({ from: '2025-12-01', to: '2025-12-31' })
    expect(presetRange('last-quarter', today)).toEqual({ from: '2025-10-01', to: '2025-12-31' })
  })

  it('handles February in a leap year', () => {
    expect(presetRange('this-month', '2028-02-10')).toEqual({ from: '2028-02-01', to: '2028-02-29' })
  })

  it('shifts dates by whole calendar days (UTC maths, so no timezone skew)', () => {
    expect(addDaysIso('2026-09-30', 0)).toBe('2026-09-30')
    expect(addDaysIso('2026-09-30', 1)).toBe('2026-10-01')
    expect(addDaysIso('2026-03-01', -1)).toBe('2026-02-28')
  })
})

describe('isIsoDate / formatRange', () => {
  it('accepts only real calendar dates', () => {
    expect(isIsoDate('2026-02-28')).toBe(true)
    expect(isIsoDate('2026-02-30')).toBe(false)
    expect(isIsoDate('2026-9-1')).toBe(false)
    expect(isIsoDate(['2026-01-01'])).toBe(false)
  })

  it('reads well', () => {
    expect(formatRange({ from: '2026-09-01', to: '2026-09-30' })).toMatch(/^1 Sept? 2026 – 30 Sept? 2026$/)
    expect(formatRange({ from: '2026-09-01', to: '2026-09-01' })).not.toContain('–')
  })
})

describe('niceTicks', () => {
  it('uses round steps that cover the maximum', () => {
    expect(niceTicks(930)).toEqual([0, 250, 500, 750, 1000])
    expect(niceTicks(4)).toEqual([0, 1, 2, 3, 4])
    expect(niceTicks(0)).toEqual([0, 1])
    expect(niceTicks(2, 4, true)).toEqual([0, 1, 2])
  })
})

describe('downloadCsv', () => {
  it('escapes quotes/commas and neutralises spreadsheet formulas', async () => {
    const captured: Blob[] = []
    vi.doMock('@/utils/fileDownload', () => ({ triggerBlobDownload: (blob: Blob) => captured.push(blob) }))
    const { downloadCsv } = await import('@/utils/csvExport')
    downloadCsv('x.csv', [{ headers: ['Name', 'Amount'], rows: [['=HYPERLINK("x")', -5], ['A, "B"', 1.5]] }])
    const text = await captured[0].text()
    expect(text).toContain(`"'=HYPERLINK(""x"")",-5`)
    expect(text).toContain('"A, ""B""",1.5')
    vi.doUnmock('@/utils/fileDownload')
  })
})
