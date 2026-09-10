<script setup lang="ts">
import { Download } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import Card from '@/components/common/Card.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import { activityCalendarService, type ActivityRecord } from '@/services/activityCalendarService'
import { useToastStore } from '@/stores/toastStore'
import type { SmartTableColumn } from '@/types/Table'
import type { SelectOption } from '@/types/Ui'
import { formatDateTime } from '@/utils/dateFormatter'

const { t } = useI18n()
const toastStore = useToastStore()

// Same "isoDate" shape as ActivityCalendarPage.vue's formatDateKey, kept
// local here since this page deals in plain from/to bounds rather than a
// calendar grid.
function isoDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
function addDays(date: Date, days: number): Date {
  const copy = new Date(date)
  copy.setDate(copy.getDate() + days)
  return copy
}

type Preset = 'today' | 'week' | 'month' | 'custom'
const preset = ref<Preset>('today')
const customFrom = ref(isoDate(addDays(new Date(), -6)))
const customTo = ref(isoDate(new Date()))

// activity_service._fetch_rows filters "changed_at >= start AND < end" --
// end is exclusive (see get_day_activity's own +1 day), so every preset
// below sends the day AFTER the last day it means to include.
const requestRange = computed<{ startDate: string; endDate: string; rangeLabel: string }>(() => {
  const today = new Date()
  if (preset.value === 'today') {
    const day = isoDate(today)
    return { startDate: day, endDate: isoDate(addDays(today, 1)), rangeLabel: t('report.employeeActivityPage.presetToday') }
  }
  if (preset.value === 'week') {
    return {
      startDate: isoDate(addDays(today, -6)),
      endDate: isoDate(addDays(today, 1)),
      rangeLabel: t('report.employeeActivityPage.presetWeek'),
    }
  }
  if (preset.value === 'month') {
    return {
      startDate: isoDate(addDays(today, -29)),
      endDate: isoDate(addDays(today, 1)),
      rangeLabel: t('report.employeeActivityPage.presetMonth'),
    }
  }
  const from = customFrom.value || isoDate(today)
  const to = customTo.value || isoDate(today)
  const endExclusive = isoDate(addDays(new Date(`${to}T00:00:00`), 1))
  return { startDate: from, endDate: endExclusive, rangeLabel: `${from} – ${to}` }
})

const userOptions = ref<SelectOption[]>([])
const selectedUserId = ref('')
const isLoading = ref(false)
const loadError = ref('')
const activities = ref<ActivityRecord[]>([])

async function loadUsers(): Promise<void> {
  try {
    const users = await activityCalendarService.getUsersForFiltering()
    userOptions.value = [{ label: t('report.employeeActivityPage.allEmployees'), value: '' }, ...users.map((u) => ({ label: u.name, value: u.id }))]
  } catch {
    // The employee filter is a convenience, not load-bearing -- an admin
    // who can already see this report can still read it with no filter.
    userOptions.value = [{ label: t('report.employeeActivityPage.allEmployees'), value: '' }]
  }
}

async function loadActivities(): Promise<void> {
  isLoading.value = true
  loadError.value = ''
  try {
    const { startDate, endDate } = requestRange.value
    activities.value = await activityCalendarService.getFilteredActivities({
      startDate,
      endDate,
      userId: selectedUserId.value || undefined,
    })
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : t('report.employeeActivityPage.loadFailed')
    activities.value = []
  } finally {
    isLoading.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadUsers(), loadActivities()])
})

function applyFilters(): void {
  void loadActivities()
}

// --- Employeewise grouping ------------------------------------------------

interface EmployeeSummaryRow {
  [key: string]: unknown
  userId: string
  employee: string
  total: number
  new: number
  updated: number
  completed: number
  approved: number
  rejected: number
}

const employeeSummaries = computed<EmployeeSummaryRow[]>(() => {
  const byUser = new Map<string, EmployeeSummaryRow>()
  for (const activity of activities.value) {
    const key = activity.userId || '0'
    let row = byUser.get(key)
    if (!row) {
      row = { userId: key, employee: activity.userName, total: 0, new: 0, updated: 0, completed: 0, approved: 0, rejected: 0 }
      byUser.set(key, row)
    }
    row.total += 1
    if (activity.type in row) row[activity.type] = (row[activity.type] as number) + 1
  }
  return [...byUser.values()].sort((a, b) => b.total - a.total)
})

const summaryColumns = computed<SmartTableColumn<EmployeeSummaryRow>[]>(() => [
  { key: 'employee', label: t('report.employeeActivityPage.columnEmployee') },
  { key: 'total', label: t('report.employeeActivityPage.columnTotal'), align: 'right', sortable: true },
  { key: 'new', label: t('report.employeeActivityPage.columnNew'), align: 'right' },
  { key: 'updated', label: t('report.employeeActivityPage.columnUpdated'), align: 'right' },
  { key: 'completed', label: t('report.employeeActivityPage.columnCompleted'), align: 'right' },
  { key: 'approved', label: t('report.employeeActivityPage.columnApproved'), align: 'right' },
  { key: 'rejected', label: t('report.employeeActivityPage.columnRejected'), align: 'right' },
])

// SmartTable's generic requires an index signature -- ActivityRecord (a
// plain interface) doesn't have one, so every row list handed to it below
// is typed through this instead of the bare service type.
type ActivityRow = ActivityRecord & Record<string, unknown>

const activityDetailColumns = computed<SmartTableColumn<ActivityRow>[]>(() => [
  { key: 'timestamp', label: t('report.employeeActivityPage.columnWhen') },
  { key: 'description', label: t('report.employeeActivityPage.columnActivity') },
  { key: 'entityName', label: t('report.employeeActivityPage.columnItem') },
  { key: 'projectName', label: t('report.employeeActivityPage.columnProject') },
])

const isDrawerOpen = ref(false)
const drawerEmployeeName = ref('')
const drawerActivities = ref<ActivityRow[]>([])

function openEmployee(row: EmployeeSummaryRow): void {
  drawerEmployeeName.value = row.employee
  drawerActivities.value = activities.value
    .filter((a) => (a.userId || '0') === row.userId)
    .sort((a, b) => b.timestamp.localeCompare(a.timestamp))
  isDrawerOpen.value = true
}

// When a single employee is already selected via the filter, skip the
// grouping table entirely and show their activity list directly -- a
// one-row summary table would just be an extra click for no reason.
const singleEmployeeActivities = computed<ActivityRow[]>(() =>
  [...activities.value].sort((a, b) => b.timestamp.localeCompare(a.timestamp)),
)

const totalActivities = computed(() => activities.value.length)
const activeEmployeeCount = computed(() => employeeSummaries.value.length)

async function handleExport(): Promise<void> {
  try {
    const { startDate, endDate } = requestRange.value
    const blob = await activityCalendarService.exportActivitiesCSV({
      startDate,
      endDate,
      userId: selectedUserId.value || undefined,
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `employee-activity-${requestRange.value.startDate}-to-${requestRange.value.endDate}.csv`
    link.click()
    URL.revokeObjectURL(url)
  } catch {
    toastStore.show('error', t('report.employeeActivityPage.exportFailed'))
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader :title="t('report.employeeActivityPage.pageTitle')" :subtitle="t('report.employeeActivityPage.pageSubtitle')">
      <template #actions>
        <BaseButton :icon="Download" variant="secondary" @click="handleExport">{{ t('report.employeeActivityPage.exportCsv') }}</BaseButton>
      </template>
    </PageHeader>

    <Card>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
        <SelectBox v-model="selectedUserId" :label="t('report.employeeActivityPage.employee')" :options="userOptions" @update:model-value="applyFilters" />
        <SelectBox
          v-model="preset"
          :label="t('report.employeeActivityPage.range')"
          :options="[
            { label: t('report.employeeActivityPage.presetToday'), value: 'today' },
            { label: t('report.employeeActivityPage.presetWeek'), value: 'week' },
            { label: t('report.employeeActivityPage.presetMonth'), value: 'month' },
            { label: t('report.employeeActivityPage.presetCustom'), value: 'custom' },
          ]"
          @update:model-value="applyFilters"
        />
        <template v-if="preset === 'custom'">
          <DatePicker v-model="customFrom" :label="t('report.employeeActivityPage.from')" :max="customTo" @update:model-value="applyFilters" />
          <DatePicker v-model="customTo" :label="t('report.employeeActivityPage.to')" :min="customFrom" @update:model-value="applyFilters" />
        </template>
        <div class="flex items-end">
          <BaseButton full-width variant="secondary" :loading="isLoading" @click="applyFilters">{{ t('report.employeeActivityPage.refresh') }}</BaseButton>
        </div>
      </div>
    </Card>

    <ErrorState v-if="loadError" :description="loadError" @retry="loadActivities" />

    <template v-else>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <ReportMetricCard :label="t('report.employeeActivityPage.metricTotal')" :value="totalActivities" color="primary" />
        <ReportMetricCard :label="t('report.employeeActivityPage.metricEmployees')" :value="activeEmployeeCount" color="info" />
        <ReportMetricCard :label="t('report.employeeActivityPage.metricRange')" :value="requestRange.rangeLabel" color="neutral" />
      </div>

      <!-- All employees: employeewise summary table, drill into a drawer per row -->
      <SmartTable
        v-if="!selectedUserId"
        :columns="summaryColumns"
        :rows="employeeSummaries"
        row-key="userId"
        :loading="isLoading"
        :searchable="true"
        :search-placeholder="t('report.employeeActivityPage.searchEmployee')"
        :empty-title="t('report.employeeActivityPage.noActivity')"
        @row-click="openEmployee"
      />

      <!-- One employee already selected: show their activity list directly -->
      <SmartTable
        v-else
        :columns="activityDetailColumns"
        :rows="singleEmployeeActivities"
        row-key="id"
        :loading="isLoading"
        :searchable="true"
        :empty-title="t('report.employeeActivityPage.noActivity')"
      >
        <template #cell-timestamp="{ value }">{{ formatDateTime(value as string) }}</template>
        <template #cell-projectName="{ value }">{{ value || '—' }}</template>
      </SmartTable>
    </template>

    <BaseDrawer v-model="isDrawerOpen" :title="drawerEmployeeName" width="lg">
      <SmartTable
        :columns="activityDetailColumns"
        :rows="drawerActivities"
        row-key="id"
        :searchable="false"
        :empty-title="t('report.employeeActivityPage.noActivity')"
      >
        <template #cell-timestamp="{ value }">{{ formatDateTime(value as string) }}</template>
        <template #cell-projectName="{ value }">{{ value || '—' }}</template>
      </SmartTable>
    </BaseDrawer>
  </div>
</template>
