<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import Card from '@/components/common/Card.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import BarChart from '@/components/reports/BarChart.vue'
import ReportDateRange from '@/components/reports/ReportDateRange.vue'
import ReportHeader from '@/components/reports/ReportHeader.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import ReportSection from '@/components/reports/ReportSection.vue'
import { formatValue } from '@/components/reports/chartUtils'
import { STATUS_CHART_COLORS } from '@/constants/chartColors'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useReportRange } from '@/composables/useReportRange'
import { reportService } from '@/services/reportService'
import type { ProjectStatus, WorkflowStage } from '@/types/Project'
import type { ClientPortfolio, ClientPortfolioProject, ClientPortfolioRow } from '@/types/Report'
import type { SmartTableColumn } from '@/types/Table'
import { downloadCsv } from '@/utils/csvExport'
import { formatDateTime } from '@/utils/dateFormatter'
import { getProjectStatusVariant, getWorkflowStageLabel } from '@/utils/projectHelpers'
import { useEnumLabel } from '@/utils/reportLabels'
import { formatRange } from '@/utils/reportRange'

const router = useRouter()
const { t } = useI18n()
const enumLabel = useEnumLabel()
const c = (key: string, values?: Record<string, unknown>) => t(`report.clientProjectsPage.${key}`, values ?? {})

const rangeState = useReportRange('this-year')
const periodLabel = computed(() => formatRange(rangeState.range.value))

const report = ref<ClientPortfolio>()
const isLoading = ref(false)
const error = ref<string>()
const generatedAt = ref('')
let requestId = 0

async function load(): Promise<void> {
  const current = ++requestId
  isLoading.value = true
  error.value = undefined
  try {
    const result = await reportService.getClientPortfolio(rangeState.range.value)
    if (current !== requestId) return
    report.value = result
    generatedAt.value = formatDateTime(new Date().toISOString())
  } catch (loadError) {
    if (current === requestId) error.value = loadError instanceof Error ? loadError.message : c('loadFailed')
  } finally {
    if (current === requestId) isLoading.value = false
  }
}

watch(() => rangeState.range.value, load, { immediate: true })

const currency = computed(() => report.value?.currency ?? '')
const money = (value: number) => formatValue(value, 'currency')
const totals = computed(() => report.value?.totals)

type ClientRow = ClientPortfolioRow & Record<string, unknown>
const rows = computed<ClientRow[]>(() => (report.value?.clients ?? []) as ClientRow[])

const clientColumns = computed<SmartTableColumn<ClientRow>[]>(() => [
  { key: 'clientName', label: c('columnClient'), sortable: true },
  { key: 'clientStatus', label: c('columnClientStatus') },
  { key: 'totalProjects', label: c('columnTotalProjects'), align: 'right', sortable: true },
  { key: 'activeProjects', label: c('columnActive'), align: 'right', sortable: true },
  { key: 'onHoldProjects', label: c('columnOnHold'), align: 'right', sortable: true },
  { key: 'completedProjects', label: c('columnCompleted'), align: 'right', sortable: true },
  { key: 'newProjectsInPeriod', label: c('columnNew'), align: 'right', sortable: true },
  { key: 'receivedInPeriod', label: `${c('columnReceived')} (${currency.value})`, align: 'right', sortable: true },
  { key: 'outstanding', label: `${c('columnOutstanding')} (${currency.value})`, align: 'right', sortable: true },
  { key: 'overdue', label: `${c('columnOverdue')} (${currency.value})`, align: 'right', sortable: true },
])

// The ten biggest balances, split overdue / not yet due (urgency colours).
const topOwed = computed(() => [...rows.value].filter((row) => row.outstanding > 0).sort((a, b) => b.outstanding - a.outstanding).slice(0, 10))
const owedSeries = computed(() => [
  { name: c('seriesOverdue'), values: topOwed.value.map((row) => row.overdue), color: STATUS_CHART_COLORS.danger },
  { name: c('seriesNotYetDue'), values: topOwed.value.map((row) => Math.max(row.outstanding - row.overdue, 0)), color: 'var(--chart-series-1)' },
])

// ---- Drill-down --------------------------------------------------------------
type ProjectRow = ClientPortfolioProject & Record<string, unknown>
const projectColumns = computed<SmartTableColumn<ProjectRow>[]>(() => [
  { key: 'projectName', label: c('columnProjectName'), sortable: true },
  { key: 'status', label: c('columnProjectStatus') },
  { key: 'currentStage', label: c('columnStage') },
  { key: 'progress', label: c('columnProgress'), align: 'right', sortable: true },
  { key: 'receivedInPeriod', label: c('columnReceived'), align: 'right', sortable: true },
  { key: 'outstanding', label: c('columnOutstanding'), align: 'right', sortable: true },
  { key: 'overdue', label: c('columnOverdue'), align: 'right', sortable: true },
])
const drawerClient = ref<ClientPortfolioRow>()
const drawerOpen = ref(false)
function openClient(row: ClientRow): void {
  drawerClient.value = row
  drawerOpen.value = true
}
function openProjectReport(projectNo: string): void {
  void router.push({ name: ROUTE_NAMES.REPORT_PROJECT, params: { projectId: projectNo }, query: { ...rangeState.urlQuery() } })
}

function exportCsv(): void {
  const data = report.value
  if (!data) return
  const money3 = `(${data.currency})`
  downloadCsv(`client-projects-${data.period.startDate}-to-${data.period.endDate}.csv`, [
    {
      title: `${c('pageTitle')} -- ${periodLabel.value}`,
      headers: [
        c('columnClient'), c('columnClientStatus'), c('columnTotalProjects'), c('columnActive'), c('columnOnHold'), c('columnCompleted'),
        c('columnCancelled'), c('columnNew'), `${c('columnReceived')} ${money3}`, `${c('columnOutstanding')} ${money3}`, `${c('columnOverdue')} ${money3}`,
      ],
      rows: data.clients.map((r) => [
        r.clientName, r.clientStatus, r.totalProjects, r.activeProjects, r.onHoldProjects, r.completedProjects, r.cancelledProjects,
        r.newProjectsInPeriod, r.receivedInPeriod, r.outstanding, r.overdue,
      ]),
    },
    {
      title: c('columnProjectName'),
      headers: [
        c('columnClient'), c('columnProjectNo'), c('columnProjectName'), c('columnProjectStatus'), c('columnStage'), `${c('columnProgress')} (%)`,
        c('columnNew'), `${c('columnReceived')} ${money3}`, `${c('columnOutstanding')} ${money3}`, `${c('columnOverdue')} ${money3}`,
      ],
      rows: data.clients.flatMap((r) =>
        r.projects.map((p) => [r.clientName, p.projectNo, p.projectName, p.status, p.currentStage, p.progress, p.newInPeriod ? 'Yes' : 'No', p.receivedInPeriod, p.outstanding, p.overdue]),
      ),
    },
  ])
}
</script>

<template>
  <div class="mx-auto max-w-6xl space-y-8 p-6 laptop:p-8">
    <BaseButton variant="ghost" size="sm" class="print:hidden" @click="router.back()">← {{ t('report.back') }}</BaseButton>

    <ReportHeader
      :title="c('pageTitle')"
      :subtitle="c('pageSubtitle')"
      :period="periodLabel"
      :generated-date="generatedAt"
      :exportable="Boolean(report)"
      @download="exportCsv"
    />

    <ReportDateRange :state="rangeState" />

    <ErrorState v-if="error" :description="error" @retry="load" />

    <div v-else-if="!report" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="6" />
    </div>

    <div v-else-if="totals" class="space-y-8 transition-opacity" :class="isLoading ? 'opacity-50' : ''">
      <p class="text-xs text-text-muted">{{ c('moneyNote', { currency }) }}</p>
      <div class="grid grid-cols-2 gap-4 laptop:grid-cols-5">
        <ReportMetricCard
          :label="c('metricClients')"
          :value="totals.clients"
          :hint="c('metricClientsHint', { active: totals.clientsWithActiveWork, none: totals.clientsWithoutProjects })"
          color="primary"
        />
        <ReportMetricCard :label="c('metricNewClients')" :value="totals.newClients" color="info" />
        <ReportMetricCard :label="c('metricProjects')" :value="formatValue(totals.projects, 'number')" :hint="c('metricProjectsHint', { count: totals.newProjects })" color="info" />
        <ReportMetricCard :label="c('metricReceived')" :value="money(totals.receivedInPeriod)" :unit="currency" color="success" />
        <ReportMetricCard
          :label="c('metricOutstanding')"
          :value="money(totals.outstanding)"
          :unit="currency"
          :hint="c('metricOutstandingHint', { overdue: `${money(totals.overdue)} ${currency}`, clients: totals.clientsWithOverdue })"
          :color="totals.overdue > 0 ? 'danger' : 'warning'"
        />
      </div>

      <ReportSection v-if="topOwed.length" :title="c('owedTitle')" :description="c('owedDescription')" full-width>
        <Card>
          <BarChart :categories="topOwed.map((row) => row.clientName)" :series="owedSeries" horizontal stacked format="currency" :category-label="c('columnClient')" show-total />
        </Card>
      </ReportSection>

      <ReportSection :title="c('metricClients')" :description="c('openHint')" full-width>
        <SmartTable
          :columns="clientColumns"
          :rows="rows"
          row-key="clientId"
          :searchable="true"
          :search-placeholder="c('searchClient')"
          :empty-title="c('noClients')"
          @row-click="openClient"
        >
          <template #cell-clientName="{ row }">
            <span class="font-medium text-accent-600">{{ (row as ClientRow).clientName }}</span>
            <StatusBadge v-if="(row as ClientRow).newClient" :label="c('newBadge')" variant="info" size="sm" class="ms-2" />
          </template>
          <template #cell-clientStatus="{ value }">
            <StatusBadge :label="value as string" :variant="value === 'Active' ? 'success' : value === 'On Hold' ? 'warning' : 'neutral'" />
          </template>
          <template #cell-receivedInPeriod="{ value }"><span class="tabular-nums">{{ money(value as number) }}</span></template>
          <template #cell-outstanding="{ value }"><span class="tabular-nums">{{ money(value as number) }}</span></template>
          <template #cell-overdue="{ value }">
            <span class="tabular-nums" :class="(value as number) > 0 ? 'font-semibold text-danger-600' : ''">{{ money(value as number) }}</span>
          </template>
        </SmartTable>
      </ReportSection>
    </div>

    <BaseDrawer v-model="drawerOpen" :title="drawerClient?.clientName ?? ''" width="lg">
      <SmartTable
        v-if="drawerClient"
        :columns="projectColumns"
        :rows="drawerClient.projects as ProjectRow[]"
        row-key="projectNo"
        :searchable="false"
        :empty-title="c('noProjectsForClient')"
        @row-click="(row) => openProjectReport((row as ProjectRow).projectNo)"
      >
        <template #cell-projectName="{ row }">
          <span class="text-accent-600">{{ (row as ProjectRow).projectNo }} · {{ (row as ProjectRow).projectName }}</span>
          <StatusBadge v-if="(row as ProjectRow).newInPeriod" :label="c('newBadge')" variant="info" size="sm" class="ms-2" />
        </template>
        <template #cell-status="{ value }">
          <StatusBadge :label="enumLabel('project.status', value as string)" :variant="getProjectStatusVariant(value as ProjectStatus)" />
        </template>
        <template #cell-currentStage="{ value }">{{ getWorkflowStageLabel(value as WorkflowStage) }}</template>
        <template #cell-progress="{ value }">{{ value }}%</template>
        <template #cell-receivedInPeriod="{ value }"><span class="tabular-nums">{{ money(value as number) }}</span></template>
        <template #cell-outstanding="{ value }"><span class="tabular-nums">{{ money(value as number) }}</span></template>
        <template #cell-overdue="{ value }">
          <span class="tabular-nums" :class="(value as number) > 0 ? 'font-semibold text-danger-600' : ''">{{ money(value as number) }}</span>
        </template>
      </SmartTable>
    </BaseDrawer>
  </div>
</template>
