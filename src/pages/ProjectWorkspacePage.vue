<script setup lang="ts">
import { Printer } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import ProjectHeader from '@/components/project/ProjectHeader.vue'
import ProjectWorkspaceTabs from '@/components/project/ProjectWorkspaceTabs.vue'
import QuotationList from '@/components/project/QuotationList.vue'
import QuotationPreview from '@/components/project/QuotationPreview.vue'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import type { ProjectWorkspaceTab, ProjectWorkspaceTabKey } from '@/types/Project'

const route = useRoute()
const projectStore = useProjectStore()
const quotationStore = useQuotationStore()

const projectId = computed(() => route.params.projectId as string)
const activeTab = ref<ProjectWorkspaceTabKey>('quotation')

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

const isLoading = computed(() => projectStore.isLoading || quotationStore.isLoading)
const error = computed(() => projectStore.error ?? quotationStore.error)

async function loadData(): Promise<void> {
  if (projectStore.projects.length === 0) {
    await projectStore.loadProjects()
  }
  await quotationStore.loadQuotationsForProject(projectId.value)
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

      <ProjectWorkspaceTabs :tabs="TABS" :active-tab="activeTab" @select="activeTab = $event" />

      <template v-if="activeTab === 'quotation'">
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

      <EmptyState
        v-else
        title="Coming soon"
        :description="TAB_COMING_SOON[activeTab]"
      />
    </template>
  </div>
</template>
