<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import BarChart from '@/components/reports/BarChart.vue'
import ReportDateRange from '@/components/reports/ReportDateRange.vue'
import ReportHeader from '@/components/reports/ReportHeader.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import ReportSection from '@/components/reports/ReportSection.vue'
import { formatValue } from '@/components/reports/chartUtils'
import { STATUS_CHART_COLORS } from '@/constants/chartColors'
import { useReportRange } from '@/composables/useReportRange'
import { reportService } from '@/services/reportService'
import type { TeamWorkloadReport, WorkloadMember } from '@/types/Report'
import { downloadCsv } from '@/utils/csvExport'
import { formatDateTime } from '@/utils/dateFormatter'
import { formatRange } from '@/utils/reportRange'

const router = useRouter()
const { t } = useI18n()
const w = (key: string, values?: Record<string, unknown>) => t(`report.workloadPage.${key}`, values ?? {})

const rangeState = useReportRange('this-month')
const periodLabel = computed(() => formatRange(rangeState.range.value))

const report = ref<TeamWorkloadReport>()
const isLoading = ref(false)
const error = ref<string>()
const generatedAt = ref('')
let requestId = 0

async function load(): Promise<void> {
  const current = ++requestId
  isLoading.value = true
  error.value = undefined
  try {
    const result = await reportService.getTeamWorkload(rangeState.range.value)
    if (current !== requestId) return
    report.value = result
    generatedAt.value = formatDateTime(new Date().toISOString())
  } catch (loadError) {
    if (current === requestId) error.value = loadError instanceof Error ? loadError.message : w('loadFailed')
  } finally {
    if (current === requestId) isLoading.value = false
  }
}

watch(() => rangeState.range.value, load, { immediate: true })

const members = computed<WorkloadMember[]>(() => report.value?.members ?? [])
const totals = computed(() => report.value?.totals)
const dueSoonDays = computed(() => report.value?.dueSoonDays ?? 7)
const count = (value: number) => formatValue(value, 'number')
const percent = (value: number | null | undefined) => (value === null || value === undefined ? '—' : `${value}%`)
const displayName = (member: WorkloadMember) => (member.inactive ? `${member.name} (${w('inactiveBadge')})` : member.name)

// Only people who actually hold open work get a bar; idle people are
// listed in the table and the "has room" note instead.
const withOpenWork = computed(() => members.value.filter((member) => member.openTasks > 0))
// Urgency colours mean something here (late / soon / fine), so status
// tokens rather than categorical slots.
const openWorkSeries = computed(() => [
  { name: w('seriesOverdue'), values: withOpenWork.value.map((m) => m.overdueTasks), color: STATUS_CHART_COLORS.danger },
  { name: w('seriesDueSoon', { days: dueSoonDays.value }), values: withOpenWork.value.map((m) => m.dueSoonTasks), color: STATUS_CHART_COLORS.warning },
  { name: w('seriesLater'), values: withOpenWork.value.map((m) => m.laterTasks), color: 'var(--chart-series-1)' },
])
const throughput = computed(() =>
  members.value
    .filter((member) => member.completedInPeriod > 0)
    .sort((a, b) => b.completedInPeriod - a.completedInPeriod)
    .map((member) => ({ label: displayName(member), value: member.completedInPeriod })),
)

const behind = computed(() => members.value.filter((member) => member.overdueTasks > 0 && !member.inactive))
const withRoom = computed(() => members.value.filter((member) => member.openTasks === 0 && !member.inactive))
const stranded = computed(() => members.value.filter((member) => member.inactive && member.openTasks > 0))
const names = (list: WorkloadMember[]) => list.map((member) => member.name).join(', ')

function exportCsv(): void {
  const data = report.value
  if (!data) return
  downloadCsv(`team-workload-${data.period.startDate}-to-${data.period.endDate}.csv`, [
    {
      title: `${w('pageTitle')} -- ${periodLabel.value}`,
      headers: [
        w('columnPerson'), 'Role', w('inactiveBadge'), w('columnProjects'), w('columnOpen'), w('columnOverdue'),
        `${w('columnOldest')} (days)`, w('columnDueSoon'), w('seriesLater'), w('columnNotStarted'), w('columnCompleted'), `${w('columnOnTime')} (%)`,
      ],
      rows: data.members.map((m) => [
        m.name, m.role, m.inactive ? 'Yes' : 'No', m.activeProjects, m.openTasks, m.overdueTasks,
        m.oldestOverdueDays, m.dueSoonTasks, m.laterTasks, m.notStartedTasks, m.completedInPeriod, m.onTimeRate,
      ]),
    },
  ])
}
</script>

<template>
  <div class="mx-auto max-w-6xl space-y-8 p-6 laptop:p-8">
    <BaseButton variant="ghost" size="sm" class="print:hidden" @click="router.back()">← {{ t('report.back') }}</BaseButton>

    <ReportHeader
      :title="w('pageTitle')"
      :subtitle="w('pageSubtitle')"
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

    <EmptyState v-else-if="members.length === 0" :title="w('noDataTitle')" :description="w('noDataDescription')" />

    <div v-else-if="totals" class="space-y-8 transition-opacity" :class="isLoading ? 'opacity-50' : ''">
      <ReportSection :title="w('overviewTitle')" :description="w('overviewDescription')" full-width>
        <div class="grid grid-cols-2 gap-4 laptop:grid-cols-5">
          <ReportMetricCard :label="w('openTasks')" :value="count(totals.openTasks)" :hint="w('openTasksHint', { people: totals.peopleWithOpenWork })" color="primary" />
          <ReportMetricCard
            :label="w('overdueTasks')"
            :value="count(totals.overdueTasks)"
            :hint="w('overdueHint', { share: percent(totals.overdueShare), people: totals.peopleWithOverdue })"
            :color="totals.overdueTasks > 0 ? 'danger' : 'neutral'"
          />
          <ReportMetricCard :label="w('dueSoon', { days: dueSoonDays })" :value="count(totals.dueSoonTasks)" color="warning" />
          <ReportMetricCard :label="w('completed')" :value="count(totals.completedInPeriod)" :hint="w('completedHint', { rate: percent(totals.onTimeRate) })" color="success" />
          <ReportMetricCard :label="w('stranded')" :value="count(totals.strandedTasks)" :hint="w('strandedHint')" :color="totals.strandedTasks > 0 ? 'danger' : 'neutral'" />
        </div>
      </ReportSection>

      <div class="grid grid-cols-1 gap-4 laptop:grid-cols-2">
        <Card>
          <h3 class="text-sm font-semibold text-text-primary">{{ w('openWorkTitle') }}</h3>
          <p class="mb-3 text-xs text-text-muted">{{ w('openWorkDescription') }}</p>
          <BarChart
            :categories="withOpenWork.map(displayName)"
            :series="openWorkSeries"
            horizontal
            stacked
            :category-label="w('columnPerson')"
            show-total
          />
        </Card>
        <Card>
          <h3 class="text-sm font-semibold text-text-primary">{{ w('throughputTitle') }}</h3>
          <p class="mb-3 text-xs text-text-muted">{{ w('throughputDescription') }}</p>
          <BarChart :data="throughput" horizontal :series-name="w('seriesCompleted')" :category-label="w('columnPerson')" show-total />
        </Card>
      </div>

      <ReportSection :title="w('tableTitle')" :description="w('tableDescription')" full-width>
        <Card>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-border-light text-left text-xs uppercase tracking-wide text-text-muted">
                  <th class="py-2 pe-3 font-medium">{{ w('columnPerson') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ w('columnProjects') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ w('columnOpen') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ w('columnOverdue') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ w('columnOldest') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ w('columnDueSoon') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ w('columnNotStarted') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ w('columnCompleted') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ w('columnOnTime') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="member in members" :key="member.userId" class="border-b border-border-light/60 last:border-0">
                  <td class="py-2 pe-3">
                    <p class="font-medium text-text-primary">{{ member.name }}</p>
                    <p class="text-xs text-text-muted">
                      {{ member.role }}
                      <StatusBadge v-if="member.inactive" :label="w('inactiveBadge')" variant="danger" class="ms-1" />
                    </p>
                  </td>
                  <td class="py-2 ps-3 text-end tabular-nums">{{ member.activeProjects }}</td>
                  <td class="py-2 ps-3 text-end font-semibold tabular-nums">{{ member.openTasks }}</td>
                  <td class="py-2 ps-3 text-end tabular-nums" :class="member.overdueTasks > 0 ? 'font-semibold text-danger-600' : ''">{{ member.overdueTasks }}</td>
                  <td class="py-2 ps-3 text-end tabular-nums text-text-secondary">{{ member.oldestOverdueDays === null ? '—' : w('days', { count: member.oldestOverdueDays }) }}</td>
                  <td class="py-2 ps-3 text-end tabular-nums">{{ member.dueSoonTasks }}</td>
                  <td class="py-2 ps-3 text-end tabular-nums">{{ member.notStartedTasks }}</td>
                  <td class="py-2 ps-3 text-end tabular-nums">{{ member.completedInPeriod }}</td>
                  <td class="py-2 ps-3 text-end tabular-nums">{{ percent(member.onTimeRate) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
      </ReportSection>

      <ReportSection :title="w('attentionTitle')" full-width>
        <Card>
          <ul class="space-y-2 text-sm">
            <li v-if="stranded.length" class="text-danger-700 dark:text-danger-400">
              {{ w('strandedText', { count: totals.strandedTasks, names: names(stranded) }) }}
            </li>
            <li v-if="behind.length" class="text-text-primary">{{ w('behindText', { names: names(behind) }) }}</li>
            <li v-if="withRoom.length" class="text-text-primary">{{ w('roomText', { names: names(withRoom) }) }}</li>
            <li v-if="!stranded.length && !behind.length" class="text-success-700 dark:text-success-400">{{ w('allClear') }}</li>
          </ul>
        </Card>
      </ReportSection>

      <p class="border-t border-border-light pt-6 text-center text-xs text-text-muted">{{ w('footerBasedOn') }}</p>
    </div>
  </div>
</template>
