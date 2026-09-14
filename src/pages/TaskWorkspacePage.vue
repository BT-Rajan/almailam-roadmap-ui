<script setup lang="ts">
import { ArrowLeft, ArrowRight } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TaskDetails from '@/components/task/TaskDetails.vue'
import { useLocale } from '@/composables/useLocale'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useProjectStore } from '@/stores/projectStore'
import { useTaskStore } from '@/stores/taskStore'
import { useToastStore } from '@/stores/toastStore'
import { useUserStore } from '@/stores/userStore'
import type { TaskStatus } from '@/types/Task'

// This page replaces four near-identical copies of "BaseDialog +
// TaskDetails + a handful of status/title/reassign/schedule handlers"
// that used to live in TasksPage.vue, MyTasksPage.vue,
// ProjectTasksTab.vue, and ActivityCalendarPage.vue -- one shared,
// route-addressable workspace instead, same idea as
// ClientWorkspacePage/ProjectWorkspacePage/SubmissionWorkspacePage.
// Each of those four now just navigates here with router.push instead
// of opening its own dialog.

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { isRtl } = useLocale()
const taskStore = useTaskStore()
const projectStore = useProjectStore()
const userStore = useUserStore()
const toastStore = useToastStore()

const backIcon = computed(() => (isRtl.value ? ArrowRight : ArrowLeft))
const taskId = computed(() => route.params.taskId as string)

// Present only when this page was opened from a project's own Tasks
// tab (ProjectTasksTab.vue) -- carried in the query rather than
// assumed from route history, so a hard refresh or a shared link still
// knows where "back" goes and still applies that context's own
// confirm-before-changing behaviour (see handleStatusChange/
// handleReassign below), instead of every entry point silently gaining
// or losing it depending on navigation history.
const originProjectId = computed(() => {
  const value = route.query.projectId
  return typeof value === 'string' ? value : undefined
})

const isLoading = ref(true)
const loadError = ref<string | undefined>(undefined)

async function loadData(): Promise<void> {
  if (taskStore.tasks.length > 0) {
    isLoading.value = false
    return
  }
  isLoading.value = true
  loadError.value = undefined
  try {
    await taskStore.loadTasks()
  } catch {
    loadError.value = t('common.pleaseTryAgain')
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadData()
  if (userStore.users.length === 0) userStore.loadUsers()
})

const task = computed(() => taskStore.tasks.find((item) => item.id === taskId.value))
const projectName = computed(
  () => taskStore.getProjectById(task.value?.projectId ?? '')?.projectName ?? t('task.unknownProject'),
)
const clientName = computed(() => taskStore.getClientNameByProjectId(task.value?.projectId ?? ''))

function goBack(): void {
  if (originProjectId.value) {
    router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId: originProjectId.value } })
    return
  }
  router.push({ name: ROUTE_NAMES.TASKS })
}

// -- Status / reassign ---------------------------------------------------
// Opened from a project's own Tasks tab, a status or reassign change can
// be exactly what closes out a Design/Permit/Supervision activity (see
// backend task_service.set_status), so that context confirms first and
// refreshes the project afterwards so the stepper/handover checklist
// elsewhere on that page catch up immediately -- ProjectTasksTab.vue
// always did this. Opened any other way (Task Board, My Tasks, Activity
// Calendar), it applies immediately, same as those always did.
type PendingChange = { kind: 'status'; value: TaskStatus } | { kind: 'reassign'; value: string }
const isConfirmDialogOpen = ref(false)
const isConfirmSaving = ref(false)
const pendingChange = ref<PendingChange | null>(null)

const confirmDialogTitle = computed(() => {
  if (!pendingChange.value) return ''
  return pendingChange.value.kind === 'status' ? t('project.tasksTab.changeStatusTitle') : t('project.tasksTab.reassignTaskTitle')
})

const confirmDialogMessage = computed(() => {
  if (!pendingChange.value || !task.value) return ''
  if (pendingChange.value.kind === 'status') {
    return t('project.tasksTab.changeStatusMessage', {
      title: task.value.title,
      from: task.value.status,
      to: pendingChange.value.value,
    })
  }
  const nextAssignee = userStore.users.find((user) => user.id === pendingChange.value?.value)?.name ?? t('project.tasksTab.thisUser')
  return t('project.tasksTab.reassignTaskMessage', { title: task.value.title, from: task.value.assignedTo, to: nextAssignee })
})

async function applyStatusChange(status: TaskStatus): Promise<void> {
  try {
    await taskStore.updateTaskStatus(taskId.value, status)
    if (status === 'Completed' && originProjectId.value) await projectStore.refreshProject(originProjectId.value)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('task.taskActions.failedToUpdateStatus'), detail)
  }
}

async function applyReassign(assignee: string): Promise<void> {
  try {
    await taskStore.updateTaskAssignee(taskId.value, assignee)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('task.taskActions.failedToReassignTask'), detail)
  }
}

async function handleConfirmPendingChange(): Promise<void> {
  if (!pendingChange.value) return
  isConfirmSaving.value = true
  try {
    if (pendingChange.value.kind === 'status') await applyStatusChange(pendingChange.value.value)
    else await applyReassign(pendingChange.value.value)
    isConfirmDialogOpen.value = false
  } finally {
    isConfirmSaving.value = false
  }
}

function handleStatusChange(status: TaskStatus): void {
  if (originProjectId.value) {
    pendingChange.value = { kind: 'status', value: status }
    isConfirmDialogOpen.value = true
  } else {
    void applyStatusChange(status)
  }
}

function handleReassign(assignee: string): void {
  if (originProjectId.value) {
    pendingChange.value = { kind: 'reassign', value: assignee }
    isConfirmDialogOpen.value = true
  } else {
    void applyReassign(assignee)
  }
}

// -- Title / schedule -- always applied immediately, no confirmation --
// routine edits, same as every entry point already treated them.
async function handleTitleChange(title: string): Promise<void> {
  try {
    await taskStore.updateTaskTitle(taskId.value, title)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('task.taskActions.failedToUpdateTitle'), detail)
  }
}

async function handleStartDateChange(startDate: string): Promise<void> {
  try {
    await taskStore.updateTaskStartDate(taskId.value, startDate)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('task.taskActions.failedToUpdateSchedule'), detail)
  }
}

async function handleDueDateChange(dueDate: string): Promise<void> {
  try {
    await taskStore.updateTaskDueDate(taskId.value, dueDate)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('task.taskActions.failedToUpdateSchedule'), detail)
  }
}

async function handleDueTimeChange(dueTime: string): Promise<void> {
  try {
    await taskStore.updateTaskDueTime(taskId.value, dueTime)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('task.taskActions.failedToUpdateSchedule'), detail)
  }
}

// -- Delete ----------------------------------------------------------------
const isDeleteConfirmOpen = ref(false)
const isDeleting = ref(false)

function requestDelete(): void {
  isDeleteConfirmOpen.value = true
}

async function handleConfirmDelete(): Promise<void> {
  if (!task.value) return
  const title = task.value.title
  isDeleting.value = true
  try {
    await taskStore.deleteTask(taskId.value)
    toastStore.show('success', t('task.taskActions.taskDeletedTitle'), t('task.taskActions.taskDeletedDescription', { title }))
    isDeleteConfirmOpen.value = false
    goBack()
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('task.taskActions.failedToDeleteTask'), detail)
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <BaseButton variant="ghost" size="sm" :icon="backIcon" class="self-start no-print" @click="goBack">
      {{ originProjectId ? t('task.workspace.backToProject') : t('task.workspace.backToTasks') }}
    </BaseButton>

    <ErrorState v-if="loadError" :description="loadError" @retry="loadData" />

    <div v-else-if="isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="8" />
    </div>

    <EmptyState
      v-else-if="!task"
      :title="t('task.workspace.notFoundTitle')"
      :description="t('task.workspace.notFoundDescription')"
    />

    <TaskDetails
      v-else
      :task="task"
      :project-name="projectName"
      :client-name="clientName"
      @status-change="handleStatusChange"
      @title-change="handleTitleChange"
      @reassign="handleReassign"
      @start-date-change="handleStartDateChange"
      @due-date-change="handleDueDateChange"
      @due-time-change="handleDueTimeChange"
      @delete="requestDelete"
    />

    <ConfirmationDialog
      v-model="isConfirmDialogOpen"
      :title="confirmDialogTitle"
      :message="confirmDialogMessage"
      :loading="isConfirmSaving"
      @confirm="handleConfirmPendingChange"
    />

    <ConfirmationDialog
      v-model="isDeleteConfirmOpen"
      :title="t('task.taskActions.deleteTaskTitle')"
      :message="t('task.taskActions.deleteTaskMessage', { title: task?.title ?? '' })"
      confirm-variant="danger"
      :loading="isDeleting"
      @confirm="handleConfirmDelete"
    />
  </div>
</template>
