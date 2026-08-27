<script setup lang="ts">
import { Building2, Calendar, Layers, User } from '@lucide/vue'
import { computed, defineAsyncComponent, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import InfoPanel from '@/components/common/InfoPanel.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import ProjectHeader from '@/components/project/ProjectHeader.vue'
import ProjectEditDialog from '@/components/project/ProjectEditDialog.vue'
import ProjectTransitionDialog from '@/components/project/ProjectTransitionDialog.vue'
import ProjectOverviewTab from '@/components/project/ProjectOverviewTab.vue'
import ProjectWorkspaceTabs from '@/components/project/ProjectWorkspaceTabs.vue'
import WorkflowProgress from '@/components/project/WorkflowProgress.vue'

// Lazy-loaded: only fetched when the user actually opens that tab, instead of
// shipping with the page on first load.
const ProjectRequirementTab = defineAsyncComponent(() => import('@/components/project/ProjectRequirementTab.vue'))
const ProjectProcessTab = defineAsyncComponent(() => import('@/components/project/ProjectProcessTab.vue'))
const ProjectQuotationTab = defineAsyncComponent(() => import('@/components/project/ProjectQuotationTab.vue'))
const ProjectContractTab = defineAsyncComponent(() => import('@/components/project/ProjectContractTab.vue'))
const ProjectDocumentsTab = defineAsyncComponent(() => import('@/components/project/ProjectDocumentsTab.vue'))
const ProjectGovernmentTab = defineAsyncComponent(() => import('@/components/project/ProjectGovernmentTab.vue'))
const ProjectCompletionDocumentsTab = defineAsyncComponent(() => import('@/components/project/ProjectCompletionDocumentsTab.vue'))
const ProjectTasksTab = defineAsyncComponent(() => import('@/components/project/ProjectTasksTab.vue'))
const PaymentWorkspacePanel = defineAsyncComponent(() => import('@/components/payment/PaymentWorkspacePanel.vue'))
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useContractStore } from '@/stores/contractStore'
import { useDocumentStore } from '@/stores/documentStore'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { usePaymentStore } from '@/stores/paymentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useTaskStore } from '@/stores/taskStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import type { ProjectUpdateInput } from '@/services/projectService'
import type { ProjectWorkspaceTab, ProjectWorkspaceTabKey, WorkflowStage } from '@/types/Project'
import { formatDate } from '@/utils/dateFormatter'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const quotationStore = useQuotationStore()
const contractStore = useContractStore()
const documentStore = useDocumentStore()
const governmentSubmissionStore = useGovernmentSubmissionStore()
const paymentStore = usePaymentStore()
const taskStore = useTaskStore()
const resultDialogStore = useResultDialogStore()

const projectId = computed(() => route.params.projectId as string)

const VALID_TAB_KEYS: ProjectWorkspaceTabKey[] = ['overview', 'requirement', 'process', 'documents', 'quotation', 'contract', 'payments', 'design', 'government', 'tasks', 'completed', 'completedDocuments']
const queryTab = route.query.tab
const initialTab = typeof queryTab === 'string' && VALID_TAB_KEYS.includes(queryTab as ProjectWorkspaceTabKey) ? (queryTab as ProjectWorkspaceTabKey) : 'overview'
const activeTab = ref<ProjectWorkspaceTabKey>(initialTab)

// Quotation, Contract, Design, Government, and Execution & Tracking
// aren't buttons here -- they're reachable from the Workflow Progress
// stepper above (see WorkflowProgress.vue), which already says those
// exact same words. Keeping both would just be the same duplication
// moved one component over. Their tab keys stay valid (VALID_TAB_KEYS
// below, and the v-if chain further down) so the stepper -- and any
// existing ?tab=process-style deep link -- can still land on them,
// with every function of that tab unchanged.
//
// Which of Overview/Documents/Payments/Tasks actually show here, and
// what the Overview pane itself shows, is driven by `stageContext`
// below -- NOT directly by the project's actual current_stage. The
// Workflow Progress stepper deliberately lets staff jump to *any*
// stage's view regardless of where the project really is right now
// (isStepNavigable in WorkflowProgress.vue always returns true, e.g. to
// draft a quotation early or review a past stage) -- keying this off
// current_stage directly meant that while looking at the Quotation
// stepper view on a project still formally at Requirement, the top
// Overview tab showed Requirement's overview instead of Quotation's,
// which is confusing and was reported as a bug. stageContext instead
// tracks whichever stage section was last actually navigated to via the
// stepper (falling back to the project's real current_stage until the
// first such navigation), so Overview always matches where staff are
// actually working. Payments is relabeled "Payment Config" at Contract,
// the only stage it's currently shown at.
const project = computed(() => projectStore.projects.find((item) => item.id === projectId.value))

const stageContext = ref<WorkflowStage>('Requirement')

// Resets to the project's real stage on first load and whenever
// switching to a different project's workspace -- but not on every
// later reactive update to the *same* project (e.g. a refreshProject()
// call after some unrelated approval), so a stepper-driven context
// someone is mid-review of isn't silently pulled out from under them.
const STAGE_TAB_KEYS: Partial<Record<ProjectWorkspaceTabKey, WorkflowStage>> = {
  requirement: 'Requirement',
  quotation: 'Quotation',
  contract: 'Contract',
  design: 'Design',
  government: 'Government Submission',
  process: 'Execution & Tracking',
  completed: 'Completed',
}

watch(
  project,
  (value, oldValue) => {
    if (value && (!oldValue || oldValue.id !== value.id)) {
      // Respects an explicit stepper-driven deep link (?tab=quotation
      // etc, already reflected in activeTab by the time the project
      // finishes loading) over the project's real stage -- only
      // defaults to the real stage when activeTab isn't already
      // pointing at a specific one.
      stageContext.value = STAGE_TAB_KEYS[activeTab.value] ?? value.currentStage
    }
  },
  { immediate: true },
)

watch(
  activeTab,
  (tab) => {
    const stage = STAGE_TAB_KEYS[tab]
    if (stage) stageContext.value = stage
    // 'completed' is a pure signal (see WorkflowProgress.vue's STAGE_TABS)
    // -- it exists only to get stageContext set above; the actual tab
    // shown is always the shared Overview pane.
    if (tab === 'completed') activeTab.value = 'overview'
  },
  { immediate: true },
)

const TABS = computed<ProjectWorkspaceTab[]>(() => {
  switch (stageContext.value) {
    case 'Requirement':
      return [{ key: 'overview', label: 'Overview' }]
    case 'Quotation':
      return [
        { key: 'overview', label: 'Overview' },
        { key: 'tasks', label: 'Tasks' },
      ]
    case 'Contract':
      return [
        { key: 'overview', label: 'Overview' },
        { key: 'documents', label: 'Documents' },
        { key: 'payments', label: 'Payment Config' },
        { key: 'tasks', label: 'Tasks' },
      ]
    case 'Design':
      // Reuses the existing 'design' tab key (ProjectDocumentsTab's
      // mode="design", Drawing-typed documents only) rather than the
      // generic 'documents' key, which would show every project
      // document, not just design deliverables.
      return [
        { key: 'overview', label: 'Overview' },
        { key: 'design', label: 'Documents' },
        { key: 'tasks', label: 'Tasks' },
      ]
    case 'Government Submission':
      // Reuses the existing 'government' tab key -- ProjectGovernmentTab.vue
      // already has the full submission list/create/detail experience, so
      // it becomes this stage's Documents tab content unchanged (see
      // "retain other features" in the request that added this case).
      return [
        { key: 'overview', label: 'Overview' },
        { key: 'government', label: 'Documents' },
        { key: 'tasks', label: 'Tasks' },
      ]
    case 'Execution & Tracking':
      // 'process' reuses the existing tab key -- ProjectProcessTab.vue's
      // own internal sub-tabs (Scope & Progress / Approval Stages /
      // Checklist / History) become this stage's "Checklist" tab,
      // alongside real Documents/Payments/Tasks tabs like every other
      // stage gets, instead of the old single giant page that crammed
      // all of that plus its own copies of Documents/Tasks together.
      return [
        { key: 'overview', label: 'Overview' },
        { key: 'process', label: 'Checklist' },
        { key: 'documents', label: 'Documents' },
        { key: 'payments', label: 'Payments' },
        { key: 'tasks', label: 'Tasks' },
      ]
    case 'Completed':
      // Documents here means three sub-tabs (Submitted Docs / Approvals &
      // Permits / Project Closure Docs), not the plain single-view
      // 'documents' key -- see ProjectCompletionDocumentsTab.vue.
      return [
        { key: 'overview', label: 'Overview' },
        { key: 'completedDocuments', label: 'Documents' },
        { key: 'payments', label: 'Payments' },
        { key: 'tasks', label: 'Tasks' },
      ]
    default:
      return [
        { key: 'overview', label: 'Overview' },
        { key: 'documents', label: 'Documents' },
        { key: 'payments', label: 'Payments' },
        { key: 'tasks', label: 'Tasks' },
      ]
  }
})

// If the stage change above just hid the tab currently being viewed
// (e.g. sitting on Documents when the context moves to Requirement,
// which only shows Overview), fall back to Overview rather than leaving
// an orphaned, no-longer-reachable pane on screen. Only applies to the
// top tab bar's own keys -- a stepper-driven view (requirement/
// quotation/contract/design/etc, never part of TABS) is never affected
// by this.
watch(TABS, (tabs) => {
  const topBarKeys: ProjectWorkspaceTabKey[] = ['overview', 'documents', 'design', 'government', 'process', 'completedDocuments', 'payments', 'tasks']
  if (topBarKeys.includes(activeTab.value) && !tabs.some((tab) => tab.key === activeTab.value)) {
    activeTab.value = 'overview'
  }
})
const client = computed(() => (project.value ? projectStore.getClientById(project.value.clientId) : undefined))

const isLoading = computed(() => projectStore.isLoading || quotationStore.isLoading || contractStore.isLoading)
const error = computed(() => projectStore.error ?? quotationStore.error ?? contractStore.error)

async function loadData(): Promise<void> {
  if (projectStore.projects.length === 0) {
    await projectStore.loadProjects()
  }
  if (paymentStore.agreements.length === 0) {
    await paymentStore.loadAll()
  }
  await Promise.all([
    quotationStore.loadQuotationsForProject(projectId.value),
    contractStore.loadContractsForProject(projectId.value),
  ])
}

onMounted(loadData)
watch(projectId, loadData)

watch(
  activeTab,
  (tab) => {
    if ((tab === 'documents' || tab === 'design' || tab === 'completedDocuments') && documentStore.documents.length === 0) {
      documentStore.loadDocuments()
    }
    if ((tab === 'government' || tab === 'completedDocuments') && governmentSubmissionStore.submissions.length === 0) {
      governmentSubmissionStore.loadSubmissions()
    }
    if (tab === 'tasks' && taskStore.tasks.length === 0) {
      taskStore.loadTasks()
    }
  },
  { immediate: true },
)

const isEditDialogOpen = ref(false)
const isEditSaving = ref(false)
const isStageDialogOpen = ref(false)
const isStageSaving = ref(false)
const isStatusDialogOpen = ref(false)
const isStatusSaving = ref(false)
const isDeleteDialogOpen = ref(false)
const isDeleteSaving = ref(false)

async function handleConfirmEdit(payload: ProjectUpdateInput): Promise<void> {
  if (!project.value) return
  isEditSaving.value = true
  try {
    await projectStore.updateProject(project.value.id, payload)
    resultDialogStore.showSuccess('Project updated', 'Changes were saved successfully.')
    isEditDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to update project', detail)
  } finally {
    isEditSaving.value = false
  }
}

async function handleConfirmStage(payload: { value: string; reason?: string }): Promise<void> {
  if (!project.value) return
  isStageSaving.value = true
  try {
    await projectStore.setStage(project.value.id, payload.value, payload.reason)
    resultDialogStore.showSuccess('Stage updated', `Project moved to ${payload.value}.`)
    isStageDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to change stage', detail)
  } finally {
    isStageSaving.value = false
  }
}

async function handleConfirmStatus(payload: { value: string; reason?: string }): Promise<void> {
  if (!project.value) return
  isStatusSaving.value = true
  try {
    await projectStore.setStatus(project.value.id, payload.value, payload.reason)
    resultDialogStore.showSuccess('Status updated', `Project marked as ${payload.value}.`)
    isStatusDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to change status', detail)
  } finally {
    isStatusSaving.value = false
  }
}

async function handleConfirmDelete(): Promise<void> {
  if (!project.value) return
  isDeleteSaving.value = true
  try {
    await projectStore.deleteProject(project.value.id)
    resultDialogStore.showSuccess('Project deleted', `${project.value.projectName} was removed.`)
    isDeleteDialogOpen.value = false
    router.push({ name: ROUTE_NAMES.PROJECTS })
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to delete project', detail)
  } finally {
    isDeleteSaving.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <ErrorState v-if="error" :description="error" @retry="loadData" />

    <template v-else-if="isLoading">
      <div class="rounded-xl border border-border-light bg-bg-card p-5">
        <SkeletonLoader :rows="4" />
      </div>
      <div class="rounded-xl border border-border-light bg-bg-card p-5">
        <SkeletonLoader :rows="8" />
      </div>
    </template>

    <EmptyState v-else-if="!project" title="Project not found" description="This project may have been removed or the link is incorrect." />

    <template v-else>
      <ProjectHeader
        :project="project"
        :client="client"
        @edit="isEditDialogOpen = true"
        @change-stage="isStageDialogOpen = true"
        @change-status="isStatusDialogOpen = true"
        @delete="isDeleteDialogOpen = true"
      />

      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-4 no-print">
        <InfoPanel label="Service" :value="project.service" :icon="Layers" />
        <InfoPanel label="Client" :value="client?.companyName ?? 'Unassigned'" :icon="Building2" color="info" />
        <InfoPanel label="Field Engineer" :value="project.engineer" :icon="User" color="ai" />
        <InfoPanel
          label="Timeline"
          :value="`${formatDate(project.startDate)} \u2013 ${formatDate(project.targetDate)}`"
          :icon="Calendar"
          color="warning"
        />
      </div>

      <WorkflowProgress class="no-print" :current-stage="project.currentStage" @navigate-tab="activeTab = $event" />

      <ProjectWorkspaceTabs :tabs="TABS" :active-tab="activeTab" @select="activeTab = $event" />

      <div v-if="activeTab === 'overview'" id="project-tabpanel-overview" role="tabpanel" aria-labelledby="project-tab-overview" tabindex="0">
        <ProjectOverviewTab :project="project" :client="client" :stage-context="stageContext" @navigate-tab="activeTab = $event" />
      </div>
      <ProjectRequirementTab v-else-if="activeTab === 'requirement'" :project="project" :client="client" @navigate-tab="activeTab = $event" />
      <ProjectProcessTab v-if="activeTab === 'process'" :project="project" />
      <ProjectQuotationTab v-else-if="activeTab === 'quotation'" :project="project" :client="client" @navigate-tab="activeTab = $event" />
      <ProjectContractTab v-else-if="activeTab === 'contract'" :project="project" :client="client" @navigate-tab="activeTab = $event" />
      <div
        v-else-if="activeTab === 'documents' || activeTab === 'design'"
        :id="activeTab === 'documents' ? 'project-tabpanel-documents' : undefined"
        role="tabpanel"
        :aria-labelledby="activeTab === 'documents' ? 'project-tab-documents' : undefined"
        tabindex="0"
      >
        <ProjectDocumentsTab :project="project" :mode="activeTab" />
      </div>
      <ProjectGovernmentTab v-else-if="activeTab === 'government'" :project-id="projectId" />
      <div
        v-else-if="activeTab === 'completedDocuments'"
        id="project-tabpanel-completedDocuments"
        role="tabpanel"
        aria-labelledby="project-tab-completedDocuments"
        tabindex="0"
      >
        <ProjectCompletionDocumentsTab :project="project" />
      </div>
      <div v-else-if="activeTab === 'tasks'" id="project-tabpanel-tasks" role="tabpanel" aria-labelledby="project-tab-tasks" tabindex="0">
        <ProjectTasksTab :project="project" />
      </div>
      <div v-else-if="activeTab === 'payments'" id="project-tabpanel-payments" role="tabpanel" aria-labelledby="project-tab-payments" tabindex="0">
        <PaymentWorkspacePanel :project-id="projectId" @navigate-tab="activeTab = $event" />
      </div>

      <ProjectEditDialog
        v-model="isEditDialogOpen"
        :project="project"
        :loading="isEditSaving"
        @confirm="handleConfirmEdit"
      />
      <ProjectTransitionDialog
        v-model="isStageDialogOpen"
        kind="stage"
        :current-value="project.currentStage"
        :loading="isStageSaving"
        @confirm="handleConfirmStage"
      />
      <ProjectTransitionDialog
        v-model="isStatusDialogOpen"
        kind="status"
        :current-value="project.status"
        :loading="isStatusSaving"
        @confirm="handleConfirmStatus"
      />
      <ConfirmationDialog
        v-model="isDeleteDialogOpen"
        title="Delete project"
        :message="`Delete ${project.projectName}? This cannot be undone from the app.`"
        confirm-label="Delete"
        confirm-variant="danger"
        :loading="isDeleteSaving"
        @confirm="handleConfirmDelete"
      />
    </template>
  </div>
</template>
