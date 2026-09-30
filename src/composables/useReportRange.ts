import { computed, type ComputedRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { RANGE_PRESETS, isIsoDate, presetRange, type DateRange, type RangePreset } from '@/utils/reportRange'

export interface ReportRange {
  preset: ComputedRef<RangePreset>
  range: ComputedRef<DateRange>
  /** Switch to a preset, or to a custom from/to (inclusive). */
  setRange: (preset: RangePreset, custom?: DateRange) => void
  /** The period as URL query, to open another report on the same period. */
  urlQuery: () => Record<string, string>
}

/**
 * A report's date range, kept in the URL (?range=last-month, or
 * ?range=custom&from=…&to=…) so a report link or a reload reopens the same
 * period. Anything malformed in the URL falls back to `defaultPreset`.
 */
export function useReportRange(defaultPreset: Exclude<RangePreset, 'custom'> = 'this-month'): ReportRange {
  const route = useRoute()
  const router = useRouter()

  const preset = computed<RangePreset>(() => {
    const value = route.query.range
    if (value === 'custom' && isIsoDate(route.query.from) && isIsoDate(route.query.to)) return 'custom'
    return RANGE_PRESETS.includes(value as Exclude<RangePreset, 'custom'>) ? (value as RangePreset) : defaultPreset
  })

  const range = computed<DateRange>(() => {
    if (preset.value !== 'custom') return presetRange(preset.value)
    const from = route.query.from as string
    const to = route.query.to as string
    return from <= to ? { from, to } : { from: to, to: from }
  })

  function setRange(next: RangePreset, custom?: DateRange): void {
    const query = { ...route.query }
    delete query.from
    delete query.to
    query.range = next
    if (next === 'custom' && custom) {
      const [from, to] = custom.from <= custom.to ? [custom.from, custom.to] : [custom.to, custom.from]
      query.from = from
      query.to = to
    }
    void router.replace({ query })
  }

  function urlQuery(): Record<string, string> {
    return preset.value === 'custom' ? { range: 'custom', from: range.value.from, to: range.value.to } : { range: preset.value }
  }

  return { preset, range, setRange, urlQuery }
}
