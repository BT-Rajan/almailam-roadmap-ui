<script setup lang="ts">
import { Download } from '@lucide/vue'
import { computed, onMounted } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TablePagination from '@/components/common/TablePagination.vue'
import { useAuditLogStore } from '@/stores/auditLogStore'
import { useToastStore } from '@/stores/toastStore'
import type { SmartTableColumn } from '@/types/Table'
import type { SelectOption } from '@/types/Ui'
import { formatDateTime } from '@/utils/dateFormatter'

const auditLogStore = useAuditLogStore()
const toastStore = useToastStore()

// Matches every ENTITY_TYPE constant actually used across the backend
// services -- kept as a plain list here rather than fetched, since it's
// a fixed set of code-level identifiers, not data.
const ENTITY_TYPE_OPTIONS: SelectOption[] = [
  { label: 'All Entities', value: 'All' },
  { label: 'Clients', value: 'CLIENT' },
  { label: 'Projects', value: 'PROJECT' },
  { label: 'Documents', value: 'DOCUMENT' },
  { label: 'Tasks', value: 'TASK' },
  { label: 'Quotations', value: 'QUOTATION' },
  { label: 'Contracts', value: 'CONTRACT' },
  { label: 'Financial Agreements', value: 'FINANCIAL_AGREEMENT' },
  { label: 'Government Authorities', value: 'GOVERNMENT_AUTHORITY' },
  { label: 'Government Forms', value: 'GOVERNMENT_FORM' },
  { label: 'Government Submissions', value: 'GOVERNMENT_SUBMISSION' },
  { label: 'Users', value: 'USER' },
  { label: 'Workflow Templates', value: 'WORKFLOW_TEMPLATE' },
  { label: 'Company Settings', value: 'COMPANY_SETTINGS' },
  { label: 'AI Configuration', value: 'AI_CONFIGURATION' },
  { label: 'Project Timeline', value: 'PROJECT_TIMELINE_EVENT' },
]

interface AuditLogRow {
  [key: string]: unknown
  id: string
  entityType: string
  entityId: string
  eventLabel: string
  changedBy: string
  changedAt: string
  reason: string
}

const TABLE_COLUMNS: SmartTableColumn<AuditLogRow>[] = [
  { key: 'eventLabel', label: 'Event' },
  { key: 'entityType', label: 'Entity Type' },
  { key: 'entityId', label: 'Entity ID' },
  { key: 'changedBy', label: 'Changed By' },
  { key: 'changedAt', label: 'Changed At' },
  { key: 'reason', label: 'Reason' },
]

const tableRows = computed<AuditLogRow[]>(() =>
  auditLogStore.logs.map((log) => ({
    id: log.id,
    entityType: log.entityType,
    entityId: log.entityId,
    eventLabel: log.eventLabel,
    changedBy: log.changedBy,
    changedAt: log.changedAt,
    reason: log.reason ?? '—',
  })),
)

function loadData(): void {
  void auditLogStore.loadLogs()
}

onMounted(loadData)

async function handleExport(): Promise<void> {
  try {
    await auditLogStore.exportCsv()
  } catch {
    toastStore.show('error', 'Export failed', 'Unable to export the audit log. Please try again.')
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader title="Audit Log" subtitle="A record of every tracked change across the system, who made it, and when.">
      <template #actions>
        <BaseButton :icon="Download" variant="secondary" @click="handleExport">Export CSV</BaseButton>
      </template>
    </PageHeader>

    <div class="flex items-center justify-between rounded-xl border border-border-light bg-bg-card p-4">
      <div class="w-56">
        <SelectBox
          :model-value="auditLogStore.entityTypeFilter"
          :options="ENTITY_TYPE_OPTIONS"
          @update:model-value="auditLogStore.setEntityTypeFilter($event as string)"
        />
      </div>
      <BaseButton v-if="auditLogStore.entityTypeFilter !== 'All'" variant="ghost" size="sm" @click="auditLogStore.setEntityTypeFilter('All')">
        Clear filter
      </BaseButton>
    </div>

    <ErrorState v-if="auditLogStore.error" :description="auditLogStore.error" @retry="loadData" />

    <template v-else>
      <SmartTable
        :columns="TABLE_COLUMNS"
        :rows="tableRows"
        row-key="id"
        :loading="auditLogStore.isLoading"
        :searchable="false"
        :paginated="false"
        empty-title="No audit events found"
        empty-description="Try a different entity type filter, or check back once more changes have been made."
      >
        <template #cell-entityType="{ value }">
          <StatusBadge :label="(value as string).replace(/_/g, ' ')" variant="info" />
        </template>
        <template #cell-changedAt="{ value }">
          {{ formatDateTime(value as string) }}
        </template>
      </SmartTable>
      <div class="rounded-xl border border-border-light bg-bg-card">
        <TablePagination
          :current-page="auditLogStore.pagination.page"
          :total-pages="auditLogStore.pagination.totalPages"
          :total-items="auditLogStore.pagination.total"
          :start-index="(auditLogStore.pagination.page - 1) * auditLogStore.pagination.pageSize"
          :end-index="Math.min(auditLogStore.pagination.page * auditLogStore.pagination.pageSize, auditLogStore.pagination.total)"
          :page-size="auditLogStore.pagination.pageSize"
          :page-size-options="[25, 50, 100]"
          @page-change="auditLogStore.setPage"
          @page-size-change="auditLogStore.setPageSize"
        />
      </div>
    </template>
  </div>
</template>
