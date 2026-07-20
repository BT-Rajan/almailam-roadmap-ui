<script setup lang="ts">
import { Building2, Calendar, Layers, MessageSquare, Plus, Printer, Upload, User } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AIResponseCard from '@/components/ai/AIResponseCard.vue'
import AISuggestionCard from '@/components/ai/AISuggestionCard.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import DetailPanel from '@/components/common/DetailPanel.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import InfoPanel from '@/components/common/InfoPanel.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ContractList from '@/components/project/ContractList.vue'
import ContractPreview from '@/components/project/ContractPreview.vue'
import ContractRevisionHistory from '@/components/project/ContractRevisionHistory.vue'
import PaymentWorkspacePanel from '@/components/payment/PaymentWorkspacePanel.vue'
import ProjectHeader from '@/components/project/ProjectHeader.vue'
import ProjectTimeline from '@/components/project/ProjectTimeline.vue'
import TimelineEntryDialog from '@/components/project/TimelineEntryDialog.vue'
import ProjectWorkspaceTabs from '@/components/project/ProjectWorkspaceTabs.vue'
import QuotationList from '@/components/project/QuotationList.vue'
import QuotationPreview from '@/components/project/QuotationPreview.vue'
import WorkflowProgress from '@/components/project/WorkflowProgress.vue'
import DocumentCard from '@/components/document/DocumentCard.vue'
import DocumentUploadDialog from '@/components/document/DocumentUploadDialog.vue'
import RequiredDocumentChecklist from '@/components/government/RequiredDocumentChecklist.vue'
import SubmissionApprovalStepper from '@/components/government/SubmissionApprovalStepper.vue'
import TaskDetails from '@/components/task/TaskDetails.vue'
import TaskList from '@/components/task/TaskList.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useContractStore } from '@/stores/contractStore'
import { useDocumentStore } from '@/stores/documentStore'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { usePaymentStore } from '@/stores/paymentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useTaskStore } from '@/stores/taskStore'
import { useTimelineStore } from '@/stores/timelineStore'
import type { ProjectDocument } from '@/types/Document'
import type { ProjectWorkspaceTab, ProjectWorkspaceTabKey } from '@/types/Project'
import type { TaskPriority, TaskStatus } from '@/types/Task'
import type { TimelineEvent } from '@/types/Timeline'
import { formatDate } from '@/utils/dateFormatter'
import { getSubmissionStatusVariant } from '@/utils/submissionHelpers'

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

const projectId = computed(() => route.params.projectId as string)

const VALID_TAB_KEYS: ProjectWorkspaceTabKey[] = ['overview', 'timeline', 'documents', 'design', 'government', 'quotation', 'contract', 'payments', 'tasks', 'activity']
const queryTab = route.query.tab
const initialTab = typeof queryTab === 'string' && VALID_TAB_KEYS.includes(queryTab as ProjectWorkspaceTabKey) ? (queryTab as ProjectWorkspaceTabKey) : 'overview'
const activeTab = ref<ProjectWorkspaceTabKey>(initialTab)

const TABS: ProjectWorkspaceTab[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'timeline', label: 'Timeline' },
  { key: 'documents', label: 'Documents' },
  { key: 'design', label: 'Design' },
  { key: 'government', label: 'Government' },
  { key: 'quotation', label: 'Quotation' },
  { key: 'contract', label: 'Contract' },
  { key: 'payments', label: 'Payments' },
  { key: 'tasks', label: 'Tasks' },
  { key: 'activity', label: 'Activity' },
]

const isDocumentUploadOpen = ref(false)
const isTimelineDialogOpen = ref(false)
const editingTimelineEvent = ref<TimelineEvent | undefined>(undefined)
const selectedSubmissionId = ref<string | undefined>(undefined)
const isSubmissionDrawerOpen = ref(false)

const projectDocuments = computed(() => documentStore.documentsByProject(projectId.value))
const projectDrawings = computed(() => projectDocuments.value.filter((document) => document.type === 'Drawing'))
const visibleDocuments = computed(() => (activeTab.value === 'documents' ? projectDocuments.value : projectDrawings.value))
const projectSubmissions = computed(() => governmentSubmissionStore.submissionsByProject(projectId.value))
const projectTasks = computed(() => taskStore.tasksByProject(projectId.value))
const activityEvents = computed(() => [...timelineStore.events].sort((a, b) => b.date.localeCompare(a.date)))

const selectedSubmission = computed(() =>
  projectSubmissions.value.find((submission) => submission.id === selectedSubmissionId.value),
)

const selectedSubmissionDetails = computed(() => {
  if (!selectedSubmission.value) return []
  const authority = governmentSubmissionStore.getAuthorityById(selectedSubmission.value.authorityId)
  const form = governmentSubmissionStore.getFormById(selectedSubmission.value.formId)

  return [
    { label: 'Authority', value: authority?.name ?? 'Unknown Authority' },
    { label: 'Form', value: form?.title ?? 'Unknown Form' },
    {
      label: 'Submitted Date',
      value: selectedSubmission.value.submittedDate
        ? formatDate(selectedSubmission.value.submittedDate)
        : 'Not submitted yet',
    },
    {
      label: 'Expected Decision',
      value: selectedSubmission.value.expectedDecisionDate
        ? formatDate(selectedSubmission.value.expectedDecisionDate)
        : 'Not set',
    },
  ]
})

const isTaskDrawerOpen = computed({
  get: () => Boolean(taskStore.selectedTaskId),
  set: (value: boolean) => {
    if (!value) taskStore.clearSelectedTask()
  },
})

function openSubmission(submissionId: string): void {
  selectedSubmissionId.value = submissionId
  isSubmissionDrawerOpen.value = true
}

function handleTaskStatusChange(status: TaskStatus): void {
  if (taskStore.selectedTaskId) taskStore.updateTaskStatus(taskStore.selectedTaskId, status)
}

function handleTaskPriorityChange(priority: TaskPriority): void {
  if (taskStore.selectedTaskId) taskStore.updateTaskPriority(taskStore.selectedTaskId, priority)
}

function handleTaskReassign(assignee: string): void {
  if (taskStore.selectedTaskId) taskStore.updateTaskAssignee(taskStore.selectedTaskId, assignee)
}

function openAddTimelineEntry(): void {
  editingTimelineEvent.value = undefined
  isTimelineDialogOpen.value = true
}

function openEditTimelineEntry(event: TimelineEvent): void {
  editingTimelineEvent.value = event
  isTimelineDialogOpen.value = true
}

function handleTimelineSave(event: TimelineEvent): void {
  if (editingTimelineEvent.value) {
    timelineStore.updateEvent(event.id, {
      title: event.title,
      description: event.description,
      status: event.status,
      date: event.date,
    })
  } else {
    timelineStore.addEvent(event)
  }
}

function handleDocumentUpload(document: ProjectDocument): void {
  documentStore.addDocument(document)
  isDocumentUploadOpen.value = false
}

function openDocument(documentId: string): void {
  router.push({ name: ROUTE_NAMES.DOCUMENT_VIEWER, params: { documentId } })
}

const project = computed(() => projectStore.projects.find((item) => item.id === projectId.value))
const client = computed(() => (project.value ? projectStore.getClientById(project.value.clientId) : undefined))

const isLoading = computed(
  () => projectStore.isLoading || quotationStore.isLoading || timelineStore.isLoading || contractStore.isLoading,
)
const error = computed(
  () => projectStore.error ?? quotationStore.error ?? timelineStore.error ?? contractStore.error,
)

const projectDetailItems = computed(() => {
  if (!project.value) return []
  return [
    { label: 'Service', value: project.value.service },
    { label: 'Responsible Engineer', value: project.value.engineer },
    { label: 'Start Date', value: formatDate(project.value.startDate) },
    { label: 'Target Completion Date', value: formatDate(project.value.targetDate) },
    { label: 'Current Stage', value: project.value.currentStage },
    { label: 'Priority', value: project.value.priority },
  ]
})

const clientDetailItems = computed(() => {
  if (!client.value) return []
  return [
    { label: 'Company Name', value: client.value.companyName },
    { label: 'Contact Person', value: client.value.contactPerson },
    { label: 'Mobile', value: client.value.mobile },
    { label: 'Email', value: client.value.email },
    { label: 'City', value: client.value.city },
  ]
})

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

function handlePrint(): void {
  window.print()
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
      <ProjectHeader :project="project" :client="client" />

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

      <template v-if="activeTab === 'overview'">
        <div class="grid grid-cols-1 gap-6 laptop:grid-cols-2">
          <DetailPanel title="Project Details" :items="projectDetailItems" />
          <div class="flex flex-col gap-3">
            <DetailPanel title="Client Details" :items="clientDetailItems" />
            <div class="flex gap-2 no-print">
              <BaseButton
                v-if="client"
                variant="secondary"
                size="sm"
                :icon="MessageSquare"
                @click="router.push({ name: ROUTE_NAMES.MESSAGE_CENTRE, query: { clientId: client.id } })"
              >
                Message Client
              </BaseButton>
              <BaseButton
                v-if="client"
                variant="ghost"
                size="sm"
                @click="router.push({ name: ROUTE_NAMES.CLIENT_WORKSPACE, params: { clientId: client.id } })"
              >
                View Full Profile
              </BaseButton>
            </div>
          </div>
        </div>
      </template>

      <template v-else-if="activeTab === 'timeline'">
        <div class="flex items-center justify-end">
          <BaseButton variant="secondary" size="sm" :icon="Plus" class="no-print" @click="openAddTimelineEntry">
            Add Update
          </BaseButton>
        </div>
        <ProjectTimeline :events="timelineStore.events" editable @edit="openEditTimelineEntry" />
      </template>

      <template v-else-if="activeTab === 'quotation'">
        <div class="flex items-center justify-end">
          <BaseButton
            v-if="quotationStore.selectedQuotation"
            variant="secondary"
            size="sm"
            :icon="Printer"
            class="no-print"
            @click="handlePrint"
          >
            Print Quotation
          </BaseButton>
        </div>

        <div class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
          <div class="laptop:col-span-2 print:col-span-3">
            <EmptyState
              v-if="!quotationStore.selectedQuotation"
              title="No quotation selected"
              description="Select a quotation from the list to preview it."
            />
            <QuotationPreview
              v-else
              :quotation="quotationStore.selectedQuotation"
              :project="project"
              :client="client"
            />
          </div>

          <div class="no-print">
            <QuotationList
              :quotations="quotationStore.quotations"
              :selected-quotation-id="quotationStore.selectedQuotationId"
              @select="quotationStore.selectQuotation($event)"
            />
          </div>
        </div>
      </template>

      <template v-else-if="activeTab === 'contract'">
        <div class="flex items-center justify-end">
          <BaseButton
            v-if="contractStore.selectedContract"
            variant="secondary"
            size="sm"
            :icon="Printer"
            class="no-print"
            @click="handlePrint"
          >
            Print Contract
          </BaseButton>
        </div>

        <EmptyState
          v-if="!contractStore.selectedContract"
          title="No contract selected"
          description="Select a contract from the list to preview it."
        />

        <div v-else class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
          <div class="flex flex-col gap-6 laptop:col-span-2 print:col-span-3">
            <ContractPreview
              :contract="contractStore.selectedContract"
              :project="project"
              :client="client"
            />

            <div class="no-print">
              <AIResponseCard
                v-if="contractStore.aiSummary"
                title="AI Contract Summary"
                :summary="contractStore.aiSummary.summary"
                :details="contractStore.aiSummary.details"
                :confidence="contractStore.aiSummary.confidence"
              />
              <div v-else-if="contractStore.isAiSummaryLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
                <SkeletonLoader :rows="3" />
              </div>
            </div>

            <AISuggestionCard
              v-if="contractStore.aiSummary?.suggestions.length"
              class="no-print"
              :suggestions="contractStore.aiSummary.suggestions"
            />
          </div>

          <div class="flex flex-col gap-6 no-print">
            <ContractList
              :contracts="contractStore.contracts"
              :selected-contract-id="contractStore.selectedContractId"
              @select="contractStore.selectContract($event)"
            />
            <ContractRevisionHistory :revisions="contractStore.selectedContract.revisions" />
          </div>
        </div>
      </template>

      <template v-else-if="activeTab === 'documents' || activeTab === 'design'">
        <div class="flex items-center justify-end">
          <BaseButton
            v-if="activeTab === 'documents'"
            variant="secondary"
            size="sm"
            :icon="Upload"
            class="no-print"
            @click="isDocumentUploadOpen = true"
          >
            Upload Document
          </BaseButton>
        </div>

        <div v-if="documentStore.isLoading" class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
          <div v-for="placeholder in 3" :key="placeholder" class="rounded-xl border border-border-light bg-bg-card p-5">
            <SkeletonLoader :rows="5" />
          </div>
        </div>

        <ErrorState v-else-if="documentStore.error" :description="documentStore.error" @retry="documentStore.loadDocuments" />

        <EmptyState
          v-else-if="visibleDocuments.length === 0"
          title="No documents yet"
          :description="
            activeTab === 'documents'
              ? 'Documents uploaded for this project will appear here.'
              : 'Design drawings uploaded for this project will appear here.'
          "
        />

        <div v-else class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
          <DocumentCard
            v-for="document in visibleDocuments"
            :key="document.id"
            :document="document"
            :project="project"
            @open="openDocument"
          />
        </div>

        <DocumentUploadDialog
          v-model="isDocumentUploadOpen"
          :projects="[project]"
          @upload="handleDocumentUpload"
        />
      </template>

      <template v-else-if="activeTab === 'government'">
        <div v-if="governmentSubmissionStore.isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
          <SkeletonLoader :rows="6" />
        </div>

        <ErrorState
          v-else-if="governmentSubmissionStore.error"
          :description="governmentSubmissionStore.error"
          @retry="governmentSubmissionStore.loadSubmissions"
        />

        <EmptyState
          v-else-if="projectSubmissions.length === 0"
          title="No submissions yet"
          description="Government submissions filed for this project will appear here."
        />

        <div v-else class="flex flex-col gap-3">
          <button
            v-for="submission in projectSubmissions"
            :key="submission.id"
            type="button"
            class="flex flex-col gap-2 rounded-xl border border-border-light bg-bg-card p-4 text-left shadow-soft transition-colors duration-fast hover:bg-bg-hover tablet:flex-row tablet:items-center tablet:justify-between"
            @click="openSubmission(submission.id)"
          >
            <div class="min-w-0">
              <p class="text-sm font-semibold text-neutral-800">{{ submission.submissionNo }}</p>
              <p class="truncate text-xs text-neutral-500">
                {{ governmentSubmissionStore.getFormById(submission.formId)?.title ?? 'Unknown Form' }} ·
                {{ governmentSubmissionStore.getAuthorityById(submission.authorityId)?.name ?? 'Unknown Authority' }}
              </p>
            </div>
            <StatusBadge :label="submission.status" :variant="getSubmissionStatusVariant(submission.status)" />
          </button>
        </div>

        <BaseButton variant="ghost" size="sm" class="no-print self-start" @click="router.push({ name: ROUTE_NAMES.GOVERNMENT_SUBMISSIONS })">
          View All Submissions
        </BaseButton>

        <BaseDrawer v-model="isSubmissionDrawerOpen" :title="selectedSubmission?.submissionNo" width="lg">
          <div v-if="selectedSubmission" class="flex flex-col gap-6">
            <SubmissionApprovalStepper :status="selectedSubmission.status" />
            <DetailPanel title="Submission Details" :items="selectedSubmissionDetails" />
            <div>
              <h3 class="mb-2 text-sm font-semibold text-neutral-800">Required Documents</h3>
              <RequiredDocumentChecklist :documents="selectedSubmission.documents" />
            </div>
            <div v-if="selectedSubmission.notes">
              <h3 class="mb-1 text-sm font-semibold text-neutral-800">Notes</h3>
              <p class="text-sm text-neutral-600">{{ selectedSubmission.notes }}</p>
            </div>
          </div>
        </BaseDrawer>
      </template>

      <template v-else-if="activeTab === 'tasks'">
        <div class="flex items-center justify-end">
          <BaseButton variant="ghost" size="sm" class="no-print" @click="router.push({ name: ROUTE_NAMES.TASKS })">
            View Task Board
          </BaseButton>
        </div>

        <div v-if="taskStore.isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
          <SkeletonLoader :rows="6" />
        </div>

        <ErrorState v-else-if="taskStore.error" :description="taskStore.error" @retry="taskStore.loadTasks" />

        <TaskList v-else :tasks="projectTasks" :get-project-by-id="taskStore.getProjectById" @open="taskStore.selectTask" />

        <BaseDrawer v-model="isTaskDrawerOpen" :title="taskStore.selectedTask?.id" width="md">
          <TaskDetails
            v-if="taskStore.selectedTask"
            :task="taskStore.selectedTask"
            :project-name="project.projectName"
            @status-change="handleTaskStatusChange"
            @priority-change="handleTaskPriorityChange"
            @reassign="handleTaskReassign"
          />
        </BaseDrawer>
      </template>

      <template v-else-if="activeTab === 'activity'">
        <div class="flex items-center justify-end">
          <BaseButton variant="secondary" size="sm" :icon="Plus" class="no-print" @click="openAddTimelineEntry">
            Add Update
          </BaseButton>
        </div>
        <ProjectTimeline :events="activityEvents" editable @edit="openEditTimelineEntry" />
      </template>

      <template v-else-if="activeTab === 'payments'">
        <PaymentWorkspacePanel :project-id="projectId" />
      </template>

      <TimelineEntryDialog
        v-model="isTimelineDialogOpen"
        :project-id="projectId"
        :event="editingTimelineEvent"
        @save="handleTimelineSave"
      />
    </template>
  </div>
</template>
