<script setup lang="ts">
import { Plus, Send, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import IconButton from '@/components/common/IconButton.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useScheduledReportStore } from '@/stores/scheduledReportStore'
import { useToastStore } from '@/stores/toastStore'
import { formatDateTime } from '@/utils/dateFormatter'
import type { SmartTableColumn } from '@/types/Table'
import type { ScheduledReport, ScheduledReportFrequency, ScheduledReportPeriod, ScheduledReportType } from '@/types/ScheduledReport'
import type { BadgeVariant } from '@/types/Ui'

interface ScheduleTableRow {
  [key: string]: unknown
  id: string
  name: string
  reportType: ScheduledReportType
  period: ScheduledReportPeriod | null
  projectNo: string | null
  frequency: ScheduledReportFrequency
  recipientCount: number
  isActive: boolean
  nextRunAt: string | null
  lastRunAt: string | null
  lastRunStatus: 'sent' | 'failed' | null
  lastRunError: string | null
}

const { t } = useI18n()
const scheduledReportStore = useScheduledReportStore()
const toastStore = useToastStore()
const router = useRouter()

const deleteTarget = ref<ScheduledReport | undefined>(undefined)
const isDeleting = ref(false)
const sendingTestId = ref<string | undefined>(undefined)

onMounted(() => {
  if (scheduledReportStore.schedules.length === 0) scheduledReportStore.loadSchedules()
})

const REPORT_TYPE_LABEL_KEYS: Record<ScheduledReportType, string> = {
  business_summary: 'administration.scheduledReportsPage.reportTypeBusinessSummary',
  financial_summary: 'administration.scheduledReportsPage.reportTypeFinancialSummary',
  project_status: 'administration.scheduledReportsPage.reportTypeProjectStatus',
}

const FREQUENCY_LABEL_KEYS: Record<ScheduledReportFrequency, string> = {
  once: 'administration.scheduledReportsPage.frequencyOnce',
  daily: 'administration.scheduledReportsPage.frequencyDaily',
  weekly: 'administration.scheduledReportsPage.frequencyWeekly',
  monthly: 'administration.scheduledReportsPage.frequencyMonthly',
}

function reportLabel(row: ScheduleTableRow): string {
  const base = t(REPORT_TYPE_LABEL_KEYS[row.reportType])
  if (row.reportType === 'project_status' && row.projectNo) return `${base} \u2014 ${row.projectNo}`
  return base
}

const TABLE_COLUMNS = computed<SmartTableColumn<ScheduleTableRow>[]>(() => [
  { key: 'name', label: t('administration.scheduledReportsPage.columnName'), sortable: true },
  { key: 'reportType', label: t('administration.scheduledReportsPage.columnReport') },
  { key: 'frequency', label: t('administration.scheduledReportsPage.columnSchedule') },
  { key: 'recipientCount', label: t('administration.scheduledReportsPage.columnRecipients') },
  { key: 'isActive', label: t('administration.scheduledReportsPage.columnStatus') },
  { key: 'lastRunAt', label: t('administration.scheduledReportsPage.columnLastRun') },
  { key: 'actions', label: '' },
])

const tableRows = computed<ScheduleTableRow[]>(() =>
  scheduledReportStore.schedules.map((schedule) => ({
    id: schedule.id,
    name: schedule.name,
    reportType: schedule.reportType,
    period: schedule.period,
    projectNo: schedule.projectNo,
    frequency: schedule.frequency,
    recipientCount: schedule.recipients.length,
    isActive: schedule.isActive,
    nextRunAt: schedule.nextRunAt,
    lastRunAt: schedule.lastRunAt,
    lastRunStatus: schedule.lastRunStatus,
    lastRunError: schedule.lastRunError,
  })),
)

function lastRunVariant(status: 'sent' | 'failed' | null): BadgeVariant {
  if (status === 'sent') return 'success'
  if (status === 'failed') return 'danger'
  return 'neutral'
}

function lastRunLabel(row: ScheduleTableRow): string {
  if (row.lastRunStatus === 'sent') return t('administration.scheduledReportsPage.lastRunSent')
  if (row.lastRunStatus === 'failed') return t('administration.scheduledReportsPage.lastRunFailed')
  return t('administration.scheduledReportsPage.neverRun')
}

// Sends straight to the dedicated schedule form page (see
// ScheduledReportFormPage.vue, which replaced ScheduledReportDialog.vue's
// modal) instead of opening a dialog here -- that page decides create vs
// edit itself from whether ':scheduleId' resolves to an existing schedule.
function openCreateDialog(): void {
  router.push({ name: ROUTE_NAMES.ADMIN_SCHEDULED_REPORT_FORM, params: { scheduleId: 'new' } })
}

function openEditDialog(row: ScheduleTableRow): void {
  router.push({ name: ROUTE_NAMES.ADMIN_SCHEDULED_REPORT_FORM, params: { scheduleId: row.id } })
}

function confirmDelete(row: ScheduleTableRow): void {
  deleteTarget.value = scheduledReportStore.schedules.find((schedule) => schedule.id === row.id)
}

async function handleDelete(): Promise<void> {
  if (!deleteTarget.value) return
  isDeleting.value = true
  try {
    const name = deleteTarget.value.name
    await scheduledReportStore.deleteSchedule(deleteTarget.value.id)
    toastStore.show('success', t('administration.scheduledReportsPage.scheduleDeletedTitle'), t('administration.scheduledReportsPage.scheduleDeletedDescription', { name }))
    deleteTarget.value = undefined
  } catch (error) {
    toastStore.show('error', t('administration.scheduledReportsPage.deleteFailedTitle'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isDeleting.value = false
  }
}

async function handleSendTest(row: ScheduleTableRow): Promise<void> {
  sendingTestId.value = row.id
  try {
    await scheduledReportStore.sendTestNow(row.id)
    toastStore.show('success', t('administration.scheduledReportsPage.testSentTitle'), t('administration.scheduledReportsPage.testSentDescription', { name: row.name }))
  } catch (error) {
    toastStore.show('error', t('administration.scheduledReportsPage.testFailedTitle'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    sendingTestId.value = undefined
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader :title="t('administration.scheduledReportsPage.pageTitle')" :subtitle="t('administration.scheduledReportsPage.pageSubtitle')">
      <template #actions>
        <BaseButton :icon="Plus" @click="openCreateDialog">{{ t('administration.scheduledReportsPage.addSchedule') }}</BaseButton>
      </template>
    </PageHeader>

    <ErrorState v-if="scheduledReportStore.error" :description="scheduledReportStore.error" @retry="scheduledReportStore.loadSchedules" />

    <SmartTable
      v-else
      :columns="TABLE_COLUMNS"
      :rows="tableRows"
      row-key="id"
      :loading="scheduledReportStore.isLoading"
      :searchable="false"
      :empty-title="t('administration.scheduledReportsPage.noSchedulesFound')"
      :empty-description="t('administration.scheduledReportsPage.noSchedulesFoundDescription')"
      @row-click="openEditDialog"
    >
      <template #cell-reportType="{ row }">
        {{ reportLabel(row) }}
      </template>
      <template #cell-frequency="{ value, row }">
        <div class="flex flex-col">
          <span>{{ t(FREQUENCY_LABEL_KEYS[value as ScheduledReportFrequency]) }}</span>
          <span class="text-xs text-text-muted">
            {{ row.nextRunAt ? t('administration.scheduledReportsPage.nextRun', { when: formatDateTime(row.nextRunAt as string) }) : t('administration.scheduledReportsPage.noNextRun') }}
          </span>
        </div>
      </template>
      <template #cell-isActive="{ value }">
        <StatusBadge
          :label="value ? t('administration.scheduledReportsPage.active') : t('administration.scheduledReportsPage.paused')"
          :variant="value ? 'success' : 'neutral'"
          show-dot
        />
      </template>
      <template #cell-lastRunAt="{ row }">
        <div class="flex max-w-xs flex-col gap-1">
          <StatusBadge :label="lastRunLabel(row)" :variant="lastRunVariant(row.lastRunStatus)" />
          <span v-if="row.lastRunAt" class="text-xs text-text-muted">{{ formatDateTime(row.lastRunAt as string) }}</span>
          <span v-if="row.lastRunStatus === 'failed' && row.lastRunError" class="truncate text-xs text-danger-600" :title="row.lastRunError">
            {{ row.lastRunError }}
          </span>
        </div>
      </template>
      <template #cell-actions="{ row }">
        <div class="flex items-center justify-end gap-1" @click.stop>
          <IconButton
            :icon="Send"
            :label="t('administration.scheduledReportsPage.sendTestNow')"
            :disabled="sendingTestId === row.id"
            @click="handleSendTest(row)"
          />
          <IconButton :icon="Trash2" variant="danger" :label="t('administration.scheduledReportsPage.deleteSchedule')" @click="confirmDelete(row)" />
        </div>
      </template>
    </SmartTable>

    <ConfirmationDialog
      :model-value="deleteTarget !== undefined"
      :title="t('administration.scheduledReportsPage.deleteSchedule')"
      :message="t('administration.scheduledReportsPage.deleteScheduleConfirmMessage', { name: deleteTarget?.name })"
      :confirm-label="t('administration.scheduledReportsPage.deleteSchedule')"
      confirm-variant="danger"
      :loading="isDeleting"
      @update:model-value="(value) => { if (!value) deleteTarget = undefined }"
      @confirm="handleDelete"
    />
  </div>
</template>
