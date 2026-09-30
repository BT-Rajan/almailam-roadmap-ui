<script setup lang="ts">
import { ChevronLeft, ChevronRight, Plus } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import ServiceTasksDialog from '@/components/project/ServiceTasksDialog.vue'
import TaskStatusBadge from '@/components/task/TaskStatusBadge.vue'
import { useLocale } from '@/composables/useLocale'
import { useClientStore } from '@/stores/clientStore'
import { useTaskStore } from '@/stores/taskStore'
import type { Project, WorkflowStage } from '@/types/Project'
import type { Task } from '@/types/Task'
import { formatTaskDueDateTime, isTaskOverdue } from '@/utils/taskHelpers'
import {
  isServiceClosed,
  projectServices,
  serviceKey,
  taskServiceKey,
  type ServiceKind,
  type ServiceRef,
} from '@/utils/serviceTaskLinks'

const props = defineProps<{
  project: Project
  // Which stage's Tasks tab this is -- Design/Supervision/Government
  // Submission each auto-create one system task per selected service
  // (see project_service.create_service_tasks), as parallel tracks that
  // can all be active on the same project at once. When set to one of
  // those three, this tab shows that track's own services plus the
  // general (unlinked) tasks -- not another track's services mixed in.
  // Omitted (or any other stage) shows every service.
  stageContext?: WorkflowStage
}>()

const emit = defineEmits<{
  // A task change that can affect the project itself (see ServiceTasksDialog's own `changed`).
  changed: []
}>()

// The Design stage's Overview embeds this list and puts each activity's
// own status/close controls in its card: `service-actions` renders in
// the card header (replacing the plain status text), `service-footer`
// right under it.
defineSlots<{
  'service-actions'?: (props: { service: ServiceRef; soleTask?: Task }) => unknown
  'service-footer'?: (props: { service: ServiceRef; soleTask?: Task }) => unknown
}>()

const taskStore = useTaskStore()
const clientStore = useClientStore()
const { t } = useI18n()
const { isRtl } = useLocale()
onMounted(() => {
  if (clientStore.clients.length === 0) clientStore.loadClients()
})

const rowChevron = computed(() => (isRtl.value ? ChevronLeft : ChevronRight))

const KIND_LABEL_KEYS: Record<ServiceKind, string> = {
  design: 'project.serviceTasks.kind.design',
  permit: 'project.serviceTasks.kind.permit',
  supervision: 'project.serviceTasks.kind.supervision',
}

const scopedKinds = computed<ServiceKind[]>(() => {
  switch (props.stageContext) {
    case 'Design':
      return ['design']
    case 'Supervision':
      return ['supervision']
    case 'Government Submission':
      return ['permit']
    default:
      return ['design', 'permit', 'supervision']
  }
})

// One list: every service's tasks -- the system-created one and any
// added by hand -- grouped under that service, then the project's
// general tasks. Each service shows even with no tasks yet, so there's
// always a place to add the first one.
interface TaskGroup {
  key: string
  service: ServiceRef | null
  tasks: Task[]
  done: number
  // The task the system auto-created for this service (same title as the
  // service -- see project_service._create_service_tasks), if still here.
  mainTask?: Task
  // Set while that main task is the service's ONLY task: the card then
  // shows it folded into the service line (owner, due date, status)
  // instead of repeating the same name as a separate row -- the list
  // only appears once there's more than one piece of work.
  soleTask?: Task
}

function isMainTaskOf(task: Task, service: ServiceRef): boolean {
  return task.title.trim().toLowerCase() === service.name.trim().toLowerCase()
}

function sortTasks(tasks: Task[]): Task[] {
  return [...tasks].sort((a, b) => {
    const aDone = a.status === 'Completed' ? 1 : 0
    const bDone = b.status === 'Completed' ? 1 : 0
    if (aDone !== bDone) return aDone - bDone
    return `${a.dueDate}T${a.dueTime}`.localeCompare(`${b.dueDate}T${b.dueTime}`)
  })
}

const groups = computed<TaskGroup[]>(() => {
  const byKey = new Map<string, Task[]>()
  for (const task of taskStore.tasksByProject(props.project.id)) {
    const key = taskServiceKey(task) ?? ''
    const list = byKey.get(key) ?? []
    list.push(task)
    byKey.set(key, list)
  }
  const result: TaskGroup[] = projectServices(props.project, scopedKinds.value).map((service) => {
    const key = serviceKey(service.kind, service.id)
    const tasks = sortTasks(byKey.get(key) ?? [])
    const mainTask = tasks.find((task) => isMainTaskOf(task, service))
    const soleTask = tasks.length === 1 ? mainTask : undefined
    return { key, service, tasks, done: tasks.filter((task) => task.status === 'Completed').length, mainTask, soleTask }
  })
  const general = sortTasks(byKey.get('') ?? [])
  result.push({ key: 'general', service: null, tasks: general, done: general.filter((task) => task.status === 'Completed').length })
  return result
})

const hasAnything = computed(() => groups.value.some((group) => group.service || group.tasks.length > 0))

// -- Dialog --------------------------------------------------------------
// Tracked by key, and the ServiceRef re-resolved from the live project,
// so the dialog's status badge follows the service after a refresh.
const isDialogOpen = ref(false)
const dialogServiceKey = ref<string>('general')
const dialogTaskId = ref<string>()
const dialogService = computed<ServiceRef | null>(
  () => groups.value.find((group) => group.key === dialogServiceKey.value)?.service ?? null,
)

function openGroup(group: TaskGroup, taskId?: string): void {
  dialogServiceKey.value = group.key
  dialogTaskId.value = taskId
  isDialogOpen.value = true
}

// The stage's phase is done once every service in it is closed: no new
// tasks from here then, general ones included.
const isPhaseComplete = computed(() => {
  const services = groups.value.filter((group) => group.service).map((group) => group.service)
  return services.length > 0 && services.every((service) => isServiceClosed(service))
})

function openGeneral(): void {
  dialogServiceKey.value = 'general'
  dialogTaskId.value = undefined
  isDialogOpen.value = true
}
</script>

<template>
  <div class="flex items-center justify-end no-print">
    <BaseButton
      size="sm"
      :icon="Plus"
      :disabled="isPhaseComplete"
      :title="isPhaseComplete ? t('project.tasksTab.phaseCompleteNoTasks') : undefined"
      @click="openGeneral"
    >{{ t('project.tasksTab.newTask') }}</BaseButton>
  </div>

  <div v-if="taskStore.isLoading && taskStore.tasksByProject(project.id).length === 0" class="rounded-xl border border-border-light bg-bg-card p-5">
    <SkeletonLoader :rows="6" />
  </div>

  <ErrorState v-else-if="taskStore.error" :description="taskStore.error" @retry="taskStore.loadTasksForProject(project.id, { force: true })" />

  <EmptyState
    v-else-if="!hasAnything"
    :title="t('project.tasksTab.emptyTitle')"
    :description="t('project.tasksTab.emptyDescription')"
  />

  <div v-else class="flex flex-col gap-4">
    <template v-for="group in groups" :key="group.key">
      <Card v-if="group.service || group.tasks.length > 0" :padded="false">
        <div class="flex flex-wrap items-center justify-between gap-3 border-b border-border-light px-5 py-3">
          <button
            type="button"
            class="flex min-w-0 flex-1 flex-col items-start gap-1 text-start"
            :aria-label="t('project.serviceTasks.openTasksFor', { service: group.service?.name ?? t('project.tasksTab.generalGroup') })"
            @click="openGroup(group, group.soleTask?.id)"
          >
            <span class="truncate text-sm font-semibold text-text-primary hover:text-primary-600">
              {{ group.service?.name ?? t('project.tasksTab.generalGroup') }}
            </span>
            <span v-if="group.soleTask" class="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-text-muted">
              <span>{{ group.soleTask.assignedTo }}</span>
              <span>&middot;</span>
              <span :class="{ 'font-medium text-danger-700': isTaskOverdue(group.soleTask) }">
                {{ t('project.tasksTab.due', { date: formatTaskDueDateTime(group.soleTask) }) }}
              </span>
              <TaskStatusBadge :status="group.soleTask.status" />
            </span>
            <span v-else class="text-xs text-text-muted">
              {{ group.service ? t(KIND_LABEL_KEYS[group.service.kind]) : t('project.tasksTab.generalGroupHint') }}
              <template v-if="group.service?.status && !$slots['service-actions']"> &middot; {{ group.service.status }}</template>
            </span>
          </button>
          <div class="flex flex-wrap items-center gap-3">
            <slot v-if="group.service" name="service-actions" :service="group.service" :sole-task="group.soleTask" />
            <div v-if="group.tasks.length > 0 && !group.soleTask" class="flex w-32 flex-col gap-1">
              <span class="text-end text-xs font-medium text-text-secondary">
                {{ t('project.serviceTasks.tasksChip', { done: group.done, total: group.tasks.length }) }}
              </span>
              <ProgressBar :value="Math.round((group.done / group.tasks.length) * 100)" />
            </div>
            <BaseButton
              variant="secondary"
              size="sm"
              :icon="Plus"
              class="no-print"
              :disabled="isServiceClosed(group.service) || (!group.service && isPhaseComplete)"
              :title="isServiceClosed(group.service) ? t('project.tasksTab.serviceClosedNoTasks') : undefined"
              @click="openGroup(group)"
            >
              {{ t('project.tasksTab.addTask') }}
            </BaseButton>
          </div>
        </div>

        <slot v-if="group.service" name="service-footer" :service="group.service" :sole-task="group.soleTask" />
        <p v-if="group.tasks.length === 0" class="px-5 py-3 text-xs text-text-muted">{{ t('project.tasksTab.noServiceTasksYet') }}</p>
        <ul v-else-if="!group.soleTask" class="divide-y divide-border-light">
          <li v-for="task in group.tasks" :key="task.id">
            <button
              type="button"
              class="flex w-full items-center gap-3 px-5 py-3 text-start transition-colors duration-fast hover:bg-bg-hover"
              @click="openGroup(group, task.id)"
            >
              <div class="min-w-0 flex-1">
                <p
                  class="truncate text-sm font-medium"
                  :class="task.status === 'Completed' ? 'text-text-muted line-through' : 'text-text-primary'"
                >{{ task.title }}</p>
                <p class="truncate text-xs text-text-muted">
                  <span
                    v-if="task.id === group.mainTask?.id"
                    class="me-1.5 rounded bg-primary-500/15 px-1.5 py-0.5 font-medium text-primary-600"
                  >{{ t('project.tasksTab.mainTask') }}</span>{{ task.assignedTo }}
                </p>
              </div>
              <TaskStatusBadge :status="task.status" />
              <span
                class="hidden w-32 text-end text-xs font-medium tablet:inline"
                :class="isTaskOverdue(task) ? 'text-danger-700' : 'text-text-muted'"
              >{{ formatTaskDueDateTime(task) }}</span>
              <component :is="rowChevron" class="h-4 w-4 shrink-0 text-text-muted" />
            </button>
          </li>
        </ul>
      </Card>
    </template>
  </div>

  <ServiceTasksDialog
    v-model="isDialogOpen"
    :project="project"
    :service="dialogService"
    :initial-task-id="dialogTaskId"
    :can-add="!(dialogService === null && isPhaseComplete)"
    @changed="emit('changed')"
  />
</template>
