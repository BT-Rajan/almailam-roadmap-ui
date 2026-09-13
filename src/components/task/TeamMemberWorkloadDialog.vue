<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseDialog from '@/components/common/BaseDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TaskStatusBadge from '@/components/task/TaskStatusBadge.vue'
import ProjectSummaryDialog from '@/components/project/ProjectSummaryDialog.vue'
import { taskService } from '@/services/taskService'
import { useProjectStore } from '@/stores/projectStore'
import { useUserStore } from '@/stores/userStore'
import { formatDate } from '@/utils/dateFormatter'
import { getWorkflowStageLabelKey } from '@/utils/projectHelpers'
import { withSalutationByName } from '@/utils/userHelpers'
import type { Task } from '@/types/Task'

const props = defineProps<{
  modelValue: boolean
  memberName?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const { t } = useI18n()
const projectStore = useProjectStore()
const userStore = useUserStore()

const isLoading = ref(false)
const memberTasks = ref<Task[]>([])
const selectedProjectId = ref<string>()
const isProjectDialogOpen = ref(false)

// title shown on the dialog -- the bare memberName plus whatever
// salutation (Mr./Ms.) is on file for them, same lookup used everywhere
// else a plain name string gets this treatment (see withSalutationByName).
const dialogTitle = computed(() => (props.memberName ? withSalutationByName(props.memberName, userStore.users) : undefined))

async function loadData(): Promise<void> {
  isLoading.value = true
  try {
    const [allTasks] = await Promise.all([
      taskService.getTasks(),
      projectStore.loadProjects(),
      userStore.users.length === 0 ? userStore.loadUsers() : Promise.resolve(),
    ])
    memberTasks.value = allTasks.filter((task) => task.assignedTo === props.memberName)
  } finally {
    isLoading.value = false
  }
}

watch(
  () => [props.modelValue, props.memberName] as const,
  ([isOpen]) => {
    if (isOpen) void loadData()
  },
)

// Every project this person touches -- either named as the project's own
// engineer, or holding at least one task in it -- not just the ones
// their tasks happen to be in, so a project they're the engineer of but
// have no tasks on yet still shows up.
const involvedProjects = computed(() => {
  if (!props.memberName) return []
  const taskProjectIds = new Set(memberTasks.value.map((task) => task.projectId))
  return projectStore.projects
    .filter((project) => project.engineer === props.memberName || taskProjectIds.has(project.id))
    .sort((a, b) => a.projectNo.localeCompare(b.projectNo))
})

function taskCountForProject(projectId: string, status: Task['status']): number {
  return memberTasks.value.filter((task) => task.projectId === projectId && task.status === status).length
}

const completedTasks = computed(() => memberTasks.value.filter((task) => task.status === 'Completed'))
const inProgressTasks = computed(() => memberTasks.value.filter((task) => task.status === 'In Progress'))
// 'Preset' is still an unreviewed to-do from this person's point of view
// -- grouped with 'Pending' rather than given its own section here.
const pendingTasks = computed(() => memberTasks.value.filter((task) => task.status === 'Pending' || task.status === 'Preset'))

function projectName(projectId: string): string {
  return projectStore.getProjectById(projectId)?.projectName ?? t('task.unknownProject')
}

function openProject(projectId: string): void {
  selectedProjectId.value = projectId
  isProjectDialogOpen.value = true
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="dialogTitle"
    size="lg"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <SkeletonLoader v-if="isLoading" :rows="5" />

    <div v-else class="flex flex-col gap-6">
      <section class="flex flex-col gap-3">
        <h3 class="text-sm font-semibold text-text-primary">{{ t('task.workloadDialog.projectsTitle') }}</h3>
        <EmptyState
          v-if="involvedProjects.length === 0"
          :title="t('task.workloadDialog.noProjectsTitle')"
          :description="t('task.workloadDialog.noProjectsDescription')"
        />
        <ul v-else class="flex flex-col divide-y divide-border-light rounded-lg border border-border-light">
          <li v-for="project in involvedProjects" :key="project.id" class="flex flex-col gap-1.5 px-3 py-2.5">
            <div class="flex items-center justify-between gap-3">
              <button
                type="button"
                class="text-start text-sm font-medium text-text-primary hover:text-primary-700 hover:underline"
                @click="openProject(project.id)"
              >
                {{ project.projectNo }} &ndash; {{ project.projectName }}
              </button>
              <StatusBadge :label="t(getWorkflowStageLabelKey(project.currentStage))" variant="primary" size="sm" />
            </div>
            <p class="text-xs text-text-muted">
              {{
                t('task.workloadDialog.projectTaskCounts', {
                  completed: taskCountForProject(project.id, 'Completed'),
                  inProgress: taskCountForProject(project.id, 'In Progress'),
                  pending: taskCountForProject(project.id, 'Pending') + taskCountForProject(project.id, 'Preset'),
                })
              }}
            </p>
          </li>
        </ul>
      </section>

      <section class="flex flex-col gap-3">
        <h3 class="text-sm font-semibold text-text-primary">{{ t('task.workloadDialog.activitiesTitle') }}</h3>
        <EmptyState
          v-if="memberTasks.length === 0"
          :title="t('task.workloadDialog.noActivitiesTitle')"
          :description="t('task.workloadDialog.noActivitiesDescription')"
        />
        <div v-else class="flex flex-col gap-4">
          <div
            v-for="group in [
              { label: t('task.workloadDialog.inProgressGroup'), tasks: inProgressTasks },
              { label: t('task.workloadDialog.pendingGroup'), tasks: pendingTasks },
              { label: t('task.workloadDialog.completedGroup'), tasks: completedTasks },
            ]"
            :key="group.label"
          >
            <template v-if="group.tasks.length > 0">
              <p class="mb-1.5 text-xs font-medium uppercase tracking-wide text-text-muted">{{ group.label }} ({{ group.tasks.length }})</p>
              <ul class="flex flex-col divide-y divide-border-light rounded-lg border border-border-light">
                <li v-for="task in group.tasks" :key="task.id" class="flex items-center justify-between gap-3 px-3 py-2.5">
                  <span class="flex flex-col gap-0.5">
                    <span class="text-sm text-text-primary">{{ task.title }}</span>
                    <span class="text-xs text-text-muted">{{ projectName(task.projectId) }} &middot; {{ formatDate(task.dueDate) }}</span>
                  </span>
                  <TaskStatusBadge :status="task.status" />
                </li>
              </ul>
            </template>
          </div>
        </div>
      </section>
    </div>
  </BaseDialog>

  <ProjectSummaryDialog v-model="isProjectDialogOpen" :project-id="selectedProjectId" />
</template>
