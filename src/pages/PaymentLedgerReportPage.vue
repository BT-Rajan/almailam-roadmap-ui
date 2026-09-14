<script setup lang="ts">
import { Download } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BarChart from '@/components/reports/BarChart.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import ReportSection from '@/components/reports/ReportSection.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import { CHART_COLORS } from '@/constants/chartColors'
import { clientService } from '@/services/clientService'
import { projectService } from '@/services/projectService'
import { reportService } from '@/services/reportService'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import { triggerBlobDownload } from '@/utils/fileDownload'
import type { PaymentLedgerEntry, PaymentProjections } from '@/types/Report'
import type { ChartDataPoint } from '@/types/Report'
import type { SmartTableColumn } from '@/types/Table'
import type { SelectOption } from '@/types/Ui'

const { t } = useI18n()

// --- Filters -----------------------------------------------------------

const projectOptions = ref<SelectOption[]>([])
const clientOptions = ref<SelectOption[]>([])
const selectedProjectNo = ref('')
const selectedClientId = ref('')
const startDate = ref('')
const endDate = ref('')

onMounted(async () => {
  // getProjects() walks every page rather than a single capped request --
  // see the identical fix in ProjectTreeReportPage.vue/taskService.ts:
  // getProjectsPage's own pageSize is bounded by the server's
  // MAX_PAGE_SIZE (200), so a company with more projects on record than
  // that would have the rest silently missing from this filter.
  const [projects, clients] = await Promise.all([projectService.getProjects(), clientService.getClients()])
  projects.sort((a, b) => a.projectName.localeCompare(b.projectName))
  projectOptions.value = [
    { label: t('report.paymentLedgerPage.allProjects'), value: '' },
    ...projects.map((p) => ({ label: `${p.projectNo} — ${p.projectName}`, value: p.projectNo })),
  ]
  clientOptions.value = [
    { label: t('report.paymentLedgerPage.allClients'), value: '' },
    ...clients.map((c) => ({ label: c.companyName ?? c.id, value: c.id })),
  ]
  await load()
})

// --- Data ----------------------------------------------------------------

const ledger = ref<PaymentLedgerEntry[]>([])
const projections = ref<PaymentProjections>()
const isLoading = ref(false)
const loadError = ref('')

async function load(): Promise<void> {
  isLoading.value = true
  loadError.value = ''
  try {
    const filter = {
      projectNo: selectedProjectNo.value || undefined,
      clientId: selectedClientId.value || undefined,
    }
    const [ledgerRows, projectionData] = await Promise.all([
      reportService.getPaymentLedger({ ...filter, startDate: startDate.value || undefined, endDate: endDate.value || undefined }),
      reportService.getPaymentProjections(filter),
    ])
    ledger.value = ledgerRows
    projections.value = projectionData
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : t('report.paymentLedgerPage.loadFailed')
    ledger.value = []
    projections.value = undefined
  } finally {
    isLoading.value = false
  }
}

watch([selectedProjectNo, selectedClientId, startDate, endDate], load)

// --- Ledger table ----------------------------------------------------------

type LedgerRow = PaymentLedgerEntry & Record<string, unknown>

const ledgerColumns = computed<SmartTableColumn<LedgerRow>[]>(() => [
  { key: 'date', label: t('report.paymentLedgerPage.columnDate'), sortable: true },
  { key: 'paymentNo', label: t('report.paymentLedgerPage.columnPaymentNo') },
  { key: 'projectName', label: t('report.paymentLedgerPage.columnProject') },
  { key: 'clientName', label: t('report.paymentLedgerPage.columnClient') },
  { key: 'service', label: t('report.paymentLedgerPage.columnService') },
  { key: 'amount', label: t('report.paymentLedgerPage.columnAmount'), align: 'right', sortable: true },
  { key: 'mode', label: t('report.paymentLedgerPage.columnMode') },
  { key: 'reference', label: t('report.paymentLedgerPage.columnReference') },
  { key: 'payer', label: t('report.paymentLedgerPage.columnPayer') },
])

// Every aggregate below is split by currency instead of summed across
// all of them -- a payment ledger spanning "All Projects"/"All Clients"
// can genuinely include more than one currency (AED/USD/SAR/KWD, see
// AdminCompanyPage; even a single project's Design and Supervision
// agreements can differ), and the per-row ledger table already shows
// each entry's real currency correctly -- only the aggregate views used
// to silently add incompatible amounts together.
interface CurrencyTotal {
  currency: string
  amount: number
}

function groupByCurrency(entries: { currency: string; amount: number }[]): CurrencyTotal[] {
  const totals = new Map<string, number>()
  for (const entry of entries) totals.set(entry.currency, (totals.get(entry.currency) ?? 0) + entry.amount)
  return [...totals.entries()].map(([currency, amount]) => ({ currency, amount })).sort((a, b) => a.currency.localeCompare(b.currency))
}

const receivedByCurrency = computed<CurrencyTotal[]>(() => groupByCurrency(ledger.value))
const outstandingByCurrency = computed<CurrencyTotal[]>(() => groupByCurrency(projections.value?.byMonth ?? []))

interface CurrencyChartGroup {
  currency: string
  data: ChartDataPoint[]
}

function chartGroupsByCurrency<T extends { currency: string; amount: number }>(
  entries: T[],
  labelKey: keyof T,
  color: string,
): CurrencyChartGroup[] {
  const currencies = [...new Set(entries.map((entry) => entry.currency))].sort()
  return currencies.map((currency) => ({
    currency,
    data: entries
      .filter((entry) => entry.currency === currency)
      .map((entry) => ({ label: String(entry[labelKey]), value: entry.amount, color })),
  }))
}

const byMonthGroups = computed<CurrencyChartGroup[]>(() =>
  chartGroupsByCurrency(projections.value?.byMonth ?? [], 'month', CHART_COLORS.blue),
)
const byServiceGroups = computed<CurrencyChartGroup[]>(() =>
  chartGroupsByCurrency(projections.value?.byService ?? [], 'service', CHART_COLORS.purple),
)

interface ProjectProjectionRow {
  [key: string]: unknown
  projectNo: string
  projectName: string
  currency: string
  amount: number
}
const byProjectRows = computed<ProjectProjectionRow[]>(() => (projections.value?.byProject ?? []).map((entry) => ({ ...entry })))
const byProjectColumns = computed<SmartTableColumn<ProjectProjectionRow>[]>(() => [
  { key: 'projectNo', label: t('report.paymentLedgerPage.columnProjectNo') },
  { key: 'projectName', label: t('report.paymentLedgerPage.columnProject') },
  { key: 'currency', label: t('report.paymentLedgerPage.columnCurrency') },
  { key: 'amount', label: t('report.paymentLedgerPage.columnOutstanding'), align: 'right', sortable: true },
])

function exportCsv(): void {
  const header = ['Date', 'Payment No', 'Project', 'Client', 'Service', 'Amount', 'Currency', 'Mode', 'Reference', 'Payer']
  const escape = (value: string) => `"${value.replace(/"/g, '""')}"`
  const lines = [header.join(',')]
  for (const entry of ledger.value) {
    lines.push(
      [
        entry.date,
        entry.paymentNo,
        entry.projectName,
        entry.clientName,
        entry.service,
        String(entry.amount),
        entry.currency,
        entry.mode,
        entry.reference ?? '',
        entry.payer,
      ]
        .map(escape)
        .join(','),
    )
  }
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  triggerBlobDownload(blob, `payment-ledger-${new Date().toISOString().slice(0, 10)}.csv`)
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader :title="t('report.paymentLedgerPage.pageTitle')" :subtitle="t('report.paymentLedgerPage.pageSubtitle')">
      <template #actions>
        <BaseButton :icon="Download" variant="secondary" @click="exportCsv">{{ t('report.paymentLedgerPage.exportCsv') }}</BaseButton>
      </template>
    </PageHeader>

    <Card>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <SelectBox v-model="selectedProjectNo" :label="t('report.paymentLedgerPage.project')" :options="projectOptions" />
        <SelectBox v-model="selectedClientId" :label="t('report.paymentLedgerPage.client')" :options="clientOptions" />
        <DatePicker v-model="startDate" :label="t('report.paymentLedgerPage.from')" :max="endDate || undefined" />
        <DatePicker v-model="endDate" :label="t('report.paymentLedgerPage.to')" :min="startDate || undefined" />
      </div>
    </Card>

    <ErrorState v-if="loadError" :description="loadError" @retry="load" />

    <template v-else>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <ReportMetricCard
          v-for="entry in receivedByCurrency"
          :key="`received-${entry.currency}`"
          :label="receivedByCurrency.length > 1 ? `${t('report.paymentLedgerPage.metricReceived')} (${entry.currency})` : t('report.paymentLedgerPage.metricReceived')"
          :value="formatCurrency(entry.amount, entry.currency)"
          color="success"
        />
        <ReportMetricCard
          v-for="entry in outstandingByCurrency"
          :key="`outstanding-${entry.currency}`"
          :label="outstandingByCurrency.length > 1 ? `${t('report.paymentLedgerPage.metricOutstanding')} (${entry.currency})` : t('report.paymentLedgerPage.metricOutstanding')"
          :value="formatCurrency(entry.amount, entry.currency)"
          color="warning"
        />
        <ReportMetricCard :label="t('report.paymentLedgerPage.metricCount')" :value="ledger.length" color="primary" />
      </div>

      <ReportSection :title="t('report.paymentLedgerPage.ledgerTitle')" :description="t('report.paymentLedgerPage.ledgerDescription')" full-width>
        <SmartTable
          :columns="ledgerColumns"
          :rows="ledger as LedgerRow[]"
          row-key="paymentNo"
          :loading="isLoading"
          :searchable="true"
          :search-placeholder="t('report.paymentLedgerPage.searchLedger')"
          :empty-title="t('report.paymentLedgerPage.noPayments')"
        >
          <template #cell-date="{ value }">{{ formatDate(value as string) }}</template>
          <template #cell-amount="{ row }">{{ formatCurrency(row.amount, row.currency) }}</template>
          <template #cell-reference="{ value }">{{ value || '—' }}</template>
        </SmartTable>
      </ReportSection>

      <ReportSection :title="t('report.paymentLedgerPage.projectionsTitle')" :description="t('report.paymentLedgerPage.projectionsDescription')" full-width>
        <div class="grid grid-cols-1 gap-4 laptop:grid-cols-2">
          <Card v-for="group in byMonthGroups" :key="`month-${group.currency}`">
            <template #header>
              <h3 class="text-sm font-semibold text-text-primary">
                {{ byMonthGroups.length > 1 ? `${t('report.paymentLedgerPage.byMonth')} (${group.currency})` : t('report.paymentLedgerPage.byMonth') }}
              </h3>
            </template>
            <BarChart :data="group.data" :height="280" />
          </Card>
          <Card v-if="byMonthGroups.length === 0">
            <template #header><h3 class="text-sm font-semibold text-text-primary">{{ t('report.paymentLedgerPage.byMonth') }}</h3></template>
            <p class="text-sm text-text-muted">{{ t('report.paymentLedgerPage.noProjections') }}</p>
          </Card>
          <Card v-for="group in byServiceGroups" :key="`service-${group.currency}`">
            <template #header>
              <h3 class="text-sm font-semibold text-text-primary">
                {{ byServiceGroups.length > 1 ? `${t('report.paymentLedgerPage.byService')} (${group.currency})` : t('report.paymentLedgerPage.byService') }}
              </h3>
            </template>
            <BarChart :data="group.data" :height="280" />
          </Card>
          <Card v-if="byServiceGroups.length === 0">
            <template #header><h3 class="text-sm font-semibold text-text-primary">{{ t('report.paymentLedgerPage.byService') }}</h3></template>
            <p class="text-sm text-text-muted">{{ t('report.paymentLedgerPage.noProjections') }}</p>
          </Card>
        </div>
        <Card class="mt-4">
          <template #header><h3 class="text-sm font-semibold text-text-primary">{{ t('report.paymentLedgerPage.byProject') }}</h3></template>
          <SmartTable
            :columns="byProjectColumns"
            :rows="byProjectRows"
            row-key="projectNo"
            :searchable="false"
            :empty-title="t('report.paymentLedgerPage.noProjections')"
          >
            <template #cell-amount="{ row }">{{ formatCurrency(row.amount, row.currency) }}</template>
          </SmartTable>
        </Card>
      </ReportSection>
    </template>
  </div>
</template>
