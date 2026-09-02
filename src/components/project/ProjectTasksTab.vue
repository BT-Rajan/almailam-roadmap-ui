<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TaskDetails from '@/components/task/TaskDetails.vue'
import TaskFormDialog from '@/components/task/TaskFormDialog.vue'
import TaskList from '@/components/task/TaskList.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import type { TaskInput } from '@/services/taskService'
import { useClientStore } from '@/stores/clientStore'
import { useTaskStore } from '@/stores/taskStore'
import { useToastStore } from '@/stores/toastStore'
import type { Project } from '@/types/Project'
import type { TaskPriority, TaskStatus } from '@/types/Task'
import { useUserStore } from '@/stores/userStore'

const props = defineProps<{
  project: Project
}>()

const router = useRouter()
const taskStore = useTaskStore()
const toastStore = useToastStore()
const userStore = useUserStore()
const clientStore = useClientStore()
onMounted(() => {
  if (clientStore.clients.length === 0) clientStore.loadClients()
})

const projectTasks = computed(() => taskStore.tasksByProject(props.project.id))
// Every task on this tab belongs to this one project, so its client is
// fixed too -- no need to resolve per-task like the cross-project Task
// Board/My Tasks views do.
const clientName = computed(() => clientStore.getClientById(props.project.clientId)?.companyName ?? 'Unknown Client')

type PendingChange =
  | { kind: 'status'; value: TaskStatus }
  | { kind: 'priority'; value: TaskPriority }
  | { kind: 'reassign'; value: string }

const isConfirmDialogOpen = ref(false)
const isConfirmSaving = ref(false)
const pendingChange = ref<PendingChange | null>(null)

const confirmDialogTitle = computed(() => {
  if (!pendingChange.value) return ''
  return { status: 'Change status', priority: 'Change priority', reassign: 'Reassign task' }[pendingChange.value.kind]
})

const confirmDialogMessage = computed(() => {
  if (!pendingChange.value || !taskStore.selectedTask) return ''
  const task = taskStore.selectedTask
  switch (pendingChange.value.kind) {
    case 'status':
      return `Change "${task.title}" from ${task.status} to ${pendingChange.value.value}?`
    case 'priority':
      return `Change the priority of "${task.title}" from ${task.priority} to ${pendingChange.value.value}?`
    case 'reassign': {
      const nextAssignee = userStore.users.find((user) => user.id === pendingChange.value?.value)?.name ?? 'this user'
      return `Reassign "${task.title}" from ${task.assignedTo} to ${nextAssignee}?`
    }
    default:
      return ''
  }
})

function requestStatusChange(status: TaskStatus): void {
  pendingChange.value = { kind: 'status', value: status }
  isConfirmDialogOpen.value = true
}

function requestPriorityChange(priority: TaskPriority): void {
  pendingChange.value = { kind: 'priority', value: priority }
  isConfirmDialogOpen.value = true
}

function requestReassign(assigneeUserId: string): void {
  pendingChange.value = { kind: 'reassign', value: assigneeUserId }
  isConfirmDialogOpen.value = true
}

async function handleConfirmPendingChange(): Promise<void> {
  if (!pendingChange.value) return
  isConfirmSaving.value = true
  try {
    if (pendingChange.value.kind === 'status') {
      await handleStatusChange(pendingChange.value.value)
    } else if (pendingChange.value.kind === 'priority') {
      await handlePriorityChange(pendingChange.value.value)
    } else {
      await handleReassign(pendingChange.value.value)
    }
    isConfirmDialogOpen.value = false
  } finally {
    isConfirmSaving.value = false
  }
}

const isDrawerOpen = computed({
  get: () => Boolean(taskStore.selectedTaskId),
  set: (value: boolean) => {
    if (!value) taskStore.clearSelectedTask()
  },
})

const isCreateDialogOpen = ref(false)

async function handleCreateTask(input: TaskInput): Promise<void> {
  try {
    const task = await taskStore.createTask(input)
    toastStore.show('success', 'Task created', `"${task.title}" was assigned to ${task.assignedTo}.`)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to create task', detail)
  }
}

// These now make a real backend call (see taskStore.ts) where they
// previously only mutated local state and could never fail -- errors
// need surfacing now that they're genuinely possible (an invalid
// status transition, a network issue, and so on).
async function handleStatusChange(status: TaskStatus): Promise<void> {
  if (!taskStore.selectedTaskId) return
  try {
    await taskStore.updateTaskStatus(taskStore.selectedTaskId, status)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to update status', detail)
  }
}

async function handlePriorityChange(priority: TaskPriority): Promise<void> {
  if (!taskStore.selectedTaskId) return
  try {
    await taskStore.updateTaskPriority(taskStore.selectedTaskId, priority)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to update priority', detail)
  }
}

async function handleReassign(assignee: string): Promise<void> {
  if (!taskStore.selectedTaskId) return
  try {
    await taskStore.updateTaskAssignee(taskStore.selectedTaskId, assignee)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to reassign task', detail)
  }
}
</script>

<template>
  <div class="flex items-center justify-between no-print">
    <BaseButton size="sm" :icon="Plus" @click="isCreateDialogOpen = true">New Task</BaseButton>
    <BaseButton variant="ghost" size="sm" @click="router.push({ name: ROUTE_NAMES.TASKS })">
      View Task Board
    </BaseButton>
  </div>

  <div v-if="taskStore.isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
    <SkeletonLoader :rows="6" />
  </div>

  <ErrorState v-else-if="taskStore.error" :description="taskStore.error" @retry="taskStore.loadTasks" />

  <TaskList
    v-else
    :tasks="projectTasks"
    :get-project-by-id="taskStore.getProjectById"
    :get-client-name-by-project-id="() => clientName"
    @open="taskStore.selectTask"
  />

  <TaskFormDialog
    v-model="isCreateDialogOpen"
    :projects="[project]"
    :default-project-id="project.id"
    @create="handleCreateTask"
  />

  <BaseDrawer v-model="isDrawerOpen" :title="taskStore.selectedTask?.id" width="md">
    <TaskDetails
      v-if="taskStore.selectedTask"
      :task="taskStore.selectedTask"
      :project-name="project.projectName"
      :client-name="clientName"
      @status-change="requestStatusChange"
      @priority-change="requestPriorityChange"
      @reassign="requestReassign"
    />
  </BaseDrawer>

  <ConfirmationDialog
    v-model="isConfirmDialogOpen"
    :title="confirmDialogTitle"
    :message="confirmDialogMessage"
    confirm-label="Confirm"
    :loading="isConfirmSaving"
    @confirm="handleConfirmPendingChange"
  />
</template>
