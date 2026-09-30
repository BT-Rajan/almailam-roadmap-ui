<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter, type LocationQueryRaw } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import BarChart from '@/components/reports/BarChart.vue'
import ReportDateRange from '@/components/reports/ReportDateRange.vue'
import ReportHeader from '@/components/reports/ReportHeader.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import ReportSection from '@/components/reports/ReportSection.vue'
import { formatValue } from '@/components/reports/chartUtils'
import { useReportRange } from '@/composables/useReportRange'
import { reportService } from '@/services/reportService'
import type { FinancialCurrencyBreakdown, FinancialPeriodSummary } from '@/types/Report'
import { downloadCsv } from '@/utils/csvExport'
import { formatDateTime } from '@/utils/dateFormatter'
import { formatRange, isIsoDate, previousPeriod, samePeriodLastYear, type DateRange } from '@/utils/reportRange'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const f = (key: string, values?: Record<string, unknown>) => t(`report.monthlyFinancialsPage.${key}`, values ?? {})

// ---- Periods: the one being looked at, and what it is compared with --------------
const rangeState = useReportRange('last-month')
const periodLabel = computed(() => formatRange(rangeState.range.value))

type CompareMode = 'previous' | 'last-year' | 'custom' | 'none'
const compareMode = computed<CompareMode>(() => {
  const value = route.query.compare
  return value === 'last-year' || value === 'custom' || value === 'none' ? value : 'previous'
})
const customFrom = ref(typeof route.query.cfrom === 'string' ? route.query.cfrom : '')
const customTo = ref(typeof route.query.cto === 'string' ? route.query.cto : '')

const comparisonRange = computed<DateRange | null>(() => {
  if (compareMode.value === 'previous') return previousPeriod(rangeState.range.value)
  if (compareMode.value === 'last-year') return samePeriodLastYear(rangeState.range.value)
  if (compareMode.value === 'custom') {
    const from = route.query.cfrom
    const to = route.query.cto
    if (isIsoDate(from) && isIsoDate(to)) return from <= to ? { from, to } : { from: to, to: from }
  }
  return null
})

function setCompareMode(mode: string): void {
  const query: LocationQueryRaw = { ...route.query, compare: mode }
  if (mode !== 'custom') {
    delete query.cfrom
    delete query.cto
  }
  void router.replace({ query })
}
function applyCustomComparison(): void {
  if (customFrom.value && customTo.value) void router.replace({ query: { ...route.query, compare: 'custom', cfrom: customFrom.value, cto: customTo.value } })
}

// ---- Data ------------------------------------------------------------------------
const current = ref<FinancialPeriodSummary>()
const comparison = ref<FinancialPeriodSummary>()
const isLoading = ref(false)
const loadError = ref('')
const generatedAt = ref('')
let requestId = 0

async function load(): Promise<void> {
  const currentRequest = ++requestId
  isLoading.value = true
  loadError.value = ''
  try {
    const { from, to } = rangeState.range.value
    const other = comparisonRange.value
    const [currentSummary, comparisonSummary] = await Promise.all([
      reportService.getFinancialSummary(from, to),
      other ? reportService.getFinancialSummary(other.from, other.to) : Promise.resolve(undefined),
    ])
    if (currentRequest !== requestId) return
    current.value = currentSummary
    comparison.value = comparisonSummary
    generatedAt.value = formatDateTime(new Date().toISOString())
  } catch (error) {
    if (currentRequest === requestId) loadError.value = error instanceof Error ? error.message : f('loadFailed')
  } finally {
    if (currentRequest === requestId) isLoading.value = false
  }
}

watch(() => [rangeState.range.value, comparisonRange.value] as const, load, { immediate: true })

// ---- Metrics, per currency ------------------------------------------------------
type MetricKey = 'received' | 'refunded' | 'net' | 'due' | 'collected' | 'rate' | 'outstanding' | 'overdue'
interface Metric {
  key: MetricKey
  label: string
  value: number | null
  compareValue: number | null
  /** Is a rise good news? (More cash yes; more overdue no.) */
  upIsGood: boolean
  percent?: boolean
  color: string
}

function metricsFor(entry: FinancialCurrencyBreakdown, other: FinancialCurrencyBreakdown | undefined, hasComparison: boolean): Metric[] {
  const rate = (e?: FinancialCurrencyBreakdown) => (e && e.totalDue > 0 ? Math.round((e.totalCollected / e.totalDue) * 1000) / 10 : null)
  const cmp = (value: number | undefined) => (hasComparison ? (value ?? 0) : null)
  return [
    { key: 'received', label: f('metricReceived'), value: entry.totalReceived, compareValue: cmp(other?.totalReceived), upIsGood: true, color: 'success' },
    { key: 'refunded', label: f('metricRefunded'), value: entry.totalRefunded, compareValue: cmp(other?.totalRefunded), upIsGood: false, color: 'warning' },
    { key: 'net', label: f('metricNet'), value: entry.netReceived, compareValue: cmp(other?.netReceived), upIsGood: true, color: 'primary' },
    { key: 'due', label: f('metricDue'), value: entry.totalDue, compareValue: cmp(other?.totalDue), upIsGood: true, color: 'info' },
    { key: 'collected', label: f('metricCollected'), value: entry.totalCollected, compareValue: cmp(other?.totalCollected), upIsGood: true, color: 'success' },
    { key: 'rate', label: f('metricCollectionRate'), value: rate(entry), compareValue: hasComparison ? rate(other) : null, upIsGood: true, percent: true, color: 'info' },
    { key: 'outstanding', label: f('metricOutstanding'), value: entry.totalOutstanding, compareValue: cmp(other?.totalOutstanding), upIsGood: false, color: 'warning' },
    { key: 'overdue', label: f('metricOverdue'), value: entry.totalOverdue, compareValue: cmp(other?.totalOverdue), upIsGood: false, color: 'danger' },
  ]
}

const groups = computed(() => {
  if (!current.value) return []
  const currencies = [...new Set([...current.value.byCurrency.map((e) => e.currency), ...(comparison.value?.byCurrency.map((e) => e.currency) ?? [])])].sort()
  const blank = (currency: string): FinancialCurrencyBreakdown => ({
    currency, totalReceived: 0, totalRefunded: 0, netReceived: 0, totalDue: 0, totalCollected: 0, totalOutstanding: 0, totalOverdue: 0,
  })
  return currencies.map((currency) => {
    const entry = current.value!.byCurrency.find((e) => e.currency === currency) ?? blank(currency)
    const other = comparison.value?.byCurrency.find((e) => e.currency === currency)
    return { currency, metrics: metricsFor(entry, other, Boolean(comparison.value)) }
  })
})

function display(metric: Metric, value: number | null): string {
  if (value === null) return '—'
  return metric.percent ? `${value}%` : formatValue(value, 'currency')
}

// No percentage against a zero base (it isn't +100%, it's new).
function change(metric: Metric): { direction: 'up' | 'down'; percentage: number; good: boolean } | undefined {
  if (metric.value === null || metric.compareValue === null || metric.compareValue === 0 || metric.value === metric.compareValue) return undefined
  const direction = metric.value > metric.compareValue ? 'up' : 'down'
  const percentage = metric.percent
    ? Math.round(Math.abs(metric.value - metric.compareValue) * 10) / 10
    : Math.round((Math.abs(metric.value - metric.compareValue) / Math.abs(metric.compareValue)) * 100)
  return { direction, percentage, good: (direction === 'up') === metric.upIsGood }
}
function changeText(metric: Metric): string {
  if (metric.value === null || metric.compareValue === null) return '—'
  if (metric.compareValue === 0) return metric.value === 0 ? '0' : f('newValue')
  const c = change(metric)
  if (!c) return '0'
  return `${c.direction === 'up' ? '+' : '−'}${c.percentage}${metric.percent ? ' pts' : '%'}`
}

// Money metrics that share one axis (the rate is a %, shown in the table only).
const CHART_KEYS: MetricKey[] = ['received', 'net', 'due', 'collected', 'outstanding', 'overdue']
function chartFor(metrics: Metric[]) {
  const chosen = metrics.filter((m) => CHART_KEYS.includes(m.key))
  return {
    categories: chosen.map((m) => m.label),
    series: [
      { name: f('currentPeriod'), values: chosen.map((m) => m.value ?? 0) },
      { name: f('comparisonPeriod'), values: chosen.map((m) => m.compareValue ?? 0), color: 'var(--chart-neutral)' },
    ],
  }
}

function exportCsv(): void {
  if (!current.value) return
  const other = comparisonRange.value
  downloadCsv(`financials-${rangeState.range.value.from}-to-${rangeState.range.value.to}.csv`, [
    ...groups.value.map((group) => ({
      title: `${f('pageTitle')} (${group.currency}) -- ${periodLabel.value}${other ? ` vs ${formatRange(other)}` : ''}`,
      headers: [f('metric'), f('currentPeriod'), f('comparisonPeriod'), f('change')],
      rows: group.metrics.map((m) => [m.label, m.value, m.compareValue, changeText(m)]),
    })),
    {
      title: f('metricPaymentCount'),
      headers: [f('currentPeriod'), f('comparisonPeriod')],
      rows: [[current.value.paymentCount, comparison.value?.paymentCount ?? null]],
    },
  ])
}
</script>

<template>
  <div class="mx-auto max-w-6xl space-y-8 p-6 laptop:p-8">
    <BaseButton variant="ghost" size="sm" class="print:hidden" @click="router.back()">← {{ t('report.back') }}</BaseButton>

    <ReportHeader
      :title="f('pageTitle')"
      :subtitle="f('pageSubtitle')"
      :period="comparisonRange ? `${periodLabel} · ${f('comparisonPeriod')} ${formatRange(comparisonRange)}` : periodLabel"
      :generated-date="generatedAt"
      :exportable="Boolean(current)"
      @download="exportCsv"
    />

    <div class="flex flex-wrap items-end gap-4">
      <ReportDateRange :state="rangeState" />
      <div class="w-56 print:hidden">
        <SelectBox
          :model-value="compareMode"
          :label="f('compareWith')"
          :options="[
            { label: f('comparePrevious'), value: 'previous' },
            { label: f('compareLastYear'), value: 'last-year' },
            { label: f('compareCustom'), value: 'custom' },
            { label: f('compareNone'), value: 'none' },
          ]"
          @update:model-value="setCompareMode"
        />
      </div>
      <template v-if="compareMode === 'custom'">
        <div class="w-44 print:hidden"><DatePicker v-model="customFrom" :label="f('compareFrom')" /></div>
        <div class="w-44 print:hidden"><DatePicker v-model="customTo" :label="f('compareTo')" :min="customFrom" /></div>
        <BaseButton class="print:hidden" :disabled="!customFrom || !customTo" @click="applyCustomComparison">{{ t('report.range.apply') }}</BaseButton>
      </template>
    </div>

    <ErrorState v-if="loadError" :description="loadError" @retry="load" />
    <div v-else-if="!current" class="rounded-xl border border-border-light bg-bg-card p-5"><SkeletonLoader :rows="6" /></div>

    <div v-else class="space-y-8 transition-opacity" :class="isLoading ? 'opacity-50' : ''">
      <p class="text-xs text-text-muted">
        {{ comparisonRange && comparison ? f('comparisonNote', { range: formatRange(comparisonRange) }) : f('noComparisonNote') }}
      </p>

      <ReportSection v-for="group in groups" :key="group.currency" :title="`${f('pageTitle')} · ${group.currency}`" full-width>
        <div class="grid grid-cols-2 gap-4 laptop:grid-cols-4">
          <ReportMetricCard
            v-for="metric in group.metrics"
            :key="metric.key"
            :label="metric.label"
            :value="display(metric, metric.value)"
            :unit="metric.percent ? undefined : group.currency"
            :change="metric.percent ? undefined : change(metric)"
            :color="metric.color"
          />
        </div>

        <div v-if="comparison" class="mt-4 grid grid-cols-1 gap-4 laptop:grid-cols-5">
          <Card class="laptop:col-span-3">
            <h3 class="text-sm font-semibold text-text-primary">{{ f('chartTitle') }}</h3>
            <p class="mb-3 text-xs text-text-muted">{{ f('chartDescription', { currency: group.currency }) }}</p>
            <BarChart v-bind="chartFor(group.metrics)" horizontal format="currency" :category-label="f('metric')" />
          </Card>
          <Card class="laptop:col-span-2">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-border-light text-left text-xs uppercase tracking-wide text-text-muted">
                  <th class="py-2 pe-3 font-medium">{{ f('metric') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ f('currentPeriod') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ f('comparisonPeriod') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ f('change') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="metric in group.metrics" :key="metric.key" class="border-b border-border-light/60 last:border-0">
                  <td class="py-2 pe-3 text-text-primary">{{ metric.label }}</td>
                  <td class="py-2 ps-3 text-end tabular-nums">{{ display(metric, metric.value) }}</td>
                  <td class="py-2 ps-3 text-end tabular-nums text-text-secondary">{{ display(metric, metric.compareValue) }}</td>
                  <td
                    class="py-2 ps-3 text-end font-medium tabular-nums"
                    :class="change(metric) ? (change(metric)!.good ? 'text-success-600' : 'text-danger-600') : 'text-text-muted'"
                  >
                    {{ changeText(metric) }}
                  </td>
                </tr>
                <tr>
                  <td class="py-2 pe-3 text-text-primary">{{ f('metricPaymentCount') }}</td>
                  <td class="py-2 ps-3 text-end tabular-nums">{{ current.paymentCount }}</td>
                  <td class="py-2 ps-3 text-end tabular-nums text-text-secondary">{{ comparison.paymentCount }}</td>
                  <td />
                </tr>
              </tbody>
            </table>
          </Card>
        </div>
      </ReportSection>
    </div>
  </div>
</template>
