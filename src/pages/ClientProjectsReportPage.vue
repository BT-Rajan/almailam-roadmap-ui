<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseDrawer from '@/components/common/BaseDrawer.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import { reportService } from '@/services/reportService'
import { getProjectStatusVariant, getWorkflowStageLabel } from '@/utils/projectHelpers'
import type { ClientProjectSummary, ClientWithProjects } from '@/types/Report'
import type { ProjectStatus, WorkflowStage } from '@/types/Project'
import type { SmartTableColumn } from '@/types/Table'

const { t } = useI18n()

const clients = ref<ClientWithProjects[]>([])
const isLoading = ref(false)
const loadError = ref('')

async function load(): Promise<void> {
  isLoading.value = true
  loadError.value = ''
  try {
    clients.value = await reportService.getClientsWithProjects()
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : t('report.clientProjectsPage.loadFailed')
  } finally {
    isLoading.value = false
  }
}

onMounted(load)

interface ClientRow {
  [key: string]: unknown
  clientId: string
  clientName: string
  clientStatus: string
  totalProjects: number
  activeProjects: number
  onHoldProjects: number
  completedProjects: number
}

const clientRows = computed<ClientRow[]>(() =>
  clients.value.map((client) => ({
    clientId: client.clientId,
    clientName: client.clientName,
    clientStatus: client.clientStatus,
    totalProjects: client.projects.length,
    activeProjects: client.projects.filter((p) => p.status === 'Active').length,
    onHoldProjects: client.projects.filter((p) => p.status === 'On Hold').length,
    completedProjects: client.projects.filter((p) => p.status === 'Completed').length,
  })),
)

const clientColumns = computed<SmartTableColumn<ClientRow>[]>(() => [
  { key: 'clientName', label: t('report.clientProjectsPage.columnClient'), sortable: true },
  { key: 'clientStatus', label: t('report.clientProjectsPage.columnClientStatus') },
  { key: 'totalProjects', label: t('report.clientProjectsPage.columnTotalProjects'), align: 'right', sortable: true },
  { key: 'activeProjects', label: t('report.clientProjectsPage.columnActive'), align: 'right' },
  { key: 'onHoldProjects', label: t('report.clientProjectsPage.columnOnHold'), align: 'right' },
  { key: 'completedProjects', label: t('report.clientProjectsPage.columnCompleted'), align: 'right' },
])

type ProjectRow = ClientProjectSummary & Record<string, unknown>

const projectColumns = computed<SmartTableColumn<ProjectRow>[]>(() => [
  { key: 'projectNo', label: t('report.clientProjectsPage.columnProjectNo') },
  { key: 'projectName', label: t('report.clientProjectsPage.columnProjectName') },
  { key: 'status', label: t('report.clientProjectsPage.columnProjectStatus') },
  { key: 'currentStage', label: t('report.clientProjectsPage.columnStage') },
  { key: 'progress', label: t('report.clientProjectsPage.columnProgress'), align: 'right' },
])

const isDrawerOpen = ref(false)
const drawerClientName = ref('')
const drawerProjects = ref<ProjectRow[]>([])

function openClient(row: ClientRow): void {
  const client = clients.value.find((c) => c.clientId === row.clientId)
  drawerClientName.value = row.clientName
  drawerProjects.value = client?.projects ?? []
  isDrawerOpen.value = true
}

const totalClients = computed(() => clients.value.length)
const clientsWithNoProjects = computed(() => clients.value.filter((c) => c.projects.length === 0).length)
const totalProjects = computed(() => clients.value.reduce((sum, c) => sum + c.projects.length, 0))
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader :title="t('report.clientProjectsPage.pageTitle')" :subtitle="t('report.clientProjectsPage.pageSubtitle')" />

    <ErrorState v-if="loadError" :description="loadError" @retry="load" />

    <template v-else>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <ReportMetricCard :label="t('report.clientProjectsPage.metricClients')" :value="totalClients" color="primary" />
        <ReportMetricCard :label="t('report.clientProjectsPage.metricProjects')" :value="totalProjects" color="info" />
        <ReportMetricCard :label="t('report.clientProjectsPage.metricNoProjects')" :value="clientsWithNoProjects" color="neutral" />
      </div>

      <SmartTable
        :columns="clientColumns"
        :rows="clientRows"
        row-key="clientId"
        :loading="isLoading"
        :searchable="true"
        :search-placeholder="t('report.clientProjectsPage.searchClient')"
        :empty-title="t('report.clientProjectsPage.noClients')"
        @row-click="openClient"
      >
        <template #cell-clientStatus="{ value }">
          <StatusBadge :label="value as string" :variant="value === 'Active' ? 'success' : value === 'On Hold' ? 'warning' : 'danger'" />
        </template>
      </SmartTable>
    </template>

    <BaseDrawer v-model="isDrawerOpen" :title="drawerClientName" width="lg">
      <SmartTable
        :columns="projectColumns"
        :rows="drawerProjects"
        row-key="projectNo"
        :searchable="false"
        :empty-title="t('report.clientProjectsPage.noProjectsForClient')"
      >
        <template #cell-status="{ value }">
          <StatusBadge :label="value as string" :variant="getProjectStatusVariant(value as ProjectStatus)" />
        </template>
        <template #cell-currentStage="{ value }">{{ getWorkflowStageLabel(value as WorkflowStage) }}</template>
        <template #cell-progress="{ value }">{{ value }}%</template>
      </SmartTable>
    </BaseDrawer>
  </div>
</template>
