<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import BarChart from '@/components/reports/BarChart.vue'
import ReportDateRange from '@/components/reports/ReportDateRange.vue'
import ReportHeader from '@/components/reports/ReportHeader.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import ReportSection from '@/components/reports/ReportSection.vue'
import { formatValue } from '@/components/reports/chartUtils'
import { STATUS_CHART_COLORS } from '@/constants/chartColors'
import { useReportRange } from '@/composables/useReportRange'
import { reportService } from '@/services/reportService'
import type { EmployeePerformanceReport, PerformanceMember } from '@/types/Report'
import type { SmartTableColumn } from '@/types/Table'
import { downloadCsv } from '@/utils/csvExport'
import { formatDateTime } from '@/utils/dateFormatter'
import { formatRange } from '@/utils/reportRange'

const router = useRouter()
const { t } = useI18n()
const e = (key: string, values?: Record<string, unknown>) => t(`report.employeePerformancePage.${key}`, values ?? {})

const rangeState = useReportRange('last-month')
const periodLabel = computed(() => formatRange(rangeState.range.value))

const report = ref<EmployeePerformanceReport>()
const isLoading = ref(false)
const error = ref<string>()
const generatedAt = ref('')
let requestId = 0

async function load(): Promise<void> {
  const current = ++requestId
  isLoading.value = true
  error.value = undefined
  try {
    const result = await reportService.getEmployeePerformance(rangeState.range.value)
    if (current !== requestId) return
    report.value = result
    generatedAt.value = formatDateTime(new Date().toISOString())
  } catch (loadError) {
    if (current === requestId) error.value = loadError instanceof Error ? loadError.message : e('loadFailed')
  } finally {
    if (current === requestId) isLoading.value = false
  }
}

watch(() => rangeState.range.value, load, { immediate: true })

const totals = computed(() => report.value?.totals)
const members = computed<PerformanceMember[]>(() => report.value?.members ?? [])
const count = (value: number) => formatValue(value, 'number')
const percent = (value: number | null | undefined) => (value === null || value === undefined ? '—' : `${value}%`)

// Outcomes carry meaning (good / late / bad / pending), so status tokens
// plus a neutral for "not due yet".
const outcomeSeries = computed(() => [
  { name: e('seriesOnTime'), values: members.value.map((m) => m.completedOnTime), color: STATUS_CHART_COLORS.success },
  { name: e('seriesLate'), values: members.value.map((m) => m.completedLate), color: STATUS_CHART_COLORS.warning },
  { name: e('seriesOverdue'), values: members.value.map((m) => m.overdueOpen), color: STATUS_CHART_COLORS.danger },
  { name: e('seriesNotYetDue'), values: members.value.map((m) => m.notYetDue), color: 'var(--chart-neutral)' },
])

type Row = PerformanceMember & Record<string, unknown>
const columns = computed<SmartTableColumn<Row>[]>(() => [
  { key: 'employeeName', label: e('columnEmployee'), sortable: true },
  { key: 'dueInPeriod', label: e('columnDue'), align: 'right', sortable: true },
  { key: 'completedOnTime', label: e('columnOnTime'), align: 'right', sortable: true },
  { key: 'completedLate', label: e('columnLate'), align: 'right', sortable: true },
  { key: 'averageDaysLate', label: e('columnAvgLate'), align: 'right', sortable: true },
  { key: 'overdueOpen', label: e('columnOverdue'), align: 'right', sortable: true },
  { key: 'notYetDue', label: e('columnNotYetDue'), align: 'right' },
  { key: 'onTimeRate', label: e('columnOnTimeRate'), align: 'right', sortable: true },
  { key: 'completionRate', label: e('columnCompletionRate'), align: 'right', sortable: true },
  { key: 'completedInPeriod', label: e('columnThroughput'), align: 'right', sortable: true },
])

function exportCsv(): void {
  const data = report.value
  if (!data) return
  downloadCsv(`employee-performance-${data.period.startDate}-to-${data.period.endDate}.csv`, [
    {
      title: `${e('pageTitle')} -- ${periodLabel.value}`,
      headers: [
        e('columnEmployee'), e('columnDue'), e('columnOnTime'), e('columnLate'), e('columnAvgLate'), e('columnOverdue'), e('columnNotYetDue'),
        `${e('columnOnTimeRate')} (%)`, `${e('columnCompletionRate')} (%)`, e('columnThroughput'),
      ],
      rows: data.members.map((m) => [
        m.employeeName, m.dueInPeriod, m.completedOnTime, m.completedLate, m.averageDaysLate, m.overdueOpen, m.notYetDue,
        m.onTimeRate, m.completionRate, m.completedInPeriod,
      ]),
    },
  ])
}
</script>

<template>
  <div class="mx-auto max-w-6xl space-y-8 p-6 laptop:p-8">
    <BaseButton variant="ghost" size="sm" class="print:hidden" @click="router.back()">← {{ t('report.back') }}</BaseButton>

    <ReportHeader :title="e('pageTitle')" :subtitle="e('pageSubtitle')" :period="periodLabel" :generated-date="generatedAt" :exportable="Boolean(report)" @download="exportCsv" />

    <ReportDateRange :state="rangeState" />

    <ErrorState v-if="error" :description="error" @retry="load" />
    <div v-else-if="!report" class="rounded-xl border border-border-light bg-bg-card p-5"><SkeletonLoader :rows="6" /></div>
    <EmptyState v-else-if="members.length === 0" :title="e('noData')" />

    <div v-else-if="totals" class="space-y-8 transition-opacity" :class="isLoading ? 'opacity-50' : ''">
      <p class="text-xs text-text-muted">{{ e('howRead') }}</p>
      <div class="grid grid-cols-2 gap-4 laptop:grid-cols-5">
        <ReportMetricCard :label="e('metricDue')" :value="count(totals.dueInPeriod)" :hint="e('metricDueHint', { count: totals.notYetDue })" color="primary" />
        <ReportMetricCard :label="e('metricOnTime')" :value="percent(totals.onTimeRate)" :hint="e('metricOnTimeHint', { count: totals.dueSoFar })" color="success" />
        <ReportMetricCard :label="e('metricDone')" :value="percent(totals.completionRate)" :hint="e('metricDoneHint', { late: totals.completedLate })" color="info" />
        <ReportMetricCard :label="e('metricOverdue')" :value="count(totals.overdueOpen)" :color="totals.overdueOpen > 0 ? 'danger' : 'neutral'" />
        <ReportMetricCard :label="e('metricThroughput')" :value="count(totals.completedInPeriod)" :hint="e('metricThroughputHint')" color="neutral" />
      </div>

      <ReportSection :title="e('chartTitle')" :description="e('chartDescription')" full-width>
        <Card>
          <BarChart :categories="members.map((m) => m.employeeName)" :series="outcomeSeries" horizontal stacked :category-label="e('columnEmployee')" show-total />
        </Card>
      </ReportSection>

      <SmartTable :columns="columns" :rows="members as Row[]" row-key="userId" :searchable="true" :search-placeholder="e('searchEmployee')" :empty-title="e('noData')">
        <template #cell-averageDaysLate="{ value }">{{ value ?? '—' }}</template>
        <template #cell-overdueOpen="{ value }">
          <span :class="(value as number) > 0 ? 'font-semibold text-danger-600' : ''">{{ value }}</span>
        </template>
        <template #cell-onTimeRate="{ value }">{{ percent(value as number | null) }}</template>
        <template #cell-completionRate="{ value }">{{ percent(value as number | null) }}</template>
      </SmartTable>
    </div>
  </div>
</template>
