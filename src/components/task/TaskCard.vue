<script setup lang="ts">
import { AlertTriangle, ArrowLeft, ArrowRight } from '@lucide/vue'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import Avatar from '@/components/common/Avatar.vue'
import IconButton from '@/components/common/IconButton.vue'
import ProjectSummaryDialog from '@/components/project/ProjectSummaryDialog.vue'
import TeamMemberWorkloadDialog from '@/components/task/TeamMemberWorkloadDialog.vue'
import { useLocale } from '@/composables/useLocale'
import { formatTaskDueDateTime, getNextTaskStatus, isTaskOverdue } from '@/utils/taskHelpers'
import type { Task, TaskStatus } from '@/types/Task'

const props = defineProps<{
  task: Task
  projectName: string
  clientName: string
}>()

const emit = defineEmits<{
  open: [taskId: string]
  advance: [taskId: string]
}>()

const { t } = useI18n()
const { isRtl } = useLocale()

// Points the way this action moves the task forward, which flips with
// reading direction.
const advanceIcon = computed(() => (isRtl.value ? ArrowLeft : ArrowRight))

const overdue = computed(() => isTaskOverdue(props.task))
const nextStatus = computed(() => getNextTaskStatus(props.task.status))

const STATUS_LABEL_KEYS: Record<TaskStatus, string> = {
  Preset: 'task.status.preset',
  Pending: 'task.status.pending',
  'In Progress': 'task.status.inProgress',
  Completed: 'task.status.completed',
}

const moveToLabel = computed(() => (nextStatus.value ? t('task.moveTo', { status: t(STATUS_LABEL_KEYS[nextStatus.value]) }) : ''))

// Project name and assignee were previously inert text on the card --
// each now pops its own quick-look dialog (project summary / team
// member workload) instead of requiring a trip to the Projects or Tasks
// page to see what else is going on with either of them.
const isProjectDialogOpen = ref(false)
const isMemberDialogOpen = ref(false)
</script>

<template>
  <div
    class="flex cursor-pointer flex-col gap-3 rounded-xl border border-border-light bg-bg-card p-4 shadow-soft transition-shadow duration-normal hover:shadow-medium"
    @click="emit('open', task.id)"
  >
    <div class="flex items-start justify-between gap-2">
      <p class="text-sm font-semibold leading-snug text-text-primary">{{ task.title }}</p>
    </div>

    <p class="truncate text-xs text-text-muted">
      <button
        type="button"
        class="hover:text-primary-700 hover:underline"
        @click.stop="isProjectDialogOpen = true"
      >{{ projectName }}</button>
      &middot; {{ clientName }}
    </p>

    <p v-if="task.status === 'Preset'" class="flex items-center gap-1 text-xs font-medium text-warning-700">
      <AlertTriangle class="h-3.5 w-3.5 shrink-0" />
      <span>{{ t('task.presetFlag') }}</span>
    </p>

    <div class="flex items-center justify-between">
      <button type="button" class="flex items-center gap-2" @click.stop="isMemberDialogOpen = true">
        <Avatar :name="task.assignedTo" size="sm" />
        <span class="text-xs text-text-secondary hover:text-primary-700 hover:underline">{{ task.assignedTo }}</span>
      </button>

      <span class="text-xs font-medium" :class="overdue ? 'text-danger-700' : 'text-text-muted'">
        {{ formatTaskDueDateTime(task) }}
      </span>
    </div>

    <IconButton
      v-if="nextStatus"
      :icon="advanceIcon"
      :label="moveToLabel"
      size="sm"
      variant="primary"
      class="self-end"
      @click.stop="emit('advance', task.id)"
    />
  </div>

  <ProjectSummaryDialog v-model="isProjectDialogOpen" :project-id="task.projectId" />
  <TeamMemberWorkloadDialog v-model="isMemberDialogOpen" :member-name="task.assignedTo" />
</template>
