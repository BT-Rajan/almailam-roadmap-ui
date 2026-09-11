<script setup lang="ts">
import { ClipboardList } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseDialog from '@/components/common/BaseDialog.vue'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TablePagination from '@/components/common/TablePagination.vue'
import { usePagination } from '@/composables/usePagination'
import { useStatusReportStore } from '@/stores/statusReportStore'
import { useUserStore } from '@/stores/userStore'
import type { StatusReport } from '@/types/StatusReport'
import type { Task } from '@/types/Task'
import { formatDate } from '@/utils/dateFormatter'

const props = defineProps<{ task: Task }>()

const { t } = useI18n()
const statusReportStore = useStatusReportStore()
const userStore = useUserStore()

// This panel only makes sense for the auto-created Design/Permit/
// Supervision service tasks (see Task.selectedActivityId/
// selectedPermitId/selectedSupervisionActivityId), and only once the
// task is actually assigned to a site engineer -- otherwise there's
// no field report to have a history of yet. Task.assignedTo is
// already resolved to a display name by the time it reaches the
// frontend (see TaskOut.from_model), so role is looked up by name the
// same way TaskAssignmentCard.vue already does.
const belongsToServiceTrack = computed(
  () => Boolean(props.task.selectedActivityId || props.task.selectedPermitId || props.task.selectedSupervisionActivityId),
)
const assigneeIsEngineer = computed(
  () => userStore.users.find((user) => user.name === props.task.assignedTo)?.role === 'Engineer',
)
const isApplicable = computed(() => belongsToServiceTrack.value && assigneeIsEngineer.value)

onMounted(() => {
  if (userStore.users.length === 0) userStore.loadUsers()
  if (isApplicable.value) statusReportStore.loadForTask(props.task.id)
})
watch(isApplicable, (applicable) => {
  if (applicable && !(props.task.id in statusReportStore.taskReports)) statusReportStore.loadForTask(props.task.id)
})

const reports = computed<StatusReport[]>(() => statusReportStore.taskReports[props.task.id] ?? [])

// The report's own free-text notes are the closest thing to a
// "summary" here -- shown as the list entry's title (first line,
// trimmed so a long report doesn't blow out the row), with the full
// text only in the detail dialog on click.
function reportSummary(report: StatusReport): string {
  const firstLine = report.notes.split('\n')[0]?.trim() ?? ''
  return firstLine.length > 100 ? `${firstLine.slice(0, 100)}…` : firstLine || t('task.fieldReportHistory.untitled')
}

const { currentPage, pageSize, totalItems, totalPages, startIndex, endIndex, goToPage, setPageSize, resetPage } =
  usePagination(() => reports.value.length)
const pagedReports = computed(() => reports.value.slice(startIndex.value, endIndex.value))
watch(reports, () => resetPage())

const selectedReport = ref<StatusReport>()
const isDetailOpen = ref(false)
function openReport(report: StatusReport): void {
  selectedReport.value = report
  isDetailOpen.value = true
}
</script>

<template>
  <Card v-if="isApplicable" :padded="false">
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ t('task.fieldReportHistory.title') }}</h3>
    </template>

    <ErrorState v-if="statusReportStore.taskError" :description="statusReportStore.taskError" class="p-5" @retry="() => statusReportStore.loadForTask(task.id)" />

    <EmptyState
      v-else-if="!statusReportStore.isTaskLoading && reports.length === 0"
      :icon="ClipboardList"
      :title="t('task.fieldReportHistory.emptyTitle')"
      :description="t('task.fieldReportHistory.emptyDescription')"
      class="p-5"
    />

    <template v-else>
      <ul class="divide-y divide-border-light">
        <li
          v-for="report in pagedReports"
          :key="report.id"
          class="flex cursor-pointer flex-col gap-1 px-4 py-3 transition-colors hover:bg-bg-hover"
          @click="openReport(report)"
        >
          <div class="flex items-center justify-between gap-3">
            <p class="truncate text-sm font-medium text-text-primary" dir="auto">{{ reportSummary(report) }}</p>
            <span class="shrink-0 text-xs text-text-muted">{{ formatDate(report.reportDate) }}</span>
          </div>
          <p class="text-xs text-text-muted">{{ t('task.fieldReportHistory.by', { name: report.engineerName }) }}</p>
        </li>
      </ul>
      <TablePagination
        :current-page="currentPage"
        :total-pages="totalPages"
        :total-items="totalItems"
        :start-index="startIndex"
        :end-index="endIndex"
        :page-size="pageSize"
        @page-change="goToPage"
        @page-size-change="setPageSize"
      />
    </template>

    <BaseDialog v-model="isDetailOpen" :title="selectedReport?.reportNo" size="md">
      <div v-if="selectedReport" class="flex flex-col gap-3 text-sm">
        <div class="flex items-center justify-between">
          <span class="font-semibold text-text-primary">{{ selectedReport.engineerName }}</span>
          <StatusBadge :label="formatDate(selectedReport.reportDate)" variant="neutral" />
        </div>
        <div v-if="selectedReport.receiptType" class="flex items-center justify-between">
          <span class="text-text-muted">{{ t('project.supervisionReportsTab.receiptHandover') }}</span>
          <span class="font-medium text-text-primary">{{ selectedReport.receiptType }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-text-muted">{{ t('project.supervisionReportsTab.supervision') }}</span>
          <span class="font-medium text-text-primary">{{ selectedReport.supervisionType }}</span>
        </div>
        <div>
          <p class="mb-1 text-text-muted">{{ t('project.supervisionReportsTab.notes') }}</p>
          <p class="whitespace-pre-wrap rounded-lg bg-bg-secondary p-3 text-text-primary" dir="auto">{{ selectedReport.notes }}</p>
        </div>
      </div>
    </BaseDialog>
  </Card>
</template>
