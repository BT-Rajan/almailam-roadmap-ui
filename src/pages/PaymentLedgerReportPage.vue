<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import BarChart from '@/components/reports/BarChart.vue'
import ReportDateRange from '@/components/reports/ReportDateRange.vue'
import ReportHeader from '@/components/reports/ReportHeader.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import ReportProjectPicker from '@/components/reports/ReportProjectPicker.vue'
import ReportSection from '@/components/reports/ReportSection.vue'
import { formatValue } from '@/components/reports/chartUtils'
import { STATUS_CHART_COLORS } from '@/constants/chartColors'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useReportRange } from '@/composables/useReportRange'
import { reportService } from '@/services/reportService'
import type { PaymentLedgerEntry, PaymentProjections } from '@/types/Report'
import type { SmartTableColumn } from '@/types/Table'
import { downloadCsv } from '@/utils/csvExport'
import { formatDate, formatDateTime } from '@/utils/dateFormatter'
import { formatRange } from '@/utils/reportRange'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const l = (key: string, values?: Record<string, unknown>) => t(`report.paymentLedgerPage.${key}`, values ?? {})

// ---- Filters: period, project, client -- all kept in the URL -------------------
const rangeState = useReportRange('this-month')
const periodLabel = computed(() => formatRange(rangeState.range.value))
const projectNo = computed(() => (typeof route.query.project === 'string' ? route.query.project : ''))
const clientId = computed(() => (typeof route.query.client === 'string' ? route.query.client : ''))
function setFilter(key: 'project' | 'client', value: string): void {
  const query = { ...route.query }
  if (value) query[key] = value
  else delete query[key]
  void router.replace({ query })
}

// ---- Data -----------------------------------------------------------------------
const ledger = ref<PaymentLedgerEntry[]>([])
const projections = ref<PaymentProjections>()
const loaded = ref(false)
const isLoading = ref(false)
const loadError = ref('')
const generatedAt = ref('')
let requestId = 0

async function load(): Promise<void> {
  const current = ++requestId
  isLoading.value = true
  loadError.value = ''
  try {
    const filter = { projectNo: projectNo.value || undefined, clientId: clientId.value || undefined }
    const { from, to } = rangeState.range.value
    const [rows, outstanding] = await Promise.all([
      reportService.getPaymentLedger({ ...filter, startDate: from, endDate: to }),
      reportService.getPaymentProjections(filter),
    ])
    if (current !== requestId) return
    ledger.value = rows
    projections.value = outstanding
    loaded.value = true
    generatedAt.value = formatDateTime(new Date().toISOString())
  } catch (error) {
    if (current === requestId) loadError.value = error instanceof Error ? error.message : l('loadFailed')
  } finally {
    if (current === requestId) isLoading.value = false
  }
}

watch(() => [rangeState.range.value, projectNo.value, clientId.value] as const, load, { immediate: true })

const money = (value: number) => formatValue(value, 'currency')

// Every total is per currency: a ledger across all projects can genuinely
// hold more than one, and adding AED to USD would be meaningless.
interface CurrencySummary {
  currency: string
  received: number
  refunded: number
  payments: number
  refunds: number
  outstanding: number
  overdue: number
}
const summaries = computed<CurrencySummary[]>(() => {
  const byCurrency = new Map<string, CurrencySummary>()
  const get = (currency: string) => {
    let entry = byCurrency.get(currency)
    if (!entry) {
      entry = { currency, received: 0, refunded: 0, payments: 0, refunds: 0, outstanding: 0, overdue: 0 }
      byCurrency.set(currency, entry)
    }
    return entry
  }
  for (const row of ledger.value) {
    const entry = get(row.currency)
    if (row.entryType === 'Refund') {
      entry.refunded += -row.amount
      entry.refunds += 1
    } else {
      entry.received += row.amount
      entry.payments += 1
    }
  }
  for (const month of projections.value?.byMonth ?? []) {
    const entry = get(month.currency)
    entry.outstanding += month.amount
    entry.overdue += month.overdue
  }
  return [...byCurrency.values()].sort((a, b) => a.currency.localeCompare(b.currency))
})

// ---- Ledger table -----------------------------------------------------------------
type LedgerRow = PaymentLedgerEntry & Record<string, unknown>
const ledgerColumns = computed<SmartTableColumn<LedgerRow>[]>(() => [
  { key: 'date', label: l('columnDate'), sortable: true },
  { key: 'entryType', label: l('columnType') },
  { key: 'paymentNo', label: l('columnPaymentNo') },
  { key: 'projectName', label: l('columnProject'), sortable: true },
  { key: 'clientName', label: l('columnClient'), sortable: true },
  { key: 'service', label: l('columnService') },
  { key: 'amount', label: l('columnAmount'), align: 'right', sortable: true },
  { key: 'mode', label: l('columnMode') },
  { key: 'reference', label: l('columnReference') },
])

// Payments per mode and currency, for bank reconciliation.
const byMode = computed(() => {
  const totals = new Map<string, { mode: string; currency: string; count: number; amount: number }>()
  for (const row of ledger.value) {
    const key = `${row.mode}|${row.currency}`
    const entry = totals.get(key) ?? { mode: row.mode, currency: row.currency, count: 0, amount: 0 }
    entry.count += 1
    entry.amount += row.amount
    totals.set(key, entry)
  }
  return [...totals.values()].sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount))
})

// ---- Still to come in ---------------------------------------------------------------
const projectionCurrencies = computed(() => [...new Set((projections.value?.byMonth ?? []).map((m) => m.currency))].sort())
function monthLabel(month: string): string {
  return new Date(`${month}-01T00:00:00Z`).toLocaleDateString('en-GB', { month: 'short', year: 'numeric', timeZone: 'UTC' })
}
function monthChart(currency: string) {
  const months = (projections.value?.byMonth ?? []).filter((m) => m.currency === currency)
  return {
    categories: months.map((m) => monthLabel(m.month)),
    series: [
      { name: l('seriesOverdue'), values: months.map((m) => m.overdue), color: STATUS_CHART_COLORS.danger },
      { name: l('seriesUpcoming'), values: months.map((m) => Math.max(m.amount - m.overdue, 0)), color: 'var(--chart-series-1)' },
    ],
  }
}
function serviceChart(currency: string) {
  return (projections.value?.byService ?? []).filter((s) => s.currency === currency).map((s) => ({ label: s.service, value: s.amount }))
}
const byProject = computed(() => [...(projections.value?.byProject ?? [])].sort((a, b) => b.amount - a.amount))

function openProject(project: string): void {
  void router.push({ name: ROUTE_NAMES.REPORT_PROJECT, params: { projectId: project }, query: rangeState.urlQuery() })
}

function exportCsv(): void {
  const { from, to } = rangeState.range.value
  downloadCsv(`payment-ledger-${from}-to-${to}.csv`, [
    {
      title: `${l('pageTitle')} -- ${periodLabel.value}`,
      headers: [l('columnDate'), l('columnType'), l('columnPaymentNo'), l('columnProjectNo'), l('columnProject'), l('columnClient'), l('columnService'), l('columnAmount'), l('columnCurrency'), l('columnMode'), l('columnReference'), l('columnPayer')],
      rows: ledger.value.map((r) => [r.date, r.entryType, r.paymentNo, r.projectNo, r.projectName, r.clientName, r.service, r.amount, r.currency, r.mode, r.reference ?? '', r.payer]),
    },
    {
      title: l('byModeTitle'),
      headers: [l('columnMode'), l('columnCurrency'), l('columnCount'), l('columnAmount')],
      rows: byMode.value.map((r) => [r.mode, r.currency, r.count, r.amount]),
    },
    {
      title: `${l('projectionsTitle')} -- ${l('byMonth')}`,
      headers: ['Month', l('columnCurrency'), l('columnOutstanding'), l('columnOverdue')],
      rows: (projections.value?.byMonth ?? []).map((m) => [m.month, m.currency, m.amount, m.overdue]),
    },
    {
      title: `${l('projectionsTitle')} -- ${l('byProject')}`,
      headers: [l('columnProjectNo'), l('columnProject'), l('columnCurrency'), l('columnOutstanding')],
      rows: byProject.value.map((p) => [p.projectNo, p.projectName, p.currency, p.amount]),
    },
  ])
}
</script>

<template>
  <div class="mx-auto max-w-6xl space-y-8 p-6 laptop:p-8">
    <BaseButton variant="ghost" size="sm" class="print:hidden" @click="router.back()">← {{ t('report.back') }}</BaseButton>

    <ReportHeader :title="l('pageTitle')" :subtitle="l('pageSubtitle')" :period="periodLabel" :generated-date="generatedAt" :exportable="loaded" @download="exportCsv" />

    <div class="flex flex-wrap items-end gap-4">
      <ReportProjectPicker :model-value="projectNo" clearable @update:model-value="(value) => setFilter('project', value)" />
      <ReportProjectPicker kind="client" :model-value="clientId" clearable @update:model-value="(value) => setFilter('client', value)" />
      <ReportDateRange :state="rangeState" />
    </div>

    <ErrorState v-if="loadError" :description="loadError" @retry="load" />

    <div v-else-if="!loaded" class="rounded-xl border border-border-light bg-bg-card p-5"><SkeletonLoader :rows="6" /></div>

    <div v-else class="space-y-8 transition-opacity" :class="isLoading ? 'opacity-50' : ''">
      <div v-for="summary in summaries" :key="summary.currency" class="grid grid-cols-2 gap-4 laptop:grid-cols-4">
        <ReportMetricCard
          :label="`${l('metricReceived')} (${summary.currency})`"
          :value="money(summary.received)"
          :hint="l('metricPaymentsHint', { count: summary.payments })"
          color="success"
        />
        <ReportMetricCard :label="`${l('metricRefunded')} (${summary.currency})`" :value="money(summary.refunded)" :hint="l('metricRefundsHint', { count: summary.refunds })" :color="summary.refunded ? 'warning' : 'neutral'" />
        <ReportMetricCard :label="`${l('metricNet')} (${summary.currency})`" :value="money(summary.received - summary.refunded)" color="primary" />
        <ReportMetricCard
          :label="`${l('metricOutstanding')} (${summary.currency})`"
          :value="money(summary.outstanding)"
          :hint="l('metricOutstandingHint', { overdue: money(summary.overdue) })"
          :color="summary.overdue > 0 ? 'danger' : 'warning'"
        />
      </div>

      <ReportSection :title="l('ledgerTitle')" :description="l('ledgerDescription')" full-width>
        <SmartTable
          :columns="ledgerColumns"
          :rows="ledger as LedgerRow[]"
          row-key="paymentNo"
          :searchable="true"
          :search-placeholder="l('searchLedger')"
          :empty-title="l('noPayments')"
        >
          <template #cell-date="{ value }"><span class="whitespace-nowrap">{{ formatDate(value as string) }}</span></template>
          <template #cell-entryType="{ value }">
            <StatusBadge :label="value === 'Refund' ? l('typeRefund') : l('typePayment')" :variant="value === 'Refund' ? 'warning' : 'success'" size="sm" />
          </template>
          <template #cell-projectName="{ row }">
            <button type="button" class="text-start text-accent-600 hover:underline" @click.stop="openProject((row as LedgerRow).projectNo)">
              {{ (row as LedgerRow).projectName }}
            </button>
          </template>
          <template #cell-amount="{ row }">
            <span class="whitespace-nowrap tabular-nums" :class="(row as LedgerRow).amount < 0 ? 'text-warning-700 dark:text-warning-400' : ''">
              {{ money((row as LedgerRow).amount) }} <span class="text-xs text-text-muted">{{ (row as LedgerRow).currency }}</span>
            </span>
          </template>
          <template #cell-reference="{ value }">{{ value || '—' }}</template>
        </SmartTable>
      </ReportSection>

      <ReportSection v-if="byMode.length" :title="l('byModeTitle')" :description="l('byModeDescription')" full-width>
        <Card>
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-border-light text-left text-xs uppercase tracking-wide text-text-muted">
                <th class="py-2 pe-3 font-medium">{{ l('columnMode') }}</th>
                <th class="py-2 ps-3 text-end font-medium">{{ l('columnCount') }}</th>
                <th class="py-2 ps-3 text-end font-medium">{{ l('columnAmount') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in byMode" :key="`${row.mode}-${row.currency}`" class="border-b border-border-light/60 last:border-0">
                <td class="py-2 pe-3 text-text-primary">{{ row.mode }}</td>
                <td class="py-2 ps-3 text-end tabular-nums">{{ row.count }}</td>
                <td class="py-2 ps-3 text-end tabular-nums">{{ money(row.amount) }} <span class="text-xs text-text-muted">{{ row.currency }}</span></td>
              </tr>
            </tbody>
          </table>
        </Card>
      </ReportSection>

      <ReportSection :title="l('projectionsTitle')" :description="l('projectionsDescription')" full-width>
        <Card v-if="projectionCurrencies.length === 0"><p class="py-6 text-center text-sm text-text-muted">{{ l('noProjections') }}</p></Card>
        <div v-for="currency in projectionCurrencies" :key="currency" class="grid grid-cols-1 gap-4 laptop:grid-cols-3">
          <Card class="laptop:col-span-2">
            <h3 class="text-sm font-semibold text-text-primary">{{ l('byMonth') }} ({{ currency }})</h3>
            <p class="mb-3 text-xs text-text-muted">{{ l('byMonthDescription') }}</p>
            <BarChart v-bind="monthChart(currency)" stacked format="currency" :category-label="l('byMonth')" show-total />
          </Card>
          <Card>
            <h3 class="mb-3 text-sm font-semibold text-text-primary">{{ l('byService') }} ({{ currency }})</h3>
            <BarChart :data="serviceChart(currency)" horizontal format="currency" :series-name="l('columnOutstanding')" show-total />
          </Card>
        </div>
        <Card v-if="byProject.length" class="mt-4">
          <h3 class="mb-3 text-sm font-semibold text-text-primary">{{ l('byProject') }}</h3>
          <div class="max-h-96 overflow-y-auto">
            <table class="w-full text-sm">
              <thead class="sticky top-0 bg-bg-card">
                <tr class="border-b border-border-light text-left text-xs uppercase tracking-wide text-text-muted">
                  <th class="py-2 pe-3 font-medium">{{ l('columnProject') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ l('columnOutstanding') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in byProject" :key="`${row.projectNo}-${row.currency}`" class="border-b border-border-light/60 last:border-0">
                  <td class="py-2 pe-3">
                    <button type="button" class="text-start text-accent-600 hover:underline" @click="openProject(row.projectNo)">{{ row.projectNo }} · {{ row.projectName }}</button>
                  </td>
                  <td class="py-2 ps-3 text-end tabular-nums">{{ money(row.amount) }} <span class="text-xs text-text-muted">{{ row.currency }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
      </ReportSection>
    </div>
  </div>
</template>
