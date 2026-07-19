<script setup lang="ts">
import { Building2, Calendar, Layers, MessageSquare, Printer, User } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AIResponseCard from '@/components/ai/AIResponseCard.vue'
import AISuggestionCard from '@/components/ai/AISuggestionCard.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import DetailPanel from '@/components/common/DetailPanel.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import InfoPanel from '@/components/common/InfoPanel.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import ContractList from '@/components/project/ContractList.vue'
import ContractPreview from '@/components/project/ContractPreview.vue'
import ContractRevisionHistory from '@/components/project/ContractRevisionHistory.vue'
import ProjectHeader from '@/components/project/ProjectHeader.vue'
import ProjectTimeline from '@/components/project/ProjectTimeline.vue'
import ProjectWorkspaceTabs from '@/components/project/ProjectWorkspaceTabs.vue'
import QuotationList from '@/components/project/QuotationList.vue'
import QuotationPreview from '@/components/project/QuotationPreview.vue'
import WorkflowProgress from '@/components/project/WorkflowProgress.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useContractStore } from '@/stores/contractStore'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useTimelineStore } from '@/stores/timelineStore'
import type { ProjectWorkspaceTab, ProjectWorkspaceTabKey } from '@/types/Project'
import { formatDate } from '@/utils/dateFormatter'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const quotationStore = useQuotationStore()
const timelineStore = useTimelineStore()
const contractStore = useContractStore()

const projectId = computed(() => route.params.projectId as string)
const activeTab = ref<ProjectWorkspaceTabKey>('overview')

const TABS: ProjectWorkspaceTab[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'timeline', label: 'Timeline' },
  { key: 'documents', label: 'Documents' },
  { key: 'design', label: 'Design' },
  { key: 'government', label: 'Government' },
  { key: 'quotation', label: 'Quotation' },
  { key: 'contract', label: 'Contract' },
  { key: 'tasks', label: 'Tasks' },
  { key: 'activity', label: 'Activity' },
]

const TAB_COMING_SOON: Record<ProjectWorkspaceTabKey, string> = {
  overview: 'A consolidated project summary will appear here.',
  timeline: 'Milestones and workflow progress will appear here.',
  documents: 'Documents linked to this project will appear here.',
  design: 'Design deliverables for this project will appear here.',
  government: 'Government submissions for this project will appear here.',
  quotation: '',
  contract: 'The contract issued for this project will appear here.',
  tasks: 'Tasks assigned within this project will appear here.',
  activity: 'A full audit trail of project activity will appear here.',
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
  await Promise.all([
    quotationStore.loadQuotationsForProject(projectId.value),
    timelineStore.loadTimelineForProject(projectId.value),
    contractStore.loadContractsForProject(projectId.value),
  ])
}

onMounted(loadData)
watch(projectId, loadData)

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
            <BaseButton
              v-if="client"
              variant="secondary"
              size="sm"
              :icon="MessageSquare"
              class="no-print self-start"
              @click="router.push({ name: ROUTE_NAMES.MESSAGE_CENTRE, query: { clientId: client.id } })"
            >
              Message Client
            </BaseButton>
          </div>
        </div>
      </template>

      <template v-else-if="activeTab === 'timeline'">
        <ProjectTimeline :events="timelineStore.events" />
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

      <EmptyState
        v-else
        title="Coming soon"
        :description="TAB_COMING_SOON[activeTab]"
      />
    </template>
  </div>
</template>
