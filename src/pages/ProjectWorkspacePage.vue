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
import ServicePickerDialog from '@/components/project/ServicePickerDialog.vue'
import type { ServicePickerConfirmPayload } from '@/components/project/ServicePickerDialog.vue'
import WorkflowProgress from '@/components/project/WorkflowProgress.vue'

// Lazy-loaded: only fetched when the user actually opens that tab, instead of
// shipping with the page on first load.
const ProjectRequirementTab = defineAsyncComponent(() => import('@/components/project/ProjectRequirementTab.vue'))
const ProjectQuotationTab = defineAsyncComponent(() => import('@/components/project/ProjectQuotationTab.vue'))
const ProjectContractTab = defineAsyncComponent(() => import('@/components/project/ProjectContractTab.vue'))
const ProjectDocumentsTab = defineAsyncComponent(() => import('@/components/project/ProjectDocumentsTab.vue'))
const ProjectGovernmentTab = defineAsyncComponent(() => import('@/components/project/ProjectGovernmentTab.vue'))
const ProjectTasksTab = defineAsyncComponent(() => import('@/components/project/ProjectTasksTab.vue'))
const PaymentPlanPanel = defineAsyncComponent(() => import('@/components/payment/PaymentPlanPanel.vue'))
const PaymentStatusPanel = defineAsyncComponent(() => import('@/components/payment/PaymentStatusPanel.vue'))
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useContractStore } from '@/stores/contractStore'
import { useDocumentStore } from '@/stores/documentStore'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { usePaymentStore } from '@/stores/paymentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useServiceCatalogStore } from '@/stores/serviceCatalogStore'
import { useTaskStore } from '@/stores/taskStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import type { ProjectUpdateInput } from '@/services/projectService'
import type { AddServicesInput, ProjectWorkspaceTab, ProjectWorkspaceTabKey, WorkflowStage } from '@/types/Project'
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
const serviceCatalogStore = useServiceCatalogStore()
const resultDialogStore = useResultDialogStore()

const projectId = computed(() => route.params.projectId as string)

const VALID_TAB_KEYS: ProjectWorkspaceTabKey[] = ['overview', 'requirement', 'documents', 'quotation', 'payment-plan', 'payment-status', 'contract', 'design', 'supervision', 'government', 'tasks']
const queryTab = route.query.tab
const initialTab = typeof queryTab === 'string' && VALID_TAB_KEYS.includes(queryTab as ProjectWorkspaceTabKey) ? (queryTab as ProjectWorkspaceTabKey) : 'overview'
const activeTab = ref<ProjectWorkspaceTabKey>(initialTab)

// Quotation, Contract, Design, and Government aren't buttons here --
// they're reachable from the Workflow Progress stepper above (see
// WorkflowProgress.vue), which already says those exact same words.
// Keeping both would just be the same duplication moved one component
// over. Their tab keys stay valid (VALID_TAB_KEYS below, and the v-if
// chain further down) so the stepper can still land on them, with
// every function of that tab unchanged.
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
// actually working.
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
  'payment-plan': 'Payment Plan',
  'payment-status': 'Payment Plan',
  contract: 'Contract',
  design: 'Design',
  supervision: 'Supervision',
  government: 'Government Submission',
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
    case 'Payment Plan':
      // Unlike Quotation/Contract/Design/Government, Payment Plan and
      // Payment Status are real top-bar tabs here rather than only
      // stepper-driven -- this is the one stage where staff are actively
      // working the payment plan itself (define/edit/approve it, then
      // track what's actually been collected against it), so both
      // deserve their own tab rather than being buried behind the
      // stepper the way a stage staff mostly just glance at doesn't.
      return [
        { key: 'overview', label: 'Overview' },
        { key: 'payment-plan', label: 'Payment Plan' },
        { key: 'payment-status', label: 'Payment Status' },
        { key: 'tasks', label: 'Tasks' },
      ]
    case 'Contract':
      // No Payments tab here -- Payment Plan is its own stage now (the
      // financial agreement is created and approved there, before a
      // project ever reaches Contract), reachable any time via the
      // Workflow Progress stepper's own Payment Plan step. Duplicating
      // that same view behind a top-tab in every later stage as well
      // was the thing being removed.
      return [
        { key: 'overview', label: 'Overview' },
        { key: 'documents', label: 'Documents' },
        { key: 'tasks', label: 'Tasks' },
      ]
    case 'Design':
      // Reuses the existing 'design' tab key (ProjectDocumentsTab's
      // mode="design", Drawing-typed documents only) rather than the
      // generic 'documents' key, which would show every project
      // document, not just design deliverables. No Payments tab here --
      // see the Contract case above for why.
      return [
        { key: 'overview', label: 'Overview' },
        { key: 'design', label: 'Documents' },
        { key: 'tasks', label: 'Tasks' },
      ]
    case 'Supervision':
      // Plain placeholder for now -- reuses the generic 'documents' mode
      // (no supervision-specific document type/filtering yet), same as
      // the Contract/Government Submission stages' own Documents tab.
      // No Payments tab here either -- see the Contract case above.
      return [
        { key: 'overview', label: 'Overview' },
        { key: 'supervision', label: 'Documents' },
        { key: 'tasks', label: 'Tasks' },
      ]
    case 'Government Submission':
      // Reuses the existing 'government' tab key -- ProjectGovernmentTab.vue
      // already has the full submission list/create/detail experience, so
      // it becomes this stage's Documents tab content unchanged. No
      // Payments tab here either -- see the Contract case above.
      return [
        { key: 'overview', label: 'Overview' },
        { key: 'government', label: 'Documents' },
        { key: 'tasks', label: 'Tasks' },
      ]
    default:
      return [
        { key: 'overview', label: 'Overview' },
        { key: 'documents', label: 'Documents' },
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
  const topBarKeys: ProjectWorkspaceTabKey[] = ['overview', 'documents', 'design', 'supervision', 'government', 'payment-plan', 'payment-status', 'tasks']
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
    if ((tab === 'documents' || tab === 'design' || tab === 'supervision') && documentStore.documents.length === 0) {
      documentStore.loadDocuments()
    }
    if (tab === 'government' && governmentSubmissionStore.submissions.length === 0) {
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
const isAddServiceDialogOpen = ref(false)
const isAddServiceSaving = ref(false)
const isDeleteDialogOpen = ref(false)
const isDeleteSaving = ref(false)

function openAddServiceDialog(): void {
  if (serviceCatalogStore.services.length === 0) serviceCatalogStore.loadServices()
  isAddServiceDialogOpen.value = true
}

async function handleAddServices(payload: ServicePickerConfirmPayload): Promise<void> {
  if (!project.value) return
  isAddServiceSaving.value = true
  try {
    // Only what's newly checked here actually gets added -- anything
    // already part of the project is silently ignored server-side (see
    // project_service.add_selected_services), so sending the dialog's
    // full current+new selection back is safe even though it also
    // includes rows the project already had.
    const input: AddServicesInput = {
      designActivities: payload.design,
      supervisionActivities: payload.supervision,
      supervisionStartDate: payload.supervisionStartDate,
      supervisionEndDate: payload.supervisionEndDate,
    }
    await projectStore.addServices(project.value.id, input)
    resultDialogStore.showSuccess(
      'Services added',
      'Cover the new work with a quotation, payment plan, and contract the same way as the rest of this project.',
    )
    isAddServiceDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to add services', detail)
  } finally {
    isAddServiceSaving.value = false
  }
}

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
        @add-service="openAddServiceDialog"
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

      <WorkflowProgress
        class="no-print"
        :current-stage="project.currentStage"
        :includes-design="project.includesDesign"
        :includes-supervision="project.includesSupervision"
        @navigate-tab="activeTab = $event"
      />

      <ProjectWorkspaceTabs :tabs="TABS" :active-tab="activeTab" @select="activeTab = $event" />

      <div v-if="activeTab === 'overview'" id="project-tabpanel-overview" role="tabpanel" aria-labelledby="project-tab-overview" tabindex="0">
        <ProjectOverviewTab :project="project" :client="client" :stage-context="stageContext" @navigate-tab="activeTab = $event" />
      </div>
      <ProjectRequirementTab v-else-if="activeTab === 'requirement'" :project="project" :client="client" @navigate-tab="activeTab = $event" />
      <ProjectQuotationTab v-else-if="activeTab === 'quotation'" :project="project" :client="client" @navigate-tab="activeTab = $event" />
      <ProjectContractTab v-else-if="activeTab === 'contract'" :project="project" :client="client" />
      <div
        v-else-if="activeTab === 'documents' || activeTab === 'design'"
        :id="activeTab === 'documents' ? 'project-tabpanel-documents' : undefined"
        role="tabpanel"
        :aria-labelledby="activeTab === 'documents' ? 'project-tab-documents' : undefined"
        tabindex="0"
      >
        <ProjectDocumentsTab :project="project" :mode="activeTab" />
      </div>
      <div v-else-if="activeTab === 'supervision'" id="project-tabpanel-supervision" role="tabpanel" aria-labelledby="project-tab-supervision" tabindex="0">
        <ProjectDocumentsTab :project="project" mode="documents" />
      </div>
      <ProjectGovernmentTab v-else-if="activeTab === 'government'" :project-id="projectId" />
      <div v-else-if="activeTab === 'tasks'" id="project-tabpanel-tasks" role="tabpanel" aria-labelledby="project-tab-tasks" tabindex="0">
        <ProjectTasksTab :project="project" />
      </div>
      <div v-else-if="activeTab === 'payment-plan'" id="project-tabpanel-payment-plan" role="tabpanel" aria-labelledby="project-tab-payment-plan" tabindex="0">
        <PaymentPlanPanel :project-id="projectId" :project="project" @navigate-tab="activeTab = $event" @add-service="openAddServiceDialog" />
      </div>
      <div v-else-if="activeTab === 'payment-status'" id="project-tabpanel-payment-status" role="tabpanel" aria-labelledby="project-tab-payment-status" tabindex="0">
        <PaymentStatusPanel :project-id="projectId" :project="project" @navigate-tab="activeTab = $event" @add-service="openAddServiceDialog" />
      </div>

      <ProjectEditDialog
        v-model="isEditDialogOpen"
        :project="project"
        :loading="isEditSaving"
        @confirm="handleConfirmEdit"
      />
      <ServicePickerDialog
        v-model="isAddServiceDialogOpen"
        :services="serviceCatalogStore.services"
        :selected-design="project.selectedActivities ?? []"
        :selected-supervision="project.selectedSupervisionActivities ?? []"
        :supervision-start-date="project.supervisionStartDate"
        :supervision-end-date="project.supervisionEndDate"
        @confirm="handleAddServices"
      />
      <ProjectTransitionDialog
        v-model="isStageDialogOpen"
        kind="stage"
        :current-value="project.currentStage"
        :includes-design="project.includesDesign"
        :includes-supervision="project.includesSupervision"
        :project-id="project.id"
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
