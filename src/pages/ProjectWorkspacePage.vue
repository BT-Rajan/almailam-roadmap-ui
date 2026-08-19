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
const ProjectTimelineTab = defineAsyncComponent(() => import('@/components/project/ProjectTimelineTab.vue'))
const ProjectQuotationTab = defineAsyncComponent(() => import('@/components/project/ProjectQuotationTab.vue'))
const ProjectContractTab = defineAsyncComponent(() => import('@/components/project/ProjectContractTab.vue'))
const ProjectDocumentsTab = defineAsyncComponent(() => import('@/components/project/ProjectDocumentsTab.vue'))
const ProjectGovernmentTab = defineAsyncComponent(() => import('@/components/project/ProjectGovernmentTab.vue'))
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
import { useTimelineStore } from '@/stores/timelineStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import type { ProjectUpdateInput } from '@/services/projectService'
import type { ProjectWorkspaceTab, ProjectWorkspaceTabKey } from '@/types/Project'
import { formatDate } from '@/utils/dateFormatter'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const quotationStore = useQuotationStore()
const timelineStore = useTimelineStore()
const contractStore = useContractStore()
const documentStore = useDocumentStore()
const governmentSubmissionStore = useGovernmentSubmissionStore()
const paymentStore = usePaymentStore()
const taskStore = useTaskStore()
const resultDialogStore = useResultDialogStore()

const projectId = computed(() => route.params.projectId as string)

const VALID_TAB_KEYS: ProjectWorkspaceTabKey[] = ['overview', 'timeline', 'documents', 'quotation', 'contract', 'payments', 'design', 'government', 'tasks', 'activity']
const queryTab = route.query.tab
const initialTab = typeof queryTab === 'string' && VALID_TAB_KEYS.includes(queryTab as ProjectWorkspaceTabKey) ? (queryTab as ProjectWorkspaceTabKey) : 'overview'
const activeTab = ref<ProjectWorkspaceTabKey>(initialTab)

const TABS: ProjectWorkspaceTab[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'timeline', label: 'Timeline' },
  { key: 'documents', label: 'Documents' },
  { key: 'quotation', label: 'Quotation' },
  { key: 'contract', label: 'Contract' },
  { key: 'payments', label: 'Payments' },
  { key: 'design', label: 'Design' },
  { key: 'government', label: 'Government' },
  { key: 'tasks', label: 'Tasks' },
  { key: 'activity', label: 'Activity' },
]

const activityEvents = computed(() => [...timelineStore.events].sort((a, b) => b.date.localeCompare(a.date)))

const project = computed(() => projectStore.projects.find((item) => item.id === projectId.value))
const client = computed(() => (project.value ? projectStore.getClientById(project.value.clientId) : undefined))

const isLoading = computed(
  () => projectStore.isLoading || quotationStore.isLoading || timelineStore.isLoading || contractStore.isLoading,
)
const error = computed(
  () => projectStore.error ?? quotationStore.error ?? timelineStore.error ?? contractStore.error,
)

async function loadData(): Promise<void> {
  if (projectStore.projects.length === 0) {
    await projectStore.loadProjects()
  }
  if (paymentStore.agreements.length === 0) {
    await paymentStore.loadAll()
  }
  await Promise.all([
    quotationStore.loadQuotationsForProject(projectId.value),
    timelineStore.loadTimelineForProject(projectId.value),
    contractStore.loadContractsForProject(projectId.value),
  ])
}

onMounted(loadData)
watch(projectId, loadData)

watch(
  activeTab,
  (tab) => {
    if ((tab === 'documents' || tab === 'design') && documentStore.documents.length === 0) {
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
        <InfoPanel label="Responsible Engineer" :value="project.engineer" :icon="User" color="ai" />
        <InfoPanel
          label="Timeline"
          :value="`${formatDate(project.startDate)} \u2013 ${formatDate(project.targetDate)}`"
          :icon="Calendar"
          color="warning"
        />
      </div>

      <WorkflowProgress class="no-print" :current-stage="project.currentStage" />

      <ProjectWorkspaceTabs :tabs="TABS" :active-tab="activeTab" @select="activeTab = $event" />

      <ProjectOverviewTab v-if="activeTab === 'overview'" :project="project" :client="client" />
      <ProjectTimelineTab
        v-else-if="activeTab === 'timeline'"
        :events="timelineStore.events"
        :project-id="projectId"
      />
      <ProjectQuotationTab v-else-if="activeTab === 'quotation'" :project="project" :client="client" />
      <ProjectContractTab v-else-if="activeTab === 'contract'" :project="project" :client="client" />
      <ProjectDocumentsTab
        v-else-if="activeTab === 'documents' || activeTab === 'design'"
        :project="project"
        :mode="activeTab"
      />
      <ProjectGovernmentTab v-else-if="activeTab === 'government'" :project-id="projectId" />
      <ProjectTasksTab v-else-if="activeTab === 'tasks'" :project="project" />
      <ProjectTimelineTab
        v-else-if="activeTab === 'activity'"
        :events="activityEvents"
        :project-id="projectId"
      />
      <PaymentWorkspacePanel v-else-if="activeTab === 'payments'" :project-id="projectId" />

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
