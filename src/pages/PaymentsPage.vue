<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import ErrorState from '@/components/common/ErrorState.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import InfoPanel from '@/components/common/InfoPanel.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { usePaymentStore } from '@/stores/paymentStore'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import { getObligationStatusVariant } from '@/utils/paymentHelpers'
import type { ObligationStatus } from '@/types/Payment'
import type { SmartTableColumn } from '@/types/Table'

const router = useRouter()
const store = usePaymentStore()

interface AgreementTableRow {
  [key: string]: unknown
  id: string
  projectId: string
  projectName: string
  clientName: string
  contractAmount: number
  totalReceived: number
  totalPending: number
  totalOverdue: number
  nextPaymentAmount: string
  nextPaymentDate: string
  nextPaymentStatus: string
}

const COLUMNS: SmartTableColumn<AgreementTableRow>[] = [
  { key: 'projectName', label: 'Project', sortable: true },
  { key: 'clientName', label: 'Client', sortable: true },
  { key: 'contractAmount', label: 'Contract Value', align: 'right', sortable: true },
  { key: 'totalReceived', label: 'Received', align: 'right', sortable: true },
  { key: 'totalPending', label: 'Pending', align: 'right', sortable: true },
  { key: 'totalOverdue', label: 'Overdue', align: 'right', sortable: true },
  { key: 'nextPaymentAmount', label: 'Next Payment', align: 'right' },
  { key: 'nextPaymentDate', label: 'Next Payment Date' },
  { key: 'nextPaymentStatus', label: 'Status' },
]

const rows = computed<AgreementTableRow[]>(() =>
  store.filteredAgreementRows.map(({ agreement, project, client, summary }) => {
    const nextPaymentStatus: ObligationStatus = !summary.nextPaymentObligation ? 'Paid' : summary.nextPaymentIsOverdue ? 'Overdue' : 'Scheduled'
    return {
      id: agreement.id,
      projectId: agreement.projectId,
      projectName: project?.projectName ?? 'Unknown Project',
      clientName: client?.companyName ?? 'Unknown Client',
      contractAmount: summary.contractAmount,
      totalReceived: summary.totalReceived,
      totalPending: summary.totalPending,
      totalOverdue: summary.totalOverdue,
      nextPaymentAmount: summary.nextPaymentObligation
        ? formatCurrency(summary.nextPaymentObligation.amountDue - summary.nextPaymentObligation.amountReceived, agreement.currency)
        : '—',
      nextPaymentDate: summary.nextPaymentObligation ? formatDate(summary.nextPaymentObligation.dueDate) : '—',
      nextPaymentStatus,
    }
  }),
)

function goToProjectPayments(row: AgreementTableRow): void {
  router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId: row.projectId }, query: { tab: 'payments' } })
}

function loadData(): void {
  void store.loadAll()
}

onMounted(loadData)
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader title="Payments" subtitle="Contract values, collections, and outstanding balances across every project." />

    <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-4">
      <InfoPanel label="Total Contract Value" :value="formatCurrency(store.portfolioSummary.contractAmount, 'KWD')" color="primary" />
      <InfoPanel label="Total Received" :value="formatCurrency(store.portfolioSummary.totalReceived, 'KWD')" color="success" />
      <InfoPanel label="Total Pending" :value="formatCurrency(store.portfolioSummary.totalPending, 'KWD')" color="warning" />
      <InfoPanel label="Total Overdue" :value="formatCurrency(store.portfolioSummary.totalOverdue, 'KWD')" :color="store.portfolioSummary.totalOverdue > 0 ? 'danger' : 'neutral'" />
    </div>

    <FilterBar
      :search-value="store.searchTerm"
      search-placeholder="Search by project or client"
      :has-active-filters="store.searchTerm.trim().length > 0"
      @update:search-value="store.setSearchTerm"
      @clear="store.setSearchTerm('')"
    />

    <ErrorState v-if="store.error" :description="store.error" @retry="loadData" />

    <SmartTable
      v-else
      :columns="COLUMNS"
      :rows="rows"
      row-key="id"
      :loading="store.isLoading"
      :searchable="false"
      empty-title="No financial agreements yet"
      empty-description="Financial agreements created from a project's Payments tab will appear here."
      @row-click="goToProjectPayments"
    >
      <template #cell-contractAmount="{ row, value }">
        {{ formatCurrency(value as number, store.getAgreementByProject((row as AgreementTableRow).projectId)?.currency ?? 'KWD') }}
      </template>
      <template #cell-totalReceived="{ row, value }">
        {{ formatCurrency(value as number, store.getAgreementByProject((row as AgreementTableRow).projectId)?.currency ?? 'KWD') }}
      </template>
      <template #cell-totalPending="{ row, value }">
        {{ formatCurrency(value as number, store.getAgreementByProject((row as AgreementTableRow).projectId)?.currency ?? 'KWD') }}
      </template>
      <template #cell-totalOverdue="{ row, value }">
        <span :class="(value as number) > 0 ? 'font-semibold text-danger-600' : ''">
          {{ formatCurrency(value as number, store.getAgreementByProject((row as AgreementTableRow).projectId)?.currency ?? 'KWD') }}
        </span>
      </template>
      <template #cell-nextPaymentAmount="{ row }">
        <span :class="(row as AgreementTableRow).nextPaymentStatus === 'Overdue' ? 'font-semibold text-danger-600' : ''">
          {{ (row as AgreementTableRow).nextPaymentAmount }}
        </span>
      </template>
      <template #cell-nextPaymentDate="{ row }">
        <span :class="(row as AgreementTableRow).nextPaymentStatus === 'Overdue' ? 'font-semibold text-danger-600' : ''">
          {{ (row as AgreementTableRow).nextPaymentDate }}
        </span>
      </template>
      <template #cell-nextPaymentStatus="{ value }">
        <StatusBadge :label="value as string" :variant="getObligationStatusVariant(value as ObligationStatus)" />
      </template>
    </SmartTable>
  </div>
</template>
