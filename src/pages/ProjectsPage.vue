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
import { useProjectStore } from '@/stores/projectStore'
import type { SmartTableColumn } from '@/types/Table'
import type { ProjectPriority, ProjectStatus, WorkflowStage } from '@/types/Project'
import type { SelectOption } from '@/types/Ui'
import { formatDate } from '@/utils/dateFormatter'
import { getProjectPriorityVariant, getProjectStatusVariant, getWorkflowStageLabel } from '@/utils/projectHelpers'

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
  { label: 'Cancelled', value: 'Cancelled' },
]

const STAGE_OPTIONS: SelectOption[] = [
  { label: 'All Stages', value: 'All' },
  { label: 'Requirement', value: 'Requirement' },
  { label: 'Quotation', value: 'Quotation' },
  { label: 'Contract', value: 'Contract' },
  { label: 'Design', value: 'Design' },
  { label: 'Supervision', value: 'Supervision' },
  { label: 'Approvals & Permits', value: 'Government Submission' },
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
  projectStore.pageItems.map((project) => ({
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

function loadData(): void {
  void projectStore.loadProjectsPage()
}

onMounted(loadData)

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
      :show-search="false"
      :has-active-filters="projectStore.hasActiveFilters"
      @clear="projectStore.clearFilters"
    >
      <template #filters>
        <div class="w-44">
          <SelectBox
            label="Status"
            :model-value="projectStore.statusFilter"
            :options="STATUS_OPTIONS"
            @update:model-value="projectStore.setStatusFilter($event as ProjectStatus | 'All')"
          />
        </div>
        <div class="w-52">
          <SelectBox
            label="Stage"
            :model-value="projectStore.stageFilter"
            :options="STAGE_OPTIONS"
            @update:model-value="projectStore.setStageFilter($event as WorkflowStage | 'All')"
          />
        </div>
        <div class="w-44">
          <SelectBox
            label="Priority"
            :model-value="projectStore.priorityFilter"
            :options="PRIORITY_OPTIONS"
            @update:model-value="projectStore.setPriorityFilter($event as ProjectPriority | 'All')"
          />
        </div>
        <BaseButton
          size="sm"
          :variant="projectStore.myProjectsOnly ? 'primary' : 'secondary'"
          :aria-pressed="projectStore.myProjectsOnly"
          @click="projectStore.setMyProjectsOnly(!projectStore.myProjectsOnly)"
        >
          My Projects
        </BaseButton>
      </template>
      <template #actions>
        <div class="flex items-center gap-1 rounded-lg border border-border-default p-1" role="group" aria-label="Project list layout">
          <IconButton
            :icon="LayoutGrid"
            label="Grid view"
            size="sm"
            :variant="projectStore.viewMode === 'grid' ? 'primary' : 'ghost'"
            :aria-pressed="projectStore.viewMode === 'grid'"
            @click="projectStore.setViewMode('grid')"
          />
          <IconButton
            :icon="TableProperties"
            label="Table view"
            size="sm"
            :variant="projectStore.viewMode === 'table' ? 'primary' : 'ghost'"
            :aria-pressed="projectStore.viewMode === 'table'"
            @click="projectStore.setViewMode('table')"
          />
        </div>
      </template>
    </FilterBar>

    <ErrorState v-if="projectStore.error" :description="projectStore.error" @retry="loadData" />

    <template v-else-if="projectStore.viewMode === 'grid'">
      <div v-if="projectStore.isPageLoading" class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
        <div v-for="placeholder in 6" :key="placeholder" class="rounded-xl border border-border-light bg-bg-card p-5">
          <SkeletonLoader :rows="5" />
        </div>
      </div>

      <EmptyState
        v-else-if="projectStore.pageItems.length === 0"
        title="No projects found"
        description="Try adjusting your search or filters, or create a new project."
        action-label="New Project"
        @action="createProject"
      />

      <template v-else>
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
          <ProjectCard
            v-for="project in projectStore.pageItems"
            :key="project.id"
            :project="project"
            :client="projectStore.getClientById(project.clientId)"
            @open="openProject"
          />
        </div>
        <div class="rounded-xl border border-border-light bg-bg-card">
          <TablePagination
            :current-page="projectStore.pagination.page"
            :total-pages="projectStore.pagination.totalPages"
            :total-items="projectStore.pagination.total"
            :start-index="(projectStore.pagination.page - 1) * projectStore.pagination.pageSize"
            :end-index="Math.min(projectStore.pagination.page * projectStore.pagination.pageSize, projectStore.pagination.total)"
            :page-size="projectStore.pagination.pageSize"
            :page-size-options="[9, 18, 27]"
            @page-change="projectStore.setPage"
            @page-size-change="projectStore.setPageSize"
          />
        </div>
      </template>
    </template>

    <template v-else>
      <SmartTable
        :columns="TABLE_COLUMNS"
        :rows="tableRows"
        row-key="id"
        :loading="projectStore.isPageLoading"
        :searchable="false"
        :paginated="false"
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
          <StatusBadge :label="getWorkflowStageLabel(value as string)" variant="info" />
        </template>
        <template #cell-progress="{ value }">
          <ProgressBar :value="value as number" show-label />
        </template>
        <template #cell-targetDate="{ value }">
          {{ formatDate(value as string) }}
        </template>
      </SmartTable>
      <div class="rounded-xl border border-border-light bg-bg-card">
        <TablePagination
          :current-page="projectStore.pagination.page"
          :total-pages="projectStore.pagination.totalPages"
          :total-items="projectStore.pagination.total"
          :start-index="(projectStore.pagination.page - 1) * projectStore.pagination.pageSize"
          :end-index="Math.min(projectStore.pagination.page * projectStore.pagination.pageSize, projectStore.pagination.total)"
          :page-size="projectStore.pagination.pageSize"
          :page-size-options="[10, 25, 50]"
          @page-change="projectStore.setPage"
          @page-size-change="projectStore.setPageSize"
        />
      </div>
    </template>
  </div>
</template>
