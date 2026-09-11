<script setup lang="ts">
import { CheckCircle2, Circle, CircleDot, XCircle } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { clientService } from '@/services/clientService'
import { projectService } from '@/services/projectService'
import { taskService } from '@/services/taskService'
import { getClientDisplayName } from '@/utils/clientHelpers'
import { formatDate } from '@/utils/dateFormatter'
import { getSelectedActivityStatusVariant, getSelectedPermitStatusVariant, getWorkflowStageLabel } from '@/utils/projectHelpers'
import { getTaskStatusVariant } from '@/utils/taskHelpers'
import type { Project, SelectedPermit, SelectedSupervisionActivity, WorkflowStage } from '@/types/Project'
import type { SelectedActivityStatus, SelectedServiceActivity } from '@/types/ServiceCatalog'
import type { Task } from '@/types/Task'
import type { SelectOption } from '@/types/Ui'

const { t } = useI18n()

// --- Project picker --------------------------------------------------------

const projectOptions = ref<SelectOption[]>([])
const selectedProjectId = ref('')
const isLoadingProjects = ref(false)

onMounted(async () => {
  isLoadingProjects.value = true
  try {
    const page = await projectService.getProjectsPage({ pageSize: 200, sort: 'projectName' })
    projectOptions.value = page.items.map((p) => ({ label: `${p.projectNo} — ${p.projectName}`, value: p.id }))
    if (projectOptions.value.length > 0) selectedProjectId.value = projectOptions.value[0].value as string
  } finally {
    isLoadingProjects.value = false
  }
})

// --- Project + task data ----------------------------------------------------

const project = ref<Project>()
const tasks = ref<Task[]>([])
const clientName = ref('')
const isLoading = ref(false)
const loadError = ref('')

async function loadTree(): Promise<void> {
  if (!selectedProjectId.value) return
  isLoading.value = true
  loadError.value = ''
  try {
    const [loadedProject, taskPage] = await Promise.all([
      projectService.getProjectById(selectedProjectId.value),
      taskService.getTasksPage({ projectId: selectedProjectId.value, pageSize: 200 }),
    ])
    project.value = loadedProject
    tasks.value = taskPage.items
    clientName.value = ''
    if (loadedProject) {
      const client = await clientService.getClientById(loadedProject.clientId)
      clientName.value = client ? getClientDisplayName(client) : ''
    }
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : t('report.projectTreePage.loadFailed')
    project.value = undefined
    tasks.value = []
  } finally {
    isLoading.value = false
  }
}

watch(selectedProjectId, loadTree)

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

function linearStatus(stage: WorkflowStage, currentStage: WorkflowStage): NodeStatus {
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
  if (isTrackDone(stage, p)) return 'complete'
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
  return { id: task.id, title: task.title, status: task.status, assignedTo: task.assignedTo, dueDate: task.dueDate }
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
    status: linearStatus(stage, project.value!.currentStage),
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
const STATUS_ICON_CLASS = { complete: 'text-success-500', current: 'text-info-500', upcoming: 'text-text-muted' } as const

const totalItems = computed(() => trackNodes.value.reduce((sum, track) => sum + track.items.length, 0))
const completeItems = computed(() =>
  trackNodes.value.reduce((sum, track) => sum + track.items.filter((i) => i.status === 'Complete' || i.status === 'Cancelled').length, 0),
)
const totalTasks = computed(() => tasks.value.length)
const completeTasks = computed(() => tasks.value.filter((task) => task.status === 'Completed').length)
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader :title="t('report.projectTreePage.pageTitle')" :subtitle="t('report.projectTreePage.pageSubtitle')" />

    <Card>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <SelectBox v-model="selectedProjectId" :label="t('report.projectTreePage.project')" :options="projectOptions" :disabled="isLoadingProjects" />
      </div>
    </Card>

    <ErrorState v-if="loadError" :description="loadError" @retry="loadTree" />
    <Card v-else-if="isLoading"><SkeletonLoader v-for="n in 6" :key="n" class="mb-2 h-8" /></Card>

    <template v-else-if="project">
      <Card>
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 class="text-lg font-semibold text-text-primary">{{ project.projectNo }} — {{ project.projectName }}</h2>
            <p class="text-sm text-text-muted">{{ clientName || t('report.projectTreePage.unknownClient') }}</p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <StatusBadge :label="project.status" variant="info" />
            <StatusBadge :label="getWorkflowStageLabel(project.currentStage)" variant="neutral" />
            <span class="text-sm text-text-muted">{{ t('report.projectTreePage.progress', { percent: project.progress }) }}</span>
          </div>
        </div>
        <div class="mt-4 grid grid-cols-2 gap-4 border-t border-border-light pt-4 sm:grid-cols-4">
          <div>
            <p class="text-xs uppercase text-text-muted">{{ t('report.projectTreePage.trackItems') }}</p>
            <p class="text-lg font-semibold text-text-primary">{{ completeItems }} / {{ totalItems }}</p>
          </div>
          <div>
            <p class="text-xs uppercase text-text-muted">{{ t('report.projectTreePage.tasks') }}</p>
            <p class="text-lg font-semibold text-text-primary">{{ completeTasks }} / {{ totalTasks }}</p>
          </div>
        </div>
      </Card>

      <!-- Tree -->
      <Card :padded="false">
        <div class="flex flex-col divide-y divide-border-light">
          <!-- Linear stages -->
          <div v-for="stage in linearStageNodes" :key="stage.key" class="flex items-center gap-3 px-4 py-3">
            <component :is="STATUS_ICON[stage.status]" :class="['h-5 w-5 shrink-0', STATUS_ICON_CLASS[stage.status]]" />
            <span class="text-sm font-medium text-text-primary">{{ stage.label }}</span>
            <StatusBadge
              class="ms-auto"
              size="sm"
              :label="t(`report.projectTreePage.status.${stage.status}`)"
              :variant="stage.status === 'complete' ? 'success' : stage.status === 'current' ? 'info' : 'neutral'"
            />
          </div>

          <!-- Parallel band -->
          <div v-for="track in trackNodes" :key="track.key" class="px-4 py-3">
            <div class="flex items-center gap-3">
              <component :is="STATUS_ICON[track.status]" :class="['h-5 w-5 shrink-0', STATUS_ICON_CLASS[track.status]]" />
              <span class="text-sm font-medium text-text-primary">{{ track.label }}</span>
              <StatusBadge
                class="ms-auto"
                size="sm"
                :label="t(`report.projectTreePage.status.${track.status}`)"
                :variant="track.status === 'complete' ? 'success' : track.status === 'current' ? 'info' : 'neutral'"
              />
            </div>

            <div v-if="track.items.length === 0" class="ms-8 mt-2 text-xs text-text-muted">
              {{ t('report.projectTreePage.noItems') }}
            </div>

            <details v-for="item in track.items" :key="item.id" class="ms-8 mt-2 rounded-lg border border-border-light">
              <summary class="flex cursor-pointer items-center gap-3 px-3 py-2 text-sm">
                <span class="flex-1 text-text-secondary">{{ item.name }}</span>
                <StatusBadge size="sm" :label="item.status" :variant="itemStatusVariant(track.key, item.status)" />
                <span class="text-xs text-text-muted">{{ t('report.projectTreePage.taskCount', { count: item.tasks.length }) }}</span>
              </summary>
              <div v-if="item.tasks.length === 0" class="border-t border-border-light px-4 py-2 text-xs text-text-muted">
                {{ t('report.projectTreePage.noTasks') }}
              </div>
              <div
                v-for="taskNode in item.tasks"
                :key="taskNode.id"
                class="flex items-center justify-between gap-3 border-t border-border-light px-4 py-2 text-sm"
              >
                <span class="text-text-secondary">{{ taskNode.title }}</span>
                <div class="flex items-center gap-2">
                  <span class="text-xs text-text-muted">{{ taskNode.assignedTo }} · {{ formatDate(taskNode.dueDate) }}</span>
                  <StatusBadge size="sm" :label="taskNode.status" :variant="getTaskStatusVariant(taskNode.status)" />
                </div>
              </div>
            </details>
          </div>

          <!-- Handover -->
          <div v-if="handoverNode" class="flex items-center gap-3 px-4 py-3">
            <component :is="STATUS_ICON[handoverNode.status]" :class="['h-5 w-5 shrink-0', STATUS_ICON_CLASS[handoverNode.status]]" />
            <span class="text-sm font-medium text-text-primary">{{ handoverNode.label }}</span>
            <StatusBadge
              class="ms-auto"
              size="sm"
              :label="t(`report.projectTreePage.status.${handoverNode.status}`)"
              :variant="handoverNode.status === 'complete' ? 'success' : handoverNode.status === 'current' ? 'info' : 'neutral'"
            />
          </div>

          <!-- General / unlinked tasks -->
          <div v-if="generalTasks.length > 0" class="px-4 py-3">
            <div class="flex items-center gap-3">
              <XCircle class="h-5 w-5 shrink-0 text-text-muted" />
              <span class="text-sm font-medium text-text-primary">{{ t('report.projectTreePage.generalTasks') }}</span>
            </div>
            <div
              v-for="taskNode in generalTasks"
              :key="taskNode.id"
              class="ms-8 mt-2 flex items-center justify-between gap-3 border-t border-border-light px-3 py-2 text-sm"
            >
              <span class="text-text-secondary">{{ taskNode.title }}</span>
              <div class="flex items-center gap-2">
                <span class="text-xs text-text-muted">{{ taskNode.assignedTo }} · {{ formatDate(taskNode.dueDate) }}</span>
                <StatusBadge size="sm" :label="taskNode.status" :variant="getTaskStatusVariant(taskNode.status)" />
              </div>
            </div>
          </div>
        </div>
      </Card>
    </template>
  </div>
</template>
