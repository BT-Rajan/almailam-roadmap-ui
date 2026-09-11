<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import ReportSection from '@/components/reports/ReportSection.vue'
import { reportService } from '@/services/reportService'
import { formatCurrency } from '@/utils/currencyFormatter'
import type { FinancialPeriodSummary } from '@/types/Report'

const { t } = useI18n()

// --- Period helpers ---------------------------------------------------

function pad(n: number): string {
  return String(n).padStart(2, '0')
}
function monthBounds(monthValue: string): { start: string; end: string } {
  const [year, month] = monthValue.split('-').map(Number)
  const lastDay = new Date(year, month, 0).getDate()
  return { start: `${monthValue}-01`, end: `${monthValue}-${pad(lastDay)}` }
}
function shiftMonth(monthValue: string, delta: number): string {
  const [year, month] = monthValue.split('-').map(Number)
  const date = new Date(year, month - 1 + delta, 1)
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}`
}
function currentMonthValue(): string {
  const now = new Date()
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}`
}

const currentMonth = ref(currentMonthValue())

type CompareMode = 'previousMonth' | 'sameMonthLastYear' | 'custom'
const compareMode = ref<CompareMode>('previousMonth')
const customCompareFrom = ref('')
const customCompareTo = ref('')

const comparisonRange = computed<{ start: string; end: string } | null>(() => {
  if (compareMode.value === 'previousMonth') return monthBounds(shiftMonth(currentMonth.value, -1))
  if (compareMode.value === 'sameMonthLastYear') return monthBounds(shiftMonth(currentMonth.value, -12))
  if (customCompareFrom.value && customCompareTo.value) return { start: customCompareFrom.value, end: customCompareTo.value }
  return null
})

// --- Data ----------------------------------------------------------------

const current = ref<FinancialPeriodSummary>()
const comparison = ref<FinancialPeriodSummary>()
const isLoading = ref(false)
const loadError = ref('')

async function load(): Promise<void> {
  isLoading.value = true
  loadError.value = ''
  try {
    const currentRange = monthBounds(currentMonth.value)
    const range = comparisonRange.value
    const [currentSummary, comparisonSummary] = await Promise.all([
      reportService.getFinancialSummary(currentRange.start, currentRange.end),
      range ? reportService.getFinancialSummary(range.start, range.end) : Promise.resolve(undefined),
    ])
    current.value = currentSummary
    comparison.value = comparisonSummary
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : t('report.monthlyFinancialsPage.loadFailed')
    current.value = undefined
    comparison.value = undefined
  } finally {
    isLoading.value = false
  }
}

onMounted(load)
watch([currentMonth, compareMode, customCompareFrom, customCompareTo], load)

function computeChange(currentValue: number, compareValue: number): { direction: 'up' | 'down'; percentage: number } | undefined {
  if (!comparison.value) return undefined
  if (compareValue === 0) return currentValue === 0 ? undefined : { direction: 'up', percentage: 100 }
  const percentage = Math.round((Math.abs(currentValue - compareValue) / compareValue) * 100)
  return { direction: currentValue >= compareValue ? 'up' : 'down', percentage }
}

const metrics = computed(() => {
  if (!current.value) return []
  const c = current.value
  const cmp = comparison.value
  return [
    { key: 'received', label: t('report.monthlyFinancialsPage.metricReceived'), value: c.totalReceived, compareValue: cmp?.totalReceived, color: 'success' },
    { key: 'due', label: t('report.monthlyFinancialsPage.metricDue'), value: c.totalDue, compareValue: cmp?.totalDue, color: 'primary' },
    { key: 'outstanding', label: t('report.monthlyFinancialsPage.metricOutstanding'), value: c.totalOutstanding, compareValue: cmp?.totalOutstanding, color: 'warning' },
    { key: 'overdue', label: t('report.monthlyFinancialsPage.metricOverdue'), value: c.totalOverdue, compareValue: cmp?.totalOverdue, color: 'danger' },
  ]
})
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader :title="t('report.monthlyFinancialsPage.pageTitle')" :subtitle="t('report.monthlyFinancialsPage.pageSubtitle')" />

    <Card>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-sm font-medium text-text-secondary">{{ t('report.monthlyFinancialsPage.currentMonth') }}</label>
          <input
            v-model="currentMonth"
            type="month"
            class="h-10 w-full rounded-lg border border-border-default bg-bg-card px-3 text-sm text-text-primary transition-colors duration-fast focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/30"
          />
        </div>
        <SelectBox
          v-model="compareMode"
          :label="t('report.monthlyFinancialsPage.compareWith')"
          :options="[
            { label: t('report.monthlyFinancialsPage.comparePreviousMonth'), value: 'previousMonth' },
            { label: t('report.monthlyFinancialsPage.compareSameMonthLastYear'), value: 'sameMonthLastYear' },
            { label: t('report.monthlyFinancialsPage.compareCustom'), value: 'custom' },
          ]"
        />
        <template v-if="compareMode === 'custom'">
          <DatePicker v-model="customCompareFrom" :label="t('report.monthlyFinancialsPage.compareFrom')" :max="customCompareTo || undefined" />
          <DatePicker v-model="customCompareTo" :label="t('report.monthlyFinancialsPage.compareTo')" :min="customCompareFrom || undefined" />
        </template>
      </div>
    </Card>

    <ErrorState v-if="loadError" :description="loadError" @retry="load" />

    <template v-else-if="current">
      <ReportSection
        :title="t('report.monthlyFinancialsPage.currentPeriodTitle', { start: current.startDate, end: current.endDate })"
        :description="comparison ? t('report.monthlyFinancialsPage.comparisonNote', { start: comparison.startDate, end: comparison.endDate }) : undefined"
        full-width
      >
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 laptop:grid-cols-4">
          <ReportMetricCard
            v-for="metric in metrics"
            :key="metric.key"
            :label="metric.label"
            :value="formatCurrency(metric.value)"
            :change="computeChange(metric.value, metric.compareValue ?? 0)"
            :color="metric.color"
          />
        </div>
      </ReportSection>

      <ReportSection v-if="comparison" :title="t('report.monthlyFinancialsPage.sideBySideTitle')" full-width>
        <div class="overflow-x-auto rounded-xl border border-border-light">
          <table class="w-full text-sm">
            <thead class="bg-bg-secondary text-start">
              <tr>
                <th class="px-4 py-2 text-start font-semibold text-text-secondary">{{ t('report.monthlyFinancialsPage.metric') }}</th>
                <th class="px-4 py-2 text-end font-semibold text-text-secondary">{{ t('report.monthlyFinancialsPage.currentPeriod') }}</th>
                <th class="px-4 py-2 text-end font-semibold text-text-secondary">{{ t('report.monthlyFinancialsPage.comparisonPeriod') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="metric in metrics" :key="metric.key" class="border-t border-border-light">
                <td class="px-4 py-2 text-text-primary">{{ metric.label }}</td>
                <td class="px-4 py-2 text-end text-text-primary">{{ formatCurrency(metric.value) }}</td>
                <td class="px-4 py-2 text-end text-text-muted">{{ formatCurrency(metric.compareValue ?? 0) }}</td>
              </tr>
              <tr class="border-t border-border-light">
                <td class="px-4 py-2 text-text-primary">{{ t('report.monthlyFinancialsPage.metricPaymentCount') }}</td>
                <td class="px-4 py-2 text-end text-text-primary">{{ current.paymentCount }}</td>
                <td class="px-4 py-2 text-end text-text-muted">{{ comparison.paymentCount }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </ReportSection>
    </template>
  </div>
</template>
