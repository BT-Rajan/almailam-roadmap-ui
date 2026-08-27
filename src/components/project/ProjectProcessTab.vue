<script setup lang="ts">
import { ChevronDown, ChevronRight, CheckCircle2, Circle, FileText, Plus } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import ChangeScopeDialog from '@/components/project/ChangeScopeDialog.vue'
import ExecutionStepChecklist from '@/components/project/ExecutionStepChecklist.vue'
import ScopeExecutionPanel from '@/components/project/ScopeExecutionPanel.vue'
import FileUploader from '@/components/document/FileUploader.vue'
import ProjectTimeline from '@/components/project/ProjectTimeline.vue'
import TimelineEntryDialog from '@/components/project/TimelineEntryDialog.vue'
import { PROCESS_STAGES } from '@/constants/processStages'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useDocumentStore } from '@/stores/documentStore'
import { useProjectStageStore } from '@/stores/projectStageStore'
import { useProjectStore } from '@/stores/projectStore'
import { useTimelineStore } from '@/stores/timelineStore'
import { useToastStore } from '@/stores/toastStore'
import type { Project } from '@/types/Project'
import type { TimelineEvent } from '@/types/Timeline'
import type { ExecutionStepBulkItem } from '@/types/ExecutionStep'
import { formatDate } from '@/utils/dateFormatter'

const props = defineProps<{
  project: Project
}>()

const router = useRouter()
// The approval stages and execution activities are two independent
// tracks that both run against the project at the same time -- neither
// gates the other (see projectStageStore for why they were merged into
// one store while staying two separate lists, not one nested inside
// the other).
const stageStore = useProjectStageStore()
const projectStore = useProjectStore()
const toastStore = useToastStore()
const timelineStore = useTimelineStore()
const documentStore = useDocumentStore()

function loadData(): void {
  stageStore.load(props.project.id)
  timelineStore.loadTimelineForProject(props.project.id)
  // Only needed for the Approval Stages accordion's per-stage tagged-
  // document list below -- loaded once, lazily, same "load if not
  // already loaded" convention the Documents tab itself uses, so
  // opening this tab first doesn't cost a duplicate fetch if the
  // Documents tab is opened afterward.
  if (documentStore.documents.length === 0) documentStore.loadDocuments()
}

onMounted(loadData)
// A project id changing under an already-mounted tab (unlikely given
// how tabs are wired, but worth guarding rather than assuming can't
// happen) should reload rather than keep showing the previous
// project's checklists.
watch(() => props.project.id, loadData)
// The "Stage" control lives in the page header, a sibling of this tab,
// not inside it -- so a stage change while this tab is already mounted
// updates the backend (including auto-completing any execution
// activities and closing any approval gates tied to stages the project
// has now moved past -- see execution_step_service.
// auto_fill_steps_for_passed_stages) without this tab ever hearing
// about it. Without this watcher the checklist below silently goes
// stale: activities/gates that are genuinely done on the server keep
// showing as outstanding until the user navigates away and back,
// forcing a remount. Reloading on every stage change keeps the two in
// sync the moment the header action completes.
watch(() => props.project.currentStage, loadData)

const isLoading = computed(() => stageStore.isLoading || timelineStore.isLoading)
const error = computed(() => stageStore.error ?? timelineStore.error)

// Four focused views instead of one long scrolling page -- scope
// tracking, the 5 approval gates, the execution checklist, and the
// project's activity history each get their own tab rather than being
// stacked on top of each other. Documents and Tasks aren't repeated
// here at all -- they're real top-level tabs now (see
// ProjectWorkspacePage.vue's TABS computed), so a quick-link back to
// them would just be the same duplication moved one component over.
type ProcessSubTab = 'scope' | 'approvals' | 'checklist' | 'history'

const SUB_TABS: { key: ProcessSubTab; label: string }[] = [
  { key: 'scope', label: 'Scope & Progress' },
  { key: 'approvals', label: 'Approval Stages' },
  { key: 'checklist', label: 'Checklist' },
  { key: 'history', label: 'History' },
]

const activeSubTab = ref<ProcessSubTab>('scope')

async function refreshProgress(): Promise<void> {
  // The backend recomputes project.progress as part of resolving an
  // execution activity -- refresh just this one project so the progress
  // shown elsewhere on this page (header, overview card) picks up the
  // new number too, not just this panel's own list.
  await projectStore.refreshProject(props.project.id)
}

const isSavingChecklist = ref(false)

async function handleSaveChecklist(items: ExecutionStepBulkItem[]): Promise<void> {
  isSavingChecklist.value = true
  try {
    await stageStore.bulkSaveSteps(props.project.id, items)
    if (stageStore.mutationError) {
      toastStore.show('error', 'Could not save checklist', stageStore.mutationError)
      return
    }
    await refreshProgress()
    toastStore.show('success', 'Checklist saved', `${items.length} ${items.length === 1 ? 'activity' : 'activities'} updated.`)
  } finally {
    isSavingChecklist.value = false
  }
}

// Staff's own "freedom to add" beyond whatever the project's assigned
// step set specified -- the complement of excluding a template-derived
// step (which the checklist's "Not applicable" checkbox already covers,
// via handleSaveChecklist's bulk save).
async function handleAddCustomStep(name: string, weightPercentage: number, stageKey: string): Promise<void> {
  await stageStore.addCustomStep(props.project.id, name, weightPercentage, stageKey)
  if (stageStore.mutationError) {
    toastStore.show('error', 'Could not add step', stageStore.mutationError)
    return
  }
  await refreshProgress()
}

async function handleRemoveCustomStep(stepId: string): Promise<void> {
  await stageStore.deleteCustomStep(props.project.id, stepId)
  if (stageStore.mutationError) {
    toastStore.show('error', 'Could not remove step', stageStore.mutationError)
    return
  }
  await refreshProgress()
}

const replacingStageKey = ref<string | null>(null)

async function handleUploadStageGateDocument(stageKey: string, file: File | undefined): Promise<void> {
  if (!file) return
  await stageStore.uploadStageGateDocument(props.project.id, stageKey, file)
  if (stageStore.mutationError) {
    toastStore.show('error', 'Could not upload stage gate document', stageStore.mutationError)
    return
  }
  replacingStageKey.value = null
  // Closing the last of the required stage gates is one of the things
  // "Government Submission" -> "Execution & Tracking" waits on -- same
  // reasoning as refreshProgress() above for the execution checklist.
  await projectStore.refreshProject(props.project.id)
  toastStore.show('success', 'Stage gate document uploaded', 'This stage is now marked complete.')
}

function handleViewStageGateDocument(stageKey: string, filename: string): void {
  void stageStore.downloadStageGateDocument(props.project.id, stageKey, filename)
}

// The Approval Stages panel -- 5 external/client gates, each with its
// own gate document and its own tagged project documents. No execution
// activities nested here: they aren't partitioned under a stage, they
// just run in parallel (see the Checklist tab instead).
const projectDocuments = computed(() => documentStore.documentsByProject(props.project.id))
const approvalStagesView = computed(() =>
  PROCESS_STAGES.map((stage) => ({
    stage,
    approvalStep: stageStore.approvalSteps.find((s) => s.stageKey === stage.key),
    documents: projectDocuments.value.filter((d) => d.stageKey === stage.key),
  })),
)

// Collapsed by default -- only one stage's detail (gate doc + tagged
// documents) is expanded at a time; opening another collapses whichever
// was open, same as any single-open accordion.
const expandedStageKey = ref<string | null>(null)

function toggleStage(key: string): void {
  expandedStageKey.value = expandedStageKey.value === key ? null : key
}

function openDocument(documentId: string): void {
  router.push({ name: ROUTE_NAMES.DOCUMENT_VIEWER, params: { documentId } })
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
      <div class="flex gap-1 overflow-x-auto border-b border-border-light no-print" role="tablist">
        <button
          v-for="tab in SUB_TABS"
          :key="tab.key"
          type="button"
          role="tab"
          class="shrink-0 whitespace-nowrap rounded-t-md border-b-2 px-4 py-3 text-sm font-medium transition-colors duration-fast focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500"
          :class="
            activeSubTab === tab.key
              ? 'border-primary-600 text-primary-700'
              : 'border-transparent text-text-muted hover:text-text-primary'
          "
          :aria-selected="activeSubTab === tab.key"
          @click="activeSubTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <div v-if="activeSubTab === 'scope'" class="flex flex-col gap-4">
        <div class="flex justify-end">
          <BaseButton variant="secondary" size="sm" class="no-print" @click="isChangeScopeDialogOpen = true">
            Change Scope
          </BaseButton>
        </div>
        <ScopeExecutionPanel :project="project" :execution-steps="stageStore.orderedExecutionSteps" @refresh="refreshProgress" />
      </div>

      <div v-else-if="activeSubTab === 'approvals'" class="flex flex-col gap-4">
        <p class="text-xs text-text-muted">5 external gates, tracked independently of the execution checklist.</p>

        <Card v-for="{ stage, approvalStep, documents } in approvalStagesView" :key="stage.key">
          <template #header>
            <div class="flex items-center justify-between gap-3">
              <button
                type="button"
                class="flex min-w-0 items-center gap-2 text-left"
                :aria-expanded="expandedStageKey === stage.key"
                @click="toggleStage(stage.key)"
              >
                <ChevronDown v-if="expandedStageKey === stage.key" class="h-4 w-4 shrink-0 text-text-muted" aria-hidden="true" />
                <ChevronRight v-else class="h-4 w-4 shrink-0 text-text-muted" aria-hidden="true" />
                <CheckCircle2 v-if="approvalStep?.isComplete" class="h-5 w-5 shrink-0 text-success-600" aria-hidden="true" />
                <Circle v-else class="h-5 w-5 shrink-0 text-text-muted" aria-hidden="true" />
                <h2 class="text-sm font-semibold text-text-primary">{{ stage.label }}</h2>
                <span class="sr-only">{{ approvalStep?.isComplete ? '(Complete)' : '(Incomplete)' }}</span>
              </button>

              <span v-if="approvalStep?.hasDocument" class="text-xs text-text-muted">
                Uploaded{{ approvalStep.uploadedByName ? ` by ${approvalStep.uploadedByName}` : '' }}{{ approvalStep.uploadedAt ? ` on ${formatDate(approvalStep.uploadedAt)}` : '' }}
              </span>
              <span v-else-if="approvalStep?.isComplete" class="text-xs text-text-muted">
                Completed from document approvals{{ approvalStep.completedByName ? ` by ${approvalStep.completedByName}` : '' }}{{ approvalStep.completedAt ? ` on ${formatDate(approvalStep.completedAt)}` : '' }}
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
                hint="Uploading marks this stage complete"
                @select="(file) => handleUploadStageGateDocument(stage.key, file)"
              />
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
      </div>

      <div v-else-if="activeSubTab === 'checklist'" class="flex flex-col gap-4">
        <p class="text-xs text-text-muted">
          {{ stageStore.executionSteps.length }} activities from this project's assigned checklist.
        </p>
        <Card>
          <ExecutionStepChecklist
            :steps="stageStore.orderedExecutionSteps"
            :is-saving="isSavingChecklist"
            @save="handleSaveChecklist"
            @add-step="handleAddCustomStep"
            @remove-step="handleRemoveCustomStep"
          />
        </Card>
      </div>

      <div v-else class="flex flex-col gap-4">
        <div class="flex items-center justify-between">
          <p class="text-xs text-text-muted">This project's full activity feed.</p>
          <BaseButton variant="secondary" size="sm" :icon="Plus" class="no-print" @click="openAddTimelineEntry">
            Add Update
          </BaseButton>
        </div>
        <ProjectTimeline :events="timelineStore.events" editable @edit="openEditTimelineEntry" />
      </div>
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
