<script setup lang="ts">
import { ArrowLeft, ArrowRight, CheckCircle2, ChevronLeft, ChevronRight, Circle, ListChecks, Plus } from '@lucide/vue'
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TextInput from '@/components/common/TextInput.vue'
import TaskDetails from '@/components/task/TaskDetails.vue'
import TaskStatusBadge from '@/components/task/TaskStatusBadge.vue'
import { useLocale } from '@/composables/useLocale'
import { useAuthStore } from '@/stores/authStore'
import { useClientStore } from '@/stores/clientStore'
import { useProjectStore } from '@/stores/projectStore'
import { useTaskStore } from '@/stores/taskStore'
import { useToastStore } from '@/stores/toastStore'
import { useUserStore } from '@/stores/userStore'
import type { Project } from '@/types/Project'
import type { Task, TaskStatus } from '@/types/Task'
import type { SelectOption } from '@/types/Ui'
import { getSelectedActivityStatusVariant, getSelectedPermitStatusVariant } from '@/utils/projectHelpers'
import { formatTaskDueDateTime, isTaskOverdue } from '@/utils/taskHelpers'
import { isServiceClosed, serviceLinkFields, taskBelongsTo, type ServiceRef } from '@/utils/serviceTaskLinks'

// Every task for one project service (a Design activity, Permit or
// Supervision activity) -- or, with `service` null, the project's
// general tasks not linked to any service -- in a modal over the
// project workspace, so working a service's tasks never navigates away
// from the project. System-created service tasks and ones added here
// by hand are the same list: a task added here is linked to this
// service (see serviceLinkFields), so it also counts towards the
// service's own "all tasks done" gate/auto-close on the backend.
//
// Two views in one dialog: the task list (one-click complete toggle,
// inline quick-add at the bottom) and a single task's full editor
// (TaskDetails -- the same component TaskWorkspacePage.vue uses), with
// a back link between them.

const props = withDefaults(defineProps<{
  modelValue: boolean
  project: Project
  service: ServiceRef | null
  // Opens straight into this task's editor instead of the list.
  initialTaskId?: string
  // False hides quick-add (e.g. general tasks once the stage's phase is
  // complete). A closed service hides it on its own -- see canAddTasks.
  canAdd?: boolean
}>(), { initialTaskId: undefined, canAdd: true })

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  // Something that can change the project itself (a linked activity
  // auto-closing, handover readiness) just happened -- the project has
  // already been refreshed; parents can reload their own derived state.
  changed: []
}>()

const { t } = useI18n()
const { isRtl } = useLocale()
const authStore = useAuthStore()
const clientStore = useClientStore()
const projectStore = useProjectStore()
const taskStore = useTaskStore()
const toastStore = useToastStore()
const userStore = useUserStore()

const backIcon = computed(() => (isRtl.value ? ArrowRight : ArrowLeft))
const rowChevron = computed(() => (isRtl.value ? ChevronLeft : ChevronRight))

const KIND_LABEL_KEYS: Record<ServiceRef['kind'], string> = {
  design: 'project.serviceTasks.kind.design',
  permit: 'project.serviceTasks.kind.permit',
  supervision: 'project.serviceTasks.kind.supervision',
}

// Design activities use their own status set; Permits and Supervision
// activities share SelectedPermitStatus's.
const serviceStatusVariant = computed(() => {
  if (!props.service?.status) return undefined
  return props.service.kind === 'design'
    ? getSelectedActivityStatusVariant(props.service.status as Parameters<typeof getSelectedActivityStatusVariant>[0])
    : getSelectedPermitStatusVariant(props.service.status as Parameters<typeof getSelectedPermitStatusVariant>[0])
})

const canAddTasks = computed(() => props.canAdd && !isServiceClosed(props.service))

const dialogTitle = computed(() => props.service?.name ?? t('project.serviceTasks.generalTitle'))
const kindLabel = computed(() => (props.service ? t(KIND_LABEL_KEYS[props.service.kind]) : t('project.serviceTasks.generalSubtitle')))

// Open tasks first (soonest due on top), completed ones sink to the bottom.
const tasks = computed<Task[]>(() =>
  taskStore
    .tasksByProject(props.project.id)
    .filter((task) => taskBelongsTo(task, props.service))
    .sort((a, b) => {
      const aDone = a.status === 'Completed' ? 1 : 0
      const bDone = b.status === 'Completed' ? 1 : 0
      if (aDone !== bDone) return aDone - bDone
      return `${a.dueDate}T${a.dueTime}`.localeCompare(`${b.dueDate}T${b.dueTime}`)
    }),
)
const doneCount = computed(() => tasks.value.filter((task) => task.status === 'Completed').length)
const progressPercent = computed(() => (tasks.value.length === 0 ? 0 : Math.round((doneCount.value / tasks.value.length) * 100)))

// -- View switching ------------------------------------------------------
const openTaskId = ref<string>()
const openTask = computed(() => tasks.value.find((task) => task.id === openTaskId.value))
const clientName = computed(() => clientStore.getClientById(props.project.clientId)?.companyName ?? t('project.unknownClient'))

const titleInputRef = ref<InstanceType<typeof TextInput>>()

// A task deleted (or relinked) out from under the editor drops back to the list.
watch(openTask, (task) => {
  if (openTaskId.value && !task && !taskStore.isLoading) openTaskId.value = undefined
})

function close(): void {
  emit('update:modelValue', false)
}

function showError(titleKey: string, error: unknown): void {
  toastStore.show('error', t(titleKey), error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain'))
}

async function refreshProject(): Promise<void> {
  await projectStore.refreshProject(props.project.id)
  emit('changed')
}

// -- Status --------------------------------------------------------------
const statusPendingId = ref<string>()

async function setStatus(task: Task, status: TaskStatus): Promise<void> {
  if (task.status === status) return
  statusPendingId.value = task.id
  try {
    await taskStore.updateTaskStatus(task.id, status)
    // Completing (or reopening) a linked task is exactly what can
    // auto-close its service or change handover readiness.
    if (status === 'Completed' || task.status === 'Completed') await refreshProject()
  } catch (error) {
    showError('task.taskActions.failedToUpdateStatus', error)
  } finally {
    statusPendingId.value = undefined
  }
}

function toggleComplete(task: Task): void {
  void setStatus(task, task.status === 'Completed' ? 'In Progress' : 'Completed')
}

// -- Single-task edits (editor view) -------------------------------------
async function runEdit(action: () => Promise<void>, errorKey: string): Promise<void> {
  try {
    await action()
  } catch (error) {
    showError(errorKey, error)
  }
}

function handleTitleChange(title: string): void {
  if (openTaskId.value) void runEdit(() => taskStore.updateTaskTitle(openTaskId.value!, title), 'task.taskActions.failedToUpdateTitle')
}
function handleReassign(assignee: string): void {
  if (openTaskId.value) void runEdit(() => taskStore.updateTaskAssignee(openTaskId.value!, assignee), 'task.taskActions.failedToReassignTask')
}
function handleStartDateChange(value: string): void {
  if (openTaskId.value) void runEdit(() => taskStore.updateTaskStartDate(openTaskId.value!, value), 'task.taskActions.failedToUpdateSchedule')
}
function handleDueDateChange(value: string): void {
  if (openTaskId.value) void runEdit(() => taskStore.updateTaskDueDate(openTaskId.value!, value), 'task.taskActions.failedToUpdateSchedule')
}
function handleDueTimeChange(value: string): void {
  if (openTaskId.value) void runEdit(() => taskStore.updateTaskDueTime(openTaskId.value!, value), 'task.taskActions.failedToUpdateSchedule')
}
function handleStatusChange(status: TaskStatus): void {
  if (openTask.value) void setStatus(openTask.value, status)
}

// -- Delete --------------------------------------------------------------
const isDeleteConfirmOpen = ref(false)
const isDeleting = ref(false)

async function confirmDelete(): Promise<void> {
  const task = openTask.value
  if (!task) return
  isDeleting.value = true
  try {
    await taskStore.deleteTask(task.id)
    toastStore.show('success', t('task.taskActions.taskDeletedTitle'), t('task.taskActions.taskDeletedDescription', { title: task.title }))
    isDeleteConfirmOpen.value = false
    openTaskId.value = undefined
    // Deleting the last open task can leave the service fully done.
    await refreshProject()
  } catch (error) {
    showError('task.taskActions.failedToDeleteTask', error)
  } finally {
    isDeleting.value = false
  }
}

// -- Quick add -----------------------------------------------------------
function inDays(days: number): string {
  const date = new Date()
  date.setDate(date.getDate() + days)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
}

const quickAdd = reactive({ title: '', assignedTo: '', dueDate: '' })
const isAdding = ref(false)
const quickAddError = ref<string>()

function resetQuickAdd(): void {
  quickAdd.title = ''
  quickAdd.assignedTo = authStore.user?.id ?? ''
  quickAdd.dueDate = inDays(7)
  quickAddError.value = undefined
}

const assigneeOptions = computed<SelectOption[]>(() =>
  userStore.users
    .filter((user) => user.status === 'Active')
    .map((user) => ({
      label: user.id === authStore.user?.id ? t('task.formDialog.assigneeMe', { name: user.name }) : user.name,
      value: user.id,
    })),
)

async function addTask(): Promise<void> {
  const title = quickAdd.title.trim()
  if (!title) {
    quickAddError.value = t('task.formDialog.titleRequired')
    titleInputRef.value?.focus()
    return
  }
  if (!quickAdd.assignedTo) {
    quickAddError.value = t('task.formDialog.assigneeRequired')
    return
  }
  if (!quickAdd.dueDate) {
    quickAddError.value = t('task.formDialog.dueDateRequired')
    return
  }
  quickAddError.value = undefined
  isAdding.value = true
  try {
    await taskStore.createTask({
      projectId: props.project.id,
      title,
      assignedTo: quickAdd.assignedTo,
      priority: 'Medium',
      severity: 'Minor',
      dueDate: quickAdd.dueDate,
      dueTime: '17:00',
      status: 'Pending',
      ...serviceLinkFields(props.service),
    })
    toastStore.show('success', t('task.taskActions.taskCreatedTitle'), t('project.serviceTasks.taskAdded', { title, service: dialogTitle.value }))
    quickAdd.title = ''
    // A new open task reopens the "all tasks done" gate for this service.
    await refreshProject()
    await nextTick()
    titleInputRef.value?.focus()
  } catch (error) {
    showError('task.taskActions.failedToCreateTask', error)
  } finally {
    isAdding.value = false
  }
}

// Declared last: the immediate run needs the quick-add state above.
watch(
  () => props.modelValue,
  (isOpen) => {
    if (!isOpen) return
    openTaskId.value = props.initialTaskId
    resetQuickAdd()
    void taskStore.loadTasksForProject(props.project.id)
    if (userStore.users.length === 0) void userStore.loadUsers()
    if (clientStore.clients.length === 0) void clientStore.loadClients()
  },
  { immediate: true },
)
</script>

<template>
  <BaseDialog :model-value="modelValue" :title="dialogTitle" size="lg" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-5">
      <!-- Single task editor -->
      <template v-if="openTask">
        <button
          type="button"
          class="inline-flex items-center gap-1.5 self-start text-sm font-medium text-primary-600 hover:text-primary-700"
          @click="openTaskId = undefined"
        >
          <component :is="backIcon" class="h-4 w-4" />
          {{ t('project.serviceTasks.backToList', { service: dialogTitle }) }}
        </button>
        <TaskDetails
          :task="openTask"
          :project-name="project.projectName"
          :client-name="clientName"
          @status-change="handleStatusChange"
          @title-change="handleTitleChange"
          @reassign="handleReassign"
          @start-date-change="handleStartDateChange"
          @due-date-change="handleDueDateChange"
          @due-time-change="handleDueTimeChange"
          @delete="isDeleteConfirmOpen = true"
        />
      </template>

      <!-- Task list -->
      <template v-else>
        <div class="flex flex-col gap-2">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <span class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ kindLabel }}</span>
              <StatusBadge
                v-if="service?.status"
                :label="service.status"
                :variant="serviceStatusVariant"
                size="sm"
              />
            </div>
            <span class="text-sm font-medium text-text-secondary">
              {{ t('project.serviceTasks.progress', { done: doneCount, total: tasks.length }) }}
            </span>
          </div>
          <ProgressBar v-if="tasks.length > 0" :value="progressPercent" />
          <p v-if="service && tasks.length > 0 && doneCount === tasks.length" class="text-xs text-success-700">
            {{ t('project.serviceTasks.allDone') }}
          </p>
        </div>

        <div v-if="taskStore.isLoading && tasks.length === 0" class="rounded-xl border border-border-light p-4">
          <SkeletonLoader :rows="3" />
        </div>

        <div
          v-else-if="tasks.length === 0"
          class="flex flex-col items-center gap-2 rounded-xl border border-dashed border-border-default px-4 py-8 text-center"
        >
          <ListChecks class="h-6 w-6 text-text-muted" />
          <p class="text-sm font-medium text-text-primary">{{ t('project.serviceTasks.emptyTitle') }}</p>
          <p class="text-xs text-text-muted">{{ t('project.serviceTasks.emptyDescription') }}</p>
        </div>

        <ul v-else class="divide-y divide-border-light overflow-hidden rounded-xl border border-border-light">
          <li
            v-for="task in tasks"
            :key="task.id"
            class="flex items-center gap-3 px-3 py-2.5 transition-colors duration-fast hover:bg-bg-hover"
          >
            <button
              type="button"
              class="shrink-0 rounded-full p-0.5 text-text-muted transition-colors hover:text-success-600 disabled:opacity-50"
              :class="{ 'text-success-600': task.status === 'Completed' }"
              :disabled="statusPendingId === task.id"
              :aria-label="task.status === 'Completed' ? t('project.serviceTasks.markNotDone', { title: task.title }) : t('project.serviceTasks.markDone', { title: task.title })"
              :title="task.status === 'Completed' ? t('project.serviceTasks.markNotDoneShort') : t('project.serviceTasks.markDoneShort')"
              @click="toggleComplete(task)"
            >
              <CheckCircle2 v-if="task.status === 'Completed'" class="h-5 w-5" />
              <Circle v-else class="h-5 w-5" />
            </button>
            <button type="button" class="flex min-w-0 flex-1 items-center gap-3 text-start" @click="openTaskId = task.id">
              <div class="min-w-0 flex-1">
                <p
                  class="truncate text-sm font-medium"
                  :class="task.status === 'Completed' ? 'text-text-muted line-through' : 'text-text-primary'"
                >{{ task.title }}</p>
                <p class="truncate text-xs text-text-muted">
                  {{ task.assignedTo }} &middot;
                  <span :class="{ 'font-medium text-danger-700': isTaskOverdue(task) }">{{ formatTaskDueDateTime(task) }}</span>
                </p>
              </div>
              <TaskStatusBadge :status="task.status" />
              <component :is="rowChevron" class="h-4 w-4 shrink-0 text-text-muted" />
            </button>
          </li>
        </ul>

        <p v-if="!canAddTasks" class="rounded-xl border border-border-light px-3 py-2.5 text-xs text-text-muted">
          {{ service ? t('project.tasksTab.serviceClosedNoTasks') : t('project.tasksTab.phaseCompleteNoTasks') }}
        </p>
        <!-- Quick add: linked to this same service, so it lands right here. -->
        <form v-else class="flex flex-col gap-3 rounded-xl border border-border-light bg-bg-card p-3" @submit.prevent="addTask">
          <TextInput
            ref="titleInputRef"
            v-model="quickAdd.title"
            :label="t('project.serviceTasks.addTitle')"
            :placeholder="t('project.serviceTasks.addPlaceholder')"
          />
          <div class="grid grid-cols-1 items-end gap-3 tablet:grid-cols-[1fr_1fr_auto]">
            <SelectBox v-model="quickAdd.assignedTo" :label="t('task.formDialog.assignTo')" :options="assigneeOptions" />
            <DatePicker v-model="quickAdd.dueDate" :label="t('task.formDialog.completionDate')" />
            <BaseButton type="submit" :icon="Plus" :loading="isAdding">{{ t('project.serviceTasks.addButton') }}</BaseButton>
          </div>
          <p v-if="quickAddError" class="text-xs text-danger-700">{{ quickAddError }}</p>
        </form>
      </template>
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="close">{{ t('project.serviceTasks.done') }}</BaseButton>
    </template>
  </BaseDialog>

  <ConfirmationDialog
    v-model="isDeleteConfirmOpen"
    :title="t('task.taskActions.deleteTaskTitle')"
    :message="t('task.taskActions.deleteTaskMessage', { title: openTask?.title ?? '' })"
    confirm-variant="danger"
    :loading="isDeleting"
    @confirm="confirmDelete"
  />
</template>
