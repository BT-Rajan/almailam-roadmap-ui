<script setup lang="ts">
import { History } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import TablePagination from '@/components/common/TablePagination.vue'
import TextArea from '@/components/common/TextArea.vue'
import { usePagination } from '@/composables/usePagination'
import { useTaskStore } from '@/stores/taskStore'
import { useToastStore } from '@/stores/toastStore'
import type { Task } from '@/types/Task'
import { formatDateTime } from '@/utils/dateFormatter'

// Not a separate "notes" field/concept -- a note is just another entry
// in the task's own history feed (see backend task_service.add_note
// and Task.ts's TaskAuditEvent), same feed as every status change,
// reassignment, and schedule edit already recorded there. Submitting
// one is the only way "notes" exist: there's no persisted "current
// note" on the task itself to overwrite, only an append-only trail of
// everything anyone has written.

const props = defineProps<{ task: Task }>()

const { t } = useI18n()
const taskStore = useTaskStore()
const toastStore = useToastStore()

onMounted(() => {
  if (!(props.task.id in taskStore.auditEventsByTask)) taskStore.loadAuditEvents(props.task.id)
})
watch(
  () => props.task.id,
  (taskId) => {
    if (!(taskId in taskStore.auditEventsByTask)) taskStore.loadAuditEvents(taskId)
  },
)

const events = computed(() => taskStore.auditEventsByTask[props.task.id] ?? [])
// Server already returns newest-first (see audit_service.get_history's
// own ORDER BY) -- re-sorting here would just be redundant work on
// every render for no behavior change.

const { currentPage, pageSize, totalItems, totalPages, startIndex, endIndex, goToPage, setPageSize, resetPage } =
  usePagination(() => events.value.length)
const pagedEvents = computed(() => events.value.slice(startIndex.value, endIndex.value))
watch(events, () => resetPage())

const noteDraft = ref('')
const isSubmitting = ref(false)

async function submitNote(): Promise<void> {
  const trimmed = noteDraft.value.trim()
  if (trimmed.length === 0) return
  isSubmitting.value = true
  try {
    await taskStore.addNote(props.task.id, trimmed)
    noteDraft.value = ''
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('task.historyPanel.failedToAddNote'), detail)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <Card :padded="false">
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ t('task.historyPanel.title') }}</h3>
    </template>

    <div class="flex flex-col gap-2 border-b border-border-light p-4">
      <TextArea
        v-model="noteDraft"
        :placeholder="t('task.historyPanel.notePlaceholder')"
        :rows="2"
        :max-length="4000"
        :disabled="isSubmitting"
      />
      <BaseButton size="sm" class="self-end" :loading="isSubmitting" :disabled="noteDraft.trim().length === 0" @click="submitNote">
        {{ t('task.historyPanel.addNote') }}
      </BaseButton>
    </div>

    <ErrorState v-if="taskStore.historyError" :description="taskStore.historyError" class="p-5" @retry="() => taskStore.loadAuditEvents(task.id)" />

    <EmptyState
      v-else-if="!taskStore.isHistoryLoading && events.length === 0"
      :icon="History"
      :title="t('task.historyPanel.emptyTitle')"
      :description="t('task.historyPanel.emptyDescription')"
      class="p-5"
    />

    <template v-else>
      <ul class="divide-y divide-border-light">
        <li v-for="event in pagedEvents" :key="event.id" class="flex flex-col gap-1 px-4 py-3">
          <div class="flex items-center justify-between gap-3">
            <p class="text-sm font-medium text-text-primary">{{ event.action }}</p>
            <p class="shrink-0 text-xs text-text-muted">{{ formatDateTime(event.timestamp) }}</p>
          </div>
          <p class="text-xs text-text-muted">{{ t('task.historyPanel.by', { user: event.user }) }}</p>
          <p v-if="event.action === 'Note added'" class="whitespace-pre-wrap text-sm text-text-secondary" dir="auto">{{ event.newValue }}</p>
          <p v-else-if="event.previousValue || event.newValue" class="text-xs text-text-secondary">
            <span v-if="event.previousValue">{{ event.previousValue }} → </span>
            <span v-if="event.newValue">{{ event.newValue }}</span>
          </p>
          <p v-if="event.reason" class="text-xs italic text-text-muted">{{ t('task.historyPanel.reason', { reason: event.reason }) }}</p>
        </li>
      </ul>
      <TablePagination
        v-if="totalItems > 0"
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
  </Card>
</template>
