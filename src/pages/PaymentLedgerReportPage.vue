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
  const [projectsPage, clients] = await Promise.all([
    projectService.getProjectsPage({ pageSize: 200, sort: 'projectName' }),
    clientService.getClients(),
  ])
  projectOptions.value = [
    { label: t('report.paymentLedgerPage.allProjects'), value: '' },
    ...projectsPage.items.map((p) => ({ label: `${p.projectNo} — ${p.projectName}`, value: p.projectNo })),
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

const totalReceived = computed(() => ledger.value.reduce((sum, entry) => sum + entry.amount, 0))
const totalOutstanding = computed(
  () => projections.value?.byMonth.reduce((sum, entry) => sum + entry.amount, 0) ?? 0,
)

const byMonthChart = computed<ChartDataPoint[]>(
  () => projections.value?.byMonth.map((entry) => ({ label: entry.month, value: entry.amount, color: CHART_COLORS.blue })) ?? [],
)
const byServiceChart = computed<ChartDataPoint[]>(
  () => projections.value?.byService.map((entry) => ({ label: entry.service, value: entry.amount, color: CHART_COLORS.purple })) ?? [],
)

interface ProjectProjectionRow {
  [key: string]: unknown
  projectNo: string
  projectName: string
  amount: number
}
const byProjectRows = computed<ProjectProjectionRow[]>(() => (projections.value?.byProject ?? []).map((entry) => ({ ...entry })))
const byProjectColumns = computed<SmartTableColumn<ProjectProjectionRow>[]>(() => [
  { key: 'projectNo', label: t('report.paymentLedgerPage.columnProjectNo') },
  { key: 'projectName', label: t('report.paymentLedgerPage.columnProject') },
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
        <ReportMetricCard :label="t('report.paymentLedgerPage.metricReceived')" :value="formatCurrency(totalReceived)" color="success" />
        <ReportMetricCard :label="t('report.paymentLedgerPage.metricOutstanding')" :value="formatCurrency(totalOutstanding)" color="warning" />
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
          <Card>
            <template #header><h3 class="text-sm font-semibold text-text-primary">{{ t('report.paymentLedgerPage.byMonth') }}</h3></template>
            <BarChart v-if="byMonthChart.length > 0" :data="byMonthChart" :height="280" />
            <p v-else class="text-sm text-text-muted">{{ t('report.paymentLedgerPage.noProjections') }}</p>
          </Card>
          <Card>
            <template #header><h3 class="text-sm font-semibold text-text-primary">{{ t('report.paymentLedgerPage.byService') }}</h3></template>
            <BarChart v-if="byServiceChart.length > 0" :data="byServiceChart" :height="280" />
            <p v-else class="text-sm text-text-muted">{{ t('report.paymentLedgerPage.noProjections') }}</p>
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
            <template #cell-amount="{ value }">{{ formatCurrency(value as number) }}</template>
          </SmartTable>
        </Card>
      </ReportSection>
    </template>
  </div>
</template>
