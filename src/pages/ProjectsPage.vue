<script setup lang="ts">
import { LayoutGrid, Plus, TableProperties } from '@lucide/vue'
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import IconButton from '@/components/common/IconButton.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TablePagination from '@/components/common/TablePagination.vue'
import ProjectCard from '@/components/project/ProjectCard.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { usePagination } from '@/composables/usePagination'
import { useProjectStore } from '@/stores/projectStore'
import type { SmartTableColumn } from '@/types/Table'
import type { ProjectPriority, ProjectStatus, WorkflowStage } from '@/types/Project'
import type { SelectOption } from '@/types/Ui'
import { formatDate } from '@/utils/dateFormatter'
import { getProjectPriorityVariant, getProjectStatusVariant } from '@/utils/projectHelpers'

interface ProjectTableRow {
  [key: string]: unknown
  id: string
  projectNo: string
  projectName: string
  clientName: string
  currentStage: WorkflowStage
  status: ProjectStatus
  priority: ProjectPriority
  progress: number
  engineer: string
  targetDate: string
}

const router = useRouter()
const projectStore = useProjectStore()

const STATUS_OPTIONS: SelectOption[] = [
  { label: 'All Statuses', value: 'All' },
  { label: 'Active', value: 'Active' },
  { label: 'On Hold', value: 'On Hold' },
  { label: 'Completed', value: 'Completed' },
  { label: 'Cancelled', value: 'Cancelled' },
]

const STAGE_OPTIONS: SelectOption[] = [
  { label: 'All Stages', value: 'All' },
  { label: 'Enquiry', value: 'Enquiry' },
  { label: 'Quotation', value: 'Quotation' },
  { label: 'Contract', value: 'Contract' },
  { label: 'Design', value: 'Design' },
  { label: 'Government Submission', value: 'Government Submission' },
  { label: 'Review', value: 'Review' },
  { label: 'Correction', value: 'Correction' },
  { label: 'Approval', value: 'Approval' },
  { label: 'Completed', value: 'Completed' },
]

const PRIORITY_OPTIONS: SelectOption[] = [
  { label: 'All Priorities', value: 'All' },
  { label: 'High', value: 'High' },
  { label: 'Medium', value: 'Medium' },
  { label: 'Low', value: 'Low' },
]

const TABLE_COLUMNS: SmartTableColumn<ProjectTableRow>[] = [
  { key: 'projectNo', label: 'Project No.', sortable: true, width: '140px' },
  { key: 'projectName', label: 'Project Name', sortable: true },
  { key: 'clientName', label: 'Client', sortable: true },
  { key: 'currentStage', label: 'Stage', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'priority', label: 'Priority', sortable: true },
  { key: 'progress', label: 'Progress', sortable: true, width: '160px' },
  { key: 'engineer', label: 'Engineer', sortable: true },
  { key: 'targetDate', label: 'Target Date', sortable: true, align: 'right' },
]

const tableRows = computed<ProjectTableRow[]>(() =>
  projectStore.filteredProjects.map((project) => ({
    id: project.id,
    projectNo: project.projectNo,
    projectName: project.projectName,
    clientName: projectStore.getClientById(project.clientId)?.companyName ?? 'Unknown Client',
    currentStage: project.currentStage,
    status: project.status,
    priority: project.priority,
    progress: project.progress,
    engineer: project.engineer,
    targetDate: project.targetDate,
  })),
)

const { currentPage, pageSize, totalItems, totalPages, startIndex, endIndex, goToPage, setPageSize } = usePagination(
  () => projectStore.filteredProjects.length,
  9,
)

const paginatedGridProjects = computed(() => projectStore.filteredProjects.slice(startIndex.value, endIndex.value))

function loadData(): void {
  projectStore.loadProjects()
}

onMounted(() => {
  if (projectStore.projects.length === 0) loadData()
})

function openProject(projectId: string): void {
  router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId } })
}

function createProject(): void {
  router.push({ name: ROUTE_NAMES.PROJECT_NEW })
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader title="Project Explorer" subtitle="Browse, filter and open every engineering consulting engagement.">
      <template #actions>
        <BaseButton :icon="Plus" @click="createProject">New Project</BaseButton>
      </template>
    </PageHeader>

    <FilterBar
      :search-value="projectStore.searchTerm"
      search-placeholder="Search by project name, number or engineer"
      :has-active-filters="projectStore.hasActiveFilters"
      @update:search-value="projectStore.setSearchTerm"
      @clear="projectStore.clearFilters"
    >
      <template #filters>
        <div class="w-44">
          <SelectBox
            :model-value="projectStore.statusFilter"
            :options="STATUS_OPTIONS"
            @update:model-value="projectStore.setStatusFilter($event as ProjectStatus | 'All')"
          />
        </div>
        <div class="w-52">
          <SelectBox
            :model-value="projectStore.stageFilter"
            :options="STAGE_OPTIONS"
            @update:model-value="projectStore.setStageFilter($event as WorkflowStage | 'All')"
          />
        </div>
        <div class="w-44">
          <SelectBox
            :model-value="projectStore.priorityFilter"
            :options="PRIORITY_OPTIONS"
            @update:model-value="projectStore.setPriorityFilter($event as ProjectPriority | 'All')"
          />
        </div>
      </template>
      <template #actions>
        <div class="flex items-center gap-1 rounded-lg border border-border-default p-1">
          <IconButton
            :icon="LayoutGrid"
            label="Grid view"
            size="sm"
            :variant="projectStore.viewMode === 'grid' ? 'primary' : 'ghost'"
            @click="projectStore.setViewMode('grid')"
          />
          <IconButton
            :icon="TableProperties"
            label="Table view"
            size="sm"
            :variant="projectStore.viewMode === 'table' ? 'primary' : 'ghost'"
            @click="projectStore.setViewMode('table')"
          />
        </div>
      </template>
    </FilterBar>

    <ErrorState v-if="projectStore.error" :description="projectStore.error" @retry="loadData" />

    <template v-else-if="projectStore.viewMode === 'grid'">
      <div v-if="projectStore.isLoading" class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
        <div v-for="placeholder in 6" :key="placeholder" class="rounded-xl border border-border-light bg-bg-card p-5">
          <SkeletonLoader :rows="5" />
        </div>
      </div>

      <EmptyState
        v-else-if="paginatedGridProjects.length === 0"
        title="No projects found"
        description="Try adjusting your search or filters, or create a new project."
        action-label="New Project"
        @action="createProject"
      />

      <template v-else>
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
          <ProjectCard
            v-for="project in paginatedGridProjects"
            :key="project.id"
            :project="project"
            :client="projectStore.getClientById(project.clientId)"
            @open="openProject"
          />
        </div>
        <div class="rounded-xl border border-border-light bg-bg-card">
          <TablePagination
            :current-page="currentPage"
            :total-pages="totalPages"
            :total-items="totalItems"
            :start-index="startIndex"
            :end-index="endIndex"
            :page-size="pageSize"
            :page-size-options="[9, 18, 27]"
            @page-change="goToPage"
            @page-size-change="setPageSize"
          />
        </div>
      </template>
    </template>

    <SmartTable
      v-else
      :columns="TABLE_COLUMNS"
      :rows="tableRows"
      row-key="id"
      :loading="projectStore.isLoading"
      :searchable="false"
      empty-title="No projects found"
      empty-description="Try adjusting your search or filters, or create a new project."
      @row-click="openProject($event.id)"
    >
      <template #cell-status="{ value }">
        <StatusBadge :label="value as string" :variant="getProjectStatusVariant(value as ProjectStatus)" show-dot />
      </template>
      <template #cell-priority="{ value }">
        <StatusBadge :label="value as string" :variant="getProjectPriorityVariant(value as ProjectPriority)" />
      </template>
      <template #cell-currentStage="{ value }">
        <StatusBadge :label="value as string" variant="info" />
      </template>
      <template #cell-progress="{ value }">
        <ProgressBar :value="value as number" show-label />
      </template>
      <template #cell-targetDate="{ value }">
        {{ formatDate(value as string) }}
      </template>
    </SmartTable>
  </div>
</template>
