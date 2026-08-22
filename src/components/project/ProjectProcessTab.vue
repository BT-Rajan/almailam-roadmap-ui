<script setup lang="ts">
import { ChevronDown, ChevronRight, CheckCircle2, Circle, FileText, ListChecks, Plus } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import ChangeScopeDialog from '@/components/project/ChangeScopeDialog.vue'
import ExecutionStepRow from '@/components/project/ExecutionStepRow.vue'
import FileUploader from '@/components/document/FileUploader.vue'
import ProjectTimeline from '@/components/project/ProjectTimeline.vue'
import TimelineEntryDialog from '@/components/project/TimelineEntryDialog.vue'
import { PROCESS_STAGES } from '@/constants/processStages'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useDocumentStore } from '@/stores/documentStore'
import { useProjectApprovalStore } from '@/stores/projectApprovalStore'
import { useProjectExecutionStore } from '@/stores/projectExecutionStore'
import { useProjectStore } from '@/stores/projectStore'
import { useTaskStore } from '@/stores/taskStore'
import { useTimelineStore } from '@/stores/timelineStore'
import { useToastStore } from '@/stores/toastStore'
import type { Project, ProjectWorkspaceTabKey } from '@/types/Project'
import type { TimelineEvent } from '@/types/Timeline'
import { formatDate } from '@/utils/dateFormatter'

const props = defineProps<{
  project: Project
}>()

const emit = defineEmits<{
  'navigate-tab': [tab: ProjectWorkspaceTabKey]
}>()

const router = useRouter()
const executionStore = useProjectExecutionStore()
const approvalStore = useProjectApprovalStore()
const projectStore = useProjectStore()
const toastStore = useToastStore()
const timelineStore = useTimelineStore()
const documentStore = useDocumentStore()
const taskStore = useTaskStore()

function loadData(): void {
  executionStore.loadSteps(props.project.id)
  approvalStore.loadSteps(props.project.id)
  timelineStore.loadTimelineForProject(props.project.id)
  // Documents and Tasks are only needed here for the status cards'
  // counts -- loaded once, lazily, same "load if not already loaded"
  // convention as the Documents/Tasks tabs use themselves, so opening
  // this tab first doesn't cost a duplicate fetch if those tabs are
  // opened afterward.
  if (documentStore.documents.length === 0) documentStore.loadDocuments()
  if (taskStore.tasks.length === 0) taskStore.loadTasks()
}

onMounted(loadData)
// A project id changing under an already-mounted tab (unlikely given
// how tabs are wired, but worth guarding rather than assuming can't
// happen) should reload rather than keep showing the previous
// project's checklists.
watch(() => props.project.id, loadData)

const isLoading = computed(() => executionStore.isLoading || approvalStore.isLoading || timelineStore.isLoading)
const error = computed(() => executionStore.error ?? approvalStore.error ?? timelineStore.error)

const projectDocuments = computed(() => documentStore.documentsByProject(props.project.id))
const pendingReviewDocuments = computed(() => projectDocuments.value.filter((d) => d.status === 'Under Review'))

const projectTasks = computed(() => taskStore.tasksByProject(props.project.id))
const openTasks = computed(() => projectTasks.value.filter((t) => t.status !== 'Completed'))
const overdueTasks = computed(() =>
  openTasks.value.filter((t) => t.dueDate < new Date().toISOString().slice(0, 10)),
)

// One unified process view -- the 5 Project Approval Process stages,
// each expanded to the execution steps, stage-gate document, and
// project documents that feed into it.
const stagesWithSteps = computed(() =>
  PROCESS_STAGES.map((stage) => {
    const executionSteps = executionStore.steps
      .filter((s) => s.stageKey === stage.key)
      .sort((a, b) => a.sequenceNumber - b.sequenceNumber)
    return {
      stage,
      approvalStep: approvalStore.steps.find((s) => s.stageKey === stage.key),
      executionSteps,
      // The backend blocks uploading a stage's gate document while any of
      // its own execution steps are still below 100% -- checked here too
      // so the uploader doesn't invite a file that's just going to fail
      // with a toast. A stage with no execution steps of its own (e.g.
      // "Permit Approved") has nothing to wait on.
      hasPendingExecutionSteps: executionSteps.some((s) => s.completionPercentage < 100),
      documents: projectDocuments.value.filter((d) => d.stageKey === stage.key),
    }
  }),
)

const stageGateCompleteCount = computed(() => approvalStore.steps.filter((s) => s.hasDocument).length)

// Collapsed by default -- only one stage's detail (steps + documents)
// is expanded at a time; opening another collapses whichever was open,
// same as any single-open accordion.
const expandedStageKey = ref<string | null>(null)

function toggleStage(key: string): void {
  expandedStageKey.value = expandedStageKey.value === key ? null : key
}

function openDocument(documentId: string): void {
  router.push({ name: ROUTE_NAMES.DOCUMENT_VIEWER, params: { documentId } })
}

async function refreshProgress(): Promise<void> {
  // The backend recomputes project.progress as part of resolving an
  // execution step -- refresh just this one project so the progress
  // shown elsewhere on this page (header, overview card) picks up the
  // new number too, not just this tab's own checklist state.
  await projectStore.refreshProject(props.project.id)
}

const savingStepId = ref<string | undefined>(undefined)

async function handleSaveStepProgress(stepId: string, percentage: number, remarks: string): Promise<void> {
  savingStepId.value = stepId
  try {
    await executionStore.setStepProgress(props.project.id, stepId, percentage, remarks)
    if (executionStore.mutationError) {
      toastStore.show('error', 'Could not save step progress', executionStore.mutationError)
      return
    }
    await refreshProgress()
  } finally {
    savingStepId.value = undefined
  }
}

const replacingStageKey = ref<string | null>(null)

async function handleUploadStageGateDocument(stageKey: string, file: File | undefined): Promise<void> {
  if (!file) return
  await approvalStore.uploadStageGateDocument(props.project.id, stageKey, file)
  if (approvalStore.mutationError) {
    toastStore.show('error', 'Could not upload stage gate document', approvalStore.mutationError)
    return
  }
  replacingStageKey.value = null
  toastStore.show('success', 'Stage gate document uploaded', 'This stage is now marked complete.')
}

function handleViewStageGateDocument(stageKey: string, filename: string): void {
  void approvalStore.downloadStageGateDocument(props.project.id, stageKey, filename)
}

// History -- the project's full timeline/activity feed, folded in here
// rather than living on its own tab (it used to be duplicated across a
// Timeline tab and an Activity tab that showed the exact same events,
// just sorted in reverse).
const isTimelineDialogOpen = ref(false)
const editingTimelineEvent = ref<TimelineEvent | undefined>(undefined)

function openAddTimelineEntry(): void {
  editingTimelineEvent.value = undefined
  isTimelineDialogOpen.value = true
}

function openEditTimelineEntry(event: TimelineEvent): void {
  editingTimelineEvent.value = event
  isTimelineDialogOpen.value = true
}

function handleSaveTimelineEntry(event: TimelineEvent): void {
  if (editingTimelineEvent.value) {
    void timelineStore.saveEventUpdate(props.project.id, event.id, {
      title: event.title,
      description: event.description,
      status: event.status,
      date: event.date,
    })
  } else {
    void timelineStore.createEvent(props.project.id, {
      title: event.title,
      description: event.description,
      status: event.status,
      date: event.date,
    })
  }
}

// Change Scope -- edits the project's scope-of-work description; if it
// actually changed, asks whether Contract/Payment need a follow-up
// update and notifies every Administrator when either does.
const isChangeScopeDialogOpen = ref(false)
const isChangingScope = ref(false)

async function handleConfirmScopeChange(
  description: string,
  contractUpdateNeeded: boolean,
  paymentUpdateNeeded: boolean,
): Promise<void> {
  isChangingScope.value = true
  try {
    await projectStore.changeScope(props.project.id, description, contractUpdateNeeded, paymentUpdateNeeded)
    isChangeScopeDialogOpen.value = false
    toastStore.show('success', 'Scope updated', 'The project scope was updated.')
  } catch (error) {
    toastStore.show('error', 'Could not update scope', error instanceof Error ? error.message : 'Please try again.')
  } finally {
    isChangingScope.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <ErrorState v-if="error" :description="error" @retry="loadData" />

    <div v-else-if="isLoading" class="rounded-xl border border-border-light bg-bg-card p-6">
      <SkeletonLoader :rows="10" />
    </div>

    <template v-else>
      <Card>
        <div class="flex flex-col gap-4 tablet:flex-row tablet:items-center tablet:justify-between">
          <div class="min-w-0">
            <h2 class="text-sm font-semibold text-text-primary">Overall Execution</h2>
            <p class="text-xs text-text-muted">
              Weighted across all 23 execution steps · {{ stageGateCompleteCount }} of 5 stage gates uploaded
            </p>
          </div>
          <div class="flex items-center gap-3">
            <div class="h-2 w-40 overflow-hidden rounded-full bg-bg-secondary">
              <div
                class="h-full rounded-full bg-primary-600 transition-[width] duration-normal"
                :style="{ width: `${executionStore.weightedProgress}%` }"
              />
            </div>
            <span class="text-lg font-semibold text-text-primary">{{ executionStore.weightedProgress }}%</span>
          </div>
          <BaseButton variant="secondary" size="sm" class="no-print" @click="isChangeScopeDialogOpen = true">
            Change Scope
          </BaseButton>
        </div>
      </Card>

      <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <button
          type="button"
          class="flex items-center gap-3 rounded-xl border border-border-light bg-bg-card p-4 text-left shadow-glass-sm transition-shadow duration-normal hover:shadow-glass"
          @click="emit('navigate-tab', 'documents')"
        >
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-info-50 text-info-600">
            <FileText class="h-5 w-5" />
          </span>
          <span class="min-w-0 flex-1">
            <span class="block text-sm font-semibold text-text-primary">
              {{ documentStore.isLoading ? '…' : projectDocuments.length }} Documents
            </span>
            <span class="block text-xs text-text-muted">
              {{ documentStore.isLoading ? 'Loading…' : `${pendingReviewDocuments.length} pending review` }}
            </span>
          </span>
        </button>

        <button
          type="button"
          class="flex items-center gap-3 rounded-xl border border-border-light bg-bg-card p-4 text-left shadow-glass-sm transition-shadow duration-normal hover:shadow-glass"
          @click="emit('navigate-tab', 'tasks')"
        >
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-warning-50 text-warning-600">
            <ListChecks class="h-5 w-5" />
          </span>
          <span class="min-w-0 flex-1">
            <span class="block text-sm font-semibold text-text-primary">
              {{ taskStore.isLoading ? '…' : openTasks.length }} Open Tasks
            </span>
            <span class="block text-xs text-text-muted">
              {{ taskStore.isLoading ? 'Loading…' : `${overdueTasks.length} overdue` }}
            </span>
          </span>
        </button>
      </div>

      <Card v-for="{ stage, approvalStep, executionSteps, hasPendingExecutionSteps, documents } in stagesWithSteps" :key="stage.key">
        <template #header>
          <div class="flex items-center justify-between gap-3">
            <button
              type="button"
              class="flex min-w-0 items-center gap-2 text-left"
              :aria-expanded="expandedStageKey === stage.key"
              @click="toggleStage(stage.key)"
            >
              <ChevronDown v-if="expandedStageKey === stage.key" class="h-4 w-4 shrink-0 text-text-muted" />
              <ChevronRight v-else class="h-4 w-4 shrink-0 text-text-muted" />
              <CheckCircle2 v-if="approvalStep?.hasDocument" class="h-5 w-5 shrink-0 text-success-600" />
              <Circle v-else class="h-5 w-5 shrink-0 text-text-muted" />
              <h2 class="text-sm font-semibold text-text-primary">{{ stage.label }}</h2>
            </button>

            <span
              v-if="approvalStep && !approvalStep.hasDocument && hasPendingExecutionSteps"
              class="text-xs text-text-muted"
            >
              Waiting on this stage's execution steps
            </span>
            <span v-else-if="approvalStep?.hasDocument" class="text-xs text-text-muted">
              Uploaded{{ approvalStep.uploadedByName ? ` by ${approvalStep.uploadedByName}` : '' }}{{ approvalStep.uploadedAt ? ` on ${formatDate(approvalStep.uploadedAt)}` : '' }}
            </span>
          </div>
        </template>

        <div v-if="expandedStageKey === stage.key" class="flex flex-col gap-5">
          <div>
            <h3 class="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">Stage Gate Review Document</h3>
            <template v-if="approvalStep?.hasDocument">
              <div class="flex items-center gap-3 rounded-lg border border-success-100 bg-success-50 p-3">
                <FileText class="h-5 w-5 shrink-0 text-success-600" />
                <span class="min-w-0 flex-1 truncate text-sm font-medium text-text-primary">{{ approvalStep.originalFilename }}</span>
                <BaseButton size="sm" variant="ghost" @click="handleViewStageGateDocument(stage.key, approvalStep.originalFilename ?? 'document')">
                  View File
                </BaseButton>
                <BaseButton
                  size="sm"
                  variant="ghost"
                  @click="replacingStageKey = replacingStageKey === stage.key ? null : stage.key"
                >
                  Replace
                </BaseButton>
              </div>
              <FileUploader
                v-if="replacingStageKey === stage.key"
                class="mt-2"
                @select="(file) => handleUploadStageGateDocument(stage.key, file)"
              />
            </template>
            <FileUploader
              v-else
              :hint="hasPendingExecutionSteps ? `Complete or waive this stage's execution steps first` : 'Uploading marks this stage complete'"
              @select="(file) => handleUploadStageGateDocument(stage.key, file)"
            />
          </div>

          <div>
            <h3 class="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">Execution Steps</h3>
            <p v-if="executionSteps.length === 0" class="text-xs text-text-muted">
              No execution steps feed into this stage -- it's an external approval gate on its own.
            </p>
            <ol v-else class="flex flex-col gap-2">
              <ExecutionStepRow
                v-for="step in executionSteps"
                :key="step.id"
                :step="step"
                :is-saving="savingStepId === step.id"
                @save="(percentage, remarks) => handleSaveStepProgress(step.id, percentage, remarks)"
              />
            </ol>
          </div>

          <div>
            <h3 class="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">Documents</h3>
            <p v-if="documents.length === 0" class="text-xs text-text-muted">
              No documents tagged to this stage yet -- add one from the Documents tab.
            </p>
            <ul v-else class="flex flex-col gap-2">
              <li
                v-for="document in documents"
                :key="document.id"
                class="flex items-center gap-3 rounded-lg border border-border-light bg-bg-card p-3"
              >
                <div class="min-w-0 flex-1">
                  <p class="text-sm font-medium text-text-primary">{{ document.title }}</p>
                  <p class="text-xs text-text-muted">
                    {{ document.revision }} · {{ document.status }} · Uploaded by {{ document.uploadedBy }}
                  </p>
                </div>
                <BaseButton size="sm" variant="ghost" @click="openDocument(document.id)">View</BaseButton>
              </li>
            </ul>
          </div>
        </div>
      </Card>

      <div class="mt-2 flex items-center justify-between">
        <h2 class="text-sm font-semibold text-text-primary">History</h2>
        <BaseButton variant="secondary" size="sm" :icon="Plus" class="no-print" @click="openAddTimelineEntry">
          Add Update
        </BaseButton>
      </div>
      <ProjectTimeline :events="timelineStore.events" editable @edit="openEditTimelineEntry" />
    </template>

    <ChangeScopeDialog
      v-model="isChangeScopeDialogOpen"
      :current-description="project.description ?? ''"
      :is-submitting="isChangingScope"
      @confirm="handleConfirmScopeChange"
    />

    <TimelineEntryDialog
      v-model="isTimelineDialogOpen"
      :project-id="project.id"
      :event="editingTimelineEvent"
      @save="handleSaveTimelineEntry"
    />
  </div>
</template>
