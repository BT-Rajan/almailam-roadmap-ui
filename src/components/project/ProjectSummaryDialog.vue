<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseDialog from '@/components/common/BaseDialog.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ClientProjectDocumentsPanel from '@/components/client/ClientProjectDocumentsPanel.vue'
import TeamMemberWorkloadDialog from '@/components/task/TeamMemberWorkloadDialog.vue'
import TaskStatusBadge from '@/components/task/TaskStatusBadge.vue'
import { taskService } from '@/services/taskService'
import { useProjectStore } from '@/stores/projectStore'
import { useUserStore } from '@/stores/userStore'
import { getProjectStatusVariant, getWorkflowStageLabelKey } from '@/utils/projectHelpers'
import type { Task } from '@/types/Task'

const props = defineProps<{
  modelValue: boolean
  projectId?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const { t } = useI18n()
const projectStore = useProjectStore()
const userStore = useUserStore()

const isLoading = ref(false)
const projectTasks = ref<Task[]>([])
const selectedMemberName = ref<string>()
const isMemberDialogOpen = ref(false)

const project = computed(() => (props.projectId ? projectStore.getProjectById(props.projectId) : undefined))
const client = computed(() => (project.value ? projectStore.getClientById(project.value.clientId) : undefined))

async function loadData(): Promise<void> {
  if (!props.projectId) return
  isLoading.value = true
  try {
    const [allTasks] = await Promise.all([taskService.getTasks(), projectStore.loadProjects(), userStore.users.length === 0 ? userStore.loadUsers() : Promise.resolve()])
    projectTasks.value = allTasks.filter((task) => task.projectId === props.projectId)
  } finally {
    isLoading.value = false
  }
}

watch(
  () => [props.modelValue, props.projectId] as const,
  ([isOpen]) => {
    if (isOpen) void loadData()
  },
)

const ROLE_LABEL_KEYS: Record<string, string> = {
  Administrator: 'administration.userRole.administrator',
  'Project Manager': 'administration.userRole.projectManager',
  Engineer: 'administration.userRole.engineer',
  'Document Controller': 'administration.userRole.documentController',
  Viewer: 'administration.userRole.viewer',
}

function roleLabelFor(name: string): string {
  const role = userStore.users.find((user) => user.name === name)?.role
  return role ? (ROLE_LABEL_KEYS[role] ? t(ROLE_LABEL_KEYS[role]) : role) : t('project.summaryDialog.teamMemberRole')
}

interface TeamMemberRow {
  name: string
  role: string
  completed: number
  inProgress: number
  pending: number
}

// Team = the project's own engineer, plus everyone with at least one
// task on this project -- not just task assignees, so the engineer of
// record still shows even before any task has been created.
const teamMembers = computed<TeamMemberRow[]>(() => {
  if (!project.value) return []
  const rows = new Map<string, TeamMemberRow>()
  function ensure(name: string): TeamMemberRow {
    let row = rows.get(name)
    if (!row) {
      row = { name, role: roleLabelFor(name), completed: 0, inProgress: 0, pending: 0 }
      rows.set(name, row)
    }
    return row
  }
  ensure(project.value.engineer)
  for (const task of projectTasks.value) {
    const row = ensure(task.assignedTo)
    if (task.status === 'Completed') row.completed += 1
    else if (task.status === 'In Progress') row.inProgress += 1
    else row.pending += 1
  }
  return [...rows.values()].sort((a, b) => a.name.localeCompare(b.name))
})

const STATUS_LABEL_KEYS_PROJECT: Record<string, string> = {
  Active: 'project.status.active',
  'On Hold': 'project.status.onHold',
  Cancelled: 'project.status.cancelled',
  Completed: 'project.status.completed',
}
function projectStatusLabel(status: string): string {
  return t(STATUS_LABEL_KEYS_PROJECT[status] ?? status)
}

function openMember(name: string): void {
  selectedMemberName.value = name
  isMemberDialogOpen.value = true
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="project ? `${project.projectNo} \u2013 ${project.projectName}` : undefined"
    size="lg"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <SkeletonLoader v-if="isLoading || !project" :rows="5" />

    <div v-else class="flex flex-col gap-6">
      <div class="flex flex-wrap items-center gap-2">
        <StatusBadge :label="t(getWorkflowStageLabelKey(project.currentStage))" variant="primary" />
        <StatusBadge :label="projectStatusLabel(project.status)" :variant="getProjectStatusVariant(project.status)" />
        <span v-if="client" class="text-sm text-text-muted">{{ client.companyName }}</span>
      </div>

      <section class="flex flex-col gap-3">
        <h3 class="text-sm font-semibold text-text-primary">{{ t('project.summaryDialog.teamTitle') }}</h3>
        <ul class="flex flex-col divide-y divide-border-light rounded-lg border border-border-light">
          <li v-for="member in teamMembers" :key="member.name" class="flex items-center justify-between gap-3 px-3 py-2.5">
            <button
              type="button"
              class="text-start text-sm font-medium text-text-primary hover:text-primary-700 hover:underline"
              @click="openMember(member.name)"
            >
              {{ member.name }}
              <span class="ml-1 font-normal text-text-muted">&middot; {{ member.role }}</span>
            </button>
            <span class="shrink-0 text-xs text-text-muted">
              {{
                t('project.summaryDialog.memberTaskCounts', {
                  completed: member.completed,
                  inProgress: member.inProgress,
                  pending: member.pending,
                })
              }}
            </span>
          </li>
        </ul>
      </section>

      <section class="flex flex-col gap-3">
        <h3 class="text-sm font-semibold text-text-primary">{{ t('project.summaryDialog.tasksTitle') }}</h3>
        <ul v-if="projectTasks.length > 0" class="flex flex-col divide-y divide-border-light rounded-lg border border-border-light">
          <li v-for="task in projectTasks" :key="task.id" class="flex items-center justify-between gap-3 px-3 py-2.5">
            <span class="flex flex-col gap-0.5">
              <span class="text-sm text-text-primary">{{ task.title }}</span>
              <span class="text-xs text-text-muted">{{ task.assignedTo }}</span>
            </span>
            <span class="shrink-0"><TaskStatusBadge :status="task.status" /></span>
          </li>
        </ul>
        <p v-else class="text-sm text-text-muted">{{ t('project.summaryDialog.noTasks') }}</p>
      </section>

      <section class="flex flex-col gap-3">
        <h3 class="text-sm font-semibold text-text-primary">{{ t('client.projectDocuments.title') }}</h3>
        <ClientProjectDocumentsPanel :projects="[project]" bare />
      </section>
    </div>
  </BaseDialog>

  <TeamMemberWorkloadDialog v-model="isMemberDialogOpen" :member-name="selectedMemberName" />
</template>
