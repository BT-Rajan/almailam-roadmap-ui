<script setup lang="ts">
import { CheckCircle2, Inbox, Paperclip } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

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

const { t } = useI18n()
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
    <PageHeader :title="t('report.inboxPage.pageTitle')" :subtitle="t('report.inboxPage.pageSubtitle')" />

    <div v-if="statusReportStore.isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="6" />
    </div>

    <ErrorState v-else-if="statusReportStore.error" :description="statusReportStore.error" @retry="statusReportStore.loadInbox" />

    <EmptyState
      v-else-if="statusReportStore.reports.length === 0"
      :icon="Inbox"
      :title="t('report.inboxPage.inboxEmpty')"
      :description="t('report.inboxPage.inboxEmptyDescription')"
    />

    <div v-else class="flex flex-col gap-3">
      <Card v-for="report in statusReportStore.reports" :key="report.id">
        <div class="flex flex-col gap-3 tablet:flex-row tablet:items-start tablet:justify-between">
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <p class="text-sm font-semibold text-text-primary">{{ report.reportNo }}</p>
              <StatusBadge :label="t('report.inboxPage.pending')" variant="warning" size="sm" />
            </div>
            <p class="mt-0.5 text-sm text-text-secondary">{{ report.projectName }}</p>
            <p class="text-xs text-text-muted">
              {{ report.engineerName }} · {{ formatDate(report.reportDate) }}
              <span v-if="report.receiptType"> · {{ report.receiptType }}</span>
            </p>
            <p class="mt-2 whitespace-pre-wrap text-sm text-text-secondary" dir="auto">{{ report.notes }}</p>
          </div>
          <BaseButton size="sm" :icon="Paperclip" class="shrink-0" @click="openAttachDialog(report)">
            {{ t('report.inboxPage.attach') }}
          </BaseButton>
        </div>
      </Card>
    </div>

    <BaseDialog v-model="isAttachDialogOpen" :title="t('report.inboxPage.attachToProject')" size="md">
      <div v-if="selectedReport" class="flex flex-col gap-4">
        <div class="rounded-lg bg-bg-secondary p-3 text-sm">
          <p class="font-medium text-text-primary">{{ selectedReport.projectName }}</p>
          <p class="text-xs text-text-muted">
            {{ selectedReport.reportNo }} · {{ selectedReport.engineerName }} · {{ formatDate(selectedReport.reportDate) }}
          </p>
        </div>

        <SelectBox
          v-model="attachTaskId"
          :label="t('report.inboxPage.task')"
          :placeholder="t('report.inboxPage.noSpecificTask')"
          :disabled="isLoadingTasks"
          :options="taskOptions"
        />

        <TextArea v-model="attachNotes" :label="t('report.inboxPage.notes')" :placeholder="t('report.inboxPage.notesPlaceholder')" :rows="3" required />
      </div>

      <template #footer>
        <BaseButton variant="secondary" @click="isAttachDialogOpen = false">{{ t('common.cancel') }}</BaseButton>
        <BaseButton :icon="CheckCircle2" :loading="isSaving" @click="handleAttach">{{ t('report.inboxPage.attachToProject') }}</BaseButton>
      </template>
    </BaseDialog>
  </div>
</template>
