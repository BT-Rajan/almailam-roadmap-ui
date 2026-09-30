<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import BarChart from '@/components/reports/BarChart.vue'
import LineChart from '@/components/reports/LineChart.vue'
import ReportDateRange from '@/components/reports/ReportDateRange.vue'
import ReportHeader from '@/components/reports/ReportHeader.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import ReportSection from '@/components/reports/ReportSection.vue'
import { formatValue } from '@/components/reports/chartUtils'
import { useReportRange } from '@/composables/useReportRange'
import { activityCalendarService, type ActivityRecord } from '@/services/activityCalendarService'
import { reportService } from '@/services/reportService'
import type { ActivityMember, EmployeeActivityReport } from '@/types/Report'
import type { SmartTableColumn } from '@/types/Table'
import type { SelectOption } from '@/types/Ui'
import { downloadCsv } from '@/utils/csvExport'
import { addDaysIso, formatDateTime } from '@/utils/dateFormatter'
import { formatRange } from '@/utils/reportRange'

const router = useRouter()
const { t } = useI18n()
const e = (key: string, values?: Record<string, unknown>) => t(`report.employeeActivityPage.${key}`, values ?? {})

const rangeState = useReportRange('this-month')
const periodLabel = computed(() => formatRange(rangeState.range.value))

const ALL = 'all'
const userOptions = ref<SelectOption[]>([{ label: e('allEmployees'), value: ALL }])
const selectedUserId = ref(ALL)
onMounted(async () => {
  try {
    const users = await activityCalendarService.getUsersForFiltering()
    userOptions.value = [{ label: e('allEmployees'), value: ALL }, ...users.map((user) => ({ label: user.name, value: user.id }))]
  } catch {
    // The filter is a convenience; the report still works for everyone.
  }
})

const report = ref<EmployeeActivityReport>()
const isLoading = ref(false)
const error = ref<string>()
const generatedAt = ref('')
let requestId = 0

async function load(): Promise<void> {
  const current = ++requestId
  isLoading.value = true
  error.value = undefined
  try {
    const result = await reportService.getEmployeeActivity(rangeState.range.value, selectedUserId.value === ALL ? undefined : selectedUserId.value)
    if (current !== requestId) return
    report.value = result
    generatedAt.value = formatDateTime(new Date().toISOString())
  } catch (loadError) {
    if (current === requestId) error.value = loadError instanceof Error ? loadError.message : e('loadFailed')
  } finally {
    if (current === requestId) isLoading.value = false
  }
}

watch(() => [rangeState.range.value, selectedUserId.value] as const, load, { immediate: true })

const count = (value: number) => formatValue(value, 'number')
const nameOf = (member: ActivityMember) => (member.system ? e('systemName') : member.name)
const bucketName = computed(() => {
  const bucket = report.value?.bucket ?? 'month'
  return t(`report.executivePage.bucket${bucket.charAt(0).toUpperCase()}${bucket.slice(1)}`)
})
const areaLabel = (area: string) => e(`areas.${area}`)

const areaPoints = computed(() =>
  [...(report.value?.areas ?? [])].sort((a, b) => b.value - a.value).map((row) => ({ label: areaLabel(row.label), value: row.value })),
)

// Four series at most (the validated palette has four slots): the three
// areas people work in most, everything else folded into "Other".
const FOLDED_AREAS = ['task', 'project', 'document'] as const
const people = computed(() => (report.value?.members ?? []).filter((member) => !member.system))
const perPersonSeries = computed(() => {
  const other = (member: ActivityMember) =>
    Object.entries(member.byArea).reduce((sum, [area, value]) => sum + ((FOLDED_AREAS as readonly string[]).includes(area) ? 0 : value), 0)
  return [
    ...FOLDED_AREAS.map((area) => ({ name: areaLabel(area), values: people.value.map((member) => member.byArea[area] ?? 0) })),
    { name: t('report.chart.other'), values: people.value.map(other) },
  ]
})

// ---- Drill-down: one person's full list -------------------------------------
type ActivityRow = ActivityRecord & Record<string, unknown>
const detailColumns = computed<SmartTableColumn<ActivityRow>[]>(() => [
  { key: 'timestamp', label: e('columnWhen') },
  { key: 'description', label: e('columnActivity') },
  { key: 'entityName', label: e('columnItem') },
  { key: 'projectName', label: e('columnProject') },
])
const drawerOpen = ref(false)
const drawerMember = ref<ActivityMember>()
const drawerRows = ref<ActivityRow[]>([])
const drawerLoading = ref(false)
const drawerError = ref<string>()

async function openMember(member: ActivityMember): Promise<void> {
  if (member.system) return
  drawerMember.value = member
  drawerOpen.value = true
  drawerLoading.value = true
  drawerError.value = undefined
  drawerRows.value = []
  try {
    const { from, to } = rangeState.range.value
    // This endpoint's end date is exclusive.
    const rows = await activityCalendarService.getFilteredActivities({ startDate: from, endDate: addDaysIso(to, 1), userId: member.userId })
    drawerRows.value = rows as ActivityRow[]
  } catch {
    drawerError.value = e('detailFailed')
  } finally {
    drawerLoading.value = false
  }
}

function exportDrawer(): void {
  if (!drawerMember.value) return
  const { from, to } = rangeState.range.value
  downloadCsv(`activity-${drawerMember.value.name.replace(/\s+/g, '-')}-${from}-to-${to}.csv`, [
    {
      title: `${drawerMember.value.name} -- ${periodLabel.value}`,
      headers: [e('columnWhen'), e('columnActivity'), e('columnItem'), e('columnProject')],
      rows: drawerRows.value.map((row) => [formatDateTime(row.timestamp), row.description, row.entityName, row.projectName ?? '']),
    },
  ])
}

function exportCsv(): void {
  const data = report.value
  if (!data) return
  const areas = ['task', 'project', 'document', 'payment', 'client', 'quotation', 'contract', 'workflow']
  downloadCsv(`employee-activity-${data.period.startDate}-to-${data.period.endDate}.csv`, [
    {
      title: `${e('pageTitle')} -- ${periodLabel.value}`,
      headers: [
        e('columnEmployee'), e('columnActions'), e('columnDays'), e('columnProjects'), e('columnCreated'), e('columnUpdated'),
        e('columnCompleted'), e('columnRejected'), e('columnDeleted'), ...areas.map(areaLabel), e('columnLast'),
      ],
      rows: data.members.map((m) => [
        nameOf(m), m.actions, m.activeDays, m.projectsTouched, m.created, m.updated, m.completed, m.rejected, m.deleted,
        ...areas.map((area) => m.byArea[area] ?? 0), formatDateTime(m.lastActivity),
      ]),
    },
    {
      title: e('trendTitle'),
      headers: ['Period', e('seriesActions')],
      rows: data.series.categories.map((label, i) => [label, data.series.actions[i]]),
    },
  ])
}
</script>

<template>
  <div class="mx-auto max-w-6xl space-y-8 p-6 laptop:p-8">
    <BaseButton variant="ghost" size="sm" class="print:hidden" @click="router.back()">← {{ t('report.back') }}</BaseButton>

    <ReportHeader
      :title="e('pageTitle')"
      :subtitle="e('pageSubtitle')"
      :period="periodLabel"
      :generated-date="generatedAt"
      :exportable="Boolean(report)"
      @download="exportCsv"
    />

    <div class="flex flex-wrap items-end gap-4">
      <div class="w-56 print:hidden"><SelectBox v-model="selectedUserId" :label="e('employee')" :options="userOptions" /></div>
      <ReportDateRange :state="rangeState" />
    </div>

    <ErrorState v-if="error" :description="error" @retry="load" />

    <div v-else-if="!report" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="6" />
    </div>

    <EmptyState v-else-if="report.members.length === 0" :title="e('noActivity')" />

    <div v-else class="space-y-8 transition-opacity" :class="isLoading ? 'opacity-50' : ''">
      <ReportSection :title="e('overviewTitle')" :description="e('overviewDescription')" full-width>
        <div class="grid grid-cols-2 gap-4 laptop:grid-cols-5">
          <ReportMetricCard
            :label="e('metricActions')"
            :value="count(report.totals.actions)"
            :hint="report.totals.systemActions ? e('metricActionsHint', { count: count(report.totals.systemActions) }) : undefined"
            color="primary"
          />
          <ReportMetricCard :label="e('metricPeople')" :value="count(report.totals.peopleActive)" color="info" />
          <ReportMetricCard :label="e('metricCreated')" :value="count(report.totals.created)" color="success" />
          <ReportMetricCard :label="e('metricCompleted')" :value="count(report.totals.completed)" color="success" />
          <ReportMetricCard :label="e('metricDeleted')" :value="count(report.totals.deleted)" :color="report.totals.deleted ? 'warning' : 'neutral'" />
        </div>
        <div class="mt-4 grid grid-cols-1 gap-4 laptop:grid-cols-2">
          <Card>
            <h3 class="text-sm font-semibold text-text-primary">{{ e('trendTitle') }}</h3>
            <p class="mb-3 text-xs text-text-muted">{{ e('trendDescription', { bucket: bucketName }) }}</p>
            <LineChart :categories="report.series.categories" :series="[{ name: e('seriesActions'), values: report.series.actions }]" :series-name="e('seriesActions')" show-total />
          </Card>
          <Card>
            <h3 class="text-sm font-semibold text-text-primary">{{ e('areasTitle') }}</h3>
            <p class="mb-3 text-xs text-text-muted">{{ e('areasDescription') }}</p>
            <BarChart :data="areaPoints" horizontal :series-name="e('seriesActions')" show-total />
          </Card>
        </div>
      </ReportSection>

      <ReportSection :title="e('perPersonTitle')" :description="e('perPersonDescription')" full-width>
        <Card v-if="people.length > 1">
          <BarChart :categories="people.map(nameOf)" :series="perPersonSeries" horizontal stacked :category-label="e('columnEmployee')" show-total />
        </Card>
        <Card class="mt-4">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-border-light text-left text-xs uppercase tracking-wide text-text-muted">
                  <th class="py-2 pe-3 font-medium">{{ e('columnEmployee') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ e('columnActions') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ e('columnDays') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ e('columnProjects') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ e('columnCreated') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ e('columnUpdated') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ e('columnCompleted') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ e('columnDeleted') }}</th>
                  <th class="py-2 ps-3 text-end font-medium">{{ e('columnLast') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="member in report.members"
                  :key="member.userId || 'system'"
                  class="border-b border-border-light/60 last:border-0"
                  :class="member.system ? 'text-text-muted' : 'cursor-pointer hover:bg-bg-hover'"
                  :tabindex="member.system ? -1 : 0"
                  @click="openMember(member)"
                  @keydown.enter="openMember(member)"
                >
                  <td class="py-2 pe-3 font-medium" :class="member.system ? '' : 'text-accent-600'">{{ nameOf(member) }}</td>
                  <td class="py-2 ps-3 text-end font-semibold tabular-nums">{{ count(member.actions) }}</td>
                  <td class="py-2 ps-3 text-end tabular-nums">{{ member.activeDays }}</td>
                  <td class="py-2 ps-3 text-end tabular-nums">{{ member.projectsTouched }}</td>
                  <td class="py-2 ps-3 text-end tabular-nums">{{ count(member.created) }}</td>
                  <td class="py-2 ps-3 text-end tabular-nums">{{ count(member.updated) }}</td>
                  <td class="py-2 ps-3 text-end tabular-nums">{{ count(member.completed) }}</td>
                  <td class="py-2 ps-3 text-end tabular-nums">{{ count(member.deleted) }}</td>
                  <td class="whitespace-nowrap py-2 ps-3 text-end text-text-secondary">{{ formatDateTime(member.lastActivity) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
      </ReportSection>
    </div>

    <BaseDrawer v-model="drawerOpen" :title="drawerMember ? `${drawerMember.name} · ${periodLabel}` : ''" width="lg">
      <div class="mb-3 flex justify-end">
        <BaseButton size="sm" variant="secondary" :disabled="drawerRows.length === 0" @click="exportDrawer">{{ t('report.header.export') }}</BaseButton>
      </div>
      <ErrorState v-if="drawerError" :description="drawerError" />
      <SmartTable
        v-else
        :columns="detailColumns"
        :rows="drawerRows"
        row-key="id"
        :loading="drawerLoading"
        :searchable="true"
        :empty-title="e('noActivity')"
      >
        <template #cell-timestamp="{ value }">{{ formatDateTime(value as string) }}</template>
        <template #cell-projectName="{ value }">{{ value || '—' }}</template>
      </SmartTable>
    </BaseDrawer>
  </div>
</template>
