<script setup lang="ts">
import { LayoutGrid, Plus, TableProperties } from '@lucide/vue'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
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
const { t } = useI18n()

const STATUS_OPTIONS = computed<SelectOption[]>(() => [
  { label: t('project.projectsPage.allStatuses'), value: 'All' },
  { label: t('project.status.active'), value: 'Active' },
  { label: t('project.status.onHold'), value: 'On Hold' },
  { label: t('project.status.cancelled'), value: 'Cancelled' },
])

const STAGE_OPTIONS = computed<SelectOption[]>(() => [
  { label: t('project.projectsPage.allStages'), value: 'All' },
  { label: t('project.stage.requirement'), value: 'Requirement' },
  { label: t('project.stage.quotation'), value: 'Quotation' },
  { label: t('project.stage.paymentPlan'), value: 'Payment Plan' },
  { label: t('project.stage.contract'), value: 'Contract' },
  { label: t('project.stage.design'), value: 'Design' },
  { label: t('project.stage.supervision'), value: 'Supervision' },
  { label: t('project.stage.governmentSubmission'), value: 'Government Submission' },
])

const PRIORITY_OPTIONS = computed<SelectOption[]>(() => [
  { label: t('project.projectsPage.allPriorities'), value: 'All' },
  { label: t('project.priority.high'), value: 'High' },
  { label: t('project.priority.medium'), value: 'Medium' },
  { label: t('project.priority.low'), value: 'Low' },
])

const TABLE_COLUMNS = computed<SmartTableColumn<ProjectTableRow>[]>(() => [
  { key: 'projectNo', label: t('project.projectsPage.columns.projectNo'), sortable: true, width: '140px' },
  { key: 'projectName', label: t('project.projectsPage.columns.projectName'), sortable: true },
  { key: 'clientName', label: t('project.projectsPage.columns.client'), sortable: true },
  { key: 'currentStage', label: t('project.projectsPage.columns.stage'), sortable: true },
  { key: 'status', label: t('project.projectsPage.columns.status'), sortable: true },
  { key: 'priority', label: t('project.projectsPage.columns.priority'), sortable: true },
  { key: 'progress', label: t('project.projectsPage.columns.progress'), sortable: true, width: '160px' },
  { key: 'engineer', label: t('project.projectsPage.columns.engineer'), sortable: true },
  { key: 'targetDate', label: t('project.projectsPage.columns.targetDate'), sortable: true, align: 'right' },
])

const tableRows = computed<ProjectTableRow[]>(() =>
  projectStore.pageItems.map((project) => ({
    id: project.id,
    projectNo: project.projectNo,
    projectName: project.projectName,
    clientName: projectStore.getClientById(project.clientId)?.companyName ?? t('project.unknownClient'),
    currentStage: project.currentStage,
    status: project.status,
    priority: project.priority,
    progress: project.progress,
    engineer: project.engineer,
    targetDate: project.targetDate,
  })),
)

const STAGE_LABEL_KEYS: Record<string, string> = {
  Requirement: 'project.stage.requirement',
  Quotation: 'project.stage.quotation',
  'Payment Plan': 'project.stage.paymentPlan',
  Contract: 'project.stage.contract',
  Design: 'project.stage.design',
  Supervision: 'project.stage.supervision',
  'Government Submission': 'project.stage.governmentSubmission',
}
function stageLabel(stage: string): string {
  return t(STAGE_LABEL_KEYS[stage] ?? getWorkflowStageLabel(stage))
}

const STATUS_LABEL_KEYS: Record<string, string> = {
  Active: 'project.status.active',
  'On Hold': 'project.status.onHold',
  Cancelled: 'project.status.cancelled',
}
function statusLabel(status: string): string {
  return t(STATUS_LABEL_KEYS[status] ?? status)
}

const PRIORITY_LABEL_KEYS: Record<string, string> = {
  High: 'project.priority.high',
  Medium: 'project.priority.medium',
  Low: 'project.priority.low',
}
function priorityLabel(priority: string): string {
  return t(PRIORITY_LABEL_KEYS[priority] ?? priority)
}

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
    <PageHeader :title="t('project.projectsPage.title')" :subtitle="t('project.projectsPage.subtitle')">
      <template #actions>
        <BaseButton :icon="Plus" @click="createProject">{{ t('project.projectsPage.newProject') }}</BaseButton>
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
            :label="t('project.projectsPage.status')"
            :model-value="projectStore.statusFilter"
            :options="STATUS_OPTIONS"
            @update:model-value="projectStore.setStatusFilter($event as ProjectStatus | 'All')"
          />
        </div>
        <div class="w-52">
          <SelectBox
            :label="t('project.projectsPage.stage')"
            :model-value="projectStore.stageFilter"
            :options="STAGE_OPTIONS"
            @update:model-value="projectStore.setStageFilter($event as WorkflowStage | 'All')"
          />
        </div>
        <div class="w-44">
          <SelectBox
            :label="t('project.projectsPage.priority')"
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
          {{ t('project.projectsPage.myProjects') }}
        </BaseButton>
      </template>
      <template #actions>
        <div class="flex items-center gap-1 rounded-lg border border-border-default p-1" role="group" :aria-label="t('project.projectsPage.layoutAria')">
          <IconButton
            :icon="LayoutGrid"
            :label="t('project.projectsPage.gridView')"
            size="sm"
            :variant="projectStore.viewMode === 'grid' ? 'primary' : 'ghost'"
            :aria-pressed="projectStore.viewMode === 'grid'"
            @click="projectStore.setViewMode('grid')"
          />
          <IconButton
            :icon="TableProperties"
            :label="t('project.projectsPage.tableView')"
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
        :title="t('project.projectsPage.noProjectsFoundTitle')"
        :description="t('project.projectsPage.noProjectsFoundDescription')"
        :action-label="t('project.projectsPage.newProject')"
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
        :empty-title="t('project.projectsPage.noProjectsFoundTitle')"
        :empty-description="t('project.projectsPage.noProjectsFoundDescription')"
        @row-click="openProject($event.id)"
      >
        <template #cell-status="{ value }">
          <StatusBadge :label="statusLabel(value as string)" :variant="getProjectStatusVariant(value as ProjectStatus)" show-dot />
        </template>
        <template #cell-priority="{ value }">
          <StatusBadge :label="priorityLabel(value as string)" :variant="getProjectPriorityVariant(value as ProjectPriority)" />
        </template>
        <template #cell-currentStage="{ value }">
          <StatusBadge :label="stageLabel(value as string)" variant="info" />
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
