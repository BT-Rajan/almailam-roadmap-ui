<script setup lang="ts">
import { CheckCircle2, Inbox, Paperclip } from '@lucide/vue'
import { onMounted, ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TextArea from '@/components/common/TextArea.vue'
import { taskService } from '@/services/taskService'
import { useStatusReportStore } from '@/stores/statusReportStore'
import { useToastStore } from '@/stores/toastStore'
import type { StatusReport } from '@/types/StatusReport'
import type { SelectOption } from '@/types/Ui'
import { formatDate } from '@/utils/dateFormatter'

const statusReportStore = useStatusReportStore()
const toastStore = useToastStore()

onMounted(() => statusReportStore.loadInbox())

const isAttachDialogOpen = ref(false)
const selectedReport = ref<StatusReport>()
const attachTaskId = ref('')
const attachNotes = ref('')
const taskOptions = ref<SelectOption[]>([])
const isLoadingTasks = ref(false)
const isSaving = ref(false)

async function openAttachDialog(report: StatusReport): Promise<void> {
  selectedReport.value = report
  attachTaskId.value = ''
  attachNotes.value = ''
  isAttachDialogOpen.value = true
  isLoadingTasks.value = true
  try {
    const page = await taskService.getTasksPage({ projectId: report.projectId, pageSize: 100 })
    taskOptions.value = page.items.map((task) => ({ label: `${task.id} — ${task.title}`, value: task.id }))
  } catch {
    taskOptions.value = []
  } finally {
    isLoadingTasks.value = false
  }
}

async function handleAttach(): Promise<void> {
  if (!selectedReport.value) return
  if (!attachNotes.value.trim()) {
    toastStore.show('error', 'Notes are required', 'Please add a brief note before attaching this report.')
    return
  }

  isSaving.value = true
  try {
    await statusReportStore.attachReport(selectedReport.value.id, {
      taskId: attachTaskId.value || undefined,
      notes: attachNotes.value.trim(),
    })
    toastStore.show('success', 'Report attached', `${selectedReport.value.reportNo} has been added to ${selectedReport.value.projectName}'s timeline.`)
    isAttachDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to attach report', detail)
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader title="Status Report Inbox" subtitle="Field reports awaiting review, oldest first." />

    <div v-if="statusReportStore.isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="6" />
    </div>

    <ErrorState v-else-if="statusReportStore.error" :description="statusReportStore.error" @retry="statusReportStore.loadInbox" />

    <EmptyState
      v-else-if="statusReportStore.reports.length === 0"
      :icon="Inbox"
      title="Inbox is empty"
      description="No status reports are waiting for review."
    />

    <div v-else class="flex flex-col gap-3">
      <Card v-for="report in statusReportStore.reports" :key="report.id">
        <div class="flex flex-col gap-3 tablet:flex-row tablet:items-start tablet:justify-between">
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <p class="text-sm font-semibold text-neutral-800">{{ report.reportNo }}</p>
              <StatusBadge label="Pending" variant="warning" size="sm" />
            </div>
            <p class="mt-0.5 text-sm text-neutral-600">{{ report.projectName }}</p>
            <p class="text-xs text-neutral-400">
              {{ report.engineerName }} · {{ formatDate(report.reportDate) }}
              <span v-if="report.receiptType"> · {{ report.receiptType }}</span>
            </p>
            <p class="mt-2 whitespace-pre-wrap text-sm text-neutral-700" dir="auto">{{ report.notes }}</p>
          </div>
          <BaseButton size="sm" :icon="Paperclip" class="shrink-0" @click="openAttachDialog(report)">
            Attach
          </BaseButton>
        </div>
      </Card>
    </div>

    <BaseDialog v-model="isAttachDialogOpen" title="Attach to Project" size="md">
      <div v-if="selectedReport" class="flex flex-col gap-4">
        <div class="rounded-lg bg-bg-secondary p-3 text-sm">
          <p class="font-medium text-neutral-800">{{ selectedReport.projectName }}</p>
          <p class="text-xs text-neutral-500">
            {{ selectedReport.reportNo }} · {{ selectedReport.engineerName }} · {{ formatDate(selectedReport.reportDate) }}
          </p>
        </div>

        <SelectBox
          v-model="attachTaskId"
          label="Task (optional)"
          placeholder="No specific task"
          :disabled="isLoadingTasks"
          :options="taskOptions"
        />

        <TextArea v-model="attachNotes" label="Notes" placeholder="Brief note for the project timeline..." :rows="3" required />
      </div>

      <template #footer>
        <BaseButton variant="secondary" @click="isAttachDialogOpen = false">Cancel</BaseButton>
        <BaseButton :icon="CheckCircle2" :loading="isSaving" @click="handleAttach">Attach to Project</BaseButton>
      </template>
    </BaseDialog>
  </div>
</template>
