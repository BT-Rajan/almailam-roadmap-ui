<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TablePagination from '@/components/common/TablePagination.vue'
import TaskDetails from '@/components/task/TaskDetails.vue'
import TaskFormDialog from '@/components/task/TaskFormDialog.vue'
import TaskList from '@/components/task/TaskList.vue'
import { usePagination } from '@/composables/usePagination'
import type { TaskInput } from '@/services/taskService'
import { useClientStore } from '@/stores/clientStore'
import { useProjectStore } from '@/stores/projectStore'
import { useTaskStore } from '@/stores/taskStore'
import { useToastStore } from '@/stores/toastStore'
import type { Project, WorkflowStage } from '@/types/Project'
import type { TaskStatus } from '@/types/Task'
import { useUserStore } from '@/stores/userStore'

const props = defineProps<{
  project: Project
  // Which stage's Tasks tab this is -- Design/Supervision/Government
  // Submission each auto-create one system task per selected service
  // (see project_service.create_service_tasks and Task.selectedActivityId/
  // selectedPermitId/selectedSupervisionActivityId), as parallel tracks
  // that can all be active on the same project at once. When set to one
  // of those three, this tab scopes to that track's own service tasks
  // plus any plain, unlinked task -- not another track's service tasks
  // mixed in. Omitted (or any other stage) shows every project task
  // unfiltered, same as before.
  stageContext?: WorkflowStage
}>()

const taskStore = useTaskStore()
const projectStore = useProjectStore()
const toastStore = useToastStore()
const userStore = useUserStore()
const clientStore = useClientStore()
const { t } = useI18n()
onMounted(() => {
  if (clientStore.clients.length === 0) clientStore.loadClients()
})

const projectTasks = computed(() => taskStore.tasksByProject(props.project.id))
const scopedProjectTasks = computed(() => {
  switch (props.stageContext) {
    case 'Design':
      return projectTasks.value.filter((task) => !task.selectedPermitId && !task.selectedSupervisionActivityId)
    case 'Supervision':
      return projectTasks.value.filter((task) => !task.selectedActivityId && !task.selectedPermitId)
    case 'Government Submission':
      return projectTasks.value.filter((task) => !task.selectedActivityId && !task.selectedSupervisionActivityId)
    default:
      return projectTasks.value
  }
})
// Every other list in the app uses this same usePagination/
// TablePagination.vue pair -- sliced client-side against the tasks
// already loaded into taskStore.
const { currentPage, pageSize, totalItems, totalPages, startIndex, endIndex, goToPage, setPageSize, resetPage } =
  usePagination(() => scopedProjectTasks.value.length)
const pagedProjectTasks = computed(() => scopedProjectTasks.value.slice(startIndex.value, endIndex.value))
watch(scopedProjectTasks, () => resetPage())
// Every task on this tab belongs to this one project, so its client is
// fixed too -- no need to resolve per-task like the cross-project Task
// Board/My Tasks views do.
const clientName = computed(() => clientStore.getClientById(props.project.clientId)?.companyName ?? t('project.unknownClient'))

type PendingChange =
  | { kind: 'status'; value: TaskStatus }
  | { kind: 'reassign'; value: string }
  | { kind: 'delete' }

const isConfirmDialogOpen = ref(false)
const isConfirmSaving = ref(false)
const pendingChange = ref<PendingChange | null>(null)

const confirmDialogTitle = computed(() => {
  if (!pendingChange.value) return ''
  return {
    status: t('project.tasksTab.changeStatusTitle'),
    reassign: t('project.tasksTab.reassignTaskTitle'),
    delete: t('project.tasksTab.deleteTaskTitle'),
  }[pendingChange.value.kind]
})

const confirmDialogMessage = computed(() => {
  if (!pendingChange.value || !taskStore.selectedTask) return ''
  const task = taskStore.selectedTask
  switch (pendingChange.value.kind) {
    case 'status':
      return t('project.tasksTab.changeStatusMessage', { title: task.title, from: task.status, to: pendingChange.value.value })
    case 'reassign': {
      const assigneeUserId = pendingChange.value.value
      const nextAssignee = userStore.users.find((user) => user.id === assigneeUserId)?.name ?? t('project.tasksTab.thisUser')
      return t('project.tasksTab.reassignTaskMessage', { title: task.title, from: task.assignedTo, to: nextAssignee })
    }
    case 'delete':
      return t('project.tasksTab.deleteTaskMessage', { title: task.title })
    default:
      return ''
  }
})

function requestStatusChange(status: TaskStatus): void {
  pendingChange.value = { kind: 'status', value: status }
  isConfirmDialogOpen.value = true
}

function requestReassign(assigneeUserId: string): void {
  pendingChange.value = { kind: 'reassign', value: assigneeUserId }
  isConfirmDialogOpen.value = true
}

function requestDelete(): void {
  pendingChange.value = { kind: 'delete' }
  isConfirmDialogOpen.value = true
}

const confirmDialogVariant = computed(() => (pendingChange.value?.kind === 'delete' ? 'danger' : 'primary'))

async function handleConfirmPendingChange(): Promise<void> {
  if (!pendingChange.value) return
  isConfirmSaving.value = true
  try {
    if (pendingChange.value.kind === 'status') {
      await handleStatusChange(pendingChange.value.value)
    } else if (pendingChange.value.kind === 'reassign') {
      await handleReassign(pendingChange.value.value)
    } else {
      await handleDeleteTask()
    }
    isConfirmDialogOpen.value = false
  } finally {
    isConfirmSaving.value = false
  }
}

const isTaskDialogOpen = computed({
  get: () => Boolean(taskStore.selectedTaskId),
  set: (value: boolean) => {
    if (!value) taskStore.clearSelectedTask()
  },
})

const isCreateDialogOpen = ref(false)

async function handleCreateTask(input: TaskInput): Promise<void> {
  try {
    const task = await taskStore.createTask(input)
    toastStore.show('success', t('project.tasksTab.taskCreatedTitle'), t('project.tasksTab.taskCreatedDescription', { title: task.title, assignee: task.assignedTo }))
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('project.tasksTab.failedToCreateTask'), detail)
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
    // Completing a task can be exactly what closes the last open item
    // under a Design activity/Permit/Supervision activity (see backend
    // task_service.set_status -> maybe_auto_close_design_activity/
    // maybe_auto_close_permit/maybe_auto_close_supervision_activity),
    // which can itself be what the project's stage was waiting on --
    // none of that reaches this tab's own project prop on its own since
    // taskStore only ever mutates its own task list, never the project
    // store. Refresh so the stepper/tabs/handover checklist elsewhere
    // on this page reflect it immediately instead of only catching up
    // whenever something else happens to reload the project.
    if (status === 'Completed') await projectStore.refreshProject(props.project.id)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('project.tasksTab.failedToUpdateStatus'), detail)
  }
}

async function handleReassign(assignee: string): Promise<void> {
  if (!taskStore.selectedTaskId) return
  try {
    await taskStore.updateTaskAssignee(taskStore.selectedTaskId, assignee)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('project.tasksTab.failedToReassignTask'), detail)
  }
}

// Same treatment as reassign/schedule changes just above -- a title
// correction is routine, no confirmation step.
async function handleTitleChange(title: string): Promise<void> {
  if (!taskStore.selectedTaskId) return
  try {
    await taskStore.updateTaskTitle(taskStore.selectedTaskId, title)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('project.tasksTab.failedToUpdateTitle'), detail)
  }
}

// Applied directly, no confirmation step -- a schedule tweak is routine,
// same treatment as reassigning a task's owner just above (only status/
// delete go through the confirm dialog here).
async function handleStartDateChange(startDate: string): Promise<void> {
  if (!taskStore.selectedTaskId) return
  try {
    await taskStore.updateTaskStartDate(taskStore.selectedTaskId, startDate)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('project.tasksTab.failedToUpdateSchedule'), detail)
  }
}

async function handleDueDateChange(dueDate: string): Promise<void> {
  if (!taskStore.selectedTaskId) return
  try {
    await taskStore.updateTaskDueDate(taskStore.selectedTaskId, dueDate)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('project.tasksTab.failedToUpdateSchedule'), detail)
  }
}

async function handleDueTimeChange(dueTime: string): Promise<void> {
  if (!taskStore.selectedTaskId) return
  try {
    await taskStore.updateTaskDueTime(taskStore.selectedTaskId, dueTime)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('project.tasksTab.failedToUpdateSchedule'), detail)
  }
}

async function handleDeleteTask(): Promise<void> {
  if (!taskStore.selectedTaskId) return
  const title = taskStore.selectedTask?.title ?? ''
  try {
    await taskStore.deleteTask(taskStore.selectedTaskId)
    toastStore.show('success', t('project.tasksTab.taskDeletedTitle'), t('project.tasksTab.taskDeletedDescription', { title }))
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('project.tasksTab.failedToDeleteTask'), detail)
  }
}
</script>

<template>
  <div class="flex items-center justify-end no-print">
    <BaseButton size="sm" :icon="Plus" @click="isCreateDialogOpen = true">{{ t('project.tasksTab.newTask') }}</BaseButton>
  </div>

  <div v-if="taskStore.isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
    <SkeletonLoader :rows="6" />
  </div>

  <ErrorState v-else-if="taskStore.error" :description="taskStore.error" @retry="taskStore.loadTasks" />

  <TaskList
    v-else
    :tasks="pagedProjectTasks"
    :get-project-by-id="taskStore.getProjectById"
    :get-client-name-by-project-id="() => clientName"
    @open="taskStore.selectTask"
  />
  <TablePagination
    v-if="!taskStore.isLoading && !taskStore.error && totalItems > 0"
    class="rounded-xl border border-border-light"
    :current-page="currentPage"
    :total-pages="totalPages"
    :total-items="totalItems"
    :start-index="startIndex"
    :end-index="endIndex"
    :page-size="pageSize"
    @page-change="goToPage"
    @page-size-change="setPageSize"
  />

  <TaskFormDialog
    v-model="isCreateDialogOpen"
    :projects="[project]"
    :default-project-id="project.id"
    @create="handleCreateTask"
  />

  <BaseDialog v-model="isTaskDialogOpen" :title="taskStore.selectedTask?.id" size="lg">
    <TaskDetails
      v-if="taskStore.selectedTask"
      :task="taskStore.selectedTask"
      :project-name="project.projectName"
      :client-name="clientName"
      @status-change="requestStatusChange"
      @title-change="handleTitleChange"
      @reassign="requestReassign"
      @start-date-change="handleStartDateChange"
      @due-date-change="handleDueDateChange"
      @due-time-change="handleDueTimeChange"
      @delete="requestDelete"
    />
  </BaseDialog>

  <ConfirmationDialog
    v-model="isConfirmDialogOpen"
    :title="confirmDialogTitle"
    :message="confirmDialogMessage"
    confirm-label="Confirm"
    :confirm-variant="confirmDialogVariant"
    :loading="isConfirmSaving"
    @confirm="handleConfirmPendingChange"
  />
</template>
