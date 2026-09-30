<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import BarChart from '@/components/reports/BarChart.vue'
import ReportDateRange from '@/components/reports/ReportDateRange.vue'
import ReportHeader from '@/components/reports/ReportHeader.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import ReportProjectPicker from '@/components/reports/ReportProjectPicker.vue'
import ReportSection from '@/components/reports/ReportSection.vue'
import { formatValue } from '@/components/reports/chartUtils'
import { useReportRange } from '@/composables/useReportRange'
import { reportService } from '@/services/reportService'
import type { ProjectPerformance, ScheduleHealth } from '@/types/Report'
import type { BadgeVariant } from '@/types/Ui'
import { downloadCsv } from '@/utils/csvExport'
import { formatDate, formatDateTime } from '@/utils/dateFormatter'
import { useEnumLabel } from '@/utils/reportLabels'
import { formatRange } from '@/utils/reportRange'

const AT_RISK_GAP_POINTS = 15
const OVERDUE_SHOWN = 15

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const enumLabel = useEnumLabel()
const p = (key: string, values?: Record<string, unknown>) => t(`report.projectPerformancePage.${key}`, values ?? {})

const rangeState = useReportRange('last-12-months')
const periodLabel = computed(() => formatRange(rangeState.range.value))
const projectNo = computed(() => (route.params.projectId as string | undefined) || undefined)

function pickProject(next: string): void {
  void router.replace({ params: { ...route.params, projectId: next }, query: route.query })
}

const report = ref<ProjectPerformance>()
const isLoading = ref(false)
const error = ref<string>()
const generatedAt = ref('')
let requestId = 0

async function loadReport(): Promise<void> {
  const current = ++requestId
  if (!projectNo.value) {
    report.value = undefined
    return
  }
  isLoading.value = true
  error.value = undefined
  try {
    const result = await reportService.getProjectPerformance(projectNo.value, rangeState.range.value)
    if (current !== requestId) return
    report.value = result
    generatedAt.value = formatDateTime(new Date().toISOString())
  } catch {
    if (current === requestId) error.value = p('loadFailed')
  } finally {
    if (current === requestId) isLoading.value = false
  }
}

watch(() => [projectNo.value, rangeState.range.value] as const, loadReport, { immediate: true })

const HEALTH_VARIANT: Record<ScheduleHealth, BadgeVariant> = {
  'on-track': 'success',
  'at-risk': 'warning',
  late: 'danger',
  completed: 'success',
  cancelled: 'neutral',
  'on-hold': 'warning',
}

const bucketName = computed(() => {
  const bucket = report.value?.bucket ?? 'month'
  return t(`report.executivePage.bucket${bucket.charAt(0).toUpperCase()}${bucket.slice(1)}`)
})
const money = (value: number) => formatValue(value, 'currency')
const percent = (value: number | null | undefined) => (value === null || value === undefined ? '—' : `${value}%`)

const taskStatusPoints = computed(() =>
  (report.value?.tasks.byStatus ?? []).map((row) => ({ label: enumLabel('task.status', row.label), value: row.value })),
)
const cashSeries = computed(() => [
  { name: t('report.executivePage.seriesReceived'), values: report.value?.money.cashFlow.received ?? [] },
  { name: t('report.executivePage.seriesBilled'), values: report.value?.money.cashFlow.billed ?? [] },
])

function exportCsv(): void {
  const data = report.value
  if (!data) return
  const s = data.schedule
  downloadCsv(`project-${data.project.projectNo}-${data.period.startDate}-to-${data.period.endDate}.csv`, [
    {
      title: `${p('pageTitle')} -- ${data.project.projectNo} ${data.project.projectName} -- ${periodLabel.value}`,
      headers: ['Field', 'Value'],
      rows: [
        [p('client'), data.project.clientName],
        [p('engineer'), data.project.engineer],
        [p('status'), data.project.status],
        [p('stage'), data.project.currentStage],
        ['Start date', s.startDate],
        ['Target date', s.targetDate],
        [`${p('progress')} (%)`, s.progressPercent],
        [`${p('timeElapsed')} (%)`, s.timeElapsedPercent],
        ['Days to target', s.daysToTarget],
        ['Schedule health', p(`health.${s.health}`)],
        [p('openTasks'), data.tasks.open],
        [p('overdueTasks'), data.tasks.overdue],
        [p('completedInPeriod'), data.tasks.completedInPeriod],
        [`${p('onTime')} (%)`, data.tasks.onTimeRate],
      ],
    },
    { title: p('tasksByStatus'), headers: [p('columnState'), p('columnCount')], rows: data.tasks.byStatus.map((r) => [r.label, r.value]) },
    {
      title: p('overdueListTitle'),
      headers: [p('columnTask'), 'Title', p('columnAssignee'), p('columnDue'), p('columnDaysLate')],
      rows: data.tasks.overdueList.map((r) => [r.taskNo, r.title, r.assignee, r.dueDate, r.daysLate]),
    },
    {
      title: p('moneyTitle'),
      headers: [p('columnStream'), 'Currency', p('columnContract'), p('columnReceived'), p('columnOutstanding'), p('columnOverdue'), p('columnReceivedInPeriod'), p('columnBilledInPeriod')],
      rows: data.money.streams.map((r) => [r.stream, r.currency, r.contractAmount, r.received, r.outstanding, r.overdue, r.receivedInPeriod, r.billedInPeriod]),
    },
    {
      title: `${p('cashFlowTitle')} (${data.money.chartCurrency ?? ''})`,
      headers: ['Period', t('report.executivePage.seriesReceived'), t('report.executivePage.seriesBilled')],
      rows: data.money.cashFlow.categories.map((label, i) => [label, data.money.cashFlow.received[i], data.money.cashFlow.billed[i]]),
    },
    {
      title: p('upcomingTitle'),
      headers: [p('columnStream'), p('columnInstalment'), p('columnDue'), p('columnAmount'), p('columnOutstanding'), 'Currency', p('overdueBadge')],
      rows: data.money.upcoming.map((r) => [r.stream, r.description, r.dueDate, r.amountDue, r.outstanding, r.currency, r.overdue ? 'Yes' : 'No']),
    },
    { title: p('documentsTitle'), headers: [p('columnState'), p('columnCount')], rows: data.documents.map((r) => [r.label, r.value]) },
    { title: p('submissionsTitle'), headers: [p('columnState'), p('columnCount')], rows: data.submissions.map((r) => [r.label, r.value]) },
  ])
}
</script>

<template>
  <div class="mx-auto max-w-6xl space-y-8 p-6 laptop:p-8">
    <BaseButton variant="ghost" size="sm" class="print:hidden" @click="router.back()">← {{ t('report.back') }}</BaseButton>

    <ReportHeader
      :title="report ? `${report.project.projectName}` : p('pageTitle')"
      :subtitle="report ? `${p('pageTitle')} · ${report.project.projectNo}` : p('pageSubtitle')"
      :period="projectNo ? periodLabel : undefined"
      :generated-date="report ? generatedAt : undefined"
      :exportable="Boolean(report)"
      @download="exportCsv"
    />

    <div class="flex flex-wrap items-end gap-4">
      <ReportProjectPicker :model-value="projectNo" @update:model-value="pickProject" />
      <ReportDateRange :state="rangeState" />
    </div>

    <Card v-if="!projectNo">
      <p class="py-8 text-center text-sm text-text-muted">{{ p('pickProject') }}</p>
    </Card>

    <ErrorState v-else-if="error" :description="error" @retry="loadReport" />

    <div v-else-if="!report" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="6" />
    </div>

    <div v-else class="space-y-8 transition-opacity" :class="isLoading ? 'opacity-50' : ''">
      <!-- Who / where -->
      <Card>
        <div class="grid grid-cols-2 gap-4 tablet:grid-cols-4">
          <div>
            <p class="text-xs font-medium uppercase text-text-muted">{{ p('client') }}</p>
            <p class="mt-1 text-sm font-medium text-text-primary">{{ report.project.clientName || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium uppercase text-text-muted">{{ p('engineer') }}</p>
            <p class="mt-1 text-sm font-medium text-text-primary">{{ report.project.engineer || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium uppercase text-text-muted">{{ p('status') }}</p>
            <p class="mt-1 text-sm font-medium text-text-primary">{{ enumLabel('project.status', report.project.status) }}</p>
          </div>
          <div>
            <p class="text-xs font-medium uppercase text-text-muted">{{ p('stage') }}</p>
            <p class="mt-1 text-sm font-medium text-text-primary">{{ enumLabel('project.stage', report.project.currentStage) }}</p>
          </div>
        </div>
      </Card>

      <!-- Schedule -->
      <ReportSection :title="p('scheduleTitle')" :description="p('scheduleDescription', { gap: AT_RISK_GAP_POINTS })" full-width>
        <Card>
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div class="flex items-center gap-3">
              <StatusBadge :label="p(`health.${report.schedule.health}`)" :variant="HEALTH_VARIANT[report.schedule.health]" show-dot />
              <span class="text-sm text-text-secondary">
                {{ p('dates', { start: formatDate(report.schedule.startDate), target: formatDate(report.schedule.targetDate) }) }}
              </span>
            </div>
            <span class="text-sm font-medium" :class="report.schedule.daysToTarget < 0 ? 'text-danger-600' : 'text-text-secondary'">
              {{ report.schedule.daysToTarget < 0 ? p('daysLate', { count: -report.schedule.daysToTarget }) : p('daysLeft', { count: report.schedule.daysToTarget }) }}
            </span>
          </div>
          <div class="mt-5 space-y-4">
            <div v-for="meter in [
              { label: p('progress'), value: report.schedule.progressPercent, fill: 'bg-accent-600', track: 'bg-accent-100 dark:bg-accent-500/15' },
              { label: p('timeElapsed'), value: report.schedule.timeElapsedPercent, fill: 'bg-neutral-500', track: 'bg-neutral-200 dark:bg-neutral-700' },
            ]" :key="meter.label">
              <div class="mb-1 flex justify-between text-xs">
                <span class="text-text-secondary">{{ meter.label }}</span>
                <span class="font-semibold tabular-nums text-text-primary">{{ Math.round(meter.value) }}%</span>
              </div>
              <div class="h-2 w-full overflow-hidden rounded-full" :class="meter.track" role="meter" :aria-valuenow="meter.value" aria-valuemin="0" aria-valuemax="100" :aria-label="meter.label">
                <div class="h-full rounded-full" :class="meter.fill" :style="{ width: `${Math.min(meter.value, 100)}%` }" />
              </div>
            </div>
          </div>
        </Card>
      </ReportSection>

      <!-- Tasks -->
      <ReportSection :title="p('tasksTitle')" :description="p('tasksDescription')" full-width>
        <div class="grid grid-cols-2 gap-4 laptop:grid-cols-4">
          <ReportMetricCard :label="p('openTasks')" :value="report.tasks.open" :hint="p('openTasksHint', { total: report.tasks.total })" color="primary" />
          <ReportMetricCard :label="p('overdueTasks')" :value="report.tasks.overdue" :color="report.tasks.overdue > 0 ? 'danger' : 'neutral'" />
          <ReportMetricCard :label="p('completedInPeriod')" :value="report.tasks.completedInPeriod" color="success" />
          <ReportMetricCard :label="p('onTime')" :value="percent(report.tasks.onTimeRate)" :hint="p('onTimeHint')" color="info" />
        </div>
        <div class="mt-4 grid grid-cols-1 gap-4 laptop:grid-cols-2">
          <Card>
            <h3 class="mb-3 text-sm font-semibold text-text-primary">{{ p('tasksByStatus') }}</h3>
            <BarChart :data="taskStatusPoints" horizontal :series-name="p('seriesTasks')" :category-label="p('columnState')" show-total />
          </Card>
          <Card>
            <h3 class="mb-3 text-sm font-semibold text-text-primary">{{ p('overdueListTitle') }}</h3>
            <p v-if="report.tasks.overdueList.length === 0" class="py-6 text-center text-sm text-text-muted">{{ p('noOverdueTasks') }}</p>
            <table v-else class="w-full text-sm">
              <thead>
                <tr class="border-b border-border-light text-left text-xs uppercase tracking-wide text-text-muted">
                  <th class="py-2 pe-3 font-medium">{{ p('columnTask') }}</th>
                  <th class="py-2 pe-3 font-medium">{{ p('columnAssignee') }}</th>
                  <th class="py-2 pe-3 font-medium">{{ p('columnDue') }}</th>
                  <th class="py-2 text-end font-medium">{{ p('columnDaysLate') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="task in report.tasks.overdueList.slice(0, OVERDUE_SHOWN)" :key="task.taskNo" class="border-b border-border-light/60 last:border-0">
                  <td class="py-2 pe-3">
                    <RouterLink :to="{ name: 'task-workspace', params: { taskId: task.taskNo } }" class="text-accent-600 hover:underline">{{ task.title }}</RouterLink>
                  </td>
                  <td class="py-2 pe-3 text-text-secondary">{{ task.assignee || '—' }}</td>
                  <td class="whitespace-nowrap py-2 pe-3 text-text-secondary">{{ formatDate(task.dueDate) }}</td>
                  <td class="py-2 text-end font-semibold tabular-nums text-danger-600">{{ task.daysLate }}</td>
                </tr>
              </tbody>
            </table>
            <p v-if="report.tasks.overdue > OVERDUE_SHOWN" class="mt-2 text-xs text-text-muted">
              {{ p('moreOverdue', { count: report.tasks.overdue - OVERDUE_SHOWN }) }}
            </p>
          </Card>
        </div>
      </ReportSection>

      <!-- Money -->
      <ReportSection :title="p('moneyTitle')" :description="p('moneyDescription')" full-width>
        <Card v-if="report.money.streams.length === 0">
          <p class="py-6 text-center text-sm text-text-muted">{{ p('noAgreement') }}</p>
        </Card>
        <template v-else>
          <Card>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-border-light text-left text-xs uppercase tracking-wide text-text-muted">
                    <th class="py-2 pe-3 font-medium">{{ p('columnStream') }}</th>
                    <th class="py-2 ps-3 text-end font-medium">{{ p('columnContract') }}</th>
                    <th class="py-2 ps-3 text-end font-medium">{{ p('columnReceived') }}</th>
                    <th class="py-2 ps-3 text-end font-medium">{{ p('columnOutstanding') }}</th>
                    <th class="py-2 ps-3 text-end font-medium">{{ p('columnOverdue') }}</th>
                    <th class="py-2 ps-3 text-end font-medium">{{ p('columnReceivedInPeriod') }}</th>
                    <th class="py-2 ps-3 text-end font-medium">{{ p('columnBilledInPeriod') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="stream in report.money.streams" :key="stream.stream" class="border-b border-border-light/60 last:border-0">
                    <td class="py-2 pe-3 text-text-primary">{{ stream.stream }} <span class="text-xs text-text-muted">{{ stream.currency }}</span></td>
                    <td class="py-2 ps-3 text-end tabular-nums">{{ money(stream.contractAmount) }}</td>
                    <td class="py-2 ps-3 text-end tabular-nums">{{ money(stream.received) }}</td>
                    <td class="py-2 ps-3 text-end tabular-nums">{{ money(stream.outstanding) }}</td>
                    <td class="py-2 ps-3 text-end tabular-nums" :class="stream.overdue > 0 ? 'font-semibold text-danger-600' : ''">{{ money(stream.overdue) }}</td>
                    <td class="py-2 ps-3 text-end tabular-nums">{{ money(stream.receivedInPeriod) }}</td>
                    <td class="py-2 ps-3 text-end tabular-nums">{{ money(stream.billedInPeriod) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Card>
          <div class="mt-4 grid grid-cols-1 gap-4 laptop:grid-cols-2">
            <Card>
              <h3 class="text-sm font-semibold text-text-primary">{{ p('cashFlowTitle') }}</h3>
              <p class="mb-3 text-xs text-text-muted">{{ p('cashFlowDescription', { bucket: bucketName, currency: report.money.chartCurrency }) }}</p>
              <BarChart :categories="report.money.cashFlow.categories" :series="cashSeries" format="currency" category-label="" show-total />
            </Card>
            <Card>
              <h3 class="text-sm font-semibold text-text-primary">{{ p('upcomingTitle') }}</h3>
              <p class="mb-3 text-xs text-text-muted">{{ p('upcomingDescription') }}</p>
              <p v-if="report.money.upcoming.length === 0" class="py-6 text-center text-sm text-text-muted">{{ p('noUpcoming') }}</p>
              <table v-else class="w-full text-sm">
                <thead>
                  <tr class="border-b border-border-light text-left text-xs uppercase tracking-wide text-text-muted">
                    <th class="py-2 pe-3 font-medium">{{ p('columnInstalment') }}</th>
                    <th class="py-2 pe-3 font-medium">{{ p('columnDue') }}</th>
                    <th class="py-2 text-end font-medium">{{ p('columnOutstanding') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, index) in report.money.upcoming" :key="index" class="border-b border-border-light/60 last:border-0">
                    <td class="py-2 pe-3 text-text-primary">{{ row.description }}</td>
                    <td class="whitespace-nowrap py-2 pe-3" :class="row.overdue ? 'font-medium text-danger-600' : 'text-text-secondary'">
                      {{ formatDate(row.dueDate) }}<span v-if="row.overdue"> · {{ p('overdueBadge') }}</span>
                    </td>
                    <td class="py-2 text-end tabular-nums">{{ money(row.outstanding) }} <span class="text-xs text-text-muted">{{ row.currency }}</span></td>
                  </tr>
                </tbody>
              </table>
            </Card>
          </div>
        </template>
      </ReportSection>

      <!-- Documents and submissions -->
      <div class="grid grid-cols-1 gap-4 laptop:grid-cols-2">
        <Card v-for="block in [
          { title: p('documentsTitle'), rows: report.documents, ns: 'document.status' },
          { title: p('submissionsTitle'), rows: report.submissions, ns: 'government.stage' },
        ]" :key="block.title">
          <h3 class="mb-3 text-sm font-semibold text-text-primary">{{ block.title }}</h3>
          <p v-if="block.rows.length === 0" class="text-sm text-text-muted">{{ p('none') }}</p>
          <dl v-else class="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <template v-for="row in block.rows" :key="row.label">
              <dt class="text-text-secondary">{{ enumLabel(block.ns, row.label) }}</dt>
              <dd class="text-end font-semibold tabular-nums text-text-primary">{{ row.value }}</dd>
            </template>
          </dl>
        </Card>
      </div>
    </div>
  </div>
</template>
