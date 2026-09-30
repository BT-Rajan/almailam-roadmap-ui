<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import BarChart from '@/components/reports/BarChart.vue'
import ReportDateRange from '@/components/reports/ReportDateRange.vue'
import ReportHeader from '@/components/reports/ReportHeader.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import ReportSection from '@/components/reports/ReportSection.vue'
import { formatValue } from '@/components/reports/chartUtils'
import { useReportRange } from '@/composables/useReportRange'
import { reportService } from '@/services/reportService'
import type { ExecutiveSummary } from '@/types/Report'
import { downloadCsv } from '@/utils/csvExport'
import { formatDateTime } from '@/utils/dateFormatter'
import { formatRange } from '@/utils/reportRange'

const router = useRouter()
const { t } = useI18n()

const rangeState = useReportRange('this-month')
const periodLabel = computed(() => formatRange(rangeState.range.value))

const report = ref<ExecutiveSummary>()
const isLoading = ref(false)
const error = ref<string>()
const generatedAt = ref('')
let requestId = 0

async function loadReport(): Promise<void> {
  const current = ++requestId
  isLoading.value = true
  error.value = undefined
  try {
    const result = await reportService.getExecutiveSummary(rangeState.range.value)
    if (current !== requestId) return // a newer period was picked meanwhile
    report.value = result
    generatedAt.value = formatDateTime(new Date().toISOString())
  } catch {
    if (current === requestId) error.value = t('report.executivePage.loadFailed')
  } finally {
    if (current === requestId) isLoading.value = false
  }
}

watch(() => rangeState.range.value, loadReport, { immediate: true })

const currency = computed(() => report.value?.currency ?? '')
const kpis = computed(() => report.value?.kpis)
const bucketName = computed(() => {
  const bucket = report.value?.bucket ?? 'month'
  return t(`report.executivePage.bucket${bucket.charAt(0).toUpperCase()}${bucket.slice(1)}`)
})

function money(value: number): string {
  return formatValue(value, 'currency')
}
function moneyWithCurrency(value: number): string {
  return `${money(value)} ${currency.value}`
}
function count(value: number): string {
  return formatValue(value, 'number')
}
function percent(value: number | null | undefined): string {
  return value === null || value === undefined ? t('report.executivePage.notApplicable') : `${value}%`
}

const cashSeries = computed(() => [
  { name: t('report.executivePage.seriesReceived'), values: report.value?.cashFlow.received ?? [] },
  { name: t('report.executivePage.seriesBilled'), values: report.value?.cashFlow.billed ?? [] },
])
const projectSeries = computed(() => [
  { name: t('report.executivePage.seriesStarted'), values: report.value?.projectFlow.started ?? [] },
  { name: t('report.executivePage.seriesCompleted'), values: report.value?.projectFlow.completed ?? [] },
])
const statusPoints = computed(() => report.value?.projectStatusNow ?? [])

function exportCsv(): void {
  const data = report.value
  if (!data) return
  const k = data.kpis
  const e = (key: string) => t(`report.executivePage.${key}`)
  downloadCsv(`executive-summary-${data.period.startDate}-to-${data.period.endDate}.csv`, [
    {
      title: `${e('pageTitle')} -- ${periodLabel.value}`,
      headers: [e('period'), `${data.period.startDate} to ${data.period.endDate}`],
      rows: [
        [e('newProjects'), k.newProjects],
        [e('projectsCompleted'), k.projectsCompleted],
        [e('newClients'), k.newClients],
        [e('contractsSigned'), k.contractsSigned],
        [`${e('contractsSigned')} (${data.currency})`, k.contractsSignedValue],
        [e('activeNow'), k.activeProjectsNow],
        [`${e('cashReceived')} (${data.currency})`, k.cashReceived],
        [`Refunded (${data.currency})`, k.refunded],
        [`Net cash (${data.currency})`, k.netCash],
        [`${e('billed')} (${data.currency})`, k.billed],
        [`Collected of billed (${data.currency})`, k.collectedOfBilled],
        [`${e('collectionRate')} (%)`, k.collectionRate],
        [`${e('outstanding')} (${data.currency})`, k.outstandingNow],
        [`Overdue today (${data.currency})`, k.overdueNow],
        [e('tasksCompleted'), k.tasksCompleted],
        [`${e('tasksOnTime')} (%)`, k.tasksOnTimeRate],
        [e('openTasks'), k.openTasksNow],
        ['Overdue tasks today', k.overdueTasksNow],
      ],
    },
    {
      title: e('cashFlowTitle'),
      headers: [e('period'), `${e('seriesReceived')} (${data.currency})`, `${e('seriesBilled')} (${data.currency})`],
      rows: data.cashFlow.categories.map((label, i) => [label, data.cashFlow.received[i], data.cashFlow.billed[i]]),
    },
    {
      title: e('projectFlowTitle'),
      headers: [e('period'), e('seriesStarted'), e('seriesCompleted')],
      rows: data.projectFlow.categories.map((label, i) => [label, data.projectFlow.started[i], data.projectFlow.completed[i]]),
    },
    {
      title: e('projectStatusTitle'),
      headers: [e('columnStatus'), e('seriesProjects')],
      rows: data.projectStatusNow.map((row) => [row.label, row.value]),
    },
    {
      title: e('topClientsTitle'),
      headers: [e('columnClient'), `${e('columnReceived')} (${data.currency})`, e('columnPayments')],
      rows: data.topClients.map((row) => [row.clientName, row.received, row.payments]),
    },
  ])
}
</script>

<template>
  <div class="mx-auto max-w-6xl space-y-8 p-6 laptop:p-8">
    <BaseButton variant="ghost" size="sm" class="print:hidden" @click="router.back()">← {{ t('report.back') }}</BaseButton>

    <ReportHeader
      :title="t('report.executivePage.pageTitle')"
      :subtitle="t('report.executivePage.pageSubtitle')"
      :period="periodLabel"
      :generated-date="generatedAt"
      :exportable="Boolean(report)"
      @download="exportCsv"
    />

    <ReportDateRange :state="rangeState" />

    <ErrorState v-if="error" :description="error" @retry="loadReport" />

    <div v-else-if="!report" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="6" />
    </div>

    <!-- Held at reduced opacity while a new period loads: no layout jump. -->
    <div v-else-if="kpis" class="space-y-8 transition-opacity" :class="isLoading ? 'opacity-50' : ''">
      <ReportSection :title="t('report.executivePage.growthTitle')" :description="t('report.executivePage.growthDescription')" full-width>
        <div class="grid grid-cols-2 gap-4 laptop:grid-cols-5">
          <ReportMetricCard :label="t('report.executivePage.newProjects')" :value="count(kpis.newProjects)" :hint="t('report.executivePage.newProjectsHint')" color="primary" />
          <ReportMetricCard :label="t('report.executivePage.projectsCompleted')" :value="count(kpis.projectsCompleted)" :hint="t('report.executivePage.projectsCompletedHint')" color="success" />
          <ReportMetricCard :label="t('report.executivePage.newClients')" :value="count(kpis.newClients)" :hint="t('report.executivePage.newClientsHint')" color="primary" />
          <ReportMetricCard
            :label="t('report.executivePage.contractsSigned')"
            :value="count(kpis.contractsSigned)"
            :hint="t('report.executivePage.contractsSignedHint', { value: moneyWithCurrency(kpis.contractsSignedValue) })"
            color="info"
          />
          <ReportMetricCard
            :label="t('report.executivePage.activeNow')"
            :value="count(kpis.activeProjectsNow)"
            :hint="t('report.executivePage.activeNowHint', { count: kpis.onHoldProjectsNow })"
            color="neutral"
          />
        </div>
      </ReportSection>

      <ReportSection :title="t('report.executivePage.moneyTitle', { currency })" :description="t('report.executivePage.moneyDescription', { currency })" full-width>
        <div class="grid grid-cols-2 gap-4 laptop:grid-cols-4">
          <ReportMetricCard
            :label="t('report.executivePage.cashReceived')"
            :value="money(kpis.cashReceived)"
            :unit="currency"
            :hint="t('report.executivePage.cashReceivedHint', { refunded: money(kpis.refunded), net: money(kpis.netCash) })"
            color="success"
          />
          <ReportMetricCard :label="t('report.executivePage.billed')" :value="money(kpis.billed)" :unit="currency" :hint="t('report.executivePage.billedHint')" color="primary" />
          <ReportMetricCard
            :label="t('report.executivePage.collectionRate')"
            :value="percent(kpis.collectionRate)"
            :hint="t('report.executivePage.collectionRateHint', { collected: money(kpis.collectedOfBilled), billed: money(kpis.billed) })"
            color="info"
          />
          <ReportMetricCard
            :label="t('report.executivePage.outstanding')"
            :value="money(kpis.outstandingNow)"
            :unit="currency"
            :hint="t('report.executivePage.outstandingHint', { overdue: moneyWithCurrency(kpis.overdueNow) })"
            :color="kpis.overdueNow > 0 ? 'danger' : 'warning'"
          />
        </div>
        <Card class="mt-4">
          <h3 class="text-sm font-semibold text-text-primary">{{ t('report.executivePage.cashFlowTitle') }}</h3>
          <p class="mb-3 text-xs text-text-muted">{{ t('report.executivePage.cashFlowDescription', { bucket: bucketName, currency }) }}</p>
          <BarChart
            :categories="report.cashFlow.categories"
            :series="cashSeries"
            format="currency"
            :category-label="t('report.executivePage.period')"
            show-total
          />
        </Card>
      </ReportSection>

      <ReportSection :title="t('report.executivePage.deliveryTitle')" :description="t('report.executivePage.deliveryDescription')" full-width>
        <div class="grid grid-cols-2 gap-4 laptop:grid-cols-3">
          <ReportMetricCard :label="t('report.executivePage.tasksCompleted')" :value="count(kpis.tasksCompleted)" color="success" />
          <ReportMetricCard :label="t('report.executivePage.tasksOnTime')" :value="percent(kpis.tasksOnTimeRate)" :hint="t('report.executivePage.tasksOnTimeHint')" color="info" />
          <ReportMetricCard
            :label="t('report.executivePage.openTasks')"
            :value="count(kpis.openTasksNow)"
            :hint="t('report.executivePage.openTasksHint', { count: kpis.overdueTasksNow })"
            :color="kpis.overdueTasksNow > 0 ? 'danger' : 'neutral'"
          />
        </div>
        <div class="mt-4 grid grid-cols-1 gap-4 laptop:grid-cols-2">
          <Card>
            <h3 class="text-sm font-semibold text-text-primary">{{ t('report.executivePage.projectFlowTitle') }}</h3>
            <p class="mb-3 text-xs text-text-muted">{{ t('report.executivePage.projectFlowDescription', { bucket: bucketName }) }}</p>
            <BarChart :categories="report.projectFlow.categories" :series="projectSeries" :category-label="t('report.executivePage.period')" show-total />
          </Card>
          <Card>
            <h3 class="text-sm font-semibold text-text-primary">{{ t('report.executivePage.projectStatusTitle') }}</h3>
            <p class="mb-3 text-xs text-text-muted">{{ t('report.executivePage.projectStatusDescription') }}</p>
            <BarChart :data="statusPoints" horizontal :series-name="t('report.executivePage.seriesProjects')" :category-label="t('report.executivePage.columnStatus')" show-total />
          </Card>
        </div>
      </ReportSection>

      <ReportSection :title="t('report.executivePage.topClientsTitle')" :description="t('report.executivePage.topClientsDescription', { currency })" full-width>
        <Card>
          <p v-if="report.topClients.length === 0" class="py-6 text-center text-sm text-text-muted">{{ t('report.executivePage.noPayments') }}</p>
          <table v-else class="w-full text-sm">
            <thead>
              <tr class="border-b border-border-light text-left text-xs uppercase tracking-wide text-text-muted">
                <th class="py-2 pe-4 font-medium">{{ t('report.executivePage.columnClient') }}</th>
                <th class="py-2 ps-4 text-end font-medium">{{ t('report.executivePage.columnReceived') }} ({{ currency }})</th>
                <th class="py-2 ps-4 text-end font-medium">{{ t('report.executivePage.columnPayments') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in report.topClients" :key="row.clientName" class="border-b border-border-light/60 last:border-0">
                <td class="py-2 pe-4 text-text-primary">{{ row.clientName }}</td>
                <td class="py-2 ps-4 text-end tabular-nums text-text-primary">{{ money(row.received) }}</td>
                <td class="py-2 ps-4 text-end tabular-nums text-text-secondary">{{ row.payments }}</td>
              </tr>
            </tbody>
          </table>
        </Card>
      </ReportSection>
    </div>

    <div class="border-t border-border-light pt-6 text-center text-xs text-text-muted">
      <p v-if="generatedAt">{{ t('report.executivePage.footerGenerated', { date: generatedAt }) }}</p>
      <p class="mt-1">{{ t('report.executivePage.footerContact') }}</p>
    </div>
  </div>
</template>
