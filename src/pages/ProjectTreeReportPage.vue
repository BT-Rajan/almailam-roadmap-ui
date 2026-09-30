<script setup lang="ts">
import { CheckCircle2, Circle, CircleDot, XCircle } from '@lucide/vue'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ReportDateRange from '@/components/reports/ReportDateRange.vue'
import ReportHeader from '@/components/reports/ReportHeader.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import ReportProjectPicker from '@/components/reports/ReportProjectPicker.vue'
import { useReportRange } from '@/composables/useReportRange'
import { clientService } from '@/services/clientService'
import { projectService } from '@/services/projectService'
import { taskService } from '@/services/taskService'
import { getClientDisplayName } from '@/utils/clientHelpers'
import { downloadCsv } from '@/utils/csvExport'
import { formatDate, formatDateTime, todayIso } from '@/utils/dateFormatter'
import { getSelectedActivityStatusVariant, getSelectedPermitStatusVariant, getWorkflowStageLabel } from '@/utils/projectHelpers'
import { useEnumLabel } from '@/utils/reportLabels'
import { formatRange } from '@/utils/reportRange'
import { getTaskStatusVariant } from '@/utils/taskHelpers'
import type { Project, SelectedPermit, SelectedSupervisionActivity, WorkflowStage } from '@/types/Project'
import type { SelectedActivityStatus, SelectedServiceActivity } from '@/types/ServiceCatalog'
import type { Task } from '@/types/Task'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const enumLabel = useEnumLabel()
const pt = (key: string, values?: Record<string, unknown>) => t(`report.projectTreePage.${key}`, values ?? {})

// --- Project and period, both kept in the URL --------------------------------

const rangeState = useReportRange('this-month')
const periodLabel = computed(() => formatRange(rangeState.range.value))
const selectedProjectId = computed(() => (typeof route.query.project === 'string' ? route.query.project : undefined))
const onlyDueInPeriod = computed(() => route.query.due === 'period')

function pickProject(projectNo: string): void {
  void router.replace({ query: { ...route.query, project: projectNo } })
}
function setOnlyDueInPeriod(value: boolean): void {
  const query = { ...route.query }
  if (value) query.due = 'period'
  else delete query.due
  void router.replace({ query })
}

// --- Project + task data ----------------------------------------------------

const project = ref<Project>()
const allTasks = ref<Task[]>([])
const clientName = ref('')
const isLoading = ref(false)
const loadError = ref('')
const generatedAt = ref('')
let requestId = 0

async function loadTree(): Promise<void> {
  const current = ++requestId
  if (!selectedProjectId.value) {
    project.value = undefined
    return
  }
  isLoading.value = true
  loadError.value = ''
  try {
    const [loadedProject, projectTasks] = await Promise.all([
      projectService.getProjectById(selectedProjectId.value),
      taskService.getTasksForProject(selectedProjectId.value),
    ])
    if (current !== requestId) return
    project.value = loadedProject
    allTasks.value = projectTasks
    clientName.value = ''
    generatedAt.value = formatDateTime(new Date().toISOString())
    if (loadedProject) {
      const client = await clientService.getClientById(loadedProject.clientId).catch(() => undefined)
      if (current === requestId) clientName.value = client ? getClientDisplayName(client) : ''
    }
  } catch (error) {
    if (current !== requestId) return
    loadError.value = error instanceof Error ? error.message : pt('loadFailed')
    project.value = undefined
    allTasks.value = []
  } finally {
    if (current === requestId) isLoading.value = false
  }
}

watch(selectedProjectId, loadTree, { immediate: true })

const today = computed(() => todayIso())
const inPeriod = (task: Task) => task.dueDate >= rangeState.range.value.from && task.dueDate <= rangeState.range.value.to
// The tree shows every task, or only those due within the chosen period.
const tasks = computed(() => (onlyDueInPeriod.value ? allTasks.value.filter(inPeriod) : allTasks.value))
const isOverdue = (task: { status: string; dueDate: string }) => task.status !== 'Completed' && task.dueDate < today.value
const daysLate = (dueDate: string) =>
  Math.round((Date.parse(`${today.value}T00:00:00Z`) - Date.parse(`${dueDate}T00:00:00Z`)) / 86_400_000)

// --- Stage-status computation ----------------------------------------------
// Mirrors WorkflowProgress.vue's own stage-status rules (see its
// currentStageRank/isTrackDone/parallelStepStatus) so this tree reads the
// same "complete / current / upcoming" story as the stepper staff already
// see on the project workspace -- kept as this page's own small copy
// rather than importing from a component file, since WorkflowProgress.vue
// doesn't currently export its logic for reuse.

type NodeStatus = 'complete' | 'current' | 'upcoming'

const LINEAR_STAGES: WorkflowStage[] = ['Requirement', 'Quotation', 'Payment Plan', 'Contract']
const PARALLEL_STAGES: WorkflowStage[] = ['Government Submission', 'Design', 'Supervision']

function linearStatus(stage: WorkflowStage, currentStage: WorkflowStage, projectStatus?: Project['status']): NodeStatus {
  // A Completed project is finished -- nothing in it reads "current".
  if (projectStatus === 'Completed') return 'complete'
  const rank = LINEAR_STAGES.indexOf(stage)
  const currentRank = PARALLEL_STAGES.includes(currentStage) || currentStage === 'Handover' ? LINEAR_STAGES.length : LINEAR_STAGES.indexOf(currentStage)
  if (rank < currentRank) return 'complete'
  if (rank === currentRank) return 'current'
  return 'upcoming'
}

function isTrackDone(stage: WorkflowStage, p: Project): boolean {
  if (stage === 'Design') {
    const items = p.selectedActivities ?? []
    return items.length > 0 && items.every((a) => a.status === 'Complete' || a.status === 'Cancelled')
  }
  if (stage === 'Government Submission') {
    const items = p.selectedPermits ?? []
    return items.length > 0 && items.every((perm) => perm.status === 'Complete' || perm.status === 'Cancelled')
  }
  const items = p.selectedSupervisionActivities ?? []
  return items.length > 0 && items.every((a) => a.status === 'Complete' || a.status === 'Cancelled')
}

function parallelStatus(stage: WorkflowStage, p: Project): NodeStatus {
  if (p.status === 'Completed' || isTrackDone(stage, p)) return 'complete'
  const isPastContract = PARALLEL_STAGES.includes(p.currentStage) || p.currentStage === 'Handover'
  return isPastContract ? 'current' : 'upcoming'
}

function handoverStatus(p: Project): NodeStatus {
  if (p.status === 'Completed') return 'complete'
  return p.currentStage === 'Handover' ? 'current' : 'upcoming'
}

// --- Tree node shapes --------------------------------------------------

interface TaskNode {
  id: string
  title: string
  status: Task['status']
  assignedTo: string
  dueDate: string
  overdue: boolean
}
interface ItemNode {
  id: string
  name: string
  status: string
  tasks: TaskNode[]
}
interface TrackNode {
  key: WorkflowStage
  label: string
  status: NodeStatus
  items: ItemNode[]
}
interface StageNode {
  key: string
  label: string
  status: NodeStatus
}

function toTaskNode(task: Task): TaskNode {
  return { id: task.id, title: task.title, status: task.status, assignedTo: task.assignedTo, dueDate: task.dueDate, overdue: isOverdue(task) }
}

function buildItems<T extends { id?: string; status?: string }>(
  items: T[],
  linkedTaskIdField: 'selectedActivityId' | 'selectedPermitId' | 'selectedSupervisionActivityId',
  nameOf: (item: T) => string,
  statusOf: (item: T) => string,
): ItemNode[] {
  return items.map((item, index) => ({
    id: item.id ?? String(index),
    name: nameOf(item),
    status: statusOf(item),
    tasks: tasks.value.filter((task) => task[linkedTaskIdField] === item.id).map(toTaskNode),
  }))
}

const linearStageNodes = computed<StageNode[]>(() => {
  if (!project.value) return []
  return LINEAR_STAGES.map((stage) => ({
    key: stage,
    label: getWorkflowStageLabel(stage),
    status: linearStatus(stage, project.value!.currentStage, project.value!.status),
  }))
})

const trackNodes = computed<TrackNode[]>(() => {
  const p = project.value
  if (!p) return []
  const tracks: TrackNode[] = []
  if (p.includesDesign) {
    tracks.push({
      key: 'Design',
      label: getWorkflowStageLabel('Design'),
      status: parallelStatus('Design', p),
      items: buildItems<SelectedServiceActivity>(
        p.selectedActivities ?? [],
        'selectedActivityId',
        (a) => a.activityName,
        (a) => a.status ?? 'Not Started',
      ),
    })
  }
  if (p.includesGovernmentSubmission) {
    tracks.push({
      key: 'Government Submission',
      label: getWorkflowStageLabel('Government Submission'),
      status: parallelStatus('Government Submission', p),
      items: buildItems<SelectedPermit>(
        p.selectedPermits ?? [],
        'selectedPermitId',
        (perm) => perm.permitName,
        (perm) => perm.status,
      ),
    })
  }
  if (p.includesSupervision) {
    tracks.push({
      key: 'Supervision',
      label: getWorkflowStageLabel('Supervision'),
      status: parallelStatus('Supervision', p),
      items: buildItems<SelectedSupervisionActivity>(
        p.selectedSupervisionActivities ?? [],
        'selectedSupervisionActivityId',
        (a) => a.activityName,
        (a) => a.status ?? 'Not Started',
      ),
    })
  }
  return tracks
})

const handoverNode = computed<StageNode | null>(() => {
  if (!project.value) return null
  return { key: 'Handover', label: getWorkflowStageLabel('Handover'), status: handoverStatus(project.value) }
})

// Tasks linked to no Design activity / Permit / Supervision activity at
// all -- still real project work, just not slotted under one of the three
// tracks, so they get their own bucket rather than silently vanishing
// from the tree.
const generalTasks = computed<TaskNode[]>(() =>
  tasks.value
    .filter((task) => !task.selectedActivityId && !task.selectedPermitId && !task.selectedSupervisionActivityId)
    .map(toTaskNode),
)

const itemStatusVariant = (trackKey: WorkflowStage, status: string) => {
  if (trackKey === 'Government Submission') return getSelectedPermitStatusVariant(status as SelectedPermit['status'])
  return getSelectedActivityStatusVariant(status as SelectedActivityStatus)
}

const STATUS_ICON = { complete: CheckCircle2, current: CircleDot, upcoming: Circle } as const
const STATUS_ICON_CLASS = { complete: 'text-success-500', current: 'text-accent-500', upcoming: 'text-text-muted' } as const

const totalItems = computed(() => trackNodes.value.reduce((sum, track) => sum + track.items.length, 0))
const completeItems = computed(() =>
  trackNodes.value.reduce((sum, track) => sum + track.items.filter((i) => i.status === 'Complete' || i.status === 'Cancelled').length, 0),
)
const totalTasks = computed(() => allTasks.value.length)
const completeTasks = computed(() => allTasks.value.filter((task) => task.status === 'Completed').length)
const overdueTasks = computed(() => allTasks.value.filter(isOverdue).length)
const dueInPeriod = computed(() => allTasks.value.filter(inPeriod))

const stageStatusVariant = (status: NodeStatus) => (status === 'complete' ? 'success' : status === 'current' ? 'info' : 'neutral')

function exportCsv(): void {
  const p = project.value
  if (!p) return
  const rows: (string | number)[][] = []
  const taskRow = (stage: string, item: string, itemStatus: string, task?: TaskNode) =>
    rows.push([stage, item, itemStatus, task?.title ?? '', task?.status ?? '', task?.assignedTo ?? '', task?.dueDate ?? '', task?.overdue ? daysLate(task.dueDate) : ''])
  for (const stage of linearStageNodes.value) taskRow(stage.label, '', pt(`status.${stage.status}`))
  for (const track of trackNodes.value) {
    taskRow(track.label, '', pt(`status.${track.status}`))
    for (const item of track.items) {
      if (item.tasks.length === 0) taskRow(track.label, item.name, item.status)
      for (const task of item.tasks) taskRow(track.label, item.name, item.status, task)
    }
  }
  if (handoverNode.value) taskRow(handoverNode.value.label, '', pt(`status.${handoverNode.value.status}`))
  for (const task of generalTasks.value) taskRow(pt('generalTasks'), '', '', task)
  downloadCsv(`project-tree-${p.projectNo}.csv`, [
    {
      title: `${pt('pageTitle')} -- ${p.projectNo} ${p.projectName}${onlyDueInPeriod.value ? ` -- ${pt('onlyDueInPeriod')}: ${periodLabel.value}` : ''}`,
      headers: [pt('columnStage'), pt('columnItem'), pt('columnItemStatus'), pt('columnTask'), pt('columnTaskStatus'), pt('columnAssignee'), pt('columnDue'), t('report.projectPerformancePage.columnDaysLate')],
      rows,
    },
  ])
}
</script>

<template>
  <div class="mx-auto flex max-w-6xl flex-col gap-6 p-6 laptop:p-8">
    <BaseButton variant="ghost" size="sm" class="self-start print:hidden" @click="router.back()">← {{ t('report.back') }}</BaseButton>

    <ReportHeader
      :title="project ? `${project.projectNo} — ${project.projectName}` : pt('pageTitle')"
      :subtitle="project ? `${pt('pageTitle')} · ${clientName || pt('unknownClient')}` : pt('pageSubtitle')"
      :period="project && onlyDueInPeriod ? periodLabel : undefined"
      :generated-date="project ? generatedAt : undefined"
      :exportable="Boolean(project)"
      @download="exportCsv"
    />

    <div class="flex flex-wrap items-end gap-4">
      <ReportProjectPicker :model-value="selectedProjectId" @update:model-value="pickProject" />
      <ReportDateRange :state="rangeState" />
      <label class="flex items-center gap-2 pb-2.5 text-sm text-text-secondary print:hidden">
        <input type="checkbox" class="h-4 w-4 rounded border-border-default" :checked="onlyDueInPeriod" @change="setOnlyDueInPeriod(($event.target as HTMLInputElement).checked)" />
        {{ pt('onlyDueInPeriod') }}
      </label>
    </div>

    <Card v-if="!selectedProjectId"><p class="py-8 text-center text-sm text-text-muted">{{ pt('pickProject') }}</p></Card>
    <ErrorState v-else-if="loadError" :description="loadError" @retry="loadTree" />
    <Card v-else-if="isLoading && !project"><SkeletonLoader v-for="n in 6" :key="n" class="mb-2 h-8" /></Card>

    <div v-else-if="project" class="flex flex-col gap-6 transition-opacity" :class="isLoading ? 'opacity-50' : ''">
      <div class="flex flex-wrap items-center gap-2">
        <StatusBadge :label="enumLabel('project.status', project.status)" variant="info" />
        <StatusBadge :label="getWorkflowStageLabel(project.currentStage)" variant="neutral" />
        <span class="text-sm text-text-muted">{{ pt('progress', { percent: project.progress }) }}</span>
      </div>

      <div class="grid grid-cols-2 gap-4 laptop:grid-cols-4">
        <ReportMetricCard :label="pt('summaryItems')" :value="`${completeItems} / ${totalItems}`" color="primary" />
        <ReportMetricCard :label="pt('summaryTasks')" :value="`${completeTasks} / ${totalTasks}`" color="success" />
        <ReportMetricCard :label="pt('summaryOverdue')" :value="overdueTasks" :color="overdueTasks > 0 ? 'danger' : 'neutral'" />
        <ReportMetricCard
          :label="pt('summaryDueInPeriod')"
          :value="dueInPeriod.length"
          :hint="`${periodLabel} · ${pt('summaryDueInPeriodHint', { done: dueInPeriod.filter((task) => task.status === 'Completed').length })}`"
          color="info"
        />
      </div>

      <!-- Tree -->
      <Card :padded="false">
        <div class="flex flex-col divide-y divide-border-light">
          <!-- Linear stages -->
          <div v-for="stage in linearStageNodes" :key="stage.key" class="flex items-center gap-3 px-4 py-3">
            <component :is="STATUS_ICON[stage.status]" :class="['h-5 w-5 shrink-0', STATUS_ICON_CLASS[stage.status]]" />
            <span class="text-sm font-medium text-text-primary">{{ stage.label }}</span>
            <StatusBadge class="ms-auto" size="sm" :label="pt(`status.${stage.status}`)" :variant="stageStatusVariant(stage.status)" />
          </div>

          <!-- Parallel band -->
          <div v-for="track in trackNodes" :key="track.key" class="px-4 py-3">
            <div class="flex items-center gap-3">
              <component :is="STATUS_ICON[track.status]" :class="['h-5 w-5 shrink-0', STATUS_ICON_CLASS[track.status]]" />
              <span class="text-sm font-medium text-text-primary">{{ track.label }}</span>
              <StatusBadge class="ms-auto" size="sm" :label="pt(`status.${track.status}`)" :variant="stageStatusVariant(track.status)" />
            </div>

            <div v-if="track.items.length === 0" class="ms-8 mt-2 text-xs text-text-muted">{{ pt('noItems') }}</div>

            <details v-for="item in track.items" :key="item.id" class="ms-8 mt-2 rounded-lg border border-border-light" :open="item.tasks.some((task) => task.overdue)">
              <summary class="flex cursor-pointer items-center gap-3 px-3 py-2 text-sm">
                <span class="flex-1 text-text-secondary">{{ item.name }}</span>
                <StatusBadge size="sm" :label="item.status" :variant="itemStatusVariant(track.key, item.status)" />
                <span class="text-xs text-text-muted">{{ t('report.projectTreePage.taskCount', { count: item.tasks.length }, item.tasks.length) }}</span>
              </summary>
              <div v-if="item.tasks.length === 0" class="border-t border-border-light px-4 py-2 text-xs text-text-muted">{{ pt('noTasks') }}</div>
              <div v-for="taskNode in item.tasks" :key="taskNode.id" class="flex items-center justify-between gap-3 border-t border-border-light px-4 py-2 text-sm">
                <RouterLink :to="{ name: 'task-workspace', params: { taskId: taskNode.id } }" class="text-accent-600 hover:underline">{{ taskNode.title }}</RouterLink>
                <div class="flex items-center gap-2">
                  <span class="text-xs" :class="taskNode.overdue ? 'font-medium text-danger-600' : 'text-text-muted'">
                    {{ taskNode.assignedTo }} · {{ formatDate(taskNode.dueDate) }}<template v-if="taskNode.overdue"> · {{ pt('daysLate', { count: daysLate(taskNode.dueDate) }) }}</template>
                  </span>
                  <StatusBadge size="sm" :label="enumLabel('task.status', taskNode.status)" :variant="getTaskStatusVariant(taskNode.status)" />
                </div>
              </div>
            </details>
          </div>

          <!-- Handover -->
          <div v-if="handoverNode" class="flex items-center gap-3 px-4 py-3">
            <component :is="STATUS_ICON[handoverNode.status]" :class="['h-5 w-5 shrink-0', STATUS_ICON_CLASS[handoverNode.status]]" />
            <span class="text-sm font-medium text-text-primary">{{ handoverNode.label }}</span>
            <StatusBadge class="ms-auto" size="sm" :label="pt(`status.${handoverNode.status}`)" :variant="stageStatusVariant(handoverNode.status)" />
          </div>

          <!-- General / unlinked tasks -->
          <div v-if="generalTasks.length > 0" class="px-4 py-3">
            <div class="flex items-center gap-3">
              <XCircle class="h-5 w-5 shrink-0 text-text-muted" />
              <span class="text-sm font-medium text-text-primary">{{ pt('generalTasks') }}</span>
            </div>
            <div v-for="taskNode in generalTasks" :key="taskNode.id" class="ms-8 mt-2 flex items-center justify-between gap-3 border-t border-border-light px-3 py-2 text-sm">
              <RouterLink :to="{ name: 'task-workspace', params: { taskId: taskNode.id } }" class="text-accent-600 hover:underline">{{ taskNode.title }}</RouterLink>
              <div class="flex items-center gap-2">
                <span class="text-xs" :class="taskNode.overdue ? 'font-medium text-danger-600' : 'text-text-muted'">
                  {{ taskNode.assignedTo }} · {{ formatDate(taskNode.dueDate) }}<template v-if="taskNode.overdue"> · {{ pt('daysLate', { count: daysLate(taskNode.dueDate) }) }}</template>
                </span>
                <StatusBadge size="sm" :label="enumLabel('task.status', taskNode.status)" :variant="getTaskStatusVariant(taskNode.status)" />
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>
